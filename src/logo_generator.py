import os
import gc
import torch
from PIL import Image
from src.logo_prompt import _extract_hex
from huggingface_hub import login
from diffusers import (
    FluxPipeline,
    FluxTransformer2DModel,
    BitsAndBytesConfig as DiffusersBnBConfig,
)
from transformers import T5EncoderModel, BitsAndBytesConfig as TransformersBnBConfig

_pipe = None


def _free_gpu():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


def _load_flux():
    global _pipe
    if _pipe is None:
        hf_token = os.environ.get("HF_TOKEN")
        if hf_token:
            login(token=hf_token)

        model_id = "black-forest-labs/FLUX.1-schnell"

        text_encoder_2 = T5EncoderModel.from_pretrained(
            model_id, subfolder="text_encoder_2",
            quantization_config=TransformersBnBConfig(
                load_in_4bit=True, bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
            ),
            torch_dtype=torch.bfloat16,
        )
        transformer = FluxTransformer2DModel.from_pretrained(
            model_id, subfolder="transformer",
            quantization_config=DiffusersBnBConfig(
                load_in_4bit=True, bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
            ),
            torch_dtype=torch.bfloat16,
        )
        _pipe = FluxPipeline.from_pretrained(
            model_id, transformer=transformer, text_encoder_2=text_encoder_2,
            torch_dtype=torch.bfloat16,
        )
        _pipe.enable_model_cpu_offload()
        _pipe.vae.enable_tiling()    # يمنع طلب 5.5GB دفعة واحدة
        _pipe.vae.enable_slicing()
    return _pipe


import random

def _run(pipe, prompt, size):
    seed = random.randint(0, 2**31 - 1)
    generator = torch.Generator("cpu").manual_seed(seed)
    print("LOGO SEED:", seed, "| PROMPT:", prompt)   # عشان تعرفي أي seed طلع أحلى
    with torch.inference_mode():
        return pipe(
            prompt=prompt[:200],
            prompt_2=prompt,
            height=size, width=size,
            num_inference_steps=6,
            guidance_scale=0.0,
            max_sequence_length=256,
            generator=generator,
        ).images[0]

def apply_palette(image, color_palette):
    """يحوّل ألوان الصورة إلى ألوان الباليت (+ الأبيض للخلفية) بالضبط."""
    hexes = [_extract_hex(c) for c in (color_palette or [])[:5]]
    rgb = [(255, 255, 255)]                       # الخلفية البيضاء
    for h in hexes:
        h = h.lstrip("#")
        rgb.append(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))

    flat = [v for c in rgb for v in c]
    flat += [0] * (768 - len(flat))               # الباليت لازم يكون 256 لون
    pal = Image.new("P", (1, 1))
    pal.putpalette(flat)

    out = image.convert("RGB").quantize(palette=pal, dither=Image.Dither.NONE)
    return out.convert("RGB")

def generate_logo(prompt: str):
    _free_gpu()                     # تنظيف أي بقايا من Qwen
    pipe = _load_flux()
    try:
        try:
            image = _run(pipe, prompt, 768)
        except torch.cuda.OutOfMemoryError:
            _free_gpu()
            image = _run(pipe, prompt, 512)   # محاولة أخيرة بدقة أقل
    finally:
        _free_gpu()
    return image