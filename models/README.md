# Models

Pre-trained model files. Run the training scripts to regenerate them.

| File | Description |
|---|---|
| `crop_model.pkl` | Random Forest crop recommendation classifier |
| `fert_model.pkl` | Random Forest fertilizer recommendation classifier |
| `le_fert.pkl` | Label encoder for fertilizer class names |
| `le_crop.pkl` | Label encoder for crop class names |
| `le_soil.pkl` | Label encoder for soil type |

## Regenerate

```bash
python src/train_crop_model.py
python src/train_fertilizer_model.py
```

> **Note:** The `.pkl` files are excluded from Git by `.gitignore` because of their size (~45 MB total).
> Download them from the [Releases](../../releases) page, or train them yourself using the datasets in `/dataset`.
