import torch, re
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

_model = None
_tokenizer = None

def _load_qwen():
    global _model, _tokenizer
    if _model is None:
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        )
        _tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")
        _model = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen3-8B", quantization_config=quant_config, device_map="auto"
        )
    return _model, _tokenizer

def generate(system_prompt: str, user_prompt: str, max_new_tokens: int = 500) -> str:
    model, tokenizer = _load_qwen()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    try:
        inputs = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True,
            return_tensors="pt", return_dict=True, enable_thinking=False
        ).to(model.device)
    except TypeError:
        inputs = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True,
            return_tensors="pt", return_dict=True
        ).to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.9,
        top_p=0.95,
    )
    input_len = inputs["input_ids"].shape[-1]
    raw = tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
    return re.sub(r'.*</think>\s*', '', raw, flags=re.DOTALL).strip()