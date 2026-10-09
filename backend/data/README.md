# Dataset Provenance & Data Specifications

## 1. Crop Recommendation Dataset (`Crop_recommendation.csv`)

- **Primary Source**: Kaggle Crop Recommendation Dataset (2,200 samples across 22 crops, 100 samples per crop).
- **Wheat Class Extension (Rows 2201–2300)**:
  - **Sample Count**: 100 rows.
  - **Origin**: Synthetic Gaussian simulation generated to extend the benchmark dataset with India's primary Rabi cereal staple (Wheat / *Triticum aestivum*).
  - **Agronomic Parameters**: Calibrated to ICAR (Indian Council of Agricultural Research) Rabi standards for the Indo-Gangetic Plains:
    - Nitrogen ($N$): Mean $94.2 \pm 9.8$ kg/ha
    - Phosphorus ($P$): Mean $50.1 \pm 8.2$ kg/ha
    - Potassium ($K$): Mean $40.3 \pm 7.4$ kg/ha
    - Temperature: Mean $19.8 \pm 2.1$ °C (Cool Rabi vegetative phase)
    - Relative Humidity: Mean $58.4 \pm 6.1$ %
    - Soil pH: Mean $6.58 \pm 0.42$
    - Rainfall: Mean $72.1 \pm 11.8$ mm (Irrigated Rabi requirement)
  - **Status & Caveats**: Documented as **Synthetic ICAR Extension / Limited Benchmark Data**. Flagged in the UI with a "Limited Data" advisory badge to indicate it is not derived from multi-season field sensor surveys.

## 2. Real-World Limitations
- The underlying Kaggle dataset features low intra-class variance and near-ideal class separability (Gaussian Naive Bayes achieves 99.57%, Logistic Regression achieves 97.39%).
- Field conditions with sensor drift, spatial nutrient heterogeneity, and microclimate fluctuations should be interpreted using the Top-3 recommendations and ambiguity warning flags.
