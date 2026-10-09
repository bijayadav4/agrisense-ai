#!/usr/bin/env python3
"""
AgriSense AI - Soil Vision CNN External Field Evaluation Tool
=============================================================
Evaluates the deployed MobileNetV2 Soil Classifier on an external, out-of-distribution
dataset (such as smartphone camera captures, new farmer field submissions, or third-party datasets).

IMPORTANT DISTINCTION:
Metrics computed by this script represent EXTERNAL VALIDATION (Field Test) and are reported
SEPARATELY from the internal holdout test benchmark. External field accuracy reflects
real-world domain shifts (lighting variations, phone cameras, moisture differences).

Usage:
    python evaluate_external.py --images-dir /path/to/phone_photos --labels-csv /path/to/labels.csv
    python evaluate_external.py -i /path/to/phone_photos -l /path/to/labels.csv --output-csv predictions_external.csv
"""

import os
import sys
import math
import argparse
import json
import torch
import numpy as np
import pandas as pd
from PIL import Image
from torchvision import transforms
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    f1_score, precision_score, recall_score
)

# Add ml_models to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ML_MODELS_DIR = os.path.join(BASE_DIR, "ml_models")
if ML_MODELS_DIR not in sys.path:
    sys.path.insert(0, ML_MODELS_DIR)

from train_soil_cnn import SoilCNNClassifier
from config import SOIL_CNN_MODEL_PATH, SOIL_CLASSES


def parse_args():
    parser = argparse.ArgumentParser(
        description="AgriSense AI - External Field Test Evaluation Tool for Soil Vision CNN"
    )
    parser.add_argument(
        "-i", "--images-dir",
        type=str,
        required=True,
        help="Path to directory containing external test images (phone photos, new field samples)."
    )
    parser.add_argument(
        "-l", "--labels-csv",
        type=str,
        required=True,
        help="Path to CSV containing columns 'filename' (or 'filepath') and 'soil_class' (or 'label')."
    )
    parser.add_argument(
        "-m", "--model-path",
        type=str,
        default=SOIL_CNN_MODEL_PATH,
        help=f"Path to trained PyTorch model checkpoint (default: {SOIL_CNN_MODEL_PATH})."
    )
    parser.add_argument(
        "-t", "--temperature",
        type=float,
        default=None,
        help="Optional temperature scalar T for calibration (default: loaded from results.json if available)."
    )
    parser.add_argument(
        "-o", "--output-csv",
        type=str,
        default=None,
        help="Optional destination path to save per-image predictions CSV."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=70.0,
        help="Confidence threshold below which sample is flagged for lab soil testing (default: 70.0%%)."
    )
    return parser.parse_args()


def wilson_score_interval(k, n, confidence=0.95):
    """Computes exact Wilson score confidence interval for binomial proportion k/n."""
    if n == 0:
        return 0.0, 0.0, 0.0
    z = 1.95996  # 95% CI normal quantile
    p = k / n
    denom = 1 + (z**2) / n
    center = (p + (z**2) / (2 * n)) / denom
    half = (z / denom) * math.sqrt((p * (1 - p) / n) + (z**2) / (4 * (n**2)))
    low = max(0.0, center - half)
    high = min(1.0, center + half)
    return p, low, high


