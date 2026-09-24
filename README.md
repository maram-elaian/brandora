

# Brandora

**AI-Powered Brand Specification Generator**

A research project that compares different Large Language Models (LLMs) in generating structured Brand Specifications from natural language briefs, as a foundation for automated logo generation.

---

## Overview

Brandora automates the traditionally manual process of converting a simple business description (brief) into a comprehensive, structured Brand Specification in JSON format. This specification then serves as the input for image generation models to produce logos.

### Workflow
```
Text Brief → [LLM] → Brand Specification (JSON) → [Image Model] → Logo
```

### Research Question
> "Which LLM performs best in transforming unstructured text briefs into structured brand specifications in terms of accuracy, speed, and cost?"

---

## Models Tested

| Model | Size | Platform | Status |
|-------|------|----------|--------|
| **Mercury 2.5** | Proprietary | Inception Labs API | ✅ Operational |
| **Qwen3-8B** | 8B | Local (Kaggle GPU) | ✅ Operational |
| **LFM2.5-2.6B** | 2.6B | Local (Kaggle GPU) | ⚠️ Limited |

### Initial Results (5 test cases)

| Model | Success Rate | Avg Score | Notes |
|-------|-------------|-----------|-------|
| Mercury 2.5 | 5/5 (100%) | 6.0/6 | Creative naming, API-based |
| Qwen3-8B | 5/5 (100%) | 6.0/6 | Structured output, local |
| LFM2.5-2.6B | 0/5 (0%) | 0.0/6 | JSON extraction failure |

**Key Finding:** Smaller models (2.6B) consume most tokens on internal reasoning and fail to produce structured JSON output, even with increased `max_tokens` (500 → 1000).

---

## Project Structure

```
brandora/
├── 02_brand_specification.ipynb   # Proof of concept
├── 03_text_model_comparison.ipynb # Full comparison pipeline
├── data/
│   └── test_briefs.json           # 30 test cases
├── evaluation/
│   ├── rubric.md                  # Evaluation criteria
│   └── results/                   # Generated results
├── fair_comparison_results.csv    # Initial comparison (5 cases)
├── fair_comparison_results.json   # Detailed JSON results
├── lfm25_improved_results.csv     # LFM2.5 retest results
├── lfm25_improved_results.json    # LFM2.5 detailed results
└── README.md
```

---

## Technical Stack

- **Platform:** Kaggle Notebooks
- **Hardware:** Tesla T4 GPU (16GB)
- **Language:** Python 3.12
- **Key Libraries:**
  - `transformers` - Model loading and inference
  - `torch` - Deep learning framework
  - `bitsandbytes` - 4-bit quantization
  - `openai` - API client (Inception Labs compatibility)
  - `huggingface_hub` - Model repository access
  - `pandas` - Results analysis

---

## Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/maram-elaian/brandora.git
cd brandora
```

### 2. Kaggle Environment Setup
1. Open notebook in Kaggle
2. Enable GPU: **Settings → Accelerator → GPU T4 x2**
3. Add secrets in **Add-ons → Secrets**:
   - `INCEPTION_API_KEY` - For Mercury 2.5
   - `HF_TOKEN` - For faster HuggingFace downloads

### 3. Install Dependencies
```bash
pip install -U bitsandbytes
pip install -U torchaudio  # Fix CUDA compatibility
```

### 4. Download Test Data
Data is fetched directly from GitHub:
```python
import requests
url = "https://raw.githubusercontent.com/maram-elaian/brandora/main/data/test_briefs.json"
briefs = requests.get(url).json()
```

---

## Usage

### Basic Model Comparison (5 cases)
Run the comparison pipeline:
```python
# Load models and run comparison
# Output: fair_comparison_results.csv & .json
```

### Retest LFM2.5 with Improved Settings
```python
# Increased max_tokens to 1000
# Stricter prompt (JSON only, no explanation)
# Output: lfm25_improved_results.csv & .json
```

### Full Evaluation (30 cases) - Coming Soon
Extended testing with comprehensive statistical analysis.

---

## Prompt Design

All models use the **same unified prompt** to ensure fair comparison:

**System Prompt:**
```
You are an expert Brand Strategist.
Given a brand brief, generate a complete Brand Specification.
You MUST reply ONLY in valid JSON format, no markdown, no extra text.
```

**User Prompt Template:**
```
Analyze this brief and generate the specification:
Industry: {industry}
Target Audience: {target_audience}
Brand Purpose: {brand_purpose}
Personality: {personality}
Tone: {tone}

Generate a JSON object with EXACTLY this structure:
{
  "brand_name": "string",
  "tagline": "string",
  "color_palette": ["color1", "color2", "color3"],
  "typography": "string",
  "visual_style": "string",
  "personality_traits": ["trait1", "trait2", "trait3"]
}
```

---

## Key Technical Challenges Solved

### 1. Library Version Conflicts
**Problem:** PyTorch (CUDA 13.0) vs TorchAudio (CUDA 12.8)  
**Solution:** Upgrade `torchaudio` to match PyTorch version

### 2. GPU Memory Constraints
**Problem:** Qwen3-8B (16GB) exceeds T4 memory  
**Solution:** 4-bit quantization via `BitsAndBytesConfig`

### 3. JSON Extraction
**Problem:** Models produce plain text instead of JSON  
**Solution:** Regex-based JSON extraction with `re.search(r'\{.*\}', text)`

### 4. Fair Comparison
**Problem:** Different configurations across models  
**Solution:** Unified prompt, same test cases, consistent evaluation metrics

### 5. Reasoning Mode Overhead
**Problem:** LFM2.5 consumes tokens on internal planning  
**Solution:** `max_tokens=1000` + strict "no explanation" prompt

---

## Evaluation Criteria

Each model output is scored on 6 fields (0-6 scale):
- `brand_name` - Creative and appropriate name
- `tagline` - Memorable short phrase
- `color_palette` - Array of 3 colors
- `typography` - Font recommendation
- `visual_style` - Design direction
- `personality_traits` - Array of traits

See `evaluation/rubric.md` for detailed scoring guidelines.

---

## Results Summary

### Quantitative Metrics
- **Success Rate:** Percentage of valid JSON outputs
- **Quality Score:** Average score out of 6
- **Token Usage:** Total tokens consumed per request
- **Latency:** Response time per request

### Qualitative Insights
- Mercury 2.5 produces more creative, marketing-oriented names
- Qwen3-8B provides more descriptive, logical naming
- LFM2.5-2.6B insufficient for complex structured output tasks

---

## Next Steps

1. Expand testing to full 30-case dataset
2. Add latency and token cost measurements
3. Qualitative human evaluation of creativity
4. Integration with image generation models (FLUX, Qwen-Image)
5. End-to-end logo generation pipeline

---

## License

This project is developed for academic research purposes.

---

## Contact

**Developer:** Maram Ashraf  
**Repository:** [github.com/maram-elaian/brandora](https://github.com/maram-elaian/brandora)

---

## Citation

If you use this work in your research, please cite:

```bibtex
@misc{brandora2026,
  title={Brandora: AI-Powered Brand Specification Generator},
  author={Ashraf, Maram},
  year={2026},
  publisher={GitHub},
  url={https://github.com/maram-elaian/brandora}
}
