"""Bound the CUDA caching allocator, including unused reserved blocks."""
from backend.settings import config


def memory_policy():
    policy=config('runtime_gpu')
    fraction=policy.get('per_process_memory_fraction')
    if isinstance(fraction,bool) or not isinstance(fraction,(int,float)) or not 0 < fraction < 1:
        raise ValueError('GPU memory fraction must be a number strictly between zero and one')
    if policy.get('device')!=0 or policy.get('version')!='bounded-cuda-cache-v1':
        raise ValueError('Unsupported inference memory policy')
    return policy


def apply_inference_memory_policy(policy, *, torch_module=None):
    if torch_module is None:
        import torch as torch_module
    fraction=policy['per_process_memory_fraction']
    if isinstance(fraction,bool) or not 0 < fraction < 1 or policy.get('device')!=0:
        raise ValueError('Invalid inference allocator limit')
    torch_module.cuda.set_per_process_memory_fraction(fraction,device=0)
    total=torch_module.cuda.get_device_properties(0).total_memory
    return {'policy':policy,'device_total_bytes':total,'allocator_budget_bytes':int(total*fraction)}


def memory_observation(engine):
    torch=getattr(engine,'torch',None)
    if torch is None:
        return None
    return {'allocated_bytes':torch.cuda.memory_allocated(),'reserved_bytes':torch.cuda.memory_reserved(),
            'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved()}
