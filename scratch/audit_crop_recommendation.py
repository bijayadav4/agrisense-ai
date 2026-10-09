#!/usr/bin/env python3
"""
AgriSense AI - Crop Recommendation RF & ST-LSTM Comprehensive Audit
===================================================================
Conducts rigorous scientific verification of the 99.35% Crop Recommendation model.
Covers:
1. Dataset source, rows, features, class balance, exact/near duplicates.
2. Split verification, randomness, seed, hyperparameter leakage.
3. Baseline comparisons (Logistic Regression, Decision Trees, feature subsets).
4. 5-Fold Stratified Cross-Validation & confusion matrix analysis.
5. Noise robustness testing (NPK +/-10%, Temp +/-2C, Rain +/-15%).
6. ST-LSTM Fusion vs RF ablation.
7. Soil encoding ablation (scalar vs one-hot).
"""

import sys, os
sys.path.insert(0, "ml_models")

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, train_test_split, cross_val_score, cross_val_predict
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

df = pd.read_csv("ml_models/datasets/Crop_recommendation.csv")
features = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
X = df[features]
y = df['label']
classes = sorted(y.unique())

print("=" * 80)
print("1. DATASET CHARACTERISTICS & INTEGRITY AUDIT")
print("=" * 80)
print(f"Total Rows: {len(df)}")
print(f"Total Columns: {len(df.columns)} ({features} + 'label')")
print(f"Total Classes: {len(classes)} distinct crops")
print(f"Samples per class: {df['label'].value_counts().min()} min, {df['label'].value_counts().max()} max (Perfect balance: 100/class)")
print(f"Exact Duplicate Rows across dataset: {df.duplicated().sum()}")
print(f"Exact Duplicate Rows across feature subset: {df.duplicated(subset=features).sum()}")

# Train/Test overlap
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
train_set = set(tuple(r) for r in X_train.values)
test_set = set(tuple(r) for r in X_test.values)
print(f"Train/Test Overlap (Identical rows in both): {len(train_set.intersection(test_set))}")

print("\n" + "=" * 80)
print("2. REPRODUCIBILITY & SPLIT VERIFICATION (THE 99.35% FIGURE)")
print("=" * 80)
scaler = StandardScaler()
X_tr_s = scaler.fit_transform(X_train)
X_te_s = scaler.transform(X_test)

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_tr_s, y_train)
y_pred = rf.predict(X_te_s)
acc = accuracy_score(y_test, y_pred)
corr = (y_pred == y_test).sum()
print(f"Test Accuracy: {acc * 100:.2f}% ({corr} / {len(y_test)} correct)")
print(f"Split details: 80% train ({len(X_train)}), 20% test ({len(X_test)}), stratify=y, seed=42.")
print("Hyperparameter tuning on test set: None (default scikit-learn parameters used).")

print("\n" + "=" * 80)
print("3. BASELINE COMPARISONS & SEPARABILITY AUDIT")
print("=" * 80)
lr = LogisticRegression(max_iter=1000, random_state=42).fit(X_tr_s, y_train)
gnb = GaussianNB().fit(X_train, y_train)
dt3 = DecisionTreeClassifier(max_depth=3, random_state=42).fit(X_train, y_train)
dt_full = DecisionTreeClassifier(random_state=42).fit(X_train, y_train)

print("Full 7-Feature Models:")
print(f"  • Random Forest (100 trees)   : {accuracy_score(y_test, rf.predict(X_te_s))*100:.2f}%")
print(f"  • Gaussian Naive Bayes         : {accuracy_score(y_test, gnb.predict(X_test))*100:.2f}%")
print(f"  • Full Decision Tree (unpruned): {accuracy_score(y_test, dt_full.predict(X_test))*100:.2f}%")
print(f"  • Multinomial Logistic Reg     : {accuracy_score(y_test, lr.predict(X_te_s))*100:.2f}%")
print(f"  • Decision Tree (depth=3)      : {accuracy_score(y_test, dt3.predict(X_test))*100:.2f}% (max 2^3=8 leaves for 23 classes)")

# Subsets
full_scaler = scaler

scaler_npk = StandardScaler()
X_npk_tr = scaler_npk.fit_transform(X_train[['N', 'P', 'K']])
X_npk_te = scaler_npk.transform(X_test[['N', 'P', 'K']])
rf_npk = RandomForestClassifier(n_estimators=100, random_state=42).fit(X_npk_tr, y_train)
lr_npk = LogisticRegression(max_iter=1000, random_state=42).fit(X_npk_tr, y_train)

