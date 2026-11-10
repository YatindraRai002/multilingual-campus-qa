from types import SimpleNamespace

import pytest


@pytest.mark.parametrize('fraction',[0,1,-.1,True,'0.75',float('nan')])
def test_invalid_allocator_budget_is_rejected(monkeypatch,fraction):
    from backend import gpu_memory
    monkeypatch.setattr(gpu_memory,'config',lambda name:{'version':'bounded-cuda-cache-v1','device':0,
        'per_process_memory_fraction':fraction})
    with pytest.raises(ValueError):
        gpu_memory.memory_policy()


def test_allocator_limit_covers_reserved_cache_and_is_applied_before_loading():
    from backend.gpu_memory import apply_inference_memory_policy
    calls=[]
    cuda=SimpleNamespace(set_per_process_memory_fraction=lambda fraction,device:calls.append((fraction,device)),
                         get_device_properties=lambda device:SimpleNamespace(total_memory=4*1024**3))
    policy={'version':'bounded-cuda-cache-v1','device':0,'per_process_memory_fraction':.75}
    observed=apply_inference_memory_policy(policy,torch_module=SimpleNamespace(cuda=cuda))
    assert calls==[(.75,0)] and observed['allocator_budget_bytes']==3*1024**3
