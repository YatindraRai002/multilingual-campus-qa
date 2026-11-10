from __future__ import annotations

import json
import time
import uuid
from collections import Counter

from backend.datasets import current_manifest, ensure_no_leakage, load_split
from backend.db import Database
from backend.hardware import audit, readiness
from backend.modeling import PrerequisiteError, messages
from backend.settings import ROOT, config, digest, model_directory, read_json, utcnow, write_json


def encode_answer(tokenizer, row, max_length, *, empty_evidence=False):
    """Use the official chat template and supervise assistant tokens only."""
    prompt = messages(row["question"],"" if empty_evidence else row["context"],row["language"])
    answer = "[ABSTAIN]" if empty_evidence or not row["answerable"] else row["reference_answer"]
    prefix = tokenizer.apply_chat_template(prompt,tokenize=True,add_generation_prompt=True)
    complete = tokenizer.apply_chat_template(prompt+[{"role":"assistant","content":answer}],tokenize=True,add_generation_prompt=False)
    if len(complete) > max_length:
        return None
    if complete[:len(prefix)] != prefix:
        raise ValueError("Official chat-template prefix mismatch; answer-only masking would be unsafe.")
    return {"input_ids":complete,"attention_mask":[1]*len(complete),"labels":[-100]*len(prefix)+complete[len(prefix):]}


def balanced_indices(rows, eligible, limit, languages, seed):
    by_language = {language:[i for i in eligible if rows[i]['language'] == language] for language in languages}
    selected_count = min([limit]+[len(indices) for indices in by_language.values()])
    if not selected_count:
        raise PrerequisiteError('Every required language needs usable train AND validation examples after token-length filtering.')
    return [i for language in sorted(by_language) for i in sorted(by_language[language],key=lambda i:digest([seed,rows[i]['benchmark_id']]))[:selected_count]]


def abstention_indices(rows,selected,seed,fraction):
    """Sample augmentation independently of the low-hash training selection budget."""
    if not 0 <= fraction <= 1:
        raise ValueError('Abstention augmentation fraction must be between zero and one')
    return [i for i in selected if int(digest(['empty-evidence-augmentation',seed,rows[i]['benchmark_id']])[:8],16)/16**8 < fraction]


def supervised_causal_loss(model, inputs, *, num_items_in_batch=None):
    """Exact masked causal CE, projecting only supervised next-token positions."""
    import torch
    import torch.nn.functional as functional
    labels = inputs['labels']
    positions = torch.where((labels[:,1:] != -100).any(dim=0))[0]
    if not positions.numel():
        raise ValueError('A training batch has no supervised assistant tokens')
    outputs = model(**{key:value for key,value in inputs.items() if key != 'labels'},
                    logits_to_keep=positions,use_cache=False)
    targets = labels[:,positions+1]
    denominator = num_items_in_batch if num_items_in_batch is not None else (targets != -100).sum()
    loss = functional.cross_entropy(outputs.logits.float().reshape(-1,outputs.logits.shape[-1]),
                                    targets.reshape(-1),ignore_index=-100,reduction='sum')/denominator
    return loss,outputs


def preflight(db: Database | None = None):
    db = db or Database()
    hardware = audit(check_torch=True)
    ready = readiness(hardware, training=True)
    blockers = ready["blockers"][:]
    manifest = current_manifest()
    model = config("model_config")
    if not manifest:
        blockers.append("Benchmark has not been acquired and prepared.")
    else:
        if manifest["training_languages_missing"]:
            blockers.append("Independent licensed training records missing for: " + ", ".join(manifest["training_languages_missing"]) + ". IndicQA is test-only and cannot be used for training.")
        baseline = [r for r in db.runs() if r["track"] == "benchmark" and r["experiment"] == "A" and
                    r["status"] == "completed" and r["dataset_version"] == manifest["version"] and
                    r["configuration"]["model_revision"] == model.get("revision") and
                    r["configuration"].get("generation") == model["generation"] and
                    r["configuration"].get("prompt_version") == model["prompt_version"] and
                    r["configuration"].get("limit_per_language") is None]
        if not baseline:
            blockers.append("Complete the original-model baseline on the full sealed benchmark before fine-tuning.")
    if not model.get("revision"):
        blockers.append("Official model revision has not been resolved.")
    return {"ready": not blockers, "blockers": blockers, "hardware": hardware,
            "dataset_version": manifest["version"] if manifest else None, "configuration": config("training")}


