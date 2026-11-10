from types import SimpleNamespace

import pytest


@pytest.mark.parametrize('with_mask',[False,True])
def test_explicit_gqa_has_same_outputs_and_gradients_as_grouped_query_attention(with_mask):
    torch=pytest.importorskip('torch')
    from backend.attention import explicit_gqa_sdpa
    torch.manual_seed(42)
    q=torch.randn(2,6,7,8,requires_grad=True)
    k=torch.randn(2,2,7,8,requires_grad=True)
    v=torch.randn(2,2,7,8,requires_grad=True)
    qr,kr,vr=[tensor.detach().clone().requires_grad_() for tensor in [q,k,v]]
    mask=torch.ones(7,7,dtype=torch.bool).tril().reshape(1,1,7,7) if with_mask else None
    expected=torch.nn.functional.scaled_dot_product_attention(qr,kr,vr,attn_mask=mask,is_causal=not with_mask,enable_gqa=True)
    actual,_=explicit_gqa_sdpa(SimpleNamespace(is_causal=True),q,k,v,mask)
    assert torch.allclose(actual,expected.transpose(1,2),atol=1e-6)
    actual.sum().backward();expected.sum().backward()
    assert all(torch.allclose(a.grad,b.grad,atol=1e-5) for a,b in [(q,qr),(k,kr),(v,vr)])


def test_registered_backend_preserves_causal_and_padding_mask_in_model():
    torch=pytest.importorskip('torch')
    from transformers import Qwen2Config,Qwen2ForCausalLM
    from backend.attention import register_attention
    register_attention('explicit_gqa_sdpa')
    config=Qwen2Config(vocab_size=32,hidden_size=16,intermediate_size=32,num_hidden_layers=1,num_attention_heads=2,num_key_value_heads=1)
    config._attn_implementation='sdpa'
    expected=Qwen2ForCausalLM(config).eval()
    other=Qwen2Config.from_dict(config.to_dict());other._attn_implementation='explicit_gqa_sdpa'
    actual=Qwen2ForCausalLM(other).eval();actual.load_state_dict(expected.state_dict())
    ids=torch.tensor([[0,0,1,2,3],[1,2,3,4,5]])
    mask=ids.ne(0).long()
    with torch.no_grad():
        a=actual(input_ids=ids,attention_mask=mask).logits
        b=expected(input_ids=ids,attention_mask=mask).logits
    assert torch.allclose(a[:,2:],b[:,2:],atol=1e-5)
