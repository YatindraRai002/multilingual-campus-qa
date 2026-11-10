"""Real approved-model memory/gradient preflight; never saved as a research run or adapter."""
import gc
import json
import time

from backend.datasets import load_split
from backend.experiments import gpu_lock
from backend.modeling import QwenEngine
from backend.settings import ROOT, config, utcnow, write_json
from backend.training import encode_answer, supervised_causal_loss

import torch
from peft import LoraConfig,get_peft_model,prepare_model_for_kbit_training
from bitsandbytes.optim import PagedAdamW8bit

settings = config('training')
selected = config('model_config')
with gpu_lock().acquire(timeout=0):
    dedicated_budget = torch.cuda.mem_get_info()[0]/2**30-.1
    engine = QwenEngine()
    torch.cuda.reset_peak_memory_stats()
    inference_started = time.perf_counter()
    long_input = torch.full((1,selected['max_input_tokens']),100,device='cuda',dtype=torch.long)
    with torch.inference_mode():
        engine.model.generate(input_ids=long_input,attention_mask=torch.ones_like(long_input),max_new_tokens=1,
                              do_sample=False,pad_token_id=engine.tokenizer.pad_token_id)
    torch.cuda.synchronize()
    inference_peak = torch.cuda.max_memory_allocated()/2**30
    inference_seconds = time.perf_counter()-inference_started
    del long_input
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    batch_input = torch.full((selected.get('evaluation_batch_size',1),1024),100,device='cuda',dtype=torch.long)
    with torch.inference_mode():
        engine.model.generate(input_ids=batch_input,attention_mask=torch.ones_like(batch_input),max_new_tokens=1,
                              do_sample=False,pad_token_id=engine.tokenizer.pad_token_id)
    torch.cuda.synchronize()
    batch_peak = torch.cuda.max_memory_allocated()/2**30
    del batch_input
    gc.collect()
    torch.cuda.empty_cache()
    rows = load_split('train')
    samples = []
    for language in ['en','hi','ta']:
        for row in rows:
            if row['language'] == language:
                sample = encode_answer(engine.tokenizer,row,settings['max_sequence_length'])
                if sample is not None:
                    samples.append(sample)
                    break
    assert len(samples) == 3,'No usable training sample in every target language'
    del rows
    gc.collect()
    model = prepare_model_for_kbit_training(engine.model,use_gradient_checkpointing=True)
    model.config.use_cache = False
    model = get_peft_model(model,LoraConfig(r=settings['lora_rank'],lora_alpha=settings['lora_alpha'],
                 lora_dropout=settings['lora_dropout'],target_modules=settings['target_modules'],bias='none',task_type='CAUSAL_LM'))
    model.train()
    optimizer = PagedAdamW8bit([p for p in model.parameters() if p.requires_grad],lr=settings['learning_rate'])
    scaler = torch.amp.GradScaler('cuda')
    steps = []
    for sample in samples:
        padding = settings['max_sequence_length']-len(sample['input_ids'])
        inputs = {key:torch.tensor([value+([engine.tokenizer.pad_token_id] if key=='input_ids' else [-100] if key=='labels' else [0])*padding],device='cuda') for key,value in sample.items()}
        torch.cuda.reset_peak_memory_stats()
        started = time.perf_counter()
        optimizer.zero_grad(set_to_none=True)
        with torch.autocast('cuda',dtype=torch.float16):
            loss,_ = supervised_causal_loss(model,inputs)
        assert torch.isfinite(loss),'Non-finite local preflight loss'
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        torch.cuda.synchronize()
        steps.append({'loss':loss.item(),'duration_seconds':time.perf_counter()-started,
                      'peak_allocated_gib':torch.cuda.max_memory_allocated()/2**30,
                      'sequence_tensor_length':settings['max_sequence_length']})
        del inputs,loss
    within_budget = max(inference_peak,batch_peak,*[step['peak_allocated_gib'] for step in steps])<=dedicated_budget
    result = {'status':'passed' if within_budget else 'shared_memory_required','checked_at':utcnow(),'model_id':selected['model_id'],'revision':selected['revision'],
              'device':torch.cuda.get_device_name(),'model_loading_seconds':engine.loading_seconds,
              'inference_probe_input_tokens':selected['max_input_tokens'],'inference_peak_allocated_gib':inference_peak,
              'batched_inference_peak_allocated_gib':batch_peak,'dedicated_memory_budget_gib':dedicated_budget,
              'within_dedicated_memory_budget':within_budget,
              'inference_probe_seconds':inference_seconds,'training_steps':steps,
              'source':'original training split only; one sample per language; padded capacity tensors',
              'research_run':False,'adapter_saved':False,'training_configuration':settings}
    write_json(ROOT/'results'/'local_model_preflight.json',result)
    print(json.dumps(result,indent=2),flush=True)
    if not within_budget:
        raise RuntimeError('The selected worst-case capacity exceeds the dedicated-memory budget')
