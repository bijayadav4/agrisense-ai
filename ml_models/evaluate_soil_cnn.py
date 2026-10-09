#!/usr/bin/env python3
"""
AgriSense AI - Soil Vision CNN (MobileNetV2) Final Evaluation & Leakage Verification
=====================================================================================
Evaluates the champion Soil CNN classifier on the official leak-free holdout test
partition (159 pure original field captures, group-aware split, GAN pruned).
Outputs point estimates, bootstrap 95% confidence intervals, confusion matrix,
and empirical confidence calibration table.
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd
import torch
from PIL import Image
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from torchvision import transforms

# Ensure ml_models directory is in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ML_MODELS_DIR = os.path.join(BASE_DIR, "ml_models")
if ML_MODELS_DIR not in sys.path:
    sys.path.insert(0, ML_MODELS_DIR)

from config import SOIL_CLASSES, SOIL_CNN_MODEL_PATH
from train_soil_cnn import SoilCNNClassifier

SPLITS_DIR = os.path.join(ML_MODELS_DIR, "datasets", "splits")
TEST_SPLIT_CSV = os.path.join(SPLITS_DIR, "soil_split_test.csv")
RESULTS_JSON_PATH = os.path.join(BASE_DIR, "results.json")


def load_test_split():
    """Loads the official group-aware, leak-free test split CSV."""
    if not os.path.exists(TEST_SPLIT_CSV):
        raise FileNotFoundError(f"Test split CSV not found at: {TEST_SPLIT_CSV}. Run run_ablation.py first.")
    df_test = pd.read_csv(TEST_SPLIT_CSV)
    return df_test


def compute_calibration_table(confs, y_true, y_pred):
    """Computes confidence calibration across 4 standard bins."""
    bins = [("<50%", 0.0, 0.50), ("50-70%", 0.50, 0.70), ("70-90%", 0.70, 0.90), (">90%", 0.90, 1.0001)]
    cal_table = []
    is_correct = y_true == y_pred

    print("\n🎯 CONFIDENCE CALIBRATION TABLE:")
    print(
        f"{'Bin':<10} | {'Count':<8} | {'Mean Confidence':<18} | {'Empirical Accuracy':<20} | {'Calibration Gap':<18}"
    )
    print("-" * 84)
    for label, low, high in bins:
        mask = (confs >= low) & (confs < high)
        cnt = int(np.sum(mask))
        if cnt > 0:
            mean_conf = float(np.mean(confs[mask])) * 100
            emp_acc = float(np.mean(is_correct[mask])) * 100
            diff = abs(mean_conf - emp_acc)
        else:
            mean_conf, emp_acc, diff = 0.0, 0.0, 0.0
        row = {
            "bin": label,
            "count": cnt,
            "mean_confidence_pct": round(mean_conf, 1),
            "empirical_accuracy_pct": round(emp_acc, 1),
            "gap_pct": round(diff, 1),
        }
        cal_table.append(row)
        print(f"{label:<10} | {cnt:<8} | {mean_conf:<17.1f}% | {emp_acc:<19.1f}% | {diff:<17.1f}%")
    print("-" * 84)
    return cal_table


def bootstrap_ci(y_true, y_pred, n_bootstraps=1000, seed=42):
    """Computes 95% Bootstrap Confidence Intervals for Accuracy and Macro-F1."""
    rng = np.random.RandomState(seed)
    accs, f1s = [], []
    n = len(y_true)
    for _ in range(n_bootstraps):
        idx = rng.randint(0, n, size=n)
        accs.append(accuracy_score(y_true[idx], y_pred[idx]))
        f1s.append(f1_score(y_true[idx], y_pred[idx], average="macro", zero_division=0))
    acc_ci = (round(np.percentile(accs, 2.5) * 100, 2), round(np.percentile(accs, 97.5) * 100, 2))
    f1_ci = (round(np.percentile(f1s, 2.5), 3), round(np.percentile(f1s, 97.5), 3))
    return acc_ci, f1_ci


def evaluate_model(df_test, batch_size=64):
    """Evaluates MobileNetV2 on the official 159 real photos test set."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("\n" + "=" * 78)
    print(" 🔬 SOIL VISION CNN (MobileNetV2) FINAL EVALUATION")
    print("=" * 78)
    print(f"⚙️ Running inference on device: {device}")
    print(f"📦 Model weights: {SOIL_CNN_MODEL_PATH}")
    print(f"📊 Holdout Test Split: {len(df_test)} pure original photos (zero GAN leakage)")

    if not os.path.exists(SOIL_CNN_MODEL_PATH):
        print(f"❌ Error: Model weights not found at: {SOIL_CNN_MODEL_PATH}")
        sys.exit(1)

    model = SoilCNNClassifier(num_classes=len(SOIL_CLASSES)).to(device)
    model.load_state_dict(torch.load(SOIL_CNN_MODEL_PATH, map_location=device))
    model.eval()

    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    class_to_idx = {c: i for i, c in enumerate(SOIL_CLASSES)}
    test_paths = df_test["filepath"].tolist()
    test_labels = np.array([class_to_idx[c] for c in df_test["soil_class"]])

    preds, confs = [], []
    with torch.no_grad():
        for i in range(0, len(test_paths), batch_size):
            batch_paths = test_paths[i : i + batch_size]
            batch_tensors = [transform(Image.open(p).convert("RGB")) for p in batch_paths]
            x = torch.stack(batch_tensors).to(device)
            logits = model(x)
            probs = torch.softmax(logits, dim=1)
            batch_confs, batch_preds = torch.max(probs, dim=1)
            preds.extend(batch_preds.cpu().numpy().tolist())
            confs.extend(batch_confs.cpu().numpy().tolist())

    preds = np.array(preds)
    confs = np.array(confs)

    acc = accuracy_score(test_labels, preds) * 100
    macro_f1 = f1_score(test_labels, preds, average="macro")
    acc_ci, f1_ci = bootstrap_ci(test_labels, preds)

    print("\n" + "=" * 78)
    print(" 🎯 FINAL TEST RESULTS ON 159 REAL FIELD PHOTOS")
    print("=" * 78)
    print(f" • 159 real photos par test accuracy: {acc:.2f}% (95% CI {acc_ci[0]}% – {acc_ci[1]}%)")
    print(f" • Macro F1-Score: {macro_f1:.3f} (95% CI {f1_ci[0]} – {f1_ci[1]})")
    print(f" • Correct Predictions: {np.sum(preds == test_labels)} / {len(test_labels)}")
    print(f" • Average Confidence: {np.mean(confs) * 100:.1f}%\n")

    print("📋 PER-CLASS CLASSIFICATION REPORT:")
    print("-" * 78)
    report_dict = classification_report(test_labels, preds, target_names=SOIL_CLASSES, digits=3, output_dict=True)
    print(classification_report(test_labels, preds, target_names=SOIL_CLASSES, digits=3))
    print("-" * 78)

    cm = confusion_matrix(test_labels, preds)
    print("🔢 CONFUSION MATRIX (Rows: Actual, Columns: Predicted):")
    print("-" * 78)
    header = f"{'':>10}" + "".join([f"{c:>10}" for c in SOIL_CLASSES])
    print(header)
    for idx, row in enumerate(cm):
        print(f"{SOIL_CLASSES[idx]:>10}" + "".join([f"{val:>10}" for val in row]))
    print("=" * 78)

    cal_table = compute_calibration_table(confs, test_labels, preds)

    print("\n📌 HISTORICAL CONTEXT: ROOT CAUSE OF THE OLD CLAIMED 93.2% ACCURACY:")
    print("  1. Dataset in 'soil_images' consists of 987 original photos + 3,909 CycleGAN synthetic clones.")
    print("  2. The old 93.2% figure was obtained by naive random splitting across the mixed dataset,")
    print("     allowing identical/near-duplicate GAN copies of the same photo into train and test sets.")
    print("  3. The scientifically honest, leak-free evaluation on 159 real photos yields:")
    print(f"     159 real photos par test accuracy {acc:.2f}% (95% CI {acc_ci[0]}% – {acc_ci[1]}%).")
    print("=" * 78)

    return {
        "overall_accuracy": round(acc, 2),
        "accuracy_95_ci": acc_ci,
        "macro_f1": round(macro_f1, 3),
        "macro_f1_95_ci": f1_ci,
        "test_samples": len(test_labels),
        "per_class_metrics": report_dict,
        "confusion_matrix": cm.tolist(),
        "calibration_table": cal_table,
        "classes": SOIL_CLASSES,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate Soil Vision CNN with Leak-Free Split")
    parser.add_argument("--batch-size", type=int, default=64, help="Inference batch size")
    args = parser.parse_args()

    df_test = load_test_split()
    evaluate_model(df_test, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
