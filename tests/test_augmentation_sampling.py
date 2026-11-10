import pytest

from backend.training import abstention_indices,balanced_indices


def test_low_hash_selection_does_not_force_every_example_into_abstention_augmentation():
    rows=[{'benchmark_id':f'isolated-fixture-{i}','language':'en'} for i in range(10000)]
    chosen=balanced_indices(rows,list(range(len(rows))),256,['en'],42)
    augmented=abstention_indices(rows,chosen,42,.1)
    assert set(augmented).issubset(chosen)
    assert 0 < len(augmented) < len(chosen)//4
    assert augmented==abstention_indices(rows,chosen,42,.1)
    assert abstention_indices(rows,chosen,42,0)==[]
    assert abstention_indices(rows,chosen,42,1)==chosen
    with pytest.raises(ValueError):
        abstention_indices(rows,chosen,42,1.1)
