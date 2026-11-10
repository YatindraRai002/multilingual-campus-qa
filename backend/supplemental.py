"""Explicitly approved IndicSQuAD training extension; IndicQA remains sealed evaluation data."""
from __future__ import annotations

import hashlib
import heapq
from collections import Counter
from pathlib import Path

import httpx

from backend.settings import ROOT, config, digest, read_json, utcnow, write_json


def acquire_supplemental():
    settings = config('benchmark')['supplemental_training']
    if not settings['enabled'] or not settings['user_approved']:
        return []
    base = ROOT/'data'/'benchmark'/'raw'/'indicsquad'/settings['revision']
    files = []
    with httpx.Client(timeout=180,follow_redirects=True) as client:
        for filename in ['README.md','Hindi/train.json','Tamil/train.json']:
            destination = base/filename
            destination.parent.mkdir(parents=True,exist_ok=True)
            url = f"https://huggingface.co/datasets/{settings['dataset_id']}/resolve/{settings['revision']}/{filename}"
            if not destination.exists():
                partial = destination.with_suffix(destination.suffix+'.part')
                with client.stream('GET',url) as response:
                    response.raise_for_status()
                    with partial.open('wb') as stream:
                        for chunk in response.iter_bytes(1024*1024):
                            stream.write(chunk)
                # Only complete downloads become immutable originals.
                partial.replace(destination)
            checksum = hashlib.sha256()
            with destination.open('rb') as stream:
                for chunk in iter(lambda:stream.read(1024*1024),b''):
                    checksum.update(chunk)
            files.append({'url':url,'path':destination.relative_to(ROOT).as_posix(),
                          'bytes':destination.stat().st_size,'sha256':checksum.hexdigest()})
    return files


def prepare_supplemental(english_training):
    import ijson
    from backend.datasets import canonical, identify_language, normalize
    settings = config('benchmark').get('supplemental_training',{})
    if not settings.get('enabled'):
        return [],None
    if not settings.get('user_approved'):
        raise ValueError('Supplemental training extension has not been approved')
    # Use only IDs mapped to the original ENGLISH TRAINING set. Unknown IDs, including
    # SQuAD 2.0-only and any held-out development IDs, never enter this extension.
    original = {r['original_source_id']:r for r in english_training}
    records,statistics = [],{}
    for language,directory in [('hi','Hindi'),('ta','Tamil')]:
        source = ROOT/'data'/'benchmark'/'raw'/'indicsquad'/settings['revision']/directory/'train.json'
        if not source.exists():
            raise ValueError('Acquire the approved IndicSQuAD training files first')
        counts,heap,seen = Counter(),[],set()
        with source.open('rb') as stream:
            for raw in ijson.items(stream,'item'):
                counts['original_training_rows'] += 1
                original_id = str(raw['id'])
                if original_id not in original:
                    counts['excluded_unmapped_original_training_id'] += 1
                    continue
                if original_id in seen:
                    counts['duplicate_original_id'] += 1
                    continue
                seen.add(original_id)
                context,question = normalize(raw['context']),normalize(raw['question'])
                answers = [normalize(text) for text in raw.get('answers',{}).get('text',[]) if normalize(text)]
                if not context or not question or not answers:
                    counts['excluded_empty_or_unanswerable_translation'] += 1
                    continue
                if identify_language(question) != language:
                    counts['excluded_script_mismatch'] += 1
                    continue
                if identify_language(context) != language:
                    counts['excluded_context_script_mismatch'] += 1
                    continue
                if not any(canonical(answer) in canonical(context) for answer in answers):
                    counts['excluded_answer_not_in_context'] += 1
                    continue
                counts['eligible_mapped_training_rows'] += 1
                mapped = original[original_id]
                row = {'benchmark_id':f"{settings['dataset_id']}:{language}:{original_id}",
                       'source_dataset':settings['dataset_id'],'language':language,'context':context,'question':question,
                       'reference_answer':answers[0],'reference_answers':answers,'answer_type':'extractive','answerable':True,
                       'original_source_id':original_id,'translation_status':'published_machine_translation_not_independently_human_verified',
                       'split':'train','original_split':'train','license':'cc-by-4.0; original SQuAD cc-by-sa-4.0 obligations retained',
                       'source_document_id':f"{settings['dataset_id']}:{language}:{raw['title']}",
                       'canonical_document_group':mapped['source_document_id'],
                       'canonical_question_group':'SQuAD:'+original_id,
                       'context_fingerprint':digest(canonical(context)),'question_fingerprint':digest(canonical(question)),
                       'validation_warnings':[],
                       'provenance':{'source_file':source.relative_to(ROOT).as_posix(),'revision':settings['revision'],
                                     'original_split':'train','original_english_id':original_id,
                                     'original_english_source':'SQuAD-v1.1 train',
                                     'original_english_context_sha256':mapped['context_fingerprint'],
                                     'mapping_method':'exact preserved SQuAD question identifier',
                                     'paper':'https://aclanthology.org/2025.paclic-1.70/',
                                     'license_card':'https://huggingface.co/datasets/l3cube-pune/indic-squad'}}
                priority = int(digest([settings['seed'],original_id]),16)
                entry = (-priority,original_id,row)
                if len(heap) < settings['maximum_records_per_language']:
                    heapq.heappush(heap,entry)
                elif priority < -heap[0][0]:
                    heapq.heapreplace(heap,entry)
        selected = [entry[2] for entry in sorted(heap,key=lambda entry:(-entry[0],entry[1]))]
        counts['selected_before_group_split'] = len(selected)
        counts['eligible_not_selected_by_budget'] = counts['eligible_mapped_training_rows']-len(selected)
        records += selected
        statistics[language] = dict(counts)
    report = {'dataset_id':settings['dataset_id'],'revision':settings['revision'],'approved_extension':True,
              'configuration':settings,'languages':statistics,'selection_uses_test_answers':False,
              'english_mapping':'original training ID only; no IndicQA English parallel mapping is asserted',
              'published_validation_and_test_files_used':False}
    write_json(ROOT/'data'/'benchmark'/'supplemental_report.json',report)
    return records,report
