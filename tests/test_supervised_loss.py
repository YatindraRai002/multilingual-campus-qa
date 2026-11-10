import copy

import pytest


def test_supervised_position_loss_and_gradients_match_full_causal_loss():
    torch = pytest.importorskip('torch')
    from transformers import Qwen2Config,Qwen2ForCausalLM
    from backend.training import supervised_causal_loss
    torch.manual_seed(42)
    model = Qwen2ForCausalLM(Qwen2Config(vocab_size=41,hidden_size=16,intermediate_size=32,num_hidden_layers=1,
                               num_attention_heads=2,num_key_value_heads=1,max_position_embeddings=32,attention_dropout=0))
    reference = copy.deepcopy(model)
    tokens = torch.tensor([[1,2,3,4,5,6,7,0],[1,8,9,10,11,12,0,0]])
    labels = tokens.clone()
    labels[:,:4] = -100
    labels[0,7:] = -100
    labels[1,6:] = -100
    inputs = {'input_ids':tokens,'attention_mask':tokens.ne(0).long(),'labels':labels}
    expected = reference(**inputs).loss
    actual,output = supervised_causal_loss(model,inputs)
    assert torch.allclose(actual,expected,atol=1e-6)
    assert output.logits.shape[1] < tokens.shape[1]
    expected.backward()
    actual.backward()
    for left,right in zip(model.parameters(),reference.parameters()):
        if left.grad is not None:
            assert torch.allclose(left.grad,right.grad,atol=1e-5)


def test_supervised_position_loss_rejects_all_masked_batch():
    torch = pytest.importorskip('torch')
    from backend.training import supervised_causal_loss
    with pytest.raises(ValueError,match='no supervised'):
        supervised_causal_loss(None,{'labels':torch.full((1,8),-100)})
