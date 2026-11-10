import pytest


def test_chroma_persistence_filters_updates_and_deletions(tmp_path):
    pytest.importorskip('chromadb')
    from backend.retrieval import _client
    client = _client(tmp_path/'isolated-fixture-chroma')
    collection = client.create_collection('unit_test_only',metadata={'hnsw:space':'cosine'},embedding_function=None)
    collection.upsert(ids=['hi','ta','unverified'],embeddings=[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]],
        documents=['Hindi test fixture','Tamil test fixture','Excluded unit fixture'],
        metadatas=[{'language':'hi','verification_status':'human_verified'},
                   {'language':'ta','verification_status':'human_verified'},
                   {'language':'en','verification_status':'pending'}])
    reopened = _client(tmp_path/'isolated-fixture-chroma').get_collection('unit_test_only',embedding_function=None)
    result = reopened.query(query_embeddings=[[1.,0.,0.]],n_results=1,
          where={'$and':[{'language':{'$eq':'hi'}},{'verification_status':{'$eq':'human_verified'}}]})
    assert result['ids'] == [['hi']]
    reopened.upsert(ids=['hi'],embeddings=[[1.,0.,0.]],documents=['updated fixture'])
    assert reopened.count() == 3
    reopened.delete(ids=['unverified'])
    assert reopened.count() == 2


def test_small_random_qwen_fixture_adapter_round_trip(tmp_path):
    # A tiny randomly initialized architecture tests PEFT contracts only. It is never a replacement
    # research model, never downloads weights, and never writes production runs or model registries.
    torch = pytest.importorskip('torch')
    transformers = pytest.importorskip('transformers')
    peft = pytest.importorskip('peft')
    torch.manual_seed(42)
    config = transformers.Qwen2Config(vocab_size=64,hidden_size=16,intermediate_size=32,num_hidden_layers=1,
                                    num_attention_heads=2,num_key_value_heads=1,max_position_embeddings=64)
    base = transformers.Qwen2ForCausalLM(config)
    model = peft.get_peft_model(base,peft.LoraConfig(r=2,lora_alpha=4,target_modules=['q_proj','v_proj'],
                                                   lora_dropout=0,bias='none',task_type='CAUSAL_LM'))
    input_ids = torch.tensor([[1,2,3,4]])
    model(input_ids=input_ids,labels=input_ids).loss.backward()
    assert any(p.grad is not None and p.grad.abs().sum() > 0 for name,p in model.named_parameters() if 'lora_' in name)
    model.eval()
    expected = model(input_ids=input_ids).logits.detach()
    base_path,adapter_path = tmp_path/'random-base',tmp_path/'unit-adapter'
    # Persist the underlying original weights without LoRA then restore the adapter onto the same base.
    original = transformers.Qwen2ForCausalLM(config)
    state = {name.replace('.base_layer',''):value for name,value in model.get_base_model().state_dict().items() if 'lora_' not in name}
    original.load_state_dict(state)
    original.save_pretrained(base_path)
    model.save_pretrained(adapter_path)
    restored = peft.PeftModel.from_pretrained(transformers.Qwen2ForCausalLM.from_pretrained(base_path),adapter_path)
    restored.eval()
    assert torch.allclose(expected,restored(input_ids=input_ids).logits,atol=1e-5)
    assert (adapter_path/'adapter_model.safetensors').is_file()


def test_real_official_tokenizer_answer_masking():
    pytest.importorskip('transformers')
    from transformers import AutoTokenizer
    from backend.settings import config
    from backend.training import encode_answer
    selected = config('model_config')
    try:
        tokenizer = AutoTokenizer.from_pretrained(selected['model_id'],revision=selected['revision'],local_files_only=True)
    except OSError:
        pytest.skip('Official tokenizer not cached; run tokenizer-check to enable this test')
    row = {'question':'நூலகம் எங்கே?','context':'நூலகம் வளாகத்தில் உள்ளது.','language':'ta',
           'reference_answer':'வளாகத்தில்','answerable':True}
    sample = encode_answer(tokenizer,row,1024)
    assert sample['labels'][0] == -100
    target = tokenizer.decode([token for token in sample['labels'] if token != -100],skip_special_tokens=True)
    assert target.strip() == row['reference_answer']
    assert encode_answer(tokenizer,row,2) is None
    abstain = encode_answer(tokenizer,row,1024,empty_evidence=True)
    target = tokenizer.decode([token for token in abstain['labels'] if token != -100],skip_special_tokens=True)
    assert target.strip() == '[ABSTAIN]'
