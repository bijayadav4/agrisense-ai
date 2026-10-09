#!/usr/bin/env python3
"""
AgriSense AI - Soil Vision CNN Final Rigorous Checks and Evaluation Pipeline
=============================================================================
1. Leak-free component clustering (exact MD5 + pHash <= 6 + numeric prefix).
2. Leakage verification proof: target 0 exact MD5 and 0 pHash <= 6 matches between test and (train_orig, val, safe_gan).
3. Ablation Training (Model A: Originals only; Model B: Originals + Safe GAN) with strict validation-based selection.
4. Export predictions_modelA.csv and predictions_modelB.csv.
5. Confusion matrices, per-class P/R/F1, and Wilson 95% CI on recalls.
6. Temperature scaling (fit strictly on val) and ECE evaluation.
"""

import os
import sys
import re
import json
import hashlib
import time
import math
import numpy as np
import pandas as pd
from PIL import Image
from collections import defaultdict
import networkx as nx
from scipy.optimize import minimize

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms, models
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, classification_report, f1_score,
    recall_score, precision_score, confusion_matrix
)
import imagehash

# Path setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML_MODELS_DIR = os.path.join(BASE_DIR, "ml_models")
if ML_MODELS_DIR not in sys.path:
    sys.path.insert(0, ML_MODELS_DIR)

from config import SOIL_CLASSES, SOIL_DATASET_DIR, SAVED_MODELS_DIR, SOIL_CNN_MODEL_PATH
from train_soil_cnn import SoilCNNClassifier

seed = 42
torch.manual_seed(seed)
np.random.seed(seed)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"⚙️ Compute device: {device}")

# Transforms
transform_eval = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

transform_train = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.15, contrast=0.15),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# -------------------------------------------------------------
# STEP 1: SCAN ALL RAW ORIGINAL IMAGES & DETECT DUPLICATE GRAPH
# -------------------------------------------------------------
print("\n" + "=" * 78)
print(" STEP 1: RAW DATASET SCAN & LEAK-FREE GRAPH CLUSTERING")
print("=" * 78)

orig_dir = os.path.join(BASE_DIR, "archive", "Orignal-Dataset")
class_mapping = {
    'Black': [('Black_Soil', 'Black_Soil')],
    'Clayey': [('Yellow_Soil', 'Yellow_Soil')],
    'Loamy': [('Alluvial_Soil', 'Alluvial_Soil')],
    'Red': [('Red_Soil', 'Red_Soil'), ('Laterite_Soil', 'Laterite_Soil')],
    'Sandy': [('Arid_Soil', 'Arid_Soil')]
}

records = []
for soil_cls, arch_list in class_mapping.items():
    p = os.path.join(SOIL_DATASET_DIR, soil_cls)
    for arch_folder, prefix in arch_list:
        arch_p = os.path.join(orig_dir, arch_folder)
        if not os.path.exists(arch_p):
            continue
        for of in sorted(os.listdir(arch_p)):
            soil_fname = f"{prefix}_{of}"
            full_soil_p = os.path.join(p, soil_fname)
            if not os.path.exists(full_soil_p):
                continue
            with open(full_soil_p, 'rb') as f:
                md5 = hashlib.md5(f.read()).hexdigest()
            with Image.open(full_soil_p) as img:
                ph = imagehash.phash(img.convert('RGB'))
            
            m = re.match(r'^([0-9]+)([a-zA-Z]*)\.(jpe?g|png)$', of, re.IGNORECASE)
            num_prefix = f"{prefix}_{m.group(1)}" if m else soil_fname
            
            records.append({
                'soil_class': soil_cls,
                'prefix': prefix,
                'orig_name': of,
                'filename': soil_fname,
                'filepath': full_soil_p,
                'md5': md5,
                'phash': ph,
                'num_prefix': num_prefix
            })

print(f"📦 Total raw original images scanned: {len(records)}")

# Build connectivity graph to cluster duplicate pairs
G = nx.Graph()
for r in records:
    G.add_node(r['filename'], record=r, soil_class=r['soil_class'])

# Edge 1: Filename numeric prefix (e.g. 12a, 12b)
prefix_map = defaultdict(list)
for r in records:
    prefix_map[r['num_prefix']].append(r['filename'])
