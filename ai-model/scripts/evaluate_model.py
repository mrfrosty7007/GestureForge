"""Model Evaluation and Benchmark Reporting for GestureForge.

Reuses the project's existing GestureClassifier model class, checkpoint loading logic,
and dataset partitioning to evaluate model accuracy, precision, recall, F1 score,
and confusion matrix. Exports visual assets and markdown documentation.

Usage:
    python scripts/evaluate_model.py
    python ai-model/scripts/evaluate_model.py
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path
from typing import Any

# Ensure script directory, ai-model directory, and repository root are in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
AI_MODEL_DIR = SCRIPT_DIR.parent
ROOT_DIR = AI_MODEL_DIR.parent

for path_entry in (str(SCRIPT_DIR), str(AI_MODEL_DIR), str(ROOT_DIR)):
    if path_entry not in sys.path:
        sys.path.insert(0, path_entry)

import joblib
import matplotlib

matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt
import numpy as np
import sklearn
from gesture_classifier import GestureClassifier
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from train_model import (
    MODEL_OUTPUT_PATH,
    RAW_DATASET_PATH,
    TARGET_GESTURES,
    load_test_dataset,
)


def evaluate_model(
    model_path: Path | str = MODEL_OUTPUT_PATH,
    dataset_path: Path | str = RAW_DATASET_PATH,
    cm_output_path: Path | str | None = None,
    report_output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Runs complete model evaluation on the test partition, saves confusion matrix,

    and exports markdown documentation.
    """
    model_path = Path(model_path)
    dataset_path = Path(dataset_path)

    assets_dir = AI_MODEL_DIR / "assets"
    docs_dir = AI_MODEL_DIR / "docs"
    assets_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    if cm_output_path is None:
        cm_output_path = assets_dir / "confusion_matrix.png"
    else:
        cm_output_path = Path(cm_output_path)
        cm_output_path.parent.mkdir(parents=True, exist_ok=True)

    if report_output_path is None:
        report_output_path = docs_dir / "model_evaluation.md"
    else:
        report_output_path = Path(report_output_path)
        report_output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("GestureForge — Hand Gesture Recognition Model Evaluation")
    print("=" * 65)

    # 1. Load trained checkpoint using project's GestureClassifier logic
    print(f"\n[1/5] Loading model checkpoint from: {model_path}")
    if not model_path.exists():
        raise FileNotFoundError(f"Model checkpoint not found at: {model_path}")

    classifier = GestureClassifier(model_path=model_path)
    if classifier.model is None:
        raise RuntimeError(f"Failed to load scikit-learn model from: {model_path}")

    # Inspect raw checkpoint bundle for metadata
    checkpoint_bundle: dict[str, Any] = {}
    try:
        raw_loaded = joblib.load(model_path)
        if isinstance(raw_loaded, dict):
            checkpoint_bundle = raw_loaded
    except Exception:
        checkpoint_bundle = {}

    classes = classifier.class_names or checkpoint_bundle.get(
        "classes", TARGET_GESTURES
    )
    framework_name = f"scikit-learn ({type(classifier.model).__name__})"
    device_name = "CPU"
    checkpoint_name = model_path.name

    print(f"      Model type: {framework_name}")
    print(f"      Target classes ({len(classes)}): {classes}")

    # 2. Load test dataset using existing test partition logic
    print(f"\n[2/5] Loading test dataset from: {dataset_path}")
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset CSV not found at: {dataset_path}")

    X_test, y_test = load_test_dataset(dataset_path, test_size=0.20, random_state=42)
    print(
        f"      Test samples: {X_test.shape[0]} | Feature dimension: {X_test.shape[1]}"
    )

    # 3. Run inference on test dataset
    print("\n[3/5] Running inference on test dataset...")
    y_pred = classifier.model.predict(X_test)

    # Compute metrics using sklearn.metrics
    acc = accuracy_score(y_test, y_pred)
    prec_weighted = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    prec_macro = precision_score(y_test, y_pred, average="macro", zero_division=0)
    rec_weighted = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    rec_macro = recall_score(y_test, y_pred, average="macro", zero_division=0)
    f1_weighted = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)

    cm = confusion_matrix(y_test, y_pred, labels=classes)
    report_dict = classification_report(
        y_test,
        y_pred,
        labels=classes,
        target_names=classes,
        output_dict=True,
        zero_division=0,
    )
    report_text = classification_report(
        y_test,
        y_pred,
        labels=classes,
        target_names=classes,
        zero_division=0,
    )

    print("\n" + "-" * 65)
    print(f"Overall Accuracy:       {acc * 100:.2f}%")
    print(f"Precision (Weighted):   {prec_weighted:.4f}  |  (Macro): {prec_macro:.4f}")
    print(f"Recall (Weighted):      {rec_weighted:.4f}  |  (Macro): {rec_macro:.4f}")
    print(f"F1 Score (Weighted):    {f1_weighted:.4f}  |  (Macro): {f1_macro:.4f}")
    print("-" * 65)
    print("\nClassification Report:\n")
    print(report_text)

    # 4. Generate and save confusion matrix
    print(f"\n[4/5] Generating confusion matrix plot -> {cm_output_path}")
    fig, ax = plt.subplots(figsize=(8, 7))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=classes)
    disp.plot(
        ax=ax,
        cmap="Blues",
        xticks_rotation=45,
        values_format="d",
        colorbar=True,
    )
    ax.set_title(
        "GestureForge Gesture Classification — Confusion Matrix",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    plt.tight_layout()
    plt.savefig(cm_output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"      Saved confusion matrix image to: {cm_output_path.resolve()}")

    # 5. Export Markdown report
    print(f"\n[5/5] Exporting Markdown evaluation report -> {report_output_path}")
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    # Build per-class breakdown markdown table
    per_class_rows = []
    for cls_name in classes:
        cls_metrics = report_dict.get(cls_name, {})
        c_prec = cls_metrics.get("precision", 0.0)
        c_rec = cls_metrics.get("recall", 0.0)
        c_f1 = cls_metrics.get("f1-score", 0.0)
        c_supp = int(cls_metrics.get("support", 0))
        per_class_rows.append(
            f"| **{cls_name}** | {c_prec:.4f} | {c_rec:.4f} | {c_f1:.4f} | {c_supp} |"
        )
    per_class_table = "\n".join(per_class_rows)

    # Build confusion matrix text table
    cm_header = "| True \\ Pred | " + " | ".join(f"**{c}**" for c in classes) + " |"
    cm_sep = "| :--- | " + " | ".join(":---:" for _ in classes) + " |"
    cm_rows = []
    for idx, cls_name in enumerate(classes):
        row_vals = " | ".join(str(cm[idx][j]) for j in range(len(classes)))
        cm_rows.append(f"| **{cls_name}** | {row_vals} |")
    cm_table = "\n".join([cm_header, cm_sep] + cm_rows)

    # Markdown document content
    markdown_content = f"""# 📊 GestureForge Model Evaluation Report

Comprehensive evaluation report for the GestureForge hand gesture recognition machine learning classifier.

---

## ℹ️ Model & Benchmark Information

| Parameter | Value |
| :--- | :--- |
| **Checkpoint Name** | `{checkpoint_name}` |
| **Framework** | `{framework_name}` |
| **Device** | `{device_name}` |
| **Feature Dimension** | `63` (21 3D normalized MediaPipe landmarks) |
| **Dataset Source** | `{dataset_path.name}` |
| **Evaluation Split** | 20% Stratified Test Split (seed=42) |
| **Total Test Samples** | `{X_test.shape[0]}` |
| **Target Classes ({len(classes)})** | `{", ".join(classes)}` |
| **Generated At** | `{now_str}` |

---

## 📈 Overall Performance Metrics

| Metric | Score | Percentage |
| :--- | :---: | :---: |
| **Accuracy** | **{acc:.4f}** | **{acc * 100:.2f}%** |
| **Precision (Weighted)** | {prec_weighted:.4f} | {prec_weighted * 100:.2f}% |
| **Precision (Macro)** | {prec_macro:.4f} | {prec_macro * 100:.2f}% |
| **Recall (Weighted)** | {rec_weighted:.4f} | {rec_weighted * 100:.2f}% |
| **Recall (Macro)** | {rec_macro:.4f} | {rec_macro * 100:.2f}% |
| **F1 Score (Weighted)** | **{f1_weighted:.4f}** | **{f1_weighted * 100:.2f}%** |
| **F1 Score (Macro)** | {f1_macro:.4f} | {f1_macro * 100:.2f}% |

---

## 📋 Per-Class Performance Breakdown

| Gesture Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
{per_class_table}
| **Macro Average** | **{report_dict.get("macro avg", {}).get("precision", 0.0):.4f}** | **{report_dict.get("macro avg", {}).get("recall", 0.0):.4f}** | **{report_dict.get("macro avg", {}).get("f1-score", 0.0):.4f}** | **{int(report_dict.get("macro avg", {}).get("support", 0))}** |
| **Weighted Average** | **{report_dict.get("weighted avg", {}).get("precision", 0.0):.4f}** | **{report_dict.get("weighted avg", {}).get("recall", 0.0):.4f}** | **{report_dict.get("weighted avg", {}).get("f1-score", 0.0):.4f}** | **{int(report_dict.get("weighted avg", {}).get("support", 0))}** |

---

## 🔍 Confusion Matrix

![Confusion Matrix](../assets/confusion_matrix.png)

### Tabular Confusion Matrix

{cm_table}

---

## 🔬 Evaluation Methodology

1. **Preprocessing & Normalization**:
   - Each hand instance consists of 21 3D landmarks $(x, y, z)$ provided by Google MediaPipe Hands.
   - Translation variance is eliminated by shifting coordinates relative to the wrist anchor (landmark 0).
   - Scale variance is normalized by dividing coordinates by the maximum Euclidean distance between the wrist and any landmark.
2. **Inference Pipeline**:
   - Features are classified using the trained `RandomForestClassifier` loaded from `ai-model/models/gesture_model.joblib`.
   - Predictions are compared against the ground truth labels from the 20% stratified test set.
3. **Reproducibility**:
   - All random seeds are fixed (`random_state=42`) ensuring fully deterministic and reproducible metrics.
"""

    with open(report_output_path, mode="w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"      Saved markdown report to: {report_output_path.resolve()}")
    print("\n" + "=" * 65)
    print("Evaluation completed successfully!")
    print("=" * 65)

    return {
        "accuracy": float(acc),
        "precision_weighted": float(prec_weighted),
        "precision_macro": float(prec_macro),
        "recall_weighted": float(rec_weighted),
        "recall_macro": float(rec_macro),
        "f1_weighted": float(f1_weighted),
        "f1_macro": float(f1_macro),
        "confusion_matrix": cm.tolist(),
        "cm_image_path": str(cm_output_path),
        "report_path": str(report_output_path),
    }


def main() -> None:
    """CLI entrypoint for standalone evaluation."""
    parser = argparse.ArgumentParser(
        description="Evaluate GestureForge Hand Gesture Recognition Model"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=str(MODEL_OUTPUT_PATH),
        help="Path to trained model checkpoint",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=str(RAW_DATASET_PATH),
        help="Path to dataset CSV",
    )
    parser.add_argument(
        "--cm-output",
        type=str,
        default=None,
        help="Path to save confusion matrix image",
    )
    parser.add_argument(
        "--report-output",
        type=str,
        default=None,
        help="Path to save markdown evaluation report",
    )
    args = parser.parse_args()

    evaluate_model(
        model_path=args.model,
        dataset_path=args.dataset,
        cm_output_path=args.cm_output,
        report_output_path=args.report_output,
    )


if __name__ == "__main__":
    main()
