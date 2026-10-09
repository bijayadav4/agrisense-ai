import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score

# Load dataset
df = pd.read_csv("ml_models/datasets/Crop_recommendation.csv")
X = df[['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']].values
y = df['label'].values

np.random.seed(42)

def add_realistic_noise(features):
    """
    Applies realistic agricultural sensor and environmental noise:
    - N, P, K: +/- 10% proportional noise
    - Temperature: +/- 2 deg C additive noise
    - Humidity: +/- 5% additive noise (bounded [0, 100])
    - pH: +/- 0.2 additive noise (bounded [0, 14])
    - Rainfall: +/- 15% proportional noise (bounded >= 0)
    """
    noisy = features.copy()
    # N, P, K
    noisy[:, 0] *= np.random.uniform(0.90, 1.10, size=noisy.shape[0])
    noisy[:, 1] *= np.random.uniform(0.90, 1.10, size=noisy.shape[0])
    noisy[:, 2] *= np.random.uniform(0.90, 1.10, size=noisy.shape[0])
    # Temperature
    noisy[:, 3] += np.random.uniform(-2.0, 2.0, size=noisy.shape[0])
    # Humidity
    noisy[:, 4] = np.clip(noisy[:, 4] + np.random.uniform(-5.0, 5.0, size=noisy.shape[0]), 0, 100)
    # pH
    noisy[:, 5] = np.clip(noisy[:, 5] + np.random.uniform(-0.2, 0.2, size=noisy.shape[0]), 0, 14)
    # Rainfall
    noisy[:, 6] = np.maximum(0, noisy[:, 6] * np.random.uniform(0.85, 1.15, size=noisy.shape[0]))
    return noisy

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

clean_model_clean_test_accs = []
clean_model_noisy_test_accs = []
noise_aug_model_clean_test_accs = []
noise_aug_model_noisy_test_accs = []

param_grid = {
    'n_estimators': [50, 100],
    'max_depth': [None, 15],
    'min_samples_split': [2, 4]
}

print("Running 5-fold CV with inner-fold tuning, clean test, and noisy test evaluation...")

for fold, (train_idx, test_idx) in enumerate(skf.split(X, y), 1):
    X_train, y_train = X[train_idx], y[train_idx]
    X_test, y_test = X[test_idx], y[test_idx]

    # Generate noisy test set
    X_test_noisy = add_realistic_noise(X_test)

    # 1. Standard Model (Tuned inside train fold)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_clean_scaled = scaler.transform(X_test)
    X_test_noisy_scaled = scaler.transform(X_test_noisy)

    # Inner CV grid search strictly within training fold
    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42 + fold)
    grid_clean = GridSearchCV(RandomForestClassifier(random_state=42), param_grid, cv=inner_cv, scoring='accuracy', n_jobs=-1)
    grid_clean.fit(X_train_scaled, y_train)
    best_clean = grid_clean.best_estimator_

    acc_clean_test = accuracy_score(y_test, best_clean.predict(X_test_clean_scaled))
    acc_noisy_test = accuracy_score(y_test, best_clean.predict(X_test_noisy_scaled))
    clean_model_clean_test_accs.append(acc_clean_test)
    clean_model_noisy_test_accs.append(acc_noisy_test)

    # 2. Noise-Augmented Model (Train set augmented with 1x noisy copy)
    X_train_aug = np.vstack([X_train, add_realistic_noise(X_train)])
    y_train_aug = np.concatenate([y_train, y_train])

    scaler_aug = StandardScaler()
    X_train_aug_scaled = scaler_aug.fit_transform(X_train_aug)
    X_test_clean_scaled_aug = scaler_aug.transform(X_test)
    X_test_noisy_scaled_aug = scaler_aug.transform(X_test_noisy)

    grid_aug = GridSearchCV(RandomForestClassifier(random_state=42), param_grid, cv=inner_cv, scoring='accuracy', n_jobs=-1)
    grid_aug.fit(X_train_aug_scaled, y_train_aug)
    best_aug = grid_aug.best_estimator_

    acc_aug_clean_test = accuracy_score(y_test, best_aug.predict(X_test_clean_scaled_aug))
    acc_aug_noisy_test = accuracy_score(y_test, best_aug.predict(X_test_noisy_scaled_aug))
    noise_aug_model_clean_test_accs.append(acc_aug_clean_test)
    noise_aug_model_noisy_test_accs.append(acc_aug_noisy_test)

    print(f"Fold {fold}:")
    print(f"  Standard Model -> Best Params: {grid_clean.best_params_} | Clean Test: {acc_clean_test*100:.2f}% | Noisy Test: {acc_noisy_test*100:.2f}%")
    print(f"  Augmented Model -> Best Params: {grid_aug.best_params_} | Clean Test: {acc_aug_clean_test*100:.2f}% | Noisy Test: {acc_aug_noisy_test*100:.2f}%")

print("\n" + "=" * 60)
print("5-FOLD CV SUMMARY REPORT (Strict Inner-Fold Tuning):")
print("=" * 60)
print(f"Standard RF (Clean Train):")
print(f"  - Clean Test Acc:  {np.mean(clean_model_clean_test_accs)*100:.2f}% ± {np.std(clean_model_clean_test_accs)*100:.2f}%")
print(f"  - Noisy Test Acc:  {np.mean(clean_model_noisy_test_accs)*100:.2f}% ± {np.std(clean_model_noisy_test_accs)*100:.2f}%")
print(f"\nNoise-Augmented RF (Clean + Noisy Train):")
print(f"  - Clean Test Acc:  {np.mean(noise_aug_model_clean_test_accs)*100:.2f}% ± {np.std(noise_aug_model_clean_test_accs)*100:.2f}%")
print(f"  - Noisy Test Acc:  {np.mean(noise_aug_model_noisy_test_accs)*100:.2f}% ± {np.std(noise_aug_model_noisy_test_accs)*100:.2f}%")
