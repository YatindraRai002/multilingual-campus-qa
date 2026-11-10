import sqlite3

import pytest

from backend.db import Database
from backend.evaluation.evaluation_runner import evaluate_predictions


def make_run(database,**changes):
    return database.create_run(track="benchmark",experiment="A",dataset_version="fixture-v1",
            evaluation_fingerprint="fixture-fingerprint",configuration={"generation":{},"model_revision":"test-only"},total=1,**changes)


def test_predictions_and_metrics_survive_reopening(database,prediction):
    run_id = make_run(database)
    database.transition(run_id,"running")
    prediction_id = database.add_prediction(run_id,prediction)
    calculated = evaluate_predictions(database.predictions(run_id))
    database.store_metrics(run_id,calculated)
    database.transition(run_id,"completed")
    reopened = Database(database.path)
    assert reopened.run(run_id)["completed"] == 1
    assert reopened.predictions(run_id)[0]["prediction_id"] == prediction_id
    assert reopened.metrics(run_id)["populations"] == calculated["populations"]
    with pytest.raises(ValueError):
        reopened.add_prediction(run_id,prediction)


def test_history_is_append_only(database,prediction):
    first,second = make_run(database),make_run(database)
    assert first != second
    database.transition(first,"running")
    prediction_id = database.add_prediction(first,prediction)
    with pytest.raises(sqlite3.IntegrityError):
        database.add_prediction(first,prediction)
    database.annotate(prediction_id,"reviewer",{"correct":False,"claims":[]})
    database.annotate(prediction_id,"reviewer",{"correct":True,"claims":[]})
    assert database.predictions(first)[0]["annotation"]["correct"] is True
    with database.connect() as connection:
        assert connection.execute("SELECT count(*) FROM annotations").fetchone()[0] == 2
    assert database.run(second)["completed"] == 0


def test_terminal_status_cannot_be_overwritten(database):
    run_id = make_run(database)
    database.transition(run_id,"failed",error="fixture")
    with pytest.raises(ValueError):
        database.transition(run_id,"running")