def train():
    database = Database()
    checked = preflight(database)
    if not checked["ready"]:
        raise PrerequisiteError("\n".join(checked["blockers"]))
    import torch
    from torch.utils.data import Dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, Trainer, TrainerCallback, TrainingArguments, DataCollatorForSeq2Seq, set_seed

    settings, model_settings = config("training"), config("model_config")
    set_seed(settings["seed"])  # Seed before creating LoRA parameters, not only when Trainer is initialized.
    train_rows, validation_rows, test_rows = (load_split(name) for name in ["train", "validation", "test"])
    ensure_no_leakage(train_rows, validation_rows, test_rows)
    del test_rows  # test labels are never used by the trainer or checkpoint selection
    training_id = str(uuid.uuid4())
    output = model_directory() / "training" / training_id
    adapter_path = model_directory() / "lora_adapter" / training_id
    logs_path = ROOT / "results" / "training" / training_id
    logs_path.mkdir(parents=True, exist_ok=False)
    payload = {"training_id": training_id, "model_id": model_settings["model_id"], "model_revision": model_settings["revision"],
               "dataset_version": checked["dataset_version"], "configuration": settings, "hardware": checked["hardware"],
               "started_at": utcnow(), "training_counts": dict(Counter(r["language"] for r in train_rows)),
               "validation_counts": dict(Counter(r["language"] for r in validation_rows)), "status": "running"}
    database.create_training(training_id, payload)
    start = time.perf_counter()
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_settings["model_id"], revision=model_settings["revision"], trust_remote_code=False)
        tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token

        class AnswerDataset(Dataset):
            def __init__(self, rows, augment=False):
                self.rows = rows
                self.augment = augment
                self.augmentation_indices = []
                self.included = []
                self.dropped = Counter()
                for index in range(len(rows)):
                    sample = self.encode(index)
                    if sample is not None:
                        self.included.append(index)
                    else:
                        row = self.rows[index if index < len(self.rows) else self.augmentation_indices[index-len(self.rows)]]
                        self.dropped[row["language"]] += 1
                if settings.get('language_balanced_selection'):
                    limit = settings['maximum_training_examples_per_language' if augment else 'maximum_validation_examples_per_language']
                    self.included = balanced_indices(rows,self.included,limit,settings['required_training_languages'],settings['seed'])
                if augment and settings['abstention_augmentation']:
                    self.augmentation_indices = abstention_indices(rows,self.included,settings['seed'],settings['abstention_fraction'])
                    self.included += [len(rows)+index for index in range(len(self.augmentation_indices)) if self.encode(len(rows)+index) is not None]

            def __len__(self):
                return len(self.included)

            def encode(self, index):
                synthetic_abstention = index >= len(self.rows)
                row = self.rows[index if not synthetic_abstention else self.augmentation_indices[index-len(self.rows)]]
                # Training-only empty-evidence augmentation is derived exclusively from train rows.
                return encode_answer(tokenizer,row,settings["max_sequence_length"],empty_evidence=synthetic_abstention)

            def __getitem__(self, index):
                return self.encode(self.included[index])

        train_data, validation_data = AnswerDataset(train_rows, True), AnswerDataset(validation_rows)
        if not len(train_data) or not len(validation_data):
            raise PrerequisiteError("No usable training/validation records fit the sequence length.")
        payload["used_training_counts"] = dict(Counter(train_rows[i]["language"] for i in train_data.included if i < len(train_rows)))
        payload["training_abstention_augmentation_count"] = sum(i >= len(train_rows) for i in train_data.included)
        payload['training_abstention_augmentation_by_language'] = dict(Counter(train_rows[train_data.augmentation_indices[i-len(train_rows)]]['language'] for i in train_data.included if i >= len(train_rows)))
        payload['used_validation_counts'] = dict(Counter(validation_rows[i]['language'] for i in validation_data.included))
        payload["dropped_overlength_training_counts"] = dict(train_data.dropped)
        payload["dropped_overlength_validation_counts"] = dict(validation_data.dropped)
        selection = {'dataset_version':checked['dataset_version'],
            'training':[{'benchmark_id':train_rows[i if i < len(train_rows) else train_data.augmentation_indices[i-len(train_rows)]]['benchmark_id'],
                         'empty_evidence_augmentation':i >= len(train_rows)} for i in train_data.included],
            'validation':[validation_rows[i]['benchmark_id'] for i in validation_data.included],
            'seed':settings['seed']}
        write_json(logs_path/'selection.json',selection,exclusive=True)
        payload['selection_sha256'] = digest(selection)
        payload['selection_manifest'] = (logs_path/'selection.json').relative_to(ROOT).as_posix()
        database.update_training_payload(training_id,payload)
        database.training_event(training_id,{'event':'dataset_prepared','used_training_counts':payload['used_training_counts'],
                   'used_validation_counts':payload['used_validation_counts'],
                   'augmentation_by_language':payload['training_abstention_augmentation_by_language']})
        if set(settings["required_training_languages"]) - set(payload["used_training_counts"]):
            raise PrerequisiteError("Sequence-length filtering removed every example in a required language.")
        quant = BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.float16)
        from backend.attention import register_attention
        register_attention(model_settings['attention_implementation'])
        model = AutoModelForCausalLM.from_pretrained(model_settings["model_id"], revision=model_settings["revision"],
                   quantization_config=quant, device_map={"": 0}, torch_dtype=torch.float16, trust_remote_code=False,
                   attn_implementation=model_settings['attention_implementation'])
        model.config.use_cache = False
        model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=settings["gradient_checkpointing"])
        model = get_peft_model(model, LoraConfig(r=settings["lora_rank"],lora_alpha=settings["lora_alpha"],
                    lora_dropout=settings["lora_dropout"], target_modules=settings["target_modules"],
                    bias="none", task_type="CAUSAL_LM"))

        class Monitor(TrainerCallback):
            def on_train_begin(self, args, state, control, **kwargs):
                payload.update(total_optimizer_steps=state.max_steps, training_examples_including_augmentation=len(train_data),
                               validation_examples=len(validation_data))
                database.update_training_payload(training_id,payload)

            def on_log(self, args, state, control, logs=None, **kwargs):
                event = {**(logs or {}), "step": state.global_step, "epoch": state.epoch,
                         "total_optimizer_steps": state.max_steps,
                         "elapsed_seconds": time.perf_counter()-start,
                         "gpu_peak_allocated_gib": torch.cuda.max_memory_allocated()/2**30}
                database.training_event(training_id, event)
                with (logs_path/"events.jsonl").open("a",encoding="utf-8") as stream:
                    stream.write(json.dumps(event)+"\n")

        args = TrainingArguments(output_dir=str(output), num_train_epochs=settings["epochs"],
                per_device_train_batch_size=settings["batch_size"], per_device_eval_batch_size=1,
                gradient_accumulation_steps=settings["gradient_accumulation_steps"], learning_rate=settings["learning_rate"],
                warmup_ratio=settings["warmup_ratio"],weight_decay=settings["weight_decay"],fp16=True,bf16=False,
                gradient_checkpointing=settings["gradient_checkpointing"], optim=settings["optimizer"],
                eval_strategy="steps", eval_steps=settings["evaluation_steps"],save_strategy="steps",save_steps=settings["save_steps"],
                logging_steps=1,load_best_model_at_end=True,metric_for_best_model="eval_loss",greater_is_better=False,
                save_total_limit=2,seed=settings["seed"],data_seed=settings["seed"],report_to=[],dataloader_num_workers=0)
        class AnswerTrainer(Trainer):
            def compute_loss(self,model,inputs,return_outputs=False,num_items_in_batch=None):
                loss,outputs = supervised_causal_loss(model,inputs,num_items_in_batch=num_items_in_batch)
                return (loss,outputs) if return_outputs else loss

        trainer_class = AnswerTrainer if settings.get('supervised_logits_only') else Trainer
        trainer = trainer_class(model=model,args=args,train_dataset=train_data,eval_dataset=validation_data,
                    data_collator=DataCollatorForSeq2Seq(tokenizer,padding=True,label_pad_token_id=-100), callbacks=[Monitor()])
        trainer.train()
        if trainer.state.best_model_checkpoint is None:
            raise PrerequisiteError("No validation-selected checkpoint exists. Reduce evaluation/save steps for a deliberately small pilot.")
        adapter_path.mkdir(parents=True,exist_ok=False)
        trainer.model.save_pretrained(adapter_path, safe_serialization=True)
        tokenizer.save_pretrained(adapter_path)
        from backend.artifacts import tree_fingerprint
        payload.update(status="completed", ended_at=utcnow(),duration_seconds=time.perf_counter()-start,
                       best_checkpoint=trainer.state.best_model_checkpoint, best_validation_loss=trainer.state.best_metric,
                       adapter_path=adapter_path.relative_to(ROOT).as_posix(), adapter_revision=tree_fingerprint(adapter_path),
                       peak_gpu_memory_gib=torch.cuda.max_memory_allocated()/2**30)
        write_json(adapter_path/"training_manifest.json", payload, exclusive=True)
        write_json(adapter_path.parent/"current.json", payload)
        database.register_adapter(payload["adapter_revision"], payload)
        database.finish_training(training_id,"completed",payload)
        write_json(logs_path/"summary.json",payload,exclusive=True)
        (ROOT/"docs"/"LORA_TRAINING_REPORT.md").write_text("# LoRA training report\n\n```json\n"+json.dumps(payload,indent=2)+"\n```\n",encoding="utf-8")
        return payload
    except Exception as exc:
        payload.update(status="failed",error=str(exc),ended_at=utcnow(),duration_seconds=time.perf_counter()-start)
        database.finish_training(training_id,"failed",payload)
        write_json(logs_path/"summary.json",payload,exclusive=True)
        raise
