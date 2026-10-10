# 🌱 AgriSense AI — Intelligent Decision Support System

AgriSense AI is an intelligent precision agriculture decision-support platform designed specifically for **Farmers** and agricultural extension officers. It combines trained Machine Learning models (Random Forest), live agro-meteorological forecasting, ICAR-calibrated soil nutrient stoichiometry, regional South Indian land unit conversions (Cents/Gunthas/Acres to Hectares), and a clean, farmer-first dashboard.

---

## 🏛️ System Architecture Flow

```
[ Farmer (User) ] 
       │
       ▼
[ User Interface (React + Vite SPA) ]
       │
       ├──► [ Land Unit Converter ] (Regional Cents & Gunthas to Hectare Conversion)
       │           │
       ├──► [ Data Collection Module ] (N, P, K, pH Soil Lab Inputs + 1-Click Presets)
       │           │
       ├──► [ Agro-Weather Module ] (📍 GPS Auto-detect / Open-Meteo & OpenWeather fallback)
       │           │
       │           ▼
       ├─────► [ AI Analysis & Scientific Engine ]
       │           │
       │           ├──► 🌾 Pillar 1: Crop Recommendation (Random Forest - 99.52% ± 0.25% 5-fold CV, benchmark data)
       │           │
       │           ├──► 📸 Soil Vision CNN (MobileNetV2 Texture Classifier)
       │           │         │
       │           │         ├──► 🧪 Fertilizer Recommendation & ICAR 50kg Bag Stoichiometry
       │           │         └──► 💧 Irrigation Planning & Hourly Spray Safety Windows
       │           │
       │           └──► ⏳ Harvest Timeline & Agronomic Management Tips
       │                   │
       │                   ▼
       └──────► [ Farmer Dashboard & Actionable Prescriptions ]
```

---

## 📁 Project Directory Structure

```
agrisense-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py           # Flask App Factory with CORS and Blueprints
│   │   ├── config.py             # Environment config and model artifact paths
│   │   ├── routes/
│   │   │   ├── predict_routes.py # POST /api/recommend/crop & /api/recommend/fertilizer
│   │   │   └── weather_routes.py # GET /api/weather (GPS Lat/Lon + City lookup, input validated)
│   │   └── services/
│   │       ├── ml_service.py     # Random Forest Inference, Soil Diagnosis, ICAR Stoichiometry
│   │       └── weather_service.py# Open-Meteo primary + OpenWeather fallback + Cache (<1ms)
│   ├── tests/
│   │   └── test_api.py           # 34 Automated unit & integration tests (100% passing)
│   ├── requirements.txt          # Python dependencies
│   ├── run.py                    # Backend server runner (Port 5000)
│   └── .env                      # Local environment configuration (git-ignored)
│
├── ml_models/
│   ├── datasets/
│   │   ├── Crop_recommendation.csv   # 2,300 agricultural records across 23 crops
│   │   └── Fertilizer Prediction.csv # 99 agricultural records across 7 fertilizer types
│   ├── saved_models/
│   │   ├── crop_recommendation_model.pkl # Trained Random Forest model (23 crops)
│   │   ├── crop_scaler.pkl               # StandardScaler fitted on 7 soil/climate features
│   │   ├── fertilizer_model.pkl          # Trained Random Forest classifier
│   │   ├── fertilizer_scaler.pkl         # StandardScaler for fertilizer inputs
│   │   └── fertilizer_encoder.pkl        # LabelEncoders for Soil and Crop types
│   ├── config.py                 # Dataset and artifact path configurations
│   ├── preprocess.py             # Stratified split (80:20) and StandardScaler normalization
│   ├── train.py                  # Crop Random Forest training script (99.52% 5-Fold CV)
│   └── train_fertilizer.py       # Fertilizer Random Forest training script
│
├── notebooks/
│   ├── 01_eda_and_preprocessing.ipynb # Full EDA, distributions, missing value check
│   └── 02_model_training.ipynb        # Model training, holdout evaluation & feature importances
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Sidebar.jsx           # Left navigation bar
    │   │   ├── Header.jsx            # Location selector, weather widget & farmer profile
    │   │   ├── DashboardView.jsx     # Farmer-first landing page with forecast & spray safety
    │   │   ├── CropView.jsx          # Soil nutrient evaluation, SHC kg/ha education & ML advice
    │   │   ├── FertilizerView.jsx    # ICAR chemical balancing & plot-level 50kg bag dosage
    │   │   ├── WeatherView.jsx       # 5-day agro-meteorological forecast & spray advisories
    │   │   └── LandUnitConverter.jsx # Regional South Indian survey unit converter (Cent/Guntha)
    │   ├── services/
    │   │   └── api.js                # Axios client connected to backend APIs
    │   ├── App.jsx                   # Main single page application orchestrator
    │   ├── App.css                   # Component-level styling and animations
    │   └── index.css                 # Design tokens, modern typography & color variables
    ├── package.json
    └── vite.config.js
```

