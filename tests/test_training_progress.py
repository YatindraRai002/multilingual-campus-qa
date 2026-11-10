def test_selected_counts_are_persisted_before_optimization(database):
    from backend.settings import utcnow
    payload={'model_id':'fixture-only','used_training_counts':{'en':2,'hi':2,'ta':2}}
    database.create_training('unit-training',{'model_id':'fixture-only'})
    database.update_training_payload('unit-training',payload)
    assert database.training()[0]['payload']['used_training_counts']==payload['used_training_counts']
    database.finish_training('unit-training','completed',payload)
    database.update_training_payload('unit-training',{'changed':True})
    assert database.training()[0]['payload']==payload
