import os
import torch, gc
from huggingface_hub import login
from diffusers import FluxPipeline, FluxTransformer2DModel, BitsAndBytesConfig as DiffusersBnBConfig
from transformers import T5EncoderModel, BitsAndBytesConfig as TransformersBnBConfig

_pipe = None

def _load_flux():
    global _pipe
    if _pipe is None:
        hf_token = os.environ.get("HF_TOKEN")
        if hf_token:
            login(token=hf_token)

        model_id = "black-forest-labs/FLUX.1-schnell"
        # ... (باقي الكود زي ما هو تماماً)

import torch, gc
from diffusers import FluxPipeline, FluxTransformer2DModel, BitsAndBytesConfig as DiffusersBnBConfig
from transformers import T5EncoderModel, BitsAndBytesConfig as TransformersBnBConfig

_pipe = None

def _load_flux():
    global _pipe
    if _pipe is None:
        model_id = "black-forest-labs/FLUX.1-schnell"

        # ترتيب التحميل مهم: T5 أولاً على GPU فاضية (درس تعلمناه بالتجربة)
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
    return _pipe

def generate_logo(prompt: str):
    pipe = _load_flux()
    image = pipe(prompt, num_inference_steps=4, guidance_scale=0.0).images[0]
    gc.collect()
    torch.cuda.empty_cache()
    return image
