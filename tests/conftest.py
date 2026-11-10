import pytest

from backend.db import Database


@pytest.fixture
def database(tmp_path):
    return Database(tmp_path/"isolated-fixtures.sqlite3")


@pytest.fixture
def prediction():
    return {"question_id":"unit-test-only","language":"en","context":"The library is open.",
            "question":"What is open?","reference_answer":"the library","reference_answers":["the library"],
            "generated_answer":"library","source_dataset":"unit-fixture-not-research","source_document_id":"fixture-doc",
            "answerable":True,"abstained":False,"evaluation_status":"completed","input_tokens":20,"output_tokens":10,
            "generation_seconds":1.0,"retrieval_seconds":.1,"total_seconds":1.2,
            "retrieval_enabled":False,"retrieved":[],"relevant_document_ids":[]}
