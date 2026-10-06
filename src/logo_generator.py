import os
import gc
import torch
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


def _run(pipe, prompt, size):
    with torch.inference_mode():
        return pipe(
            prompt,
            height=size, width=size,
            num_inference_steps=4,
            guidance_scale=0.0,
            max_sequence_length=256,
        ).images[0]


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