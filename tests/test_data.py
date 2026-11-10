import copy

import pytest

from backend.datasets import (BENCHMARK, canonical, current_manifest, ensure_no_leakage,
                              group_split, identify_language, language_code, load_split, normalize)


@pytest.mark.parametrize("text,expected",[("Where is the library?","en"),("पुस्तकालय कहाँ है?","hi"),
                                           ("நூலகம் எங்கே உள்ளது?","ta"),("123?!",None)])
def test_language_routing(text,expected):
    assert identify_language(text) == expected


def test_language_alias_and_unicode():
    assert language_code("hin_Deva") == "hi"
    assert language_code("tam-Taml") == "ta"
    assert normalize("  தமிழ்\n நூலகம் ") == "தமிழ் நூலகம்"
    with pytest.raises(ValueError):
        language_code("fr")


def test_document_group_split():
    rows = [{"source_document_id":f"doc-{i//3}","question":str(i)} for i in range(100)]
    split = group_split(rows)
    mapping = {}
    for row in split:
        mapping.setdefault(row["source_document_id"],set()).add(row["split"])
    assert all(len(values) == 1 for values in mapping.values())
    assert group_split(rows) == split


def test_shared_context_is_leakage():
    row = {"benchmark_id":"a","source_document_id":"doc1","context_fingerprint":"context","question_fingerprint":"question1"}
    other = {**row,"benchmark_id":"b","source_document_id":"doc2","question_fingerprint":"question2"}
    with pytest.raises(ValueError,match="context_fingerprint"):
        ensure_no_leakage([row],[],[other])


def test_downloaded_splits_integrity_and_answerability():
    if not current_manifest():
        pytest.skip("Official benchmark not acquired in this checkout")
    manifest = current_manifest()
    train,validation,test = [load_split(split) for split in ["train","validation","test"]]
    ensure_no_leakage(train,validation,test)
    assert len(test) == manifest["splits"]["test"]["total"]
    assert manifest["test_records_removed"] == 0
    unanswerable = [r for r in test if r["provenance"].get("source_category") == "NO"]
    assert unanswerable and all(not row["answerable"] for row in unanswerable)
    assert all(row["reference_answer"] == "" for row in unanswerable)
    assert len({row["benchmark_id"] for row in test}) == len(test)
    assert all(row["split"] == "train" for row in train)
    assert not any(row["source_dataset"] == "ai4bharat/IndicQA" for row in train+validation)
    if manifest.get('supplemental_training'):
        from backend.settings import read_json
        original = read_json(BENCHMARK/'raw'/'squad'/'train-v1.1.json')
        english_ids = {str(qa['id']) for article in original['data'] for paragraph in article['paragraphs'] for qa in paragraph['qas']}
        supplement = [row for row in train+validation if row['source_dataset'] == 'l3cube-pune/indic-squad']
        assert {row['language'] for row in supplement} == {'hi','ta'}
        assert all(row['original_source_id'] in english_ids for row in supplement)
        assert all(row['canonical_question_group'] == 'SQuAD:'+row['original_source_id'] for row in supplement)
        assert manifest['training_languages_missing'] == []


def test_invalid_dataset_version_is_not_a_path():
    with pytest.raises(ValueError,match="Invalid dataset version"):
        load_split("test",version="../../private")
