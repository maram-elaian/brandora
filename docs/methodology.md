# Methodology

This document describes how models were compared and selected for Brandora, the evaluation criteria, the problems encountered during development, and how the final system was evaluated.

> Items in **[brackets]** are placeholders: replace them with your actual experiment details before submitting.

---

## 1. Goal

Select the best free, open-weight models for two tasks and verify the final system's output quality:

1. **Text generation**: produce a structured brand specification (name, slogan, color palette, typography, visual style, logo concept) as valid JSON.
2. **Logo generation**: produce a logo mark from the specification.

Constraint: everything must run on free resources (Kaggle, Tesla T4 with 16 GB VRAM).

---

## 2. Test Set

All candidate models were tested on the **same 30 standardized brand briefs** in [`data/test_briefs.json`](../data/test_briefs.json).

Each brief contains: industry, target audience, brand purpose, personality traits, and tone.

Using identical inputs for every model makes the comparison fair and repeatable. The briefs cover **[describe diversity: e.g., food, fashion, technology, services, formal vs. playful tones]**.

---

## 3. Evaluation Criteria

### 3.1 Technical validation (pass/fail and counts)

| Criterion | How it was checked |
|---|---|
| Environment compatibility | Model loads and runs on a T4 in Kaggle without errors |
| Resource requirements | Peak GPU memory and loading time |
| Valid structured output (text models) | Output parses as JSON with all required fields |
| Generation speed | Time per generation **[seconds/minutes]** |

### 3.2 Human assessment

Outputs were scored using the rubric in [`evaluation/rubric.md`](../evaluation/rubric.md).

Criteria: **[list the rubric dimensions, e.g., creativity, relevance to brief, memorability, visual clarity, palette fit]**, each on a **[1 to 5]** scale.

### 3.3 Automated metrics for the final system

Color contrast was checked with WCAG criteria (`src/evaluator.py`). Logo-to-concept fidelity was measured with CLIP (Section 7).

---

## 4. Text Model Comparison

| Model | Result | Decision |
|---|---|---|
| **Qwen3-8B** (4-bit) | Produced valid JSON across all 30 briefs; strong naming quality; Apache 2.0 license | **Selected** |
| LiquidAI/LFM2.5-2.6B | Failed to consistently produce valid structured JSON | Rejected |
| **[other models tested, if any]** | **[result]** | **[decision]** |

**Reasoning.** Reliable structured output is essential because the interface and the logo prompt depend on parsing the specification. **[Add numbers if available, e.g., "valid JSON in X of 30 briefs for model Y".]**

---

## 5. Image Model Comparison

| Model | Result | Decision |
|---|---|---|
| **FLUX.1-schnell** (4-bit) | Fast generation with few inference steps; good logo-like output; open weights; fits in memory with CPU offload | **Selected** |
| Stable Diffusion 3 Medium | Technical compatibility issue in the development environment: **[describe the error]** | Rejected |
| Qwen-Image-2.1 | Technically successful; **[reason it was not chosen, e.g., speed or memory]** | Not selected |
| PlaygroundV2.5 | Technically successful; **[reason it was not chosen]** | Not selected (planned as optional future model) |

**Reasoning.** Selection was based on technical compatibility, output quality, resource requirements, and performance across the standardized briefs.

---

## 6. Engineering Issues and Solutions

| # | Problem | Cause | Solution |
|---|---|---|---|
| 1 | CUDA out-of-memory when generating the logo | Qwen and FLUX competing for 16 GB; VAE decoding requested about 5.5 GB at once | Qwen is explicitly unloaded before FLUX runs (remove accelerate hooks, delete references, `gc.collect`, clear CUDA cache); VAE tiling and slicing; `expandable_segments`; 768 px generation with a 512 px fallback. Verified by measuring allocated GPU memory after unloading (about 0.01 GB) |
| 2 | Brand Kit export crashed (`'tuple' object cannot be interpreted as an integer`) | The Gradio image component returned a non-PIL type | Added a conversion function handling PIL, NumPy, path, tuple, and dict inputs; set `type="pil"` |
| 3 | Prompt truncated by the CLIP text encoder (136 > 77 tokens) | FLUX's CLIP branch accepts only 77 tokens | Short prompt for CLIP (`prompt`), full prompt for T5 (`prompt_2`) |
| 4 | Generic, repetitive logos | Prompt described style rather than the symbol; negative phrases are ineffective in FLUX | Qwen now generates a concrete `logo_concept` and `logo_shape_language`; the prompt uses positive descriptions only; random style variants and seeds |
| 5 | Logo colors did not follow the palette | FLUX does not follow exact color instructions | Post-generation palette enforcement: each pixel is mapped to the nearest palette color (plus white) |
| 6 | Kernel crash during bulk generation | Host RAM exhausted while loading large models | Ran generation as a separate process with a log; resumable script that skips completed briefs |
| 7 | Unreadable text in the UI | Dark-mode defaults and theme colors | Custom CSS with explicit text colors; dark text on light result cards |

---

## 7. Final System Evaluation (CLIP)

### 7.1 Procedure

1. `generate_samples.py` generates three proposals per brief and a logo for each (**21 logos** in the final run), saving both the raw FLUX output and the palette-enforced version.
2. `evaluate_folder.py` evaluates every logo with **CLIP ViT-B/32** (on CPU) and writes `results/report.csv` and `results/summary.md`.

### 7.2 Metrics

| Metric | Definition | Better |
|---|---|---|
| Concept score | Cosine similarity between the logo and "a minimalist logo of [logo_concept]" | Higher |
| Margin | Concept score for the logo's own concept minus its mean score for the other brands' concepts | Positive and higher |
| Retrieval accuracy | Fraction of logos whose own concept is the best match among all concepts | Higher (chance = 1/21 = 0.048) |
| Text-free score | CLIP zero-shot probability that the logo contains no letters | Closer to 1 |
| Palette distance | Mean RGB distance from logo pixels (64×64) to the nearest palette color or white | Closer to 0 |

### 7.3 Results

| Version | Concept score | Margin | Retrieval acc. | Text-free | Palette dist. |
|---|---|---|---|---|---|
| FLUX raw | 0.306 | +0.075 | 0.571 | 0.803 | 11.4 |
| After palette | 0.303 | +0.067 | 0.619 | 0.797 | 8.7 |

### 7.4 Interpretation

- Positive margins and retrieval accuracy of 0.57 to 0.62 (about 12 to 13 times chance) show that logos reflect their own concept.
- Palette enforcement reduced palette distance by about 24% (11.4 to 8.7) while leaving concept fidelity essentially unchanged (0.306 to 0.303).
- The retrieval change between versions is one logo out of 21, which is not a meaningful difference on a sample this small.

---

## 8. Limitations

- CLIP measures semantic alignment only; it does not measure aesthetics, originality, or professional quality. Human evaluation is needed for those.
- The sample is small (21 logos), so small differences are not conclusive.
- CLIP is evaluated against the same concept text that guided generation.
- CLIP zero-shot detection of text in logos is approximate.
- **[Add: whether a baseline with the original prompt was evaluated.]**

---

## 9. Reproducing the Experiments

```bash
pip install -r requirements.txt
export HF_TOKEN=<your token>        # required to download FLUX.1-schnell

python generate_samples.py          # generates results/<brief>/<n>/...
python evaluate_folder.py           # writes results/report.csv and results/summary.md
```

Hardware used: Kaggle, NVIDIA Tesla T4 (16 GB VRAM). Evaluation runs on CPU.