---

## 🤖 Machine Learning & Scientific Models

### 1. Crop Recommendation Model (Pillar 1 - Random Forest Classifier)
- **Dataset**: `Crop_recommendation.csv` containing **2,300 records** uniformly distributed across **23 crops** (exactly 100 records per crop):
  *rice, maize, chickpea, kidneybeans, pigeonpeas, mothbeans, mungbean, blackgram, lentil, pomegranate, banana, mango, grapes, watermelon, muskmelon, apple, orange, papaya, coconut, cotton, jute, coffee, wheat*.
- **Features (7)**: Nitrogen ($N$), Phosphorus ($P$), Potassium ($K$), Temperature (°C), Humidity (%), Soil pH, and Rainfall (mm).
- **Model**: `RandomForestClassifier(n_estimators=100, random_state=42)` trained on standardized features.
- **Performance**:
  - **5-Fold Stratified Cross-Validation**: **99.52% +/- 0.25% (5-fold CV, benchmark data)** (Fold range: 99.13% – 99.78%).
  - **Single Holdout Run (80:20 Stratified, seed 42)**: 99.35% accuracy (457 / 460 correct). *Note: 5-fold CV is the primary reported benchmark metric.*
- **Wheat Provenance & Dataset Structure**:
  - The standard open-source Kaggle Crop Recommendation dataset contains 22 crops (2,200 rows).
  - Rows 2201–2300 (100 samples) for **Wheat** were synthetically generated and appended based on ICAR Rabi agronomic envelopes (mean N=94, P=50, K=40, Temp=19.8°C, Rain=72mm, pH=6.6) to support India's staple Rabi cereal.
  - In the UI, Wheat recommendations carry an explicit *"Limited benchmark data (synthetic ICAR extension)"* badge.
- **Ambiguity Detection**:
  - Returns top-3 crops with individual confidence probabilities.
  - If the probability gap between top-1 and top-2 is $<15\%$ ($<0.15$), the API flags `"is_ambiguous": true` and the UI renders a warning advising field validation.
- **Deprecation of Multimodal ST-LSTM Fusion**:
  - Historical fusion metrics (98.26% test, 98.84% val, 97.97% test) are marked as **invalid (target leakage)** because the historical training pipeline looked up `soil_type` using the target crop label (`soil_type_map.get(c_label)`).
  - On static tabular data, synthesizing artificial 7-day meteorological trajectories introduced noise without new information.
  - ST-LSTM fusion has been decommissioned from the production path; `/api/crop/fusion` is maintained solely as an experimental research endpoint behind an `"is_experimental": true` flag. Production recommendations are served exclusively by **Pillar 1 (Random Forest)**.
- **Dataset Limitations & Separability**:
  - The 2,300-row Kaggle benchmark features artificially well-separated unimodal Gaussian clusters: a simple linear **Multinomial Logistic Regression achieves 97.39%**, and **Gaussian Naive Bayes achieves 99.57%**.
  - In real agricultural environments, biological plasticity and microclimates create significant overlap between crop suitability zones that this clean benchmark does not capture.

