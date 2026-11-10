from __future__ import annotations

import logging
import time
import uuid

from backend.modeling import ABSTAIN, cited_sources
from backend.settings import config, utcnow
from backend.source_attribution import VERBATIM_CITATIONS, citation_policy, verbatim_source_label

log = logging.getLogger(__name__)


def infer_record(engine, row: dict, *, track: str, experiment: str, retriever=None):
    start = time.perf_counter()
    selected = config("model_config")
    rag = experiment in {"C","D"}
    output = {"question_id":row["benchmark_id"],"language":row["language"],"context":row["context"],
              "question":row["question"],"reference_answer":row["reference_answer"],
              "reference_answers":row.get("reference_answers",[row["reference_answer"]]),
              "answerable":row.get("answerable",True),"source_dataset":row["source_dataset"],
              "relevant_document_ids":row.get("relevant_document_ids",[]),
              "source_document_id":row.get("source_document_id"),
              "model_configuration":experiment,"model_id":selected["model_id"],"model_revision":selected["revision"],
              "prompt_version":selected["prompt_version"],"generation_settings":selected["generation"],
              "retrieval_enabled":rag,"retrieved":[],"retrieval_seconds":0.0,"generation_seconds":0.0,
              "input_tokens":0,"output_tokens":0,"abstained":False,"citations":[],"created_at":utcnow()}
    try:
        if rag:
            policy = citation_policy(getattr(retriever, "settings", {}))
            output["citation_policy"] = policy
            hits,duration = retriever.query(row["question"])
            evidence, used = retriever.context(hits)
            output.update(retrieved=hits,retrieval_seconds=duration,context=evidence,
                          context_document_ids=[h["source_document_id"] for h in used])
            if not evidence:
                output.update(generated_answer=ABSTAIN[row["language"]],raw_generated_answer="[ABSTAIN]",
                              abstained=True,abstention_reason="insufficient_verified_retrieval")
            else:
                output.update(engine.generate(row["question"],evidence,row["language"],citations=True))
                citations,unknown = cited_sources(output["generated_answer"],used)
                if not output["abstained"] and not unknown and not citations and policy == VERBATIM_CITATIONS:
                    label = verbatim_source_label(output["generated_answer"], used)
                    if label:
                        output["generated_answer"] = output["generated_answer"].rstrip() + f" [{label}]"
                        citations, unknown = cited_sources(output["generated_answer"], used)
                        output["citation_origin"] = "verbatim_source_attribution"
                if not output["abstained"] and (unknown or not citations):
                    output.update(generated_answer=ABSTAIN[row["language"]],abstained=True,
                                  abstention_reason="invalid_or_missing_source_citation",rejected_source_labels=unknown)
                else:
                    output["citations"] = citations
                    if citations:
                        output.setdefault("citation_origin", "model_emitted")
        else:
            output.update(engine.generate(row["question"],row["context"] if track == "benchmark" else "",
                                         row["language"],closed_book=track == "campus"))
        output["evaluation_status"] = "completed"
    except Exception as exc:
        log.exception("Inference failed for %s",row["benchmark_id"])
        output.update(evaluation_status="failed",error=str(exc),generated_answer="")
    output["total_seconds"] = time.perf_counter()-start
    return output


def infer_benchmark_batch(engine,rows,*,experiment):
    start = time.perf_counter()
    batch_id = str(uuid.uuid4())
    answers,generation_seconds = engine.generate_batch(rows)
    if len(answers)!=len(rows):
        raise ValueError('The engine returned a different number of batch answers')
    class RecordedAnswer:
        def __init__(self,answer):
            self.answer=answer
        def generate(self,*args,**kwargs):
            return self.answer
    # Reuse the exact single-record metadata schema; generation has already been measured once.
    predictions = [infer_record(RecordedAnswer(answer),row,track='benchmark',experiment=experiment)
                   for row,answer in zip(rows,answers)]
    elapsed = time.perf_counter()-start
    for prediction in predictions:
        prediction.update(total_seconds=elapsed,generation_batch_id=batch_id,generation_batch_seconds=generation_seconds,
                          batch_size=len(rows),latency_condition='simultaneously submitted batch; response completes with batch')
    return predictions