def main():
    args = parse_args()
    
    print("\n" + "=" * 80)
    print(" 📱 AGRISENSE AI - EXTERNAL FIELD TEST EVALUATION")
    print("=" * 80)
    print(" ⚠️  CRITICAL NOTE: This is an EXTERNAL INDEPENDENT TEST dataset.")
    print("     Metrics here are distinct from the benchmark holdout test set")
    print("     and quantify real-world smartphone camera / domain shift robustness.")
    print("=" * 80)

    if not os.path.exists(args.images_dir):
        print(f"❌ Error: Images directory not found at: {args.images_dir}")
        sys.exit(1)

    if not os.path.exists(args.labels_csv):
        print(f"❌ Error: Labels CSV not found at: {args.labels_csv}")
        sys.exit(1)

    # Load labels
    df_labels = pd.read_csv(args.labels_csv)
    fname_col = next((c for c in ['filename', 'image', 'filepath', 'file'] if c in df_labels.columns), None)
    label_col = next((c for c in ['soil_class', 'label', 'class', 'target'] if c in df_labels.columns), None)

    if not fname_col or not label_col:
        print(f"❌ Error: CSV must have filename/image column and soil_class/label column. Found: {list(df_labels.columns)}")
        sys.exit(1)

    # Load model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n⚙️ Loading Model: {args.model_path}")
    print(f"⚙️ Compute Device: {device}")
    
    model = SoilCNNClassifier(num_classes=len(SOIL_CLASSES)).to(device)
    if not os.path.exists(args.model_path):
        print(f"❌ Error: Model checkpoint not found at: {args.model_path}")
        sys.exit(1)

    checkpoint = torch.load(args.model_path, map_location=device)
    model.load_state_dict(checkpoint)
    model.eval()

    # Temperature scaling
    temperature = args.temperature
    if temperature is None:
        results_json_path = os.path.join(BASE_DIR, "results.json")
        if os.path.exists(results_json_path):
            try:
                with open(results_json_path, 'r') as f:
                    meta = json.load(f)
                    temperature = meta.get("temperature_scaling", {}).get("optimal_temperature_T", 1.0)
            except Exception:
                temperature = 1.0
        else:
            temperature = 1.0

    print(f"🌡️ Temperature Scaling Factor: T = {temperature:.4f}")
    print(f"🛡️ Low-Confidence Flag Threshold: {args.threshold:.1f}%\n")

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    results = []
    y_true_list = []
    y_pred_list = []
    low_conf_count = 0

    print(f"🔍 Evaluating {len(df_labels)} external samples from: {args.images_dir}")

    for idx, row in df_labels.iterrows():
        raw_fname = str(row[fname_col]).strip()
        img_p = raw_fname if os.path.isabs(raw_fname) else os.path.join(args.images_dir, raw_fname)
        
        if not os.path.exists(img_p):
            print(f"⚠️ Warning: Image not found: {img_p}. Skipping.")
            continue
            
        true_cls = str(row[label_col]).strip()
        if true_cls not in SOIL_CLASSES:
            print(f"⚠️ Warning: Unknown class '{true_cls}' for image {raw_fname}. Skipping.")
            continue

        try:
            img = Image.open(img_p).convert("RGB")
            t_img = transform(img).unsqueeze(0).to(device)
            with torch.no_grad():
                logits = model(t_img)
                scaled_logits = logits / temperature
                probs = torch.softmax(scaled_logits, dim=1).cpu().numpy()[0]
                pred_idx = int(np.argmax(probs))
                pred_cls = SOIL_CLASSES[pred_idx]
                conf = float(probs[pred_idx]) * 100

            is_correct = (pred_cls == true_cls)
            is_low_conf = (conf < args.threshold)
            if is_low_conf:
                low_conf_count += 1

            y_true_list.append(SOIL_CLASSES.index(true_cls))
            y_pred_list.append(pred_idx)

            res_record = {
                'filename': raw_fname,
                'ground_truth': true_cls,
                'predicted_class': pred_cls,
                'confidence_pct': round(conf, 2),
                'correct': is_correct,
                'low_confidence_flag': is_low_conf,
                'recommendation': "Laboratory soil test recommended" if is_low_conf else "Standard recommendation"
            }
            for c_idx, c_name in enumerate(SOIL_CLASSES):
                res_record[f'prob_{c_name}'] = round(float(probs[c_idx]), 4)
            results.append(res_record)
        except Exception as e:
            print(f"❌ Error processing {raw_fname}: {e}")

    if len(results) == 0:
        print("❌ Error: No valid external samples could be evaluated.")
        sys.exit(1)

    y_true = np.array(y_true_list)
    y_pred = np.array(y_pred_list)
    total_eval = len(results)
    total_correct = int(np.sum(y_true == y_pred))
    acc = (total_correct / total_eval) * 100
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(SOIL_CLASSES))))

    print("\n" + "=" * 80)
    print(" 📊 EXTERNAL TEST PERFORMANCE SUMMARY")
    print("=" * 80)
    print(f"Total External Photos Evaluated : {total_eval}")
    print(f"Correct Predictions             : {total_correct} / {total_eval}")
    print(f"Overall External Accuracy       : {acc:.2f}%")
    print(f"Macro F1-Score                  : {macro_f1:.3f}")
    print(f"Weighted F1-Score               : {weighted_f1:.3f}")
    print(f"Low-Confidence Flagged (<{args.threshold:.0f}%)  : {low_conf_count} ({low_conf_count/total_eval*100:.1f}%)")

    print("\n" + "-" * 80)
    print(" 🔬 PER-CLASS METRICS & WILSON 95% CONFIDENCE INTERVALS ON RECALL:")
    print("-" * 80)
    print(f"{'Class':<10} | {'Count (n)':<10} | {'Precision':<11} | {'Recall':<10} | {'Wilson 95% CI':<24} | {'F1':<8}")
    print("-" * 80)

    for idx, c in enumerate(SOIL_CLASSES):
        tp = cm[idx, idx]
        support = int(np.sum(y_true == idx))
        prec = precision_score(y_true, y_pred, labels=[idx], average='micro', zero_division=0)
        rec = recall_score(y_true, y_pred, labels=[idx], average='micro', zero_division=0)
        f1 = f1_score(y_true, y_pred, labels=[idx], average='micro', zero_division=0)
        
        _, w_low, w_high = wilson_score_interval(tp, support)
        ci_str = f"[{w_low*100:.1f}%, {w_high*100:.1f}%]"
        print(f"{c:<10} | {support:<10} | {prec*100:<10.1f}% | {rec*100:<9.1f}% | {ci_str:<24} | {f1:<8.3f}")

    print("-" * 80)
    print("\nConfusion Matrix (Rows = Ground Truth, Cols = Predicted [Black, Clayey, Loamy, Red, Sandy]):")
    print(cm)

    # Save output CSV if requested
    if args.output_csv:
        df_out = pd.DataFrame(results)
        df_out.to_csv(args.output_csv, index=False)
        print(f"\n💾 Predictions saved to: {args.output_csv}")

    print("\n✅ External Evaluation Completed.")


if __name__ == "__main__":
    main()
