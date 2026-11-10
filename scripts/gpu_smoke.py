"""Small real CUDA/NF4 kernel validation. This is not model training or research evaluation."""
import json
import time

from backend.settings import ROOT, utcnow, write_json

import torch
import bitsandbytes as bnb

if not torch.cuda.is_available():
    raise RuntimeError('CUDA-enabled PyTorch cannot access a GPU')
torch.manual_seed(42)
torch.cuda.reset_peak_memory_stats()
layer = bnb.nn.Linear4bit(128,64,bias=False,compute_dtype=torch.float16,quant_type='nf4',compress_statistics=True).to('cuda')
inputs = torch.randn(2,128,device='cuda',dtype=torch.float16,requires_grad=True)
started = time.perf_counter()
outputs = layer(inputs)
outputs.float().square().mean().backward()
torch.cuda.synchronize()
assert torch.isfinite(outputs).all() and torch.isfinite(inputs.grad).all()
result = {'status':'passed','checked_at':utcnow(),'device':torch.cuda.get_device_name(),
          'torch':torch.__version__,'cuda_runtime':torch.version.cuda,'bitsandbytes':bnb.__version__,
          'operation':'small NF4 linear forward/backward kernel smoke check',
          'duration_seconds':time.perf_counter()-started,'peak_allocated_bytes':torch.cuda.max_memory_allocated(),
          'research_training':False}
write_json(ROOT/'results'/'gpu_smoke.json',result)
print(json.dumps(result,indent=2))
