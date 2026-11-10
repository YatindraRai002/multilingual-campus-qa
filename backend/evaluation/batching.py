"""Deterministic batching uses input language/length/ID only, never reference answers."""
def pack_batches(rows,lengths,*,maximum_size,token_budget):
    if len(rows)!=len(lengths) or maximum_size<1 or token_budget<1:
        raise ValueError('Invalid batch configuration or length count')
    ordered = sorted(zip(rows,lengths),key=lambda item:(item[0]['language'],item[1],item[0]['benchmark_id']))
    batch,max_length,language = [],0,None
    for row,length in ordered:
        candidate=max(max_length,length)
        if batch and (row['language']!=language or len(batch)>=maximum_size or candidate*(len(batch)+1)>token_budget):
            yield batch
            batch,max_length=[],0
        batch.append(row)
        language=row['language']
        max_length=max(max_length,length)
    if batch:
        yield batch
