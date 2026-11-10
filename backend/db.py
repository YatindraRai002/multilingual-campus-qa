from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from backend.settings import ROOT, utcnow

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS datasets(version TEXT PRIMARY KEY, manifest TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS models(model_id TEXT NOT NULL, revision TEXT NOT NULL, payload TEXT NOT NULL,
 PRIMARY KEY(model_id,revision));
CREATE TABLE IF NOT EXISTS adapters(revision TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs(
 run_id TEXT PRIMARY KEY, track TEXT NOT NULL, experiment TEXT NOT NULL,
 status TEXT NOT NULL, dataset_version TEXT NOT NULL, evaluation_fingerprint TEXT NOT NULL,
 configuration TEXT NOT NULL, created_at TEXT NOT NULL, ended_at TEXT,
 total INTEGER NOT NULL DEFAULT 0, completed INTEGER NOT NULL DEFAULT 0, error TEXT);
CREATE TABLE IF NOT EXISTS predictions(
 prediction_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
 question_id TEXT NOT NULL, language TEXT NOT NULL, payload TEXT NOT NULL,
 UNIQUE(run_id,question_id));
CREATE TABLE IF NOT EXISTS retrieval_results(
 run_id TEXT NOT NULL REFERENCES runs(run_id), prediction_id TEXT NOT NULL REFERENCES predictions(prediction_id),
 rank INTEGER NOT NULL, document_id TEXT NOT NULL, payload TEXT NOT NULL,
 PRIMARY KEY(prediction_id,rank));
CREATE TABLE IF NOT EXISTS annotations(
 annotation_id INTEGER PRIMARY KEY AUTOINCREMENT, prediction_id TEXT NOT NULL REFERENCES predictions(prediction_id),
 reviewer TEXT NOT NULL, created_at TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS metrics(
 metric_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL REFERENCES runs(run_id),
 computed_at TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS training_runs(
 training_id TEXT PRIMARY KEY, status TEXT NOT NULL, created_at TEXT NOT NULL,
 ended_at TEXT, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS training_logs(
 event_id INTEGER PRIMARY KEY AUTOINCREMENT, training_id TEXT NOT NULL REFERENCES training_runs(training_id),
 created_at TEXT NOT NULL, payload TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS predictions_run ON predictions(run_id);
CREATE INDEX IF NOT EXISTS annotations_prediction ON annotations(prediction_id,annotation_id);
CREATE INDEX IF NOT EXISTS metrics_run ON metrics(run_id,metric_id);
CREATE TABLE IF NOT EXISTS job_processes(run_id TEXT PRIMARY KEY REFERENCES runs(run_id),pid INTEGER NOT NULL,process_started REAL NOT NULL);
"""


class Database:
    def __init__(self, path: Path | None = None):
        self.path = path or ROOT / "data" / "research.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def register_dataset(self, manifest: dict):
        with self.connect() as connection:
            connection.execute("INSERT OR IGNORE INTO datasets VALUES (?,?,?)",
                               (manifest["version"], json.dumps(manifest), utcnow()))

    def register_model(self, payload: dict):
        with self.connect() as connection:
            connection.execute("INSERT OR IGNORE INTO models VALUES (?,?,?)",
                               (payload["model_id"], payload["revision"], json.dumps(payload)))

    def create_run(self, *, track: str, experiment: str, dataset_version: str,
                   evaluation_fingerprint: str, configuration: dict, total: int):
        run_id = str(uuid.uuid4())
        with self.connect() as connection:
            connection.execute("INSERT INTO runs(run_id,track,experiment,status,dataset_version,"
                               "evaluation_fingerprint,configuration,created_at,total) VALUES(?,?,?,?,?,?,?,?,?)",
                               (run_id, track, experiment, "queued", dataset_version, evaluation_fingerprint,
                                json.dumps(configuration), utcnow(), total))
        return run_id

    def transition(self, run_id: str, status: str, *, error=None):
        transitions = {"queued": {"running", "failed"}, "running": {"completed", "failed", "interrupted"}}
        with self.connect() as connection:
            row = connection.execute("SELECT status FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if not row or status not in transitions.get(row["status"], set()):
                raise ValueError("Invalid run status transition")
            connection.execute("UPDATE runs SET status=?,ended_at=?,error=? WHERE run_id=?",
                               (status, utcnow() if status in {"failed", "completed", "interrupted"} else None,
                                error, run_id))

    def recover_interrupted(self):
        import psutil
        with self.connect() as connection:
            rows = connection.execute("SELECT r.run_id,j.pid,j.process_started FROM runs r LEFT JOIN job_processes j ON r.run_id=j.run_id WHERE r.status IN ('queued','running')").fetchall()
            for row in rows:
                alive = False
                try:
                    alive = row["pid"] is not None and abs(psutil.Process(row["pid"]).create_time()-row["process_started"]) < 1
                except (psutil.Error,TypeError):
                    pass
                if not alive:
                    connection.execute("UPDATE runs SET status='interrupted',ended_at=?,error=? WHERE run_id=?",
                                       (utcnow(),"Worker exited before completion; create a new run to retry.",row["run_id"]))

    def register_worker(self, run_id, pid):
        import psutil
        with self.connect() as connection:
            connection.execute("INSERT INTO job_processes VALUES(?,?,?)",(run_id,pid,psutil.Process(pid).create_time()))

    def add_prediction(self, run_id: str, payload: dict):
        prediction_id = str(uuid.uuid4())
        with self.connect() as connection:
            row = connection.execute("SELECT status FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if not row or row["status"] != "running":
                raise ValueError("Predictions can only be appended to a running experiment")
            connection.execute("INSERT INTO predictions VALUES(?,?,?,?,?)",
                               (prediction_id, run_id, payload["question_id"], payload["language"], json.dumps(payload)))
            for rank, hit in enumerate(payload.get("retrieved", []), start=1):
                connection.execute("INSERT INTO retrieval_results VALUES(?,?,?,?,?)",
                                   (run_id, prediction_id, rank, hit["source_document_id"], json.dumps(hit)))
            connection.execute("UPDATE runs SET completed=completed+1 WHERE run_id=?", (run_id,))
        return prediction_id

    def run(self, run_id: str):
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if not row:
            return None
        result = dict(row)
        result["configuration"] = json.loads(result["configuration"])
        return result

    def runs(self, *, limit=100):
        with self.connect() as connection:
            ids = [r[0] for r in connection.execute("SELECT run_id FROM runs ORDER BY created_at DESC LIMIT ?", (limit,))]
        return [self.run(run_id) for run_id in ids]

    def predictions(self, run_id: str, *, offset=0, limit=100, language: str | None = None):
        clause = " AND p.language=?" if language else ""
        args = [run_id] + ([language] if language else []) + [limit, offset]
        with self.connect() as connection:
            rows = connection.execute("SELECT p.*,a.payload AS review,a.reviewer,a.created_at AS reviewed_at "
                                      "FROM predictions p LEFT JOIN annotations a ON a.annotation_id=("
                                      "SELECT MAX(a2.annotation_id) FROM annotations a2 WHERE a2.prediction_id=p.prediction_id) "
                                      "WHERE p.run_id=?" + clause + " ORDER BY p.rowid LIMIT ? OFFSET ?", args).fetchall()
        return [{**json.loads(row["payload"]), "prediction_id": row["prediction_id"],
                 "annotation": json.loads(row["review"]) if row["review"] else None,
                 "reviewer": row["reviewer"], "reviewed_at": row["reviewed_at"]} for row in rows]

    def annotate(self, prediction_id: str, reviewer: str, annotation: dict):
        with self.connect() as connection:
            row = connection.execute("SELECT run_id FROM predictions WHERE prediction_id=?", (prediction_id,)).fetchone()
            if not row:
                raise KeyError("Prediction not found")
            connection.execute("INSERT INTO annotations(prediction_id,reviewer,created_at,payload) VALUES(?,?,?,?)",
                               (prediction_id, reviewer, utcnow(), json.dumps(annotation)))
        return row["run_id"]

    def prediction(self, prediction_id: str):
        with self.connect() as connection:
            row = connection.execute("SELECT run_id,payload FROM predictions WHERE prediction_id=?",(prediction_id,)).fetchone()
        return {"run_id":row["run_id"],**json.loads(row["payload"])} if row else None

    def store_metrics(self, run_id: str, payload: dict):
        with self.connect() as connection:
            connection.execute("INSERT INTO metrics(run_id,computed_at,payload) VALUES(?,?,?)",
                               (run_id, utcnow(), json.dumps(payload)))

    def metrics(self, run_id: str):
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM metrics WHERE run_id=? ORDER BY metric_id DESC LIMIT 1", (run_id,)).fetchone()
        return {**json.loads(row["payload"]), "computed_at": row["computed_at"]} if row else None

    def training(self):
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM training_runs ORDER BY created_at DESC").fetchall()
            results = []
            for row in rows:
                logs = connection.execute("SELECT payload FROM training_logs WHERE training_id=? ORDER BY event_id", (row["training_id"],)).fetchall()
                results.append({**dict(row), "payload": json.loads(row["payload"]), "logs": [json.loads(log[0]) for log in logs]})
        return results

    def create_training(self, training_id: str, payload: dict):
        with self.connect() as connection:
            connection.execute("INSERT INTO training_runs VALUES(?,?,?,?,?)",
                               (training_id, "running", utcnow(), None, json.dumps(payload)))

    def training_event(self, training_id: str, payload: dict):
        with self.connect() as connection:
            connection.execute("INSERT INTO training_logs(training_id,created_at,payload) VALUES(?,?,?)",
                               (training_id, utcnow(), json.dumps(payload)))

    def update_training_payload(self,training_id,payload):
        with self.connect() as connection:
            connection.execute("UPDATE training_runs SET payload=? WHERE training_id=? AND status='running'",(json.dumps(payload),training_id))

    def finish_training(self, training_id: str, status: str, payload: dict):
        with self.connect() as connection:
            connection.execute("UPDATE training_runs SET status=?,ended_at=?,payload=? WHERE training_id=? AND status='running'",
                               (status, utcnow(), json.dumps(payload), training_id))

    def register_adapter(self, revision: str, payload: dict):
        with self.connect() as connection:
            connection.execute("INSERT INTO adapters VALUES(?,?,?)", (revision, json.dumps(payload), utcnow()))
