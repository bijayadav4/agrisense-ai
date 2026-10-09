# AgriSense AI — Model Cards & Scientific Specification

This document provides transparent, reproducible, and scientifically audited model cards for all artificial intelligence models, rule-based agronomic calculation engines, and empirical data tables powering **AgriSense AI**.

---

## 1. Soil Vision Classifier (Soil CNN)

| Dimension | Specification |
| :--- | :--- |
| **Method / Architecture** | MobileNetV2 pretrained backbone with custom head: `Dropout(0.2) -> Linear(128) -> BatchNorm1d -> ReLU -> Dropout(0.2) -> Linear(5)`. Categorical Cross-Entropy Loss with inverse class frequency weights. Temperature scaling ($T = 0.811$) fitted on validation split. |
| **Training Data** | **987 original field photographs** collected across Indian agricultural soil zones. Split at the connected-component cluster level (exact MD5 + perceptual hash distance $\le 6$) into **Train (699)**, **Validation (144)**, and **Holdout Test (144)**. **Real field photos only** (CycleGAN synthetic clones removed due to documented $-9.72\%$ test domain degradation). |
| **Evaluation Metric** | **Holdout Test Accuracy: 88.19% (127 / 144 correct)** [Wilson 95% CI: 82.64% – 93.07%]. **Macro-F1: 0.809** [Wilson 95% CI: 0.708 – 0.884]. |
| **Per-Class Metrics & 95% CI** | - **Black** ($n=37$): Precision 94.6%, Recall 94.6% [CI: 82.3% – 98.5%], F1: 0.946<br>- **Red** ($n=47$): Precision 93.5%, Recall 91.5% [CI: 80.1% – 96.6%], F1: 0.925<br>- **Sandy** ($n=43$): Precision 97.3%, Recall 83.7% [CI: 70.0% – 91.9%], F1: 0.900<br>- **Clayey** ($n=9$): Precision 72.7%, Recall 88.9% [CI: 56.5% – 98.0%], F1: 0.800<br>- **Loamy** ($n=8$): Precision 38.5%, Recall 62.5% [CI: 30.6% – 86.3%], F1: 0.476 |
| **Calibration** | Expected Calibration Error (ECE) reduced from $12.4\%$ to $5.2\%$ via post-hoc temperature scaling ($T=0.811$) fitted strictly on the validation set. Confidence $< 70\%$ automatically triggers a field test disclaimer in the UI. |
| **Known Limitations** | **Weak performance on Loamy soil** due to small sample size ($n=8$ in test set; precision 38.5%). Wide Wilson confidence intervals on Clayey and Loamy. Photographic glare, moisture shadows, and camera white balance can bias classification. Manual soil texture selection override is provided in the UI. |

---

## 2. Crop Recommendation Model (Pillar 1)

| Dimension | Specification |
| :--- | :--- |
| **Method / Architecture** | `RandomForestClassifier(n_estimators=100, random_state=42)` fitted on standard-scaled 7-dimensional agronomic vectors: $[N, P, K, \text{Temperature}, \text{Humidity}, \text{pH}, \text{Rainfall}]$. |
| **Training Data** | **2,300 tabular records** across 23 crop classes (exactly 100 rows per class).<br>- **Classes 1–22 (Rows 1–2200)**: Open-source Kaggle Crop Recommendation benchmark dataset.<br>- **Class 23 (Wheat, Rows 2201–2300)**: **Synthetic Gaussian simulation** generated to match ICAR Rabi agronomic envelopes for the Indo-Gangetic Plains ($N=94.2 \pm 9.8, P=50.1 \pm 8.2, K=40.3 \pm 7.4$ kg/ha, Temp $19.8 \pm 2.1$°C, Humidity $58.4 \pm 6.1\%$, pH $6.58 \pm 0.42$, Rain $72.1 \pm 11.8$ mm). |
| **Evaluation Metric** | **5-Fold Stratified Cross-Validation: 99.52% ± 0.25% (benchmark data)**. Inner-fold hyperparameter tuned: 99.48% ± 0.22% clean, 95.91% ± 0.37% under realistic sensor noise ($\pm 10\%$ NPK, $\pm 2^\circ\text{C}$, $\pm 15\%$ rain). |
| **Target Leakage / Deprecated Fusion** | Historical Multimodal Spatio-Temporal LSTM Fusion model (98.26% test, 98.84% val, 97.97% test) is marked as **INVALID (TARGET LEAKAGE)** because the training script looked up soil type using the target crop label (`soil_type_map.get(c_label)`). Fusion has been retired from production and isolated under `/api/crop/fusion` with `"is_experimental": true`. |
| **Ambiguity & Decision Boundaries** | Generates Top-3 candidates with exact probabilities. If the probability gap between Rank-1 and Rank-2 is $< 0.15$ ($15\%$), the system flags `"is_ambiguous": true` and issues an agronomic uncertainty warning. |
| **Known Limitations** | **Artificial Dataset Separability**: Benchmark features unimodal, non-overlapping clusters where linear Multinomial Logistic Regression achieves 97.39% and Gaussian Naive Bayes achieves 99.57%. Does not represent real-world soil heterogeneity or microclimatic drift without sensor noise calibration. **Wheat data is synthetic**, carrying an explicit UI badge. |

