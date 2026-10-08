# 🎨 Brandora

An AI-powered system that generates a complete visual brand identity (brand name, slogan, color palette, typography direction, and logo) from a short textual description, and exports it as a Brand Kit PDF.

**Field Training Project** by Maram Ashraf Ellain. The goal is to demonstrate an end-to-end AI system combining text and image generation using fully free resources, supported by a documented model-comparison methodology and a quantitative evaluation.

📄 Full report: [`docs/Brandora_Field_Training_Project_Report.pdf`](docs/Brandora_Field_Training_Project_Report.pdf)

---

## ✨ How It Works

1. The user describes the brand: **industry, target audience, purpose, personality, and tone**.
2. **Qwen3-8B** generates **three brand proposals**, each with a name, slogan, color palette, typography direction, visual style, and a concrete logo concept.
3. The user compares the proposals and **chooses one**.
4. **FLUX.1-schnell** generates a logo from the chosen concept, and the image is recolored to the exact brand palette.
5. The user downloads a complete **Brand Kit PDF**.

The interface is built with **Gradio**.

---

## 🧠 Models Used

| Task | Model | Why |
| ---- | ----- | --- |
| Text generation | **Qwen3-8B** (4-bit quantized) | Apache 2.0 license; consistently produced valid structured JSON across all 30 test cases |
| Logo generation | **FLUX.1-schnell** (4-bit quantized) | Open weights, low resource requirements, fast generation |
| Evaluation | **CLIP ViT-B/32** | Measures how well each logo matches its brand concept |

### Models Tested and Rejected

Documented in [`docs/methodology.md`](docs/methodology.md):

* **LiquidAI/LFM2.5-2.6B**: failed to consistently produce valid structured JSON.
* **Stable Diffusion 3 Medium**: technical compatibility issue in the development environment.
* **Qwen-Image-2.1**: technically successful, but not selected as the primary model.
* **PlaygroundV2.5**: technically successful, but not selected as the primary model.

---

## 🔧 Key Technical Features

* **GPU memory management**: Qwen is fully unloaded before FLUX runs, so both models fit on a single 16 GB GPU. FLUX uses 4-bit quantization, CPU offload, and VAE tiling.
* **Concept-driven logo prompts**: Qwen outputs a concrete `logo_concept` and `logo_shape_language`, which produce more distinctive logos than generic style descriptions. Prompts use positive descriptions only, with a compact prompt for CLIP and the full prompt for T5.
* **Palette enforcement**: generated logos are recolored to the exact palette chosen by Qwen, because FLUX does not reliably follow color instructions.
* **Diversity control**: banned generic words, duplicate names, and similar name prefixes are rejected across the three proposals.
* **CLIP-based evaluation** of logo-to-concept fidelity (see below).

---

## 📁 Project Structure

```text
brandora/
├── app.py                     # Entry point: Gradio interface
├── generate_samples.py        # Generates a sample set (packages + logos) into results/
├── evaluate_folder.py         # Evaluates results/ with CLIP and writes a summary
├── requirements.txt
├── src/
│   ├── text_generator.py      # Loads, calls, and unloads Qwen3-8B
│   ├── run_text_gen.py        # Runs Qwen3-8B as a separate process
│   ├── brand_package.py       # Prompting and generation of brand packages
│   ├── logo_prompt.py         # Builds the logo prompt from the brand package
│   ├── logo_generator.py      # Loads and calls FLUX.1-schnell; palette enforcement
│   ├── brand_kit_export.py    # Composes the Brand Kit image/PDF
│   ├── clip_eval.py           # CLIP-based evaluation metrics
│   ├── name_generator.py      # Extracts the brand name from the specification
│   ├── slogan_generator.py    # Extracts the slogan from the specification
│   └── evaluator.py           # Color contrast using WCAG criteria
├── data/
│   └── test_briefs.json       # 30 standardized test cases for model comparison
├── results/                   # Generated samples and CLIP evaluation outputs
├── notebooks/                 # Kaggle notebooks for testing individual models
├── docs/
│   ├── methodology.md         # Model comparison methodology and rejection decisions
│   └── Brandora_Field_Training_Project_Report.pdf
└── evaluation/
    └── rubric.md              # Human evaluation criteria
```

Additional helper and experimental modules (e.g., color and logo composition utilities) also live in `src/`.

---

## 🚀 Running the Project on Kaggle

Brandora requires a GPU and was developed on a **Tesla T4 (16 GB VRAM)**.

### 1. Clone the Repository