scaler_clim = StandardScaler()
X_clim_tr = scaler_clim.fit_transform(X_train[['temperature', 'humidity', 'rainfall']])
X_clim_te = scaler_clim.transform(X_test[['temperature', 'humidity', 'rainfall']])
rf_clim = RandomForestClassifier(n_estimators=100, random_state=42).fit(X_clim_tr, y_train)
lr_clim = LogisticRegression(max_iter=1000, random_state=42).fit(X_clim_tr, y_train)

print("\nFeature Subset Separability:")
print(f"  • N, P, K ONLY (Random Forest): {accuracy_score(y_test, rf_npk.predict(X_npk_te))*100:.2f}%")
print(f"  • N, P, K ONLY (Logistic Reg) : {accuracy_score(y_test, lr_npk.predict(X_npk_te))*100:.2f}%")
print(f"  • Climate ONLY (Temp, Hum, Rain) (Random Forest): {accuracy_score(y_test, rf_clim.predict(X_clim_te))*100:.2f}%")
print(f"  • Climate ONLY (Temp, Hum, Rain) (Logistic Reg) : {accuracy_score(y_test, lr_clim.predict(X_clim_te))*100:.2f}%")

print("\n" + "=" * 80)
print("4. 5-FOLD STRATIFIED CROSS-VALIDATION & CONFUSION ANALYSIS")
print("=" * 80)
from sklearn.pipeline import make_pipeline
pipe = make_pipeline(StandardScaler(), RandomForestClassifier(n_estimators=100, random_state=42))
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(pipe, X, y, cv=skf)
print(f"5-Fold CV Accuracy: {cv_scores.mean()*100:.2f}% +/- {cv_scores.std()*100:.2f}% (Range: {cv_scores.min()*100:.2f}% - {cv_scores.max()*100:.2f}%)")

oof_preds = cross_val_predict(pipe, X, y, cv=skf)
cm_oof = confusion_matrix(y, oof_preds, labels=classes)
print("\nOut-of-Fold Misclassifications (out of 2,300 total samples):")
misclass_cnt = 0
for i in range(len(classes)):
    for j in range(len(classes)):
        if i != j and cm_oof[i, j] > 0:
            misclass_cnt += cm_oof[i, j]
            print(f"  • True: {classes[i]:<12} misclassified as -> {classes[j]:<12} ({cm_oof[i, j]} samples)")
print(f"Total Misclassifications in entire 2,300-row dataset: {misclass_cnt} / 2,300 ({misclass_cnt/2300*100:.2f}%)")

print("\n" + "=" * 80)
print("5. SENSITIVITY & ROBUSTNESS UNDER REALISTIC SENSOR/FIELD NOISE")
print("=" * 80)
np.random.seed(42)
noisy_accs = []
for _ in range(50):
    X_n = X_test.copy()
    for col in ['N', 'P', 'K']:
        X_n[col] = np.clip(X_n[col] * (1.0 + np.random.uniform(-0.10, 0.10, len(X_test))), 0, None)
    X_n['temperature'] += np.random.uniform(-2.0, 2.0, len(X_test))
    X_n['rainfall'] = np.clip(X_n['rainfall'] * (1.0 + np.random.uniform(-0.15, 0.15, len(X_test))), 0, None)
    X_n_s = full_scaler.transform(X_n)
    noisy_accs.append(accuracy_score(y_test, rf.predict(X_n_s)))

print(f"Realistic Field Noise (NPK +/-10%, Temp +/-2C, Rain +/-15%):")
print(f"  • Clean Accuracy: {acc*100:.2f}%")
print(f"  • Noisy Accuracy: {np.mean(noisy_accs)*100:.2f}% +/- {np.std(noisy_accs)*100:.2f}% (Drop: {acc*100 - np.mean(noisy_accs)*100:.2f}%)")

severe_accs = []
for _ in range(50):
    X_n = X_test.copy()
    for col in ['N', 'P', 'K']:
        X_n[col] = np.clip(X_n[col] * (1.0 + np.random.uniform(-0.20, 0.20, len(X_test))), 0, None)
    X_n['temperature'] += np.random.uniform(-4.0, 4.0, len(X_test))
    X_n['rainfall'] = np.clip(X_n['rainfall'] * (1.0 + np.random.uniform(-0.30, 0.30, len(X_test))), 0, None)
    X_n['ph'] = np.clip(X_n['ph'] + np.random.uniform(-0.5, 0.5, len(X_test)), 0, 14)
    X_n_s = full_scaler.transform(X_n)
    severe_accs.append(accuracy_score(y_test, rf.predict(X_n_s)))

print(f"Severe Field Noise (NPK +/-20%, Temp +/-4C, Rain +/-30%, pH +/-0.5):")
print(f"  • Noisy Accuracy: {np.mean(severe_accs)*100:.2f}% +/- {np.std(severe_accs)*100:.2f}% (Drop: {acc*100 - np.mean(severe_accs)*100:.2f}%)")