---

## 3. Fertilizer Prescription & Stoichiometry Engine

| Dimension | Specification |
| :--- | :--- |
| **Method / Architecture** | **Rule-Based Agronomic Stoichiometry Engine (Deterministic, No ML Used in Production)**.<br>Chemical mass balancing based on nutrient content of commercial fertilizers:<br>- DAP (Di-Ammonium Phosphate): $18\%\text{ N}, 46\%\text{ P}_2\text{O}_5$<br>- Urea: $46\%\text{ N}$<br>- MOP (Muriate of Potash): $60\%\text{ K}_2\text{O}$ |
| **Data Source** | Indian Council of Agricultural Research (ICAR) fertilizer application guidelines; Fertilizer Control Order (FCO) chemical formulations. Area conversion factors: 1 Acre = 0.404686 Hectare; 1 Cent = 0.01 Acre; 1 Guntha = 0.025 Acre. Standard commercial package unit: 50 kg bags. |
| **Calculation Flow** | 1. Calculate required $P_2O_5$ deficit; satisfy entirely using DAP.<br>2. Calculate elemental Nitrogen supplied by DAP: $\text{N}_{\text{from DAP}} = \text{DAP}_{\text{kg}} \times 0.18$.<br>3. Deduct $\text{N}_{\text{from DAP}}$ from total Nitrogen requirement; satisfy remaining deficit using Urea ($\text{Urea}_{\text{kg}} = \text{Remaining N} / 0.46$).<br>4. Satisfy Potassium deficit using MOP ($\text{MOP}_{\text{kg}} = \text{K}_2\text{O} / 0.60$).<br>5. Divide net kilogram requirement by 50 to compute commercial 50 kg bag counts. |
| **Metric / Verification** | Deterministic unit tests with hand-calculated expected values covering standard and edge nutrient deficit cases. 100% mathematical consistency. |
| **Known Limitations** | Does not account for dynamic soil nutrient fixation rates, microbial volatilization, or varying irrigation salinity without comprehensive laboratory soil test reports (SHC). Assumes standard commercial fertilizer purity. |

---

## 4. Irrigation Hydrology Engine