### 2. Fertilizer Prescription & Stoichiometry Engine
- **Classifier**: `RandomForestClassifier(n_estimators=100)` predicting fertilizer brand/type (*Urea, DAP, 14-35-14, 28-28, 17-17-17, 20-20, 10-26-26*).
  *Note: Evaluated on 20 stratified holdout test samples (dataset size: 99 records).*
- **ICAR Stoichiometric Balancing**: Real-world farm application requires actual bag counts. AgriSense applies chemical balancing rules:
  1. DAP application satisfies phosphorus requirement ($46\% \text{ P}_2\text{O}_5$) while providing $18\%$ elemental Nitrogen.
  2. Remaining Nitrogen is supplemented via Urea ($46\% \text{ N}$).
  3. Potassium is supplemented via Muriate of Potash ($60\% \text{ K}_2\text{O}$).
  4. Output is scaled to the farmer's custom land size (in Hectares, converted from Cents or Gunthas) into standard **50 kg commercial bags**.

### 3. Soil Vision CNN (MobileNetV2 Transfer Learning)
- **Architecture**: MobileNetV2 pretrained backbone with custom Dropout (p=0.2) + Linear (128) + BatchNorm + ReLU + Linear classification head (5 soil classes: *Black, Clayey, Loamy, Red, Sandy*).
- **Leak-Free Connected-Component Split**: 987 original field photos scanned with exact MD5 and perceptual hashing (pHash distance $\le 6$). All 40 exact duplicate pairs and 81 near-duplicate pairs across raw data were clustered into 754 disjoint connected components. Stratified 70/15/15 group partition guarantees **0 exact MD5 matches** and **0 pHash ($\le 6$) matches** between test and train/val sets.
- **Evaluation**: **88.19% holdout test accuracy (95% CI 82.64% – 93.07%)**, Macro-F1: **0.809 (95% CI 0.708 – 0.884)** on 144 pure original photos (127 / 144 correct).
  *(Historical note: The old claim of ~93.2% was due to CycleGAN synthetic clone leakage between random train/test splits. Scientifically verified leak-free accuracy is 88.19%).*
- **GAN Augmentation Ablation (Why GAN was Removed)**:
  - Model A (Originals Only): **87.50% Val Acc**, **88.19% Test Acc** (127/144 correct).
  - Model B (Originals + Safe GAN): **77.63% Val Acc**, **78.47% Test Acc** (113/144 correct).
  - *Conclusion*: CycleGAN synthetic images degraded model generalization on real field photos (-9.72% test accuracy drop) by introducing synthetic texture artifacts. Consequently, **GAN data has been completely removed from the production training pipeline** (`ml_models/train_soil_cnn.py` trains solely on pure original field photos with inverse frequency class weights).
- **Class Imbalance & Wilson 95% Confidence Intervals**:
  - Black ($n=37$): Precision 94.6%, Recall 94.6% (Wilson 95% CI: [82.3%, 98.5%]), F1: 0.946
  - Red ($n=47$): Precision 93.5%, Recall 91.5% (Wilson 95% CI: [80.1%, 96.6%]), F1: 0.925
  - Sandy ($n=43$): Precision 97.3%, Recall 83.7% (Wilson 95% CI: [70.0%, 91.9%]), F1: 0.900
  - Clayey ($n=9$): Precision 72.7%, Recall 88.9% (Wilson 95% CI: [56.5%, 98.0%]), F1: 0.800
  - Loamy ($n=8$): Precision 38.5%, Recall 62.5% (Wilson 95% CI: [30.6%, 86.3%]), F1: 0.476
  - *Statistical Nuance*: Due to limited field samples for minority classes (Loamy $n=8$, Clayey $n=9$), recall estimates exhibit wide Wilson confidence intervals. The system does not claim definitive certainty for Loamy, and instead provides manual override in UI.
