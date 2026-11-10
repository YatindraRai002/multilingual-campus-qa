"""Link a new recovery run to immutable observations from an interrupted run."""
from collections import defaultdict

from backend.modeling import PrerequisiteError
from backend.settings import digest


IDENTITY_FIELDS=('model_id','model_revision','adapter','prompt_version','generation','max_input_tokens','seed',
                 'ingestion','limit_per_language','context_condition','test_ids','inference_execution','model_execution')
REVIEW_FIELDS={'annotation','reviewer','reviewed_at'}


def raw_observation(row):
    return {key:value for key,value in row.items() if key not in REVIEW_FIELDS}


def recovery_selection(database, source_run_id, *, configuration, fingerprint, dataset_version, track, experiment):
    source=database.run(source_run_id)
    if not source or source['status']!='interrupted':
        raise PrerequisiteError('Recovery requires an interrupted source run; active runs cannot be copied')
    if (source['track'],source['experiment'],source['dataset_version'],source['evaluation_fingerprint'])!=(track,experiment,dataset_version,fingerprint):
        raise PrerequisiteError('Recovery population or experiment differs from the source')
    for key in IDENTITY_FIELDS:
        if digest(source['configuration'].get(key))!=digest(configuration.get(key)):
            raise PrerequisiteError(f'Recovery changes frozen configuration: {key}')
    # The launcher may still be unloading after interruption. Wait for actual exit.
    import psutil
    with database.connect() as connection:
        worker=connection.execute('SELECT pid,process_started FROM job_processes WHERE run_id=?',(source_run_id,)).fetchone()
    if worker:
        try:
            if abs(psutil.Process(worker['pid']).create_time()-worker['process_started'])<1:
                raise PrerequisiteError('The original worker must exit before recovery is submitted')
        except psutil.Error:
            pass
    rows=database.predictions(source_run_id,limit=1_000_000)
    wanted=set(configuration['test_ids'])
    if any(row['question_id'] not in wanted for row in rows):
        raise PrerequisiteError('The source contains a question outside the sealed population')
    groups=defaultdict(list)
    for row in rows:
        groups[row.get('generation_batch_id') or row['prediction_id']].append(row)
    selected=[]
    excluded=[]
    for group in groups.values():
        sizes={row.get('batch_size',1) for row in group}
        if len(sizes)!=1 or len(group)!=next(iter(sizes)) or any(row['evaluation_status']!='completed' for row in group):
            excluded.extend(row['question_id'] for row in group)
        else:
            selected.extend(group)
    if not selected:
        raise PrerequisiteError('No complete successful observation batches are available for recovery')
    # Database row order is stable; sort for an explicit portable snapshot checksum.
    selected.sort(key=lambda row:row['question_id'])
    descriptor={'source_run_id':source_run_id,'source_configuration_sha256':digest(source['configuration']),
                'observations_sha256':digest([raw_observation(row) for row in selected]),'reused_count':len(selected),
                'pending_count':len(wanted)-len(selected),'excluded_incomplete_or_failed_question_ids':sorted(excluded),
                'policy':'Reuse actual saved observations with origin IDs; generate only remaining complete batches. Human annotations are not copied.'}
    return descriptor,selected


def restore_observations(database, run, append):
    expected=run['configuration']['recovery']
    observed,rows=recovery_selection(database,expected['source_run_id'],configuration=run['configuration'],
        fingerprint=run['evaluation_fingerprint'],dataset_version=run['dataset_version'],track=run['track'],experiment=run['experiment'])
    if observed!=expected:
        raise PrerequisiteError('Recovery source observations differ from the sealed recovery manifest')
    inherited=set()
    for row in rows:
        payload={key:value for key,value in row.items() if key not in REVIEW_FIELDS|{'prediction_id'}}
        payload['recovery_origin']={'source_run_id':expected['source_run_id'],'source_prediction_id':row['prediction_id'],
                                    'previous_origin':row.get('recovery_origin')}
        payload.setdefault('execution_segment_id',expected['source_run_id'])
        append(payload)
        inherited.add(row['question_id'])
    return inherited
