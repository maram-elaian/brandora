import os
import re
import random

import torch

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)


_model = None
_tokenizer = None

MODEL_ID = os.getenv("BRANDORA_TEXT_MODEL", "Qwen/Qwen3-8B")


def _load_qwen():
    global _model, _tokenizer

    if _model is None:
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        )

        _tokenizer = AutoTokenizer.from_pretrained(
            MODEL_ID,
            trust_remote_code=True,
        )

        if _tokenizer.pad_token is None:
            _tokenizer.pad_token = _tokenizer.eos_token

        _tokenizer.padding_side = "left"

        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            quantization_config=quant_config,
            device_map="auto",
            low_cpu_mem_usage=True,
            trust_remote_code=True,
        )

        _model.eval()

    return _model, _tokenizer


def _strip_thinking(text: str) -> str:
    """
    يشيل أي thinking من Qwen3 إذا ظهر.
    """
    text = text.strip()

    # الحالة الطبيعية: < think>...< /think> JSON
    if "" in text:
        text = text.split("", 1)[1]

    # في حال كان هناك think tag بدون closing tag
    text = re.sub(
        r"< think>.*?(?:< /think>|$)",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    ).strip()

    # إزالة أي tags متبقية
    text = re.sub(r"</?think>", "", text, flags=re.IGNORECASE).strip()

    return text


def generate(
    system_prompt: str,
    user_prompt: str,
    max_new_tokens: int = 900,
    temperature: float = 0.9,
    top_p: float = 0.95,
    top_k: int = 50,
    repetition_penalty: float = 1.05,
    seed=None,
) -> str:
    """
    توليد نص من Qwen3-8B.

    ملاحظات:
    - لا تستعملي seed ثابت إذا بدك تنويع.
    - max_new_tokens=900 مناسبة لـ brand package واحد.
    """
    model, tokenizer = _load_qwen()

    if seed is not None:
        torch.manual_seed(seed)
        random.seed(seed)

    enhanced_system_prompt = (
        system_prompt.strip()
        + "\n\nIMPORTANT OUTPUT RULES:\n"
        + "- Do not include reasoning.\n"
        + "- Do not include < think> tags.\n"
        + "- Do not include markdown.\n"
        + "- Do not include explanations.\n"
        + "- Output valid JSON only.\n"
    )

    messages = [
        {"role": "system", "content": enhanced_system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        inputs = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
            enable_thinking=False,
        ).to(model.device)
    except TypeError:
        inputs = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
        ).to(model.device)

    eos_id = tokenizer.eos_token_id
    pad_id = tokenizer.pad_token_id or eos_id

    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repetition_penalty=repetition_penalty,
            pad_token_id=pad_id,
            eos_token_id=eos_id,
        )

    input_len = inputs["input_ids"].shape[-1]
    raw = tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)

    cleaned = _strip_thinking(raw)

    return cleaned if cleaned else raw.strip()


def unload_qwen():
    global _model, _tokenizer

    if _model is not None:
        del _model
        del _tokenizer
        _model = None
        _tokenizer = None
        torch.cuda.empty_cache()