def test_preflight_blocks_overlap_without_allocating_cuda(tmp_path, monkeypatch):
    from backend import experiments
    monkeypatch.setattr(experiments,'ROOT',tmp_path)
    audits=[]
    def audit(*,check_torch):
        audits.append(check_torch)
        return {'fixture_only':True}
    monkeypatch.setattr(experiments,'audit',audit)
    monkeypatch.setattr(experiments,'readiness',lambda hardware:{'blockers':[]})
    monkeypatch.setattr(experiments,'evaluation_rows',lambda track:({'version':'unit-fixture'},[]))
    with experiments.gpu_lock().acquire(timeout=0):
        checked=experiments.preflight_evaluation('benchmark','A')
        assert not checked['ready']
        assert any('already running' in message for message in checked['blockers'])
        assert audits==[False]
    assert experiments.preflight_evaluation('benchmark','A')['ready']
    assert audits==[False,True]
