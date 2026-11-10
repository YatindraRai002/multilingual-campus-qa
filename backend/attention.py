
def explicit_gqa_sdpa(module,query,key,value,attention_mask=None,dropout=0.0,scaling=None,is_causal=None,**kwargs):
    import torch
    groups=query.shape[1]//key.shape[1]
    if groups>1:
        key=key.repeat_interleave(groups,dim=1)
        value=value.repeat_interleave(groups,dim=1)
    if attention_mask is not None and attention_mask.ndim==4:
        attention_mask=attention_mask[:,:,:,:key.shape[-2]]
    if is_causal is None:
        is_causal=query.shape[-2]>1 and attention_mask is None and getattr(module,'is_causal',True)
    output=torch.nn.functional.scaled_dot_product_attention(query,key,value,attn_mask=attention_mask,
                            dropout_p=dropout,is_causal=is_causal,scale=scaling,enable_gqa=False)
    return output.transpose(1,2).contiguous(),None


def register_attention(name):
    if name=='explicit_gqa_sdpa':
        from transformers import AttentionInterface
        from transformers.masking_utils import AttentionMaskInterface,ALL_MASK_ATTENTION_FUNCTIONS
        AttentionInterface.register(name,explicit_gqa_sdpa)
        AttentionMaskInterface.register(name,ALL_MASK_ATTENTION_FUNCTIONS['sdpa'])