| Dimension | Specification |
| :--- | :--- |
| **Method / Architecture** | **FAO-56 Dual Hydrology Engine** combining live meteorological reference evapotranspiration ($ET_0$) with empirical single-crop coefficient ($K_c$) curves:<br>$$ET_c = ET_0 \times K_c$$<br>Net irrigation depth ($\text{mm/day}$) is converted to volumetric demand ($\text{Liters/day}$) based on plot area ($1\text{ mm} = 10,000\text{ L/ha}$). |
| **Data Source** | - **Live $ET_0$**: Open-Meteo High-Resolution Numerical Weather API (`et0_fao_evapotranspiration` via FAO-56 Penman-Monteith).<br>- **Fallback $ET_0$**: FAO-56 Equation 21 extraterrestrial solar radiation ($R_a$) Hargreaves temperature equation calibrated for latitude and day-of-year.<br>- **Crop Coefficients ($K_c$)**: Table of 24 crops across 4 phenological stages (Initial, Development, Mid-Season, Late Season). Values compiled from FAO Irrigation and Drainage Paper 56. |
| **Metric / Verification** | Compared against ICAR Water Technology Centre benchmark figures across 7-day live forecast schedules. Automated unit tests verify volumetric bounds and efficiency scaling (Drip: 90%, Sprinkler: 75%, Surface: 60%). |
| **Data Status Flags** | - $ET_0$ from Open-Meteo API: **VERIFIED (FAO-56 Reference)**.<br>- $ET_0$ from Hargreaves Fallback: **ESTIMATED (Temperature-based proxy)**.<br>- $K_c$ values for minor crops without explicit FAO-56 single-crop tables: **ESTIMATED (Derived from related crop genus)**. |
| **Known Limitations** | Ground soil percolation losses and capillary rise are estimated via static soil texture holding capacities rather than continuous TDR moisture sensor telemetry. Extreme localized microclimate anomalies require on-field validation. |

---

## 5. Harvest Prediction & Economic Modeling Engine

| Dimension | Specification |
| :--- | :--- |
| **Method / Architecture** | **Phenological Degree / Calendar Stage Projection & Indicative Economic Yield Modeler**.<br>Maturity dates projected from sowing date using crop-specific phenological stage divisions (`crop_cycles.json`). Yield and gross revenue calculated using historical ICAR state averages and Government Minimum Support Price (MSP) benchmarks. |
| **Data Source** | - **Phenological Cycle Lengths**: Compiled from Indian Agricultural Statistics Research Institute (IASRI) & ICAR crop production manuals.<br>- **Minimum Support Price (MSP)**: `backend/data/msp.json`. Crops covered under Central Government MSP (Paddy, Wheat, Maize, Cotton, etc.) and non-MSP market estimates. |
| **Data Status Flags** | - Crop Duration & Stages: **INDICATIVE (Subject to thermal time and variety)**.<br>- MSP Benchmark Values: **UNVERIFIED (Requires periodic validation against latest CACP / PIB official gazette notifications)**.<br>- Non-MSP Crop Valuations: **MARKET ESTIMATE (Indicative regional wholesale price)**. |
| **Known Limitations** | Extreme weather events (heatwaves, unseasonal frost, waterlogging) alter biological degree days (GDD) and can shift maturity dates by 1–3 weeks. Yield projections represent regional potential and do not account for pest outbreaks or suboptimal fertilization without field inspection. |

---

## 6. Scientific Governance & Status Summary

| Module | Core Paradigm | Training Data Status | Key Metric Claim | Governance / Audit Status |
| :--- | :--- | :--- | :--- | :--- |
| **Soil CNN** | MobileNetV2 Vision | 987 Real Field Photos | **88.19% Holdout Test Accuracy** (95% CI: 82.6% – 93.1%) | ✅ Audited; 0 test leakage; GAN clones removed |
| **Crop RF** | Random Forest | 2,200 Benchmark + 100 Synthetic Wheat | **99.52% ± 0.25% (5-fold CV, benchmark)** | ✅ Audited; Wheat marked synthetic; Ambiguity flag active |
| **Crop Fusion** | ST-LSTM Multimodal | Synthetic Weather Drift | Historical claims invalid | ⚠️ Retired from production; Prototype flag active |
| **Fertilizer** | Stoichiometric Balancing | Physical Chemistry Laws & ICAR FCO | 100% Mathematical Conservation | ✅ Audited; Hand-calculated test verified |
| **Irrigation** | FAO-56 Penman-Monteith | Open-Meteo Live API + FAO-56 $K_c$ | Exact volumetric balance | ✅ Audited; ET0 fallback Ra verified |
| **Harvest** | Calendar Phenology + MSP | ICAR Cycle Manuals + MSP Tables | Historical Indicative Mean | ⚠️ MSP values marked UNVERIFIED pending CACP gazette |

*All AgriSense AI recommendations are decision-support estimates. Farmers should cross-verify advisories with local Krishi Vigyan Kendra (KVK) officers or state agricultural extension personnel.*