- **Confidence Calibration & Temperature Scaling**:
  - Temperature scalar $T = 0.811$ was fitted strictly by minimizing cross-entropy NLL on the **validation set** (test set untouched during tuning).
  - Expected Calibration Error (ECE) on test set improved from **5.31% to 4.36%**.
  - Risk-derived threshold: Validation samples below 70% confidence exhibited a 32.4% error rate. Hence, when predicted confidence is $<70\%$, the UI issues a proactive warning: *"Low confidence. Please get a laboratory soil test done."*.
- **External Field Validation (`evaluate_external.py`)**:
  - Independent CLI evaluation tool for smartphone captures and new farm photos:
    ```bash
    python evaluate_external.py -i /path/to/phone_photos -l /path/to/labels.csv
    ```
  - External field evaluation metrics are reported separately from the benchmark holdout partition to quantify phone camera sensor / lighting domain shifts.

---

## 🌦️ Agro-Meteorological Data Pipeline

1. **Layer 1 (Primary)**: High-resolution ECMWF / Open-Meteo hourly & 5-day daily forecast. Free, real-time, no API key required.
2. **Layer 2 (Secondary Fallback)**: OpenWeatherMap Current Weather API, authenticated securely via `.env` (`OPENWEATHER_API_KEY`).
3. **Layer 3 (Fail-Safe Baseline)**: Hardcoded typical agricultural baseline (27°C, 65% humidity) with sync advisory notice to guarantee zero system crashes.
4. **Caching**: In-memory coordinate cache (`WEATHER_CACHE`, TTL = 600s) and geocoding cache (`GEO_CACHE`) delivering sub-millisecond responses.

---

---

## ⚡ Setup & Production Deployment Guide

### 1. Model Artifact Verification

Ensure model weights are present before launching:
```bash
python scripts/download_models.py
```

### 2. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your specific production configuration (if needed)
```

### 3. Local Development Mode

```bash
# Terminal 1: Backend Server (Port 5000)
source venv/bin/activate
pip install -r backend/requirements.txt
python backend/run.py

# Terminal 2: Frontend Client (Port 5173)
cd frontend
npm install
npm run dev
```

Open **`http://localhost:5173`** in your browser.

### 4. Production WSGI Server (Gunicorn)

```bash
source venv/bin/activate
gunicorn --config backend/gunicorn.conf.py backend.run:app
```

### 5. Full-Stack Docker Deployment

Launch backend + frontend Nginx containers with health checks:
```bash
docker compose up --build -d
```

### 6. Automated Testing & Quality Assurance

```bash
# Run 39 automated unit & integration tests via pytest
pytest backend/tests/

# Run Ruff linter across backend and ML models
ruff check backend/ ml_models/

# Verify React frontend production bundle
cd frontend && npm run build
```

---

## 📡 REST API Documentation

| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Service health check, model loaded status, and active features | `200` |
| `GET` | `/api/weather?location=<city>` | Real-time weather, 7-day forecast & agro-spray advisory | `200`, `400` |
| `GET` | `/api/weather?lat=<lat>&lon=<lon>` | High-resolution GPS meteorological query with validation | `200`, `400` |
| `POST` | `/api/recommend/crop` | Top-3 crops with probabilities, ambiguity gap & seasonal warnings | `200`, `400` |
| `POST` | `/api/crop/fusion` | *[Experimental Prototype]* Multimodal ST-LSTM recommendation | `200`, `400` |
| `POST` | `/api/recommend/fertilizer` | Fertilizer brand + ICAR bag dosage scaled to plot size | `200`, `400` |
| `POST` | `/api/classify/soil-image` | Soil texture classification via MobileNetV2 Vision CNN | `200`, `400` |
| `POST` | `/api/irrigation/plan` | FAO-56 Penman-Monteith daily water need, drip runtime & schedule | `200`, `400` |
| `POST` | `/api/harvest/predict` | Phenological maturity timeline, yield estimation & MSP benchmark | `200`, `400` |
| `POST` | `/api/report/generate` | Official downloadable Farmer Advisory Report Card PDF | `200`, `400`, `500` |

For detailed model cards, validation datasets, confidence intervals, and governance notes, consult [MODEL_CARD.md](MODEL_CARD.md).