```python
!git clone https://github.com/maram-elaian/brandora.git /kaggle/working/brandora_repo
%cd /kaggle/working/brandora_repo
```

### 2. Install Dependencies

```python
!pip install -r requirements.txt -q
```

### 3. Configure the Hugging Face Token

A Hugging Face token is required to download **FLUX.1-schnell**. Accept the model's terms on Hugging Face, then store your token as a Kaggle Secret named `HF_TOKEN`.

```python
import os
from kaggle_secrets import UserSecretsClient

os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")
```

### 4. Launch the Interface

```python
!python app.py
```

A public Gradio URL is printed. It stays valid while the notebook is running (Kaggle share links expire after one week).

> **⏱️ Generation time:** The first run is the slowest because the models must be downloaded and loaded. Qwen is loaded for text generation and then unloaded to free GPU memory for FLUX, which stays cached after its first load. This is an intentional memory-management trade-off for running both models on a single 16 GB GPU, not an application error.

---

## ⚙️ GPU Requirements

* **Minimum VRAM:** 16 GB
* **Tested GPU:** NVIDIA Tesla T4
* **Quantization:** 4-bit using `bitsandbytes`
* Both Qwen3-8B and FLUX.1-schnell use 4-bit quantization to fit within the available VRAM.

---

## 📊 Evaluation

### Model selection

All candidate models were evaluated on the **same 30 standardized briefs** in [`data/test_briefs.json`](data/test_briefs.json). Details are in [`docs/methodology.md`](docs/methodology.md) and [`evaluation/rubric.md`](evaluation/rubric.md).

### CLIP evaluation of generated logos

Generate a sample set and evaluate it:

```bash
python generate_samples.py     # writes results/<brief>/<n>/{package.json, logo_raw.png, logo.png}
python evaluate_folder.py      # writes results/report.csv and results/summary.md
```

Metrics:

* **Concept score**: cosine similarity between a logo and its concept text.
* **Margin**: the logo's score for its own concept minus its average score for the other brands' concepts (positive means correct targeting).
* **Retrieval accuracy**: how often the logo's own concept is the best match among all concepts.
* **Text-free score**: CLIP zero-shot probability that the logo contains no letters.
* **Palette distance**: mean RGB distance between logo pixels and the nearest palette color (lower is better).

Results on **21 logos** (generated from 8 briefs, three proposals each; random-chance retrieval accuracy = 0.048):

| Version | Concept score | Margin | Retrieval acc. | Text-free | Palette dist. |
|---|---|---|---|---|---|
| FLUX raw | 0.306 | +0.075 | 0.571 | 0.803 | 11.4 |
| After palette | 0.303 | +0.067 | 0.619 | 0.797 | 8.7 |

CLIP identified the correct brand for roughly 57% to 62% of logos among 21 candidates (about 12 to 13 times above chance), and palette enforcement reduced color deviation by about 24% without noticeably changing semantic fidelity. The one-logo difference in retrieval accuracy between the two versions is not statistically meaningful on a sample this small.

#### Why CLIP, and how it compares with alternatives

CLIP ViT-B/32 was chosen because it is lightweight (it runs on CPU, so it does not compete with FLUX for GPU memory), fast, a standard measure of text-image alignment, and reproducible on free resources. It measures semantic alignment only, not aesthetics, and is weaker at composition and negation (so the text-free score is approximate).

| Method | Measures | Role in this project |
|---|---|---|
| **CLIP ViT-B/32** | Text-image alignment | **Primary metric (used)** |
| OpenCLIP (e.g., ViT-L/14) | Text-image alignment, larger model | Secondary check |
| SigLIP 2 | Text-image alignment (sigmoid loss) | Secondary check |
| BLIP (ITM head) | Fine-grained text-image matching | Possible |
| Aesthetic predictor / ImageReward | Visual appeal and human preference | Complementary (future work) |

Only CLIP was used; the alternatives were reviewed but not tested. See Appendix A of the project report for details.

**Limitations:** CLIP measures semantic alignment, not aesthetics or originality, and the sample is small. It should be complemented by human evaluation.

---

## 🔜 Future Improvements

* Add **ImageReward** as a complementary metric that estimates perceived quality (human preference), addressing CLIP's inability to assess aesthetics. Its scores should be validated against human ratings, since it was not trained specifically on logos.
* Human evaluation study with multiple raters.
* Gallery of several logo variants per proposal.
* Public deployment as a Hugging Face Space (ZeroGPU), keeping models resident in memory for faster responses.
* Optional alternative image model such as **PlaygroundV2.5**.
* Vector (SVG) logo export.
