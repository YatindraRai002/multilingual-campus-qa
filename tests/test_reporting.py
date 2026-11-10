def test_running_run_has_no_implied_scores_then_saved_metrics_are_reported(tmp_path, monkeypatch, database, prediction):
    from backend import reporting
    from backend.evaluation.evaluation_runner import evaluate_predictions
    monkeypatch.setattr(reporting, 'ROOT', tmp_path)
    run = database.create_run(track='benchmark', experiment='A', dataset_version='isolated-fixture',
        evaluation_fingerprint='unit-only', configuration={'model_id':'unit-only', 'test_ids':['unit-test-only']}, total=1)
    database.transition(run, 'running')
    database.add_prediction(run, prediction)
    reporting.write_evaluation_report(database)
    report = (tmp_path/'docs'/'EVALUATION_REPORT.md').read_text(encoding='utf-8')
    assert 'Status: **running**' in report
    assert 'No calculated metric snapshot exists yet.' in report
    assert 'No runs recorded for this track.' in report
    database.store_metrics(run, evaluate_predictions(database.predictions(run)))
    database.transition(run, 'completed')
    reporting.write_run_report(database, run)
    report = (tmp_path/'docs'/'EVALUATION_REPORT.md').read_text(encoding='utf-8')
    assert 'Status: **completed**' in report
    assert '| en | 1 | 100.00% | 100.00% | Pending | Pending |' in report
    assert (tmp_path/'results'/'reports'/run/'report.md').exists()
    compact = reporting.report_run(database.run(run))
    assert compact['configuration']['test_ids_summary']['count'] == 1
    assert 'test_ids' not in compact['configuration']
    assert database.run(run)['configuration']['test_ids'] == ['unit-test-only']


def test_metric_replay_preserves_outputs_and_appends_snapshots(tmp_path,monkeypatch,database,prediction):
    from backend import reporting
    from backend.evaluation.evaluation_runner import recompute_run
    monkeypatch.setattr(reporting,'ROOT',tmp_path)
    run=database.create_run(track='benchmark',experiment='A',dataset_version='unit-fixture',
        evaluation_fingerprint='unit-fixture',configuration={},total=1)
    database.transition(run,'running')
    database.add_prediction(run,prediction)
    database.transition(run,'completed')
    original=database.predictions(run)
    first=recompute_run(database,run)
    second=recompute_run(database,run,reason='explicit_repeat')
    assert first['definitions_version']==second['definitions_version']=='qa-metrics-v3-all-retrieval-queries'
    assert first['populations']==second['populations']
    assert database.predictions(run)==original
    with database.connect() as connection:
        assert connection.execute('SELECT count(*) FROM metrics WHERE run_id=?',(run,)).fetchone()[0]==2
    assert len(list((tmp_path/'results'/'reports'/run).glob('metrics-*.json')))==2
