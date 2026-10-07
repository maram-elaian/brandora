# Brandora: CLIP Evaluation Summary

- Number of logos: **21**
- Random-chance retrieval accuracy: **0.048**

| Version | Concept score | Margin | Retrieval acc. | Text-free | Palette dist. |
|---|---|---|---|---|---|
| FLUX raw | 0.306 | +0.075 | 0.571 | 0.803 | 11.4 |
| After palette | 0.303 | +0.067 | 0.619 | 0.797 | 8.7 |

## How to read
- **Retrieval acc.** must be well above random chance.
- **Margin** above 0 means the logo matches its own concept more than other brands' concepts.
- **Text-free** close to 1 means no accidental letters.
- **Palette dist.** close to 0 means the logo uses Qwen's colors.