# 🎨 Brandora

An AI-powered system that generates a complete visual brand identity — including a brand name, slogan, color palette, typography recommendations, and logo — from a simple textual description.

**Field Training Project** — The primary goal is to demonstrate the ability to build an end-to-end AI system combining text and image generation using fully free resources, supported by a documented model comparison methodology.

---

## ✨ How It Works

1. The user provides a brief describing the brand's **industry, target audience, personality, tone, and objective**.
2. A text model, **Qwen3-8B**, generates the brand name, slogan, color palette, and typography recommendations.
3. An image model, **FLUX.1-schnell**, generates a logo mark based on the visual style extracted from the generated brand specification.
4. The complete result is presented through an interactive **Gradio** interface.

---

## 🧠 Models Used

| Task                                   | Model                                             | Why                                                                                                   |
| -------------------------------------- | ------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Text generation (name, slogan, colors) | **Qwen3-8B** — self-hosted, 4-bit quantized       | Apache 2.0 license, unrestricted, and achieved strong performance across all 30 test cases            |
| Logo generation                        | **FLUX.1-schnell** — self-hosted, 4-bit quantized | Open-weight model with lower resource requirements and faster generation than the tested alternatives |

### Models Tested and Rejected

Several models were evaluated during development and documented in [`docs/methodology.md`](docs/methodology.md):

* **LiquidAI/LFM2.5-2.6B** — Failed to consistently produce valid structured JSON.
* **Stable Diffusion 3 Medium** — Encountered a technical compatibility issue in the development environment.
* **Qwen-Image-2.1** — Technically successful, but not selected as the final primary model.
* **PlaygroundV2.5** — Technically successful, but not selected as the final primary model.

The final model selection was based on technical compatibility, output quality, resource requirements, and performance across the standardized test cases.

---

## 📁 Project Structure

```text
brandora/
├── app.py                    # Entry point — Gradio interface
├── scripts/
│   └── run_text_gen.py       # Runs Qwen3-8B as a separate process for memory management
├── src/
│   ├── text_generator.py     # Loads and calls Qwen3-8B
│   ├── brand_package.py      # Creative prompt and brand specification generation
│   ├── name_generator.py     # Extracts the brand name from the specification
│   ├── slogan_generator.py   # Extracts the slogan from the specification
│   ├── logo_generator.py     # Loads and calls FLUX.1-schnell
│   └── logo_prompt.py        # Builds the image-generation prompt from the specification
│   └── evaluator.py          # Calculates color contrast using WCAG criteria
├── data/
│   └── test_briefs.json      # 30 standardized test cases for model comparison
├── notebooks/                # Kaggle notebooks for testing individual models
├── docs/
│   └── methodology.md        # Model comparison methodology and rejection decisions
└── evaluation/
    └── rubric.md             # Human evaluation criteria
```

---

## 🚀 Running the Project on Kaggle

Brandora requires a GPU and was developed and tested on a **Tesla T4 with 16 GB VRAM**. Running the full system locally requires a GPU with sufficient VRAM.

### 1. Clone the Repository

Store your GitHub Personal Access Token as a Kaggle Secret named `GITHUB_TOKEN`, then run:

```python
from kaggle_secrets import UserSecretsClient

user_secrets = UserSecretsClient()
GITHUB_TOKEN = user_secrets.get_secret("GITHUB_TOKEN")

repo_url = f"https://{GITHUB_TOKEN}@github.com/maram-elaian/brandora.git"
!git clone --depth 1 {repo_url} /kaggle/working/brandora_repo

%cd /kaggle/working/brandora_repo
```

### 2. Install Dependencies

```python
!pip install -r requirements.txt -q
```

### 3. Configure the Hugging Face Token

A Hugging Face token is required to download **FLUX.1-schnell**.

First, accept the model's access terms on Hugging Face, then store your token as a Kaggle Secret named `HF_TOKEN`.

```python
import os

os.environ["HF_TOKEN"] = user_secrets.get_secret("HF_TOKEN")
```

### 4. Launch the Interface

```python
!python app.py
```

A public Gradio URL will be generated. Open the URL in any browser to access the application.

> **⏱️ Generation Time:** Each generation currently takes approximately **8 minutes**. Qwen3-8B and FLUX are loaded from scratch for each request to prevent GPU memory conflicts when running both models on a single 16 GB GPU. This is a known and intentional resource-management limitation, not an application error.

---

## ⚙️ GPU Requirements

* **Minimum VRAM:** 16 GB
* **Tested GPU:** NVIDIA Tesla T4
* **Quantization:** 4-bit using `bitsandbytes`
* Both Qwen3-8B and FLUX.1-schnell use 4-bit quantization to fit within the available VRAM.

---

## 📊 Evaluation Methodology

All tested models were evaluated using the **same 30 standardized brand briefs** stored in [`data/test_briefs.json`](data/test_briefs.json).

The experiments use consistent test cases and evaluation criteria to make model comparisons more meaningful.

Detailed experiment logs, technical issues, solutions, model comparisons, and rejection decisions are documented in:

* [`docs/methodology.md`](docs/methodology.md)
* [`evaluation/rubric.md`](evaluation/rubric.md)

The evaluation combines technical validation with human assessment of the generated brand outputs.

---

## 🔜 Future Improvements

The following improvements are planned but are **outside the scope of the current delivery**:

* Add an option to select an alternative image-generation model such as **PlaygroundV2.5**.
* Separate text generation from logo generation: first present three brand name/color proposals, then generate the logo after the user selects one.
* Export a complete **Brand Kit as PDF**.
* Improve response time by keeping models loaded in memory instead of reloading them for every request.