for _, fnames in prefix_map.items():
    for i in range(len(fnames)):
        for j in range(i+1, len(fnames)):
            G.add_edge(fnames[i], fnames[j], reason='filename_prefix')

# Edge 2: Exact MD5 matches across raw dataset (the 40 collision pairs)
md5_map = defaultdict(list)
for r in records:
    md5_map[r['md5']].append(r['filename'])
raw_md5_collisions = {k: v for k, v in md5_map.items() if len(v) > 1}
total_md5_pairs = sum(len(v)*(len(v)-1)//2 for v in raw_md5_collisions.values())
print(f"🔍 Raw exact MD5 collision groups: {len(raw_md5_collisions)} (total {total_md5_pairs} pairs)")
for _, fnames in raw_md5_collisions.items():
    for i in range(len(fnames)):
        for j in range(i+1, len(fnames)):
            G.add_edge(fnames[i], fnames[j], reason='exact_md5')

# Edge 3: Perceptual hash distance <= 6 within the same class
phash_edges_count = 0
for i in range(len(records)):
    for j in range(i+1, len(records)):
        if records[i]['soil_class'] == records[j]['soil_class']:
            d = records[i]['phash'] - records[j]['phash']
            if d <= 6:
                G.add_edge(records[i]['filename'], records[j]['filename'], reason=f'phash_{d}')
                phash_edges_count += 1
print(f"🔍 Near-duplicate pHash (dist<=6) edges merged: {phash_edges_count}")

# Find connected components (each component is an atomic group that cannot be split)
components = list(nx.connected_components(G))
print(f"✅ Clustered into {len(components)} strictly disjoint group components.")

comp_list = []
for idx, c in enumerate(components):
    c_nodes = list(c)
    cls = G.nodes[c_nodes[0]]['soil_class']
    comp_list.append({
        'comp_id': f"group_{idx:04d}",
        'soil_class': cls,
        'nodes': c_nodes,
        'size': len(c_nodes)
    })

df_comps = pd.DataFrame(comp_list)
print("\n📊 Disjoint Groups per Class:")
for c, cnt in df_comps['soil_class'].value_counts().items():
    print(f"  • {c:<7}: {cnt} groups")

# -------------------------------------------------------------
# STEP 2: STRATIFIED GROUP SPLIT (70% train / 15% val / 15% test)
# -------------------------------------------------------------
print("\n" + "=" * 78)
print(" STEP 2: STRATIFIED GROUP SPLIT (70% Train, 15% Val, 15% Test)")
print("=" * 78)

c_train, c_temp, y_train, y_temp = train_test_split(
    df_comps['comp_id'], df_comps['soil_class'], test_size=0.30, random_state=seed, stratify=df_comps['soil_class']
)
c_val, c_test, y_val, y_test = train_test_split(
    c_temp, y_temp, test_size=0.50, random_state=seed, stratify=y_temp
)

train_comp_set = set(c_train)
val_comp_set = set(c_val)
test_comp_set = set(c_test)

train_rows, val_rows, test_rows = [], [], []
for comp in comp_list:
    cid = comp['comp_id']
    for fn in comp['nodes']:
        rec = G.nodes[fn]['record']
        row = {
            'filepath': rec['filepath'],
            'filename': rec['filename'],
            'soil_class': rec['soil_class'],
            'group_id': cid,
            'is_orig': True,
            'md5': rec['md5'],
            'phash': str(rec['phash'])
        }
        if cid in train_comp_set:
            row['split'] = 'train'
            train_rows.append(row)
        elif cid in val_comp_set:
            row['split'] = 'val'
            val_rows.append(row)
        else:
            row['split'] = 'test'
            test_rows.append(row)

df_train_orig = pd.DataFrame(train_rows)
df_val_orig = pd.DataFrame(val_rows)
df_test_orig = pd.DataFrame(test_rows)

print(f"📊 Partition Counts (Original Field Photos):")
print(f"  • Train Orig : {len(df_train_orig)} images ({len(c_train)} groups)")
print(f"  • Val Orig   : {len(df_val_orig)} images ({len(c_val)} groups)")
print(f"  • Test Orig  : {len(df_test_orig)} images ({len(c_test)} groups)")

splits_dir = os.path.join(ML_MODELS_DIR, "datasets", "splits")
os.makedirs(splits_dir, exist_ok=True)
df_train_orig.to_csv(os.path.join(splits_dir, "soil_split_train_orig.csv"), index=False)
df_val_orig.to_csv(os.path.join(splits_dir, "soil_split_val.csv"), index=False)
df_test_orig.to_csv(os.path.join(splits_dir, "soil_split_test.csv"), index=False)

# -------------------------------------------------------------
# STEP 3: SCAN GAN DATASET & PRUNE ANY LEAKAGE TO TEST OR VAL
# -------------------------------------------------------------
print("\n" + "=" * 78)
print(" STEP 3: SCAN SYNTHETIC GAN IMAGES & PRUNE HOLDOUT LEAKAGE")
print("=" * 78)

orig_fnames = set(r['filename'] for r in records)
gan_rows = []
for c in SOIL_CLASSES:
    p = os.path.join(SOIL_DATASET_DIR, c)
    for f in sorted(os.listdir(p)):
        if f not in orig_fnames:
            fp = os.path.join(p, f)
            if not os.path.isfile(fp):
                continue
            with open(fp, 'rb') as f_obj:
                m_val = hashlib.md5(f_obj.read()).hexdigest()
            with Image.open(fp) as g_img:
                ph_val = imagehash.phash(g_img.convert('RGB'))
            gan_rows.append({
                'filepath': fp,
                'filename': f,
                'soil_class': c,
                'group_id': 'gan',
                'split': 'train',
                'is_orig': False,
                'md5': m_val,
                'phash': ph_val
            })

print(f"📦 Total synthetic GAN candidates: {len(gan_rows)}")

# Collect all holdout hashes (Test + Val)
holdout_md5s = set(df_test_orig['md5']).union(set(df_val_orig['md5']))
holdout_test_phashes = [imagehash.hex_to_hash(h) for h in df_test_orig['phash']]
holdout_val_phashes = [imagehash.hex_to_hash(h) for h in df_val_orig['phash']]
all_holdout_phashes = holdout_test_phashes + holdout_val_phashes

safe_gan_rows = []
gan_pruned_md5 = 0
gan_pruned_phash = 0

for grow in gan_rows:
    g_md5 = grow['md5']
    g_ph = grow['phash']
    if g_md5 in holdout_md5s:
        gan_pruned_md5 += 1
        continue
    # Check pHash distance <= 6 to ANY holdout image
    is_phash_leak = False
    for hph in all_holdout_phashes:
        if (g_ph - hph) <= 6:
            is_phash_leak = True
            break
    if is_phash_leak:
        gan_pruned_phash += 1
        continue
    
    safe_gan_rows.append({
        'filepath': grow['filepath'],
        'filename': grow['filename'],
        'soil_class': grow['soil_class'],
        'group_id': 'gan',
        'split': 'train',
        'is_orig': False,
        'md5': grow['md5'],
        'phash': str(grow['phash'])
    })

df_safe_gan = pd.DataFrame(safe_gan_rows)
print(f"🚫 GAN images pruned due to exact MD5 match: {gan_pruned_md5}")
print(f"🚫 GAN images pruned due to pHash (dist<=6) match: {gan_pruned_phash}")
print(f"✅ Safe GAN images retained for Model B: {len(df_safe_gan)}")

df_safe_gan.to_csv(os.path.join(splits_dir, "soil_split_train_safe_gan.csv"), index=False)
df_train_combined = pd.concat([df_train_orig, df_safe_gan], ignore_index=True)
df_train_combined.to_csv(os.path.join(splits_dir, "soil_split_train_combined.csv"), index=False)

# -------------------------------------------------------------
# STEP 4: VERIFY LEAKAGE PROOF (TARGET = 0)
# -------------------------------------------------------------
print("\n" + "=" * 78)
print(" STEP 4: RIGOROUS LEAKAGE AUDIT (Target: Exactly 0)")
print("=" * 78)

test_hashes = [(r['filepath'], r['md5'], imagehash.hex_to_hash(r['phash'])) for _, r in df_test_orig.iterrows()]

def check_leakage_against(target_df, name):
    exact_matches = 0
    phash_matches = 0
    for tfp, tmd5, tph in test_hashes:
        for _, row in target_df.iterrows():
            if tmd5 == row['md5']:
                exact_matches += 1
                print(f"  [LEAK] Exact MD5: {tfp} == {row['filepath']}")
            o_ph = imagehash.hex_to_hash(row['phash'])
            dist = tph - o_ph
            if dist <= 6:
                phash_matches += 1
                print(f"  [LEAK] pHash dist={dist}: {tfp} ~ {row['filepath']}")
    return exact_matches, phash_matches

e_val, p_val = check_leakage_against(df_val_orig, "Validation Set")
e_train, p_train = check_leakage_against(df_train_orig, "Train Originals")
e_gan, p_gan = check_leakage_against(df_safe_gan, "Train Safe GAN")

total_exact_leaks = e_val + e_train + e_gan
total_phash_leaks = p_val + p_train + p_gan

print(f"\n📊 FINAL LEAKAGE AUDIT PROOF TABLE:")
print(f"{'Comparison':<35} | {'Exact MD5 Matches':<18} | {'pHash (dist<=6) Matches':<22}")
print("-" * 82)
print(f"{'Test vs Validation (val)':<35} | {e_val:<18} | {p_val:<22}")
print(f"{'Test vs Train Originals (train_orig)':<35} | {e_train:<18} | {p_train:<22}")
print(f"{'Test vs Train Safe GAN (train_safe_gan)':<35} | {e_gan:<18} | {p_gan:<22}")
print("-" * 82)
print(f"{'TOTAL LEAKS TO TEST SET':<35} | {total_exact_leaks:<18} | {total_phash_leaks:<22}")

assert total_exact_leaks == 0, f"Error: Exact MD5 leaks found ({total_exact_leaks})"
assert total_phash_leaks == 0, f"Error: pHash leaks found ({total_phash_leaks})"
print("🎉 PERFECT LEAK-FREE STATUS VERIFIED: 0 MD5 matches, 0 pHash matches!")

# -------------------------------------------------------------
# STEP 5: PYTORCH DATASETS & DATALOADERS
# -------------------------------------------------------------
class SoilDFDataset(Dataset):
    def __init__(self, df, transform=None):
        self.df = df.reset_index(drop=True)
        self.transform = transform
        self.class_to_idx = {c: i for i, c in enumerate(SOIL_CLASSES)}
        
    def __len__(self):
        return len(self.df)
        
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img = Image.open(row['filepath']).convert("RGB")
        target = self.class_to_idx[row['soil_class']]
        if self.transform:
            img = self.transform(img)
        return img, target

val_dataset = SoilDFDataset(df_val_orig, transform=transform_eval)
test_dataset = SoilDFDataset(df_test_orig, transform=transform_eval)
val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

# Class weights for training
cls_counts = df_train_orig['soil_class'].value_counts()
class_weights_list = [
    float(len(df_train_orig) / (len(SOIL_CLASSES) * max(1, cls_counts.get(c, 1))))
    for c in SOIL_CLASSES
]
class_weights_tensor = torch.tensor(class_weights_list, dtype=torch.float).to(device)
print(f"\n⚖️ Class Weights (Inverse frequency for original train set):")
for i, c in enumerate(SOIL_CLASSES):
    print(f"  • {c:<7}: weight={class_weights_list[i]:.3f} (n={cls_counts.get(c, 0)})")

# -------------------------------------------------------------
# STEP 6: TRAINING (MODEL A & MODEL B) WITH STRICT VAL-BASED SELECTION
# -------------------------------------------------------------
print("\n" + "=" * 78)
print(" STEP 6: MODEL TRAINING & VAL-SET BASED SELECTION")
print("=" * 78)

def train_soil_model(train_df, model_name="model", epochs=8, batch_size=32, lr=1e-3, use_weights=True):
    print(f"\n🚀 Training {model_name} ({len(train_df)} images, {epochs} epochs)...")
    train_ds = SoilDFDataset(train_df, transform=transform_train)
    train_ld = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    
    model = SoilCNNClassifier(num_classes=len(SOIL_CLASSES)).to(device)
    for p in model.backbone.features.parameters():
        p.requires_grad = False
        
    optimizer = torch.optim.Adam(model.backbone.classifier.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss(weight=class_weights_tensor if use_weights else None)
    
    best_val_acc = 0.0
    best_weights = None
    
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        for imgs, lbls in train_ld:
            imgs, lbls = imgs.to(device), lbls.to(device)
            optimizer.zero_grad()
            out = model(imgs)
            loss = criterion(out, lbls)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * imgs.size(0)
            preds = out.argmax(dim=1)
            correct += (preds == lbls).sum().item()
            total += lbls.size(0)
            
        train_acc = (correct / total) * 100
        
        # Validation accuracy (Early stopping / best checkpoint selection)
        model.eval()
        v_correct = 0
        with torch.no_grad():
            for v_imgs, v_lbls in val_loader:
                v_imgs, v_lbls = v_imgs.to(device), v_lbls.to(device)
                v_preds = model(v_imgs).argmax(dim=1)
                v_correct += (v_preds == v_lbls).sum().item()
        val_acc = (v_correct / len(df_val_orig)) * 100
        print(f"  Epoch [{epoch+1}/{epochs}] Loss: {running_loss/total:.4f} | Train Acc: {train_acc:.2f}% | Val Acc: {val_acc:.2f}%")
        
        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            best_weights = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            
    model.load_state_dict(best_weights)
    return model, best_val_acc

# Train Model A
model_a, val_acc_a = train_soil_model(df_train_orig, "Model A (Originals Only)", epochs=8, use_weights=True)

# Train Model B
model_b, val_acc_b = train_soil_model(df_train_combined, "Model B (Originals + Safe GAN)", epochs=6, use_weights=True)

print("\n" + "-" * 78)
print(" 🎯 VALIDATION SET EVALUATION & MODEL SELECTION (TEST SET UNTOUCHED):")
print("-" * 78)
print(f"  • Model A (Originals Only)      : Validation Accuracy = {val_acc_a:.2f}%")
print(f"  • Model B (Originals + Safe GAN): Validation Accuracy = {val_acc_b:.2f}%")

if val_acc_a >= val_acc_b:
    champion_name = "Model A (Originals Only)"
    champion_model = model_a
    print(f"\n🏆 CHAMPION SELECTED BY VALIDATION ACCURACY: {champion_name} ({val_acc_a:.2f}% vs {val_acc_b:.2f}%)")
else:
    champion_name = "Model B (Originals + Safe GAN)"
    champion_model = model_b
    print(f"\n🏆 CHAMPION SELECTED BY VALIDATION ACCURACY: {champion_name} ({val_acc_b:.2f}% vs {val_acc_a:.2f}%)")

# Save Champion Model
torch.save(champion_model.state_dict(), SOIL_CNN_MODEL_PATH)
print(f"💾 Champion model saved to: {SOIL_CNN_MODEL_PATH}")

# Save Model B checkpoint for reproducibility
model_b_path = os.path.join(SAVED_MODELS_DIR, "soil_cnn_model_b.pth")
torch.save(model_b.state_dict(), model_b_path)
print(f"💾 Model B model saved to: {model_b_path}")

# -------------------------------------------------------------
# STEP 7: INFERENCE ON TEST SET & SAVE PREDICTIONS CSV
# -------------------------------------------------------------
print("\n" + "=" * 78)
print(" STEP 7: TEST SET EVALUATION & EXPORT PREDICTIONS CSV")
print("=" * 78)

def run_test_inference(model, model_tag, out_csv_path):
    model.eval()
    records_out = []
    y_true_list = []
    y_pred_list = []
    logits_list = []
    
    with torch.no_grad():
        for i in range(len(df_test_orig)):
            row = df_test_orig.iloc[i]
            img = Image.open(row['filepath']).convert("RGB")
            t_img = transform_eval(img).unsqueeze(0).to(device)
            logits = model(t_img)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
            pred_idx = int(np.argmax(probs))
            pred_cls = SOIL_CLASSES[pred_idx]
            true_cls = row['soil_class']
            correct = (pred_cls == true_cls)
            
            y_true_list.append(SOIL_CLASSES.index(true_cls))
            y_pred_list.append(pred_idx)
            logits_list.append(logits.cpu().numpy()[0])
            
            rec = {
                'filename': row['filename'],
                'filepath': row['filepath'],
                'soil_class': true_cls,
                'predicted_class': pred_cls,
                'confidence': round(float(probs[pred_idx]) * 100, 2),
                'correct': correct
            }
            for cls_idx, c_name in enumerate(SOIL_CLASSES):
                rec[f'prob_{c_name}'] = round(float(probs[cls_idx]), 4)
            records_out.append(rec)
            
    df_out = pd.DataFrame(records_out)
    df_out.to_csv(out_csv_path, index=False)
    print(f"💾 Saved {model_tag} predictions to: {out_csv_path}")
    
    y_true = np.array(y_true_list)
    y_pred = np.array(y_pred_list)
    logits_arr = np.array(logits_list)
    acc = accuracy_score(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred)
    rep = classification_report(y_true, y_pred, target_names=SOIL_CLASSES, digits=3, output_dict=True)
    
    return {
        'df_out': df_out,
        'y_true': y_true,
        'y_pred': y_pred,
        'logits': logits_arr,
        'accuracy': acc,
        'cm': cm,
        'rep': rep
    }

pred_a_path = os.path.join(ML_MODELS_DIR, "predictions_modelA.csv")
pred_b_path = os.path.join(ML_MODELS_DIR, "predictions_modelB.csv")

eval_a = run_test_inference(model_a, "Model A", pred_a_path)
eval_b = run_test_inference(model_b, "Model B", pred_b_path)

# Reconcile Model B and Model A
total_test = len(df_test_orig)
correct_a = int(eval_a['df_out']['correct'].sum())
correct_b = int(eval_b['df_out']['correct'].sum())

print("\n" + "=" * 78)
print(" 🔬 COMPARATIVE PERFORMANCE ON CLEAN LEAK-FREE TEST SET:")
print("=" * 78)
print(f"Total Test Samples: {total_test}")
print(f"Model A (Originals Only): {correct_a}/{total_test} correct = {eval_a['accuracy']*100:.2f}%")
print(f"Model B (Originals + Safe GAN): {correct_b}/{total_test} correct = {eval_b['accuracy']*100:.2f}%")

# -------------------------------------------------------------
# STEP 8: WILSON 95% CONFIDENCE INTERVALS FOR MODEL A
# -------------------------------------------------------------
print("\n" + "=" * 78)
print(" STEP 8: MODEL A PER-CLASS METRICS & WILSON 95% CONFIDENCE INTERVALS")
print("=" * 78)

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

print(f"\n{'Class':<10} | {'Test Count (n)':<15} | {'Precision':<12} | {'Recall':<10} | {'Wilson 95% CI for Recall':<28} | {'F1-Score':<10}")
print("-" * 92)

cm_a = eval_a['cm']
wilson_ci_dict = {}

for idx, c in enumerate(SOIL_CLASSES):
    tp = cm_a[idx, idx]
    fn = cm_a[idx].sum() - tp
    support = tp + fn
    rec_val = eval_a['rep'][c]['recall']
    prec_val = eval_a['rep'][c]['precision']
    f1_val = eval_a['rep'][c]['f1-score']
    
    p_hat, w_low, w_high = wilson_score_interval(tp, support)
    wilson_ci_dict[c] = {
        'support': int(support),
        'tp': int(tp),
        'precision': round(prec_val, 3),
        'recall': round(rec_val, 3),
        'f1': round(f1_val, 3),
        'wilson_95_ci': [round(w_low * 100, 1), round(w_high * 100, 1)]
    }
    ci_str = f"[{w_low*100:.1f}%, {w_high*100:.1f}%]"
    print(f"{c:<10} | {support:<15} | {prec_val*100:<11.1f}% | {rec_val*100:<9.1f}% | {ci_str:<28} | {f1_val:<10.3f}")

print("-" * 92)
print("Model A Full Confusion Matrix (Rows=True, Cols=Pred: Black, Clayey, Loamy, Red, Sandy):")
print(cm_a)

# -------------------------------------------------------------
# STEP 9: TEMPERATURE SCALING (VAL-ONLY FIT) & ECE EVALUATION
# -------------------------------------------------------------
print("\n" + "=" * 78)
print(" STEP 9: TEMPERATURE SCALING (FIT ON VAL SET ONLY) & ECE")
print("=" * 78)

# 1. Extract logits on Validation Set
model_a.eval()
val_logits_list = []
val_targets_list = []
with torch.no_grad():
    for imgs, targets in val_loader:
        imgs = imgs.to(device)
        logits = model_a(imgs)
        val_logits_list.append(logits.cpu().numpy())
        val_targets_list.append(targets.numpy())

val_logits = np.concatenate(val_logits_list, axis=0)
val_targets = np.concatenate(val_targets_list, axis=0)

# 2. Fit scalar temperature T strictly on validation set by minimizing cross-entropy NLL
def nll_obj(T_scalar):
    T = T_scalar[0]
    scaled_logits = val_logits / T
    # Softmax
    exp_l = np.exp(scaled_logits - np.max(scaled_logits, axis=1, keepdims=True))
    probs = exp_l / np.sum(exp_l, axis=1, keepdims=True)
    correct_p = probs[np.arange(len(val_targets)), val_targets]
    eps = 1e-12
    return -np.mean(np.log(np.clip(correct_p, eps, 1.0)))

res_opt = minimize(nll_obj, x0=[1.0], bounds=[(0.05, 5.0)], method='L-BFGS-B')
optimal_T = float(res_opt.x[0])
print(f"🌡️ Optimal Temperature T fit on validation set: {optimal_T:.4f} (NLL: {res_opt.fun:.4f})")

# 3. Calculate ECE function
def compute_ece(probs, y_true, n_bins=10):
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    confidences = np.max(probs, axis=1)
    predictions = np.argmax(probs, axis=1)
    accuracies = (predictions == y_true)
    
    ece = 0.0
    for b in range(n_bins):
        b_low, b_high = bin_boundaries[b], bin_boundaries[b+1]
        mask = (confidences > b_low) & (confidences <= b_high) if b > 0 else (confidences >= b_low) & (confidences <= b_high)
        cnt = np.sum(mask)
        if cnt > 0:
            avg_conf = np.mean(confidences[mask])
            avg_acc = np.mean(accuracies[mask])
            ece += (cnt / len(y_true)) * abs(avg_acc - avg_conf)
    return ece * 100

test_logits = eval_a['logits']
test_targets = eval_a['y_true']

# Uncalibrated probs on test set
uncal_exp = np.exp(test_logits - np.max(test_logits, axis=1, keepdims=True))
uncal_probs = uncal_exp / np.sum(uncal_exp, axis=1, keepdims=True)
ece_uncal = compute_ece(uncal_probs, test_targets)

# Calibrated probs with optimal_T
cal_exp = np.exp((test_logits / optimal_T) - np.max(test_logits / optimal_T, axis=1, keepdims=True))
cal_probs = cal_exp / np.sum(cal_exp, axis=1, keepdims=True)
ece_cal = compute_ece(cal_probs, test_targets)

print(f"📊 Test Set ECE before scaling: {ece_uncal:.2f}%")
print(f"📊 Test Set ECE after scaling (T={optimal_T:.3f}): {ece_cal:.2f}%")

# Calibration Table on Test Set (Calibrated)
bins = [
    ('<50%', 0.0, 0.50),
    ('50-70%', 0.50, 0.70),
    ('70-90%', 0.70, 0.90),
    ('>90%', 0.90, 1.0001)
]

cal_confs = np.max(cal_probs, axis=1)
cal_preds = np.argmax(cal_probs, axis=1)
cal_is_correct = (cal_preds == test_targets)

print(f"\n🎯 TEST SET CALIBRATION TABLE (Temperature Scaled T={optimal_T:.3f}):")
print(f"{'Bin':<10} | {'Count':<8} | {'Mean Conf':<12} | {'Empirical Acc':<15} | {'Gap':<10}")
print("-" * 65)
cal_table = []
for label, low, high in bins:
    mask = (cal_confs >= low) & (cal_confs < high)
    cnt = int(np.sum(mask))
    if cnt > 0:
        mean_c = float(np.mean(cal_confs[mask])) * 100
        emp_a = float(np.mean(cal_is_correct[mask])) * 100
        gap = abs(mean_c - emp_a)
    else:
        mean_c, emp_a, gap = 0.0, 0.0, 0.0
    cal_table.append({
        'bin': label,
        'count': cnt,
        'mean_confidence_pct': round(mean_c, 1),
        'empirical_accuracy_pct': round(emp_a, 1),
        'gap_pct': round(gap, 1)
    })
    print(f"{label:<10} | {cnt:<8} | {mean_c:<11.1f}% | {emp_a:<14.1f}% | {gap:<9.1f}%")

# Low confidence threshold analysis on validation set
val_exp = np.exp((val_logits / optimal_T) - np.max(val_logits / optimal_T, axis=1, keepdims=True))
val_cal_probs = val_exp / np.sum(val_exp, axis=1, keepdims=True)
val_cal_confs = np.max(val_cal_probs, axis=1)
val_cal_preds = np.argmax(val_cal_probs, axis=1)
val_correct_mask = (val_cal_preds == val_targets)

# Check error rate below 70% vs above 70% on val set
val_sub70_err = 100.0 - (float(np.mean(val_correct_mask[val_cal_confs < 0.70])) * 100 if np.sum(val_cal_confs < 0.70) > 0 else 0.0)
val_above70_acc = float(np.mean(val_correct_mask[val_cal_confs >= 0.70])) * 100 if np.sum(val_cal_confs >= 0.70) > 0 else 0.0

print(f"\n🛡️ Validation-Derived Low Confidence Threshold:")
print(f"  • Validation samples with confidence < 70%: Error Rate = {val_sub70_err:.1f}%")
print(f"  • Validation samples with confidence >= 70%: Accuracy = {val_above70_acc:.1f}%")
print(f"  • Recommended warning threshold: 70.0% (validated against error risk on val set).")

# -------------------------------------------------------------
# STEP 10: SAVE COMPREHENSIVE RESULTS JSON
# -------------------------------------------------------------
results_data = {
    "model_version": "mobilenet_v2_soil_v3_leak_free_wilson",
    "evaluation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
    "leakage_verification": {
        "connected_components_groups": len(components),
        "raw_md5_duplicate_pairs": total_md5_pairs,
        "test_vs_val_md5_matches": e_val,
        "test_vs_val_phash_matches": p_val,
        "test_vs_train_orig_md5_matches": e_train,
        "test_vs_train_orig_phash_matches": p_train,
        "test_vs_safe_gan_md5_matches": e_gan,
        "test_vs_safe_gan_phash_matches": p_gan,
        "total_test_leakage": 0
    },
    "dataset_summary": {
        "train_samples": len(df_train_orig),
        "val_samples": len(df_val_orig),
        "test_samples": len(df_test_orig),
        "safe_gan_samples": len(df_safe_gan)
    },
    "model_selection": {
        "criterion": "Validation Accuracy (Test set untouched during selection)",
        "model_a_val_accuracy": round(val_acc_a, 2),
        "model_b_val_accuracy": round(val_acc_b, 2),
        "champion_selected": champion_name
    },
    "test_set_ablation_results": {
        "model_a_originals_only": {
            "accuracy": round(eval_a['accuracy'] * 100, 2),
            "correct": correct_a,
            "total": total_test,
            "macro_f1": round(f1_score(eval_a['y_true'], eval_a['y_pred'], average='macro'), 3),
            "weighted_f1": round(f1_score(eval_a['y_true'], eval_a['y_pred'], average='weighted'), 3),
            "confusion_matrix": cm_a.tolist(),
            "wilson_ci": wilson_ci_dict
        },
        "model_b_originals_plus_safe_gan": {
            "accuracy": round(eval_b['accuracy'] * 100, 2),
            "correct": correct_b,
            "total": total_test,
            "macro_f1": round(f1_score(eval_b['y_true'], eval_b['y_pred'], average='macro'), 3),
            "weighted_f1": round(f1_score(eval_b['y_true'], eval_b['y_pred'], average='weighted'), 3),
            "confusion_matrix": eval_b['cm'].tolist()
        }
    },
    "temperature_scaling": {
        "optimal_temperature_T": round(optimal_T, 4),
        "fitted_on": "Validation Set NLL",
        "test_ece_uncalibrated_pct": round(ece_uncal, 2),
        "test_ece_calibrated_pct": round(ece_cal, 2),
        "calibration_table": cal_table,
        "low_confidence_threshold_pct": 70.0
    }
}

with open(os.path.join(BASE_DIR, "results.json"), "w") as f:
    json.dump(results_data, f, indent=2)

with open(os.path.join(ML_MODELS_DIR, "results.json"), "w") as f:
    json.dump(results_data, f, indent=2)

print("\n✅ All results written to results.json and ml_models/results.json successfully!")
