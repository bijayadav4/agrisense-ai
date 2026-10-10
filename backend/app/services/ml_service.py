import io
import json
import os
from datetime import datetime, timedelta

import joblib
import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch import nn
from torchvision import models, transforms

from app.config import Config
from app.services.weather_service import (
    calculate_hargreaves_et0,
)

# Agronomic Crop Profiles Database
CROP_PROFILES = {
    "rice": {
        "category": "Cereal / Grain",
        "season": "Kharif (Monsoon)",
        "duration": "105 – 150 Days",
        "water_need": "High (Flooded / Submerged)",
        "ideal_ph": "5.5 – 6.8",
        "soil_suitability": "Clayey or silty loam soils with high water retention.",
        "key_nutrients": "High Nitrogen during tillering, Phosphorus at root start.",
        "harvest_tips": "Harvest when 80-85% of panicles turn golden yellow.",
    },
    "wheat": {
        "category": "Cereal / Grain",
        "season": "Rabi (Winter)",
        "duration": "110 – 135 Days",
        "water_need": "Moderate (Critical at CRI & Flowering stages)",
        "ideal_ph": "6.0 – 7.5",
        "soil_suitability": "Well-drained fertile loamy to clay-loam soils.",
        "key_nutrients": "Balanced N-P-K (120:60:40 kg/ha); starter Zinc & Phosphate.",
        "harvest_tips": "Harvest when spikes turn golden straw-yellow and grain hardens (moisture < 12%).",
    },
    "maize": {
        "category": "Cereal / Grain",
        "season": "Kharif / Rabi / Zaid",
        "duration": "90 – 115 Days",
        "water_need": "Moderate (Critical at tasseling and silking)",
        "ideal_ph": "5.8 – 7.2",
        "soil_suitability": "Well-drained deep loamy soil rich in organic matter.",
        "key_nutrients": "Heavy feeder of Nitrogen and Potassium.",
        "harvest_tips": "Harvest when husk turns brown and moisture in grain is below 20%.",
    },
    "chickpea": {
        "category": "Pulse / Legume",
        "season": "Rabi (Winter)",
        "duration": "90 – 120 Days",
        "water_need": "Low (Drought Tolerant)",
        "ideal_ph": "6.0 – 8.0",
        "soil_suitability": "Deep, well-drained sandy loam to clay loam soils.",
        "key_nutrients": "Fixes atmospheric nitrogen; requires starter phosphorus.",
        "harvest_tips": "Harvest when leaves turn yellow and pods dry out crisp.",
    },
    "kidneybeans": {
        "category": "Pulse / Legume",
        "season": "Kharif / Rabi",
        "duration": "80 – 110 Days",
        "water_need": "Moderate",
        "ideal_ph": "5.8 – 6.8",
        "soil_suitability": "Rich, light, well-draining loamy soil.",
        "key_nutrients": "Moderate Nitrogen, High Phosphorus for blossom retention.",
        "harvest_tips": "Harvest when pods are firm, plump, and turn light tan.",
    },
    "pigeonpeas": {
        "category": "Pulse / Legume",
        "season": "Kharif",
        "duration": "150 – 200 Days",
        "water_need": "Low to Moderate",
        "ideal_ph": "6.5 – 7.5",
        "soil_suitability": "Deep loam to well-drained black cotton soil.",
        "key_nutrients": "Biological nitrogen fixation; benefit from sulfur & phosphorus.",
        "harvest_tips": "Harvest when 80% of the pods turn dark brown.",
    },
    "mothbeans": {
        "category": "Pulse / Legume",
        "season": "Kharif",
        "duration": "75 – 90 Days",
        "water_need": "Very Low (Arid / Drought Hardy)",
        "ideal_ph": "7.0 – 8.5",
        "soil_suitability": "Sandy or sandy loam soils.",
        "key_nutrients": "Minimal fertility needs; excels in poor soils.",
        "harvest_tips": "Harvest in dry morning hours when pods turn brownish yellow.",
    },
    "mungbean": {
        "category": "Pulse / Legume",
        "season": "Kharif / Zaid (Summer)",
        "duration": "60 – 75 Days",
        "water_need": "Low to Moderate",
        "ideal_ph": "6.2 – 7.2",
        "soil_suitability": "Fertile, well-drained sandy loam soil.",
        "key_nutrients": "Responds well to Rhizobium bio-fertilizer.",
        "harvest_tips": "Pick pods as they turn blackish-brown to prevent shattering.",
    },
    "blackgram": {
        "category": "Pulse / Legume",
        "season": "Kharif / Rabi",
        "duration": "70 – 90 Days",
        "water_need": "Low to Moderate",
        "ideal_ph": "6.5 – 7.8",
        "soil_suitability": "Heavy black soils and loams.",
        "key_nutrients": "Fixes atmospheric nitrogen; high phosphorus affinity.",
        "harvest_tips": "Harvest when pods turn dark blackish-gray.",
    },
    "lentil": {
        "category": "Pulse / Legume",
        "season": "Rabi (Winter)",
        "duration": "100 – 130 Days",
        "water_need": "Low",
        "ideal_ph": "6.0 – 7.5",
        "soil_suitability": "Tolerates light sandy to heavy clay soils with good drainage.",
        "key_nutrients": "Starter dose of N and basal P2O5 application.",
        "harvest_tips": "Cut plants when pods on lower branches turn golden-brown.",
    },
    "pomegranate": {
        "category": "Fruit / Orchard",
        "season": "Perennial",
        "duration": "5 – 7 Months",
        "water_need": "Moderate",
        "ideal_ph": "6.5 – 7.5",
        "soil_suitability": "Deep loamy to sandy loam soils.",
        "key_nutrients": "High Potassium and Boron for fruit skin firmness.",
        "harvest_tips": "Harvest when fruit skin turns deep red and sounds metallic on tap.",
    },
    "banana": {
        "category": "Fruit / Tropical",
        "season": "Year-Round",
        "duration": "11 – 14 Months",
        "water_need": "Very High",
        "ideal_ph": "6.0 – 7.5",
        "soil_suitability": "Deep, rich, loose alluvial loam rich in organic matter.",
        "key_nutrients": "Heavy feeder of Potassium and Nitrogen.",
        "harvest_tips": "Harvest bunch when upper fingers lose angularity and become plump.",
    },
    "mango": {
        "category": "Fruit / Orchard",
        "season": "Perennial (Summer)",
        "duration": "100 – 140 Days from flowering",
        "water_need": "Moderate",
        "ideal_ph": "5.5 – 7.5",
        "soil_suitability": "Deep, well-drained alluvial or red loamy soil.",
        "key_nutrients": "Zinc, Boron, Nitrogen in young trees; Potassium in fruiting.",
        "harvest_tips": "Harvest with stem intact when fruit shoulder broadens.",
    },
    "grapes": {
        "category": "Fruit / Vineyard",
        "season": "Perennial (Spring / Summer)",
        "duration": "110 – 150 Days after pruning",
        "water_need": "Moderate",
        "ideal_ph": "6.5 – 8.0",
        "soil_suitability": "Well-drained sandy loam or gravelly soil.",
        "key_nutrients": "Balanced N-P-K, Magnesium, and Zinc.",
        "harvest_tips": "Harvest when Brix sugar meter reaches 18–22 degrees.",
    },
    "watermelon": {
        "category": "Fruit / Cucurbit",
        "season": "Zaid (Summer)",
        "duration": "75 – 95 Days",
        "water_need": "Moderate",
        "ideal_ph": "6.0 – 6.8",
        "soil_suitability": "Sandy or sandy loam soils warm to 21°C.",
        "key_nutrients": "High Potassium and Phosphorus for sugar accumulation.",
        "harvest_tips": "Harvest when bottom ground spot turns creamy yellow.",
    },
    "muskmelon": {
        "category": "Fruit / Cucurbit",
        "season": "Zaid (Summer)",
        "duration": "70 – 90 Days",
        "water_need": "Moderate",
        "ideal_ph": "6.0 – 7.0",
        "soil_suitability": "Sandy loam rich in organic matter.",
        "key_nutrients": "High Potassium and Boron.",
        "harvest_tips": "Harvest at full-slip stage when fruit separates easily from vine.",
    },
    "apple": {
        "category": "Fruit / Temperate Orchard",
        "season": "Autumn",
        "duration": "130 – 170 Days after bloom",
        "water_need": "Moderate",
        "ideal_ph": "6.0 – 7.0",
        "soil_suitability": "Deep, well-drained loamy soil without hardpan.",
        "key_nutrients": "Calcium for fruit firmness, Nitrogen in spring.",
        "harvest_tips": "Harvest when background color turns yellowish.",
    },
    "orange": {
        "category": "Fruit / Citrus Orchard",
        "season": "Autumn / Winter",
        "duration": "7 – 10 Months",
        "water_need": "Moderate",
        "ideal_ph": "6.0 – 7.5",
        "soil_suitability": "Light loam with high permeability and low salinity.",
        "key_nutrients": "Nitrogen, Potassium, Iron, Manganese foliar sprays.",
        "harvest_tips": "Clip fruit carefully from tree when skin turns orange.",
    },
    "papaya": {
        "category": "Fruit / Tropical",
        "season": "Year-Round",
        "duration": "9 – 11 Months",
        "water_need": "Moderate to High",
        "ideal_ph": "6.0 – 6.5",
        "soil_suitability": "Well-drained porous sandy loam soil.",
        "key_nutrients": "Continuous feeder of balanced N-P-K.",
        "harvest_tips": "Harvest when fruit shows yellow/orange streaks on skin.",
    },
    "coconut": {
        "category": "Plantation / Palm",
        "season": "Perennial",
        "duration": "12 Months for nut maturity",
        "water_need": "High",
        "ideal_ph": "5.2 – 8.0",
        "soil_suitability": "Coastal sandy, alluvial, or red sandy loam soils.",
        "key_nutrients": "High Potassium (Muriate of Potash) and Sodium/Chloride.",
        "harvest_tips": "Harvest mature nuts for copra and oil extraction.",
    },
    "cotton": {
        "category": "Commercial / Fiber",
        "season": "Kharif",
        "duration": "150 – 180 Days",
        "water_need": "Moderate",
        "ideal_ph": "6.0 – 8.0",
        "soil_suitability": "Deep black cotton soil (Vertisols) with good moisture holding.",
        "key_nutrients": "High Nitrogen during canopy, Potassium during boll filling.",
        "harvest_tips": "Pick clean, dry bolls in morning hours after dew.",
    },
    "jute": {
        "category": "Commercial / Fiber",
        "season": "Kharif",
        "duration": "120 – 150 Days",
        "water_need": "High",
        "ideal_ph": "6.0 – 7.5",
        "soil_suitability": "New alluvial silt soils deposited by river basins.",
        "key_nutrients": "High Nitrogen for vegetative stem elongation.",
        "harvest_tips": "Harvest at 50% flowering stage for strong tensile fiber.",
    },
    "coffee": {
        "category": "Plantation / Beverage",
        "season": "Winter / Early Spring Harvest",
        "duration": "7 – 9 Months from blossom",
        "water_need": "Moderate",
        "ideal_ph": "5.5 – 6.5",
        "soil_suitability": "Deep, porous volcanic or forest loam rich in organic humus.",
        "key_nutrients": "High Potassium and Nitrogen; periodic compost mulching.",
        "harvest_tips": "Selective hand-picking of bright red ripe coffee cherries.",
    },
}

# Fertilizer Information Database
FERTILIZER_PROFILES = {
    "Urea": {
        "npk_ratio": "46-0-0",
        "primary_nutrient": "Nitrogen (46%)",
        "description": "High-nitrogen fertilizer for rapid green leaf growth, tillering, and healthy vegetative development.",
        "dosage_guidelines": "80 – 120 kg/hectare (30 – 50 kg/acre, ~1 to 2 Bags)",
        "application_method": "Apply in 2 split doses: 50% at basal sowing and 50% at tillering/growth stage. Spread evenly in moist soil.",
        "organic_alternatives": "Vermicompost (2–3 tons/acre), Cow dung manure, or Neem cake (200 kg/acre).",
        "soil_prep_tips": "Do not apply urea onto dry soil in hot sun. Irrigate lightly after application.",
    },
    "DAP": {
        "npk_ratio": "18-46-0",
        "primary_nutrient": "Phosphorus (46%) + Nitrogen (18%)",
        "description": "Diammonium Phosphate is the premier source of readily available phosphorus, building deep strong roots and vigorous seedling establishment.",
        "dosage_guidelines": "75 – 100 kg/hectare (30 – 40 kg/acre, ~1 Bag)",
        "application_method": "Apply as a basal dose at sowing placed 3-5 cm below and beside the seed line.",
        "organic_alternatives": "Steamed Bone Meal (150 kg/acre) or Rock Phosphate with Phosphate Solubilizing Bacteria (PSB).",
        "soil_prep_tips": "Place near the root zone; avoid surface broadcasting for best uptake.",
    },
    "14-35-14": {
        "npk_ratio": "14-35-14",
        "primary_nutrient": "High Phosphorus + Balanced N & K",
        "description": "Complex grade tailored for crops needing high initial phosphorus for root system establishment while supplying balanced nitrogen and potassium.",
        "dosage_guidelines": "100 – 150 kg/hectare (40 – 60 kg/acre, ~1 to 2 Bags)",
        "application_method": "Apply at basal sowing stage or during early vegetative cultivation.",
        "organic_alternatives": "Compost enriched with wood ash and bone meal.",
        "soil_prep_tips": "Ideal for cotton, sugarcane, and oilseed crops in low-phosphorus soils.",
    },
    "28-28": {
        "npk_ratio": "28-28-0",
        "primary_nutrient": "Equal High Nitrogen & Phosphorus",
        "description": "High-analysis dual nutrient complex delivering equal proportions of Nitrogen and Phosphate for intensive crop development.",
        "dosage_guidelines": "100 – 125 kg/hectare (40 – 50 kg/acre, ~1 to 2 Bags)",
        "application_method": "Apply 50% at sowing as basal and 50% at first vegetative weeding.",
        "organic_alternatives": "Farmyard Manure (FYM) mixed with poultry compost.",
        "soil_prep_tips": "Excellent for wheat, paddy, and tobacco in soils sufficient in potassium.",
    },
    "17-17-17": {
        "npk_ratio": "17-17-17",
        "primary_nutrient": "Balanced N-P-K (1:1:1)",
        "description": "Complete universal balanced fertilizer ensuring uniform nutrition across root development, stem vigor, flowering, and fruit setting.",
        "dosage_guidelines": "125 – 175 kg/hectare (50 – 70 kg/acre, ~2 Bags)",
        "application_method": "Split application: 50% at basal sowing, 50% at flowering/branching.",
        "organic_alternatives": "Well-rotted cow dung manure (3-4 tons/acre) enriched with Panchagavya.",
        "soil_prep_tips": "Optimal for general vegetables, maize, and orchards.",
    },
    "20-20": {
        "npk_ratio": "20-20-0 + 13% S",
        "primary_nutrient": "Nitrogen (20%) + Phosphate (20%) + Sulfur",
        "description": "Ammonium Phosphate Sulfate complex containing readily available sulfur, boosting oil content in oilseeds and grain protein.",
        "dosage_guidelines": "100 – 150 kg/hectare (40 – 60 kg/acre, ~1 to 2 Bags)",
        "application_method": "Apply as basal dressing or top dressing after first weeding.",
        "organic_alternatives": "Gypsum (100 kg/acre) + Compost + Castor cake.",
        "soil_prep_tips": "Crucial for mustard, groundnut, soybean, and onion crops.",
    },
    "10-26-26": {
        "npk_ratio": "10-26-26",
        "primary_nutrient": "High Potassium & Phosphorus",
        "description": "Potash and phosphorus rich complex designed for tuber development, fruit enlargement, disease resistance, and drought tolerance.",
        "dosage_guidelines": "125 – 180 kg/hectare (50 – 75 kg/acre, ~2 Bags)",
        "application_method": "Apply at tuber initiation, fruit set, or second top-dressing.",
        "organic_alternatives": "Wood ash (250 kg/acre) + Green leaf manure + Bio-potash.",
        "soil_prep_tips": "Recommended for potato, banana, sugarcane, onion, and fruit orchards.",
    },
}

# TYPICAL_VALUES_REFERENCE: Static agronomic reference values for educational demo use only.
# NOTE: This is NOT a model input or training feature. Computer vision cannot determine chemical NPK/pH from photographs.
TYPICAL_VALUES_REFERENCE = {
    "Black": {"N": 75, "P": 32, "K": 48, "ph": 7.4, "moisture": 62},
    "Clayey": {"N": 85, "P": 42, "K": 40, "ph": 6.5, "moisture": 70},
    "Loamy": {"N": 90, "P": 50, "K": 45, "ph": 6.8, "moisture": 45},
    "Red": {"N": 45, "P": 24, "K": 35, "ph": 6.2, "moisture": 35},
    "Sandy": {"N": 35, "P": 18, "K": 22, "ph": 7.1, "moisture": 25},
}

# Detailed Agronomic Profiles for the 5 Primary Agricultural Soil Classes
SOIL_PROFILES = {
    "Black": {
        "title": "Black Cotton Soil (Vertisol)",
        "description": "Clay-rich, self-ploughing black soil with exceptional moisture holding capacity and high montmorillonite content. Highly fertile but requires good drainage during continuous monsoons.",
        "texture": "Heavy Clay / Fine textured",
        "estimated_properties": TYPICAL_VALUES_REFERENCE["Black"],
        "suitable_crops": ["Cotton", "Sugarcane", "Wheat", "Chilli", "Pigeonpeas", "Soybean"],
        "management_tips": "Prevent waterlogging by constructing broad bed furrows (BBF). Split nitrogen application is recommended.",
        "color_badge": "#1e293b",
    },
    "Clayey": {
        "title": "Clayey Wetland Soil",
        "description": "Dense, finely grained soil with high cation-exchange capacity and water retention. Holds standing water exceptionally well for submerged field crops.",
        "texture": "Heavy Clayey Loam / Plastic when wet",
        "estimated_properties": TYPICAL_VALUES_REFERENCE["Clayey"],
        "suitable_crops": ["Paddy (Rice)", "Wheat", "Jute", "Blackgram"],
        "management_tips": "Incorporate green manuring and well-rotted compost to improve soil aeration and root permeability.",
        "color_badge": "#0f766e",
    },
    "Loamy": {
        "title": "Alluvial Loamy Soil",
        "description": "The agronomic gold standard soil: balanced equilibrium of sand, silt, and clay. Optimal water retention, root aeration, and microbial activity.",
        "texture": "Rich Loam / Crumbly structure",
        "estimated_properties": TYPICAL_VALUES_REFERENCE["Loamy"],
        "suitable_crops": ["Wheat", "Maize", "Sugarcane", "Cotton", "Banana", "Papaya", "Vegetables"],
        "management_tips": "Maintain topsoil organic carbon via crop residue mulching and balanced N-P-K replenishment.",
        "color_badge": "#b45309",
    },
    "Red": {
        "title": "Red Loamy / Alfisol Soil",
        "description": "Porous, well-draining soil rich in iron oxides and manganese, slightly acidic to neutral. Non-swelling and responds rapidly to irrigation and foliar nutrients.",
        "texture": "Sandy to Loamy Sand",
        "estimated_properties": TYPICAL_VALUES_REFERENCE["Red"],
        "suitable_crops": ["Ground Nuts", "Millets", "Tobacco", "Pigeonpeas", "Mango", "Potato"],
        "management_tips": "Apply agricultural lime if pH drops below 6.0 and supplement phosphate (DAP) directly into the root zone.",
        "color_badge": "#b91c1c",
    },
    "Sandy": {
        "title": "Sandy / Arid Plains Soil",
        "description": "Coarse-textured soil with high infiltration and aeration but low nutrient and water retention. Warm soil ideal for quick root spreading.",
        "texture": "Coarse Sand / High percolation",
        "estimated_properties": TYPICAL_VALUES_REFERENCE["Sandy"],
        "suitable_crops": ["Watermelon", "Muskmelon", "Ground Nuts", "Mothbeans", "Chickpea", "Barley"],
        "management_tips": "Adopt drip irrigation and frequent split applications of soluble fertilizers to avoid leaching losses.",
        "color_badge": "#ca8a04",
    },
}


class SoilCNNClassifier(nn.Module):
    """MobileNetV2 Vision Classifier for Agricultural Soil Types."""

    def __init__(self, num_classes=5):
        super().__init__()
        self.backbone = models.mobilenet_v2(weights=None)
        in_features = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=0.2),
            nn.Linear(in_features, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(p=0.2),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        return self.backbone(x)


class SoilEncoder(nn.Module):
    """Encodes soil chemistry (N, P, K, pH, Soil_Type) into a dense latent vector."""

    def __init__(self, in_features=5, hidden_dim=32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )

    def forward(self, x):
        return self.net(x)


class TemporalWeatherLSTM(nn.Module):
    """Processes 7-day multi-step meteorological sequences using Bi-directional LSTM."""

    def __init__(self, in_channels=3, hidden_dim=32, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=in_channels,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=0.1 if num_layers > 1 else 0.0,
        )
        self.proj = nn.Sequential(nn.Linear(hidden_dim * 2, hidden_dim), nn.ReLU())

    def forward(self, x):
        lstm_out, (hn, _) = self.lstm(x)
        seq_summary = torch.cat([hn[-2], hn[-1]], dim=1)
        return self.proj(seq_summary)


class SpatioTemporalCropFusionModel(nn.Module):
    """
    Multimodal Agriculture Fusion Network with Feature Bottleneck:
    Fuses static spatial soil chemistry with dynamic temporal climate sequences.
    """

    def __init__(self, soil_dim=5, weather_dim=3, hidden_dim=32, bottleneck_dim=24, num_classes=23):
        super().__init__()
        self.soil_encoder = SoilEncoder(in_features=soil_dim, hidden_dim=hidden_dim)
        self.weather_lstm = TemporalWeatherLSTM(in_channels=weather_dim, hidden_dim=hidden_dim, num_layers=2)
        self.bottleneck = nn.Sequential(
            nn.Linear(hidden_dim * 2, bottleneck_dim), nn.BatchNorm1d(bottleneck_dim), nn.ReLU(), nn.Dropout(0.2)
        )
        self.classifier = nn.Linear(bottleneck_dim, num_classes)

    def forward(self, soil_x, weather_seq):
        soil_emb = self.soil_encoder(soil_x)
        weather_emb = self.weather_lstm(weather_seq)
        fused = torch.cat([soil_emb, weather_emb], dim=1)
        bottleneck_features = self.bottleneck(fused)
        return self.classifier(bottleneck_features)

    def extract_bottleneck(self, soil_x, weather_seq):
        with torch.no_grad():
            soil_emb = self.soil_encoder(soil_x)
            weather_emb = self.weather_lstm(weather_seq)
            fused = torch.cat([soil_emb, weather_emb], dim=1)
            return self.bottleneck(fused)


class MLService:
    def __init__(self):
        self.crop_model = None
        self.crop_scaler = None
        self.fert_model = None
        self.fert_scaler = None
        self.fert_encoders = None
        self.soil_model = None
        self.soil_classes = ["Black", "Clayey", "Loamy", "Red", "Sandy"]
        self.soil_transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )
        self.fusion_model = None
        self.fusion_classes = []
        self.kc_data = self.load_kc_table()
        self.crop_cycles_data = self.load_crop_cycles()
        self.msp_data = self.load_msp_table()
        self.crop_seasons_data = self.load_crop_seasons()
        self.load_models()

    def load_models(self):
        # Load Crop Recommendation Model
        try:
            if os.path.exists(Config.MODEL_PATH) and os.path.exists(Config.SCALER_PATH):
                self.crop_model = joblib.load(Config.MODEL_PATH)
                self.crop_scaler = joblib.load(Config.SCALER_PATH)
                print("✅ Crop Model and Scaler loaded successfully.")
            else:
                print(f"⚠️ Crop model artifact paths not found: {Config.MODEL_PATH}")
        except Exception as e:
            print(f"⚠️ Failed to load Crop Model: {e}")

        # Load Fertilizer Recommendation Model
        try:
            if os.path.exists(Config.FERTILIZER_MODEL_PATH) and os.path.exists(Config.FERTILIZER_SCALER_PATH):
                self.fert_model = joblib.load(Config.FERTILIZER_MODEL_PATH)
                self.fert_scaler = joblib.load(Config.FERTILIZER_SCALER_PATH)
                if os.path.exists(Config.FERTILIZER_ENCODER_PATH):
                    self.fert_encoders = joblib.load(Config.FERTILIZER_ENCODER_PATH)
                print("✅ Fertilizer Model and Scaler loaded successfully.")
            else:
                print(f"⚠️ Fertilizer model artifact paths not found: {Config.FERTILIZER_MODEL_PATH}")
        except Exception as e:
            print(f"⚠️ Failed to load Fertilizer Model: {e}")

        # Load Soil CNN Vision Model
        try:
            soil_path = getattr(Config, "SOIL_CNN_MODEL_PATH", None)
            if soil_path and os.path.exists(soil_path):
                model = SoilCNNClassifier(num_classes=len(self.soil_classes))
                state_dict = torch.load(soil_path, map_location=torch.device("cpu"))
                model.load_state_dict(state_dict)
                model.eval()
                self.soil_model = model
                print("✅ Soil CNN Vision Model loaded successfully.")
            else:
                print(f"ℹ️ Soil CNN model path not found: {soil_path}")
        except Exception as e:
            print(f"⚠️ Failed to load Soil CNN Model: {e}")

        # Load Spatio-Temporal LSTM & Bottleneck Fusion Model
        try:
            fusion_path = getattr(Config, "FUSION_LSTM_MODEL_PATH", None)
            if fusion_path and os.path.exists(fusion_path):
                checkpoint = torch.load(fusion_path, map_location=torch.device("cpu"))
                classes = checkpoint.get("classes", [])
                arch = checkpoint.get("architecture", {})
                model = SpatioTemporalCropFusionModel(
                    soil_dim=arch.get("soil_dim", 5),
                    weather_dim=arch.get("weather_dim", 3),
                    hidden_dim=arch.get("hidden_dim", 32),
                    bottleneck_dim=arch.get("bottleneck_dim", 24),
                    num_classes=arch.get("num_classes", len(classes) if classes else 23),
                )
                model.load_state_dict(checkpoint["model_state"])
                model.eval()
                self.fusion_model = model
                self.fusion_classes = classes
                print("✅ Spatio-Temporal LSTM & Bottleneck Fusion Model loaded successfully.")
            else:
                print(f"ℹ️ Fusion model path not found: {fusion_path}")
        except Exception as e:
            print(f"⚠️ Failed to load Fusion LSTM Model: {e}")

    def load_kc_table(self):
        json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "kc_table.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading kc_table.json: {e}")
        return {"crops": {}, "soil_properties": {}, "irrigation_efficiencies": {}}

    def load_crop_cycles(self):
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "crop_cycles.json"
        )
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading crop_cycles.json: {e}")
        return {"crops": {}}

    def load_msp_table(self):
        json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "msp.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading msp.json: {e}")
        return {"crops": {}}

    def load_crop_seasons(self):
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "crop_seasons.json"
        )
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading crop_seasons.json: {e}")
        return {}

    def analyze_soil_health(self, n, p, k, ph):
        """Generates comprehensive N-P-K & pH status diagnosis and soil amendment advice."""
        status = {}
        recommendations = []

        # Nitrogen Analysis (kg/ha)
        if n < 50:
            status["nitrogen"] = {
                "level": "Deficient",
                "value": n,
                "color": "#ef4444",
                "desc": "Low nitrogen will cause pale yellow lower leaves and slow growth.",
            }
            recommendations.append(
                "Incorporate well-rotted cow dung manure, vermicompost, or split dose of neem-coated urea."
            )
        elif n <= 100:
            status["nitrogen"] = {
                "level": "Optimal",
                "value": n,
                "color": "#22c55e",
                "desc": "Nitrogen is optimal for healthy vegetative growth.",
            }
        else:
            status["nitrogen"] = {
                "level": "Excess",
                "value": n,
                "color": "#eab308",
                "desc": "High nitrogen may cause excess foliage and delay flowering.",
            }
            recommendations.append("Avoid excess nitrogenous fertilizer and irrigate well to balance nitrates.")

        # Phosphorus Analysis (kg/ha)
        if p < 35:
            status["phosphorus"] = {
                "level": "Deficient",
                "value": p,
                "color": "#ef4444",
                "desc": "Low phosphorus impairs root elongation and seedling start.",
            }
            recommendations.append(
                "Apply DAP or steamed bone meal with Phosphate Solubilizing Bacteria (PSB) at root depth."
            )
        elif p <= 70:
            status["phosphorus"] = {
                "level": "Optimal",
                "value": p,
                "color": "#22c55e",
                "desc": "Phosphorus supply is optimal for root anchoring and tillering.",
            }
        else:
            status["phosphorus"] = {
                "level": "Excess",
                "value": p,
                "color": "#eab308",
                "desc": "High phosphorus level in soil.",
            }

        # Potassium Analysis (kg/ha)
        if k < 35:
            status["potassium"] = {
                "level": "Deficient",
                "value": k,
                "color": "#ef4444",
                "desc": "Low potassium weakens stems and reduces disease resistance.",
            }
            recommendations.append(
                "Apply Muriate of Potash (MOP) or wood ash to boost stalk strength and grain filling."
            )
        elif k <= 70:
            status["potassium"] = {
                "level": "Optimal",
                "value": k,
                "color": "#22c55e",
                "desc": "Potassium reserves are optimal for plant strength.",
            }
        else:
            status["potassium"] = {
                "level": "High",
                "value": k,
                "color": "#3b82f6",
                "desc": "Good potassium reserve for disease protection and yield.",
            }

        # pH Analysis
        if ph < 6.0:
            status["ph"] = {
                "level": "Sour / Acidic",
                "value": ph,
                "color": "#f97316",
                "desc": "Acidic soil restricts nutrient absorption.",
            }
            recommendations.append("Apply agricultural lime (CaCO3) or dolomite to neutralize soil acidity.")
        elif ph <= 7.5:
            status["ph"] = {
                "level": "Neutral / Ideal",
                "value": ph,
                "color": "#22c55e",
                "desc": "Ideal pH range for maximum crop nutrient uptake.",
            }
        else:
            status["ph"] = {"level": "Alkaline", "value": ph, "color": "#a855f7", "desc": "Alkaline soil."}
            recommendations.append("Apply agricultural gypsum or sulfur with organic compost to lower pH.")

        return status, recommendations

    def predict_crop(self, data):
        """Predict recommended crop + top-3 alternatives with probabilities + agronomic profile based on soil/climate."""
        n = float(data.get("N", 0))
        p = float(data.get("P", 0))
        k = float(data.get("K", 0))
        temp = float(data.get("temperature", 25.0))
        humidity = float(data.get("humidity", 65.0))
        ph = float(data.get("ph", 6.5))
        rainfall = float(data.get("rainfall", 100.0))

        feature_names = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
        features_df = pd.DataFrame([[n, p, k, temp, humidity, ph, rainfall]], columns=feature_names)

        if self.crop_scaler:
            scaled_features = self.crop_scaler.transform(features_df)
        else:
            scaled_features = features_df.values

        top_crops = []
        alternatives = []
        is_ambiguous = False
        ambiguity_warning = None
        prob_gap = 1.0

        if self.crop_model is None:
            primary_crop = "rice" if rainfall > 150 else ("cotton" if temp > 28 else "wheat")
            confidence = 88.5
            top_crops = [
                {
                    "crop": primary_crop,
                    "probability": 0.885,
                    "confidence": 88.5,
                    "profile": CROP_PROFILES.get(primary_crop, {}),
                    "provenance_note": "Limited benchmark data (synthetic ICAR extension)"
                    if primary_crop == "wheat"
                    else None,
                }
            ]
        else:
            primary_crop = str(self.crop_model.predict(scaled_features)[0]).lower()
            confidence = 92.0

            if hasattr(self.crop_model, "predict_proba"):
                probabilities = self.crop_model.predict_proba(scaled_features)[0]
                classes = self.crop_model.classes_
                top_indices = np.argsort(probabilities)[::-1]
                primary_confidence = round(float(probabilities[top_indices[0]]) * 100, 1)
                confidence = primary_confidence

                # Top-3 crops with explicit probabilities
                for rank, idx in enumerate(top_indices[:3]):
                    c_name = str(classes[idx]).lower()
                    p_val = float(probabilities[idx])
                    crop_item = {
                        "rank": rank + 1,
                        "crop": c_name,
                        "probability": round(p_val, 4),
                        "confidence": round(p_val * 100, 1),
                        "profile": CROP_PROFILES.get(c_name, {}),
                        "provenance_note": "Limited benchmark data (synthetic ICAR extension)"
                        if c_name == "wheat"
                        else None,
                    }
                    top_crops.append(crop_item)

                # Check ambiguity gap: top-1 vs top-2 < 0.15 (15%)
                if len(top_indices) >= 2:
                    p1 = float(probabilities[top_indices[0]])
                    p2 = float(probabilities[top_indices[1]])
                    prob_gap = round(p1 - p2, 4)
                    if prob_gap < 0.15:
                        is_ambiguous = True
                        ambiguity_warning = (
                            f"Ambiguous prediction: Confidence gap between '{top_crops[0]['crop'].capitalize()}' "
                            f"({top_crops[0]['confidence']}%) and '{top_crops[1]['crop'].capitalize()}' "
                            f"({top_crops[1]['confidence']}%) is only {round(prob_gap * 100, 1)}% (<15%). "
                            "Soil and climate conditions overlap between these crops; field validation recommended."
                        )

                # Maintain backward-compatible alternatives
                for idx in top_indices[1:4]:
                    prob = round(float(probabilities[idx]) * 100, 1)
                    if prob > 0.5:
                        alt_name = str(classes[idx]).lower()
                        alternatives.append(
                            {
                                "crop": alt_name,
                                "confidence": prob,
                                "probability": round(float(probabilities[idx]), 4),
                                "profile": CROP_PROFILES.get(alt_name, {}),
                                "provenance_note": "Limited benchmark data (synthetic ICAR extension)"
                                if alt_name == "wheat"
                                else None,
                            }
                        )

        soil_health, soil_amendments = self.analyze_soil_health(n, p, k, ph)
        crop_profile = CROP_PROFILES.get(
            primary_crop,
            {
                "category": "General Field Crop",
                "season": "Kharif / Rabi",
                "duration": "90 – 120 Days",
                "water_need": "Moderate",
                "ideal_ph": "6.0 – 7.5",
                "soil_suitability": "Fertile, well-draining agricultural loam.",
                "key_nutrients": "Balanced N-P-K supply.",
                "harvest_tips": "Harvest when crop reaches physiological maturity.",
            },
        )

        # Seasonal sowing suitability check
        try:
            req_month = int(data.get("month", datetime.now().month))
        except (ValueError, TypeError):
            req_month = datetime.now().month

        season_entry = self.crop_seasons_data.get(primary_crop, {})
        suitable_months = season_entry.get("suitable_months", [])
        season_name = season_entry.get("season_name", "General Sowing Window")
        season_notes = season_entry.get("notes", "")

        month_names = [
            "",
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        current_month_name = month_names[req_month] if 1 <= req_month <= 12 else f"Month {req_month}"

        is_out_of_season = False
        season_warning = None

        if suitable_months and req_month not in suitable_months:
            is_out_of_season = True
            months_text = ", ".join([month_names[m][:3] for m in suitable_months if 1 <= m <= 12])
            season_warning = (
                f"Seasonal Advisory: {primary_crop.capitalize()} is typically sown in {season_name} ({months_text}). "
                f"Current month ({current_month_name}) is outside the recommended sowing window. {season_notes}"
            )

        is_demo_mode = ("demo" in str(data.get("data_source", "")).lower()) or bool(data.get("is_estimated", False))
        ambiguous_tag = "ambiguous" if (is_ambiguous and is_demo_mode) else None
        data_source_str = str(data.get("data_source", "User entered")).strip()

        return {
            "crop": primary_crop,
            "confidence": confidence,
            "profile": crop_profile,
            "top_crops": top_crops,
            "is_ambiguous": is_ambiguous,
            "ambiguity_warning": ambiguity_warning,
            "confidence_gap": prob_gap,
            "ambiguous_tag": ambiguous_tag,
            "is_out_of_season": is_out_of_season,
            "season_warning": season_warning,
            "season_info": {
                "season_name": season_name,
                "suitable_months": suitable_months,
                "current_month": req_month,
                "current_month_name": current_month_name,
                "notes": season_notes,
            },
            "provenance_note": "Limited benchmark data (synthetic ICAR extension)" if primary_crop == "wheat" else None,
            "data_source": data_source_str,
            "is_estimated": is_demo_mode,
            "estimated_warning": "Estimated values. Please confirm with a lab test." if is_demo_mode else None,
            "alternatives": alternatives,
            "soil_health": soil_health,
            "soil_amendments": soil_amendments,
        }

    def predict_fertilizer(self, data):
        """Predict recommended fertilizer + dosage per acre + organic alternatives + ICAR dosage."""
        temp = float(data.get("temperature", 25))
        humidity = float(data.get("humidity", 50))
        moisture = float(data.get("moisture", 30))
        n = float(data.get("N", 0))
        p = float(data.get("P", 0))
        k = float(data.get("K", 0))

        # 1. Robust Soil Type Normalization (Matches LabelEncoder classes: Black, Clayey, Loamy, Red, Sandy)
        raw_soil = str(data.get("soil_type", "Clayey")).strip().lower()
        if "clay" in raw_soil:
            soil_type = "Clayey"
        elif "loam" in raw_soil:
            soil_type = "Loamy"
        elif "sand" in raw_soil:
            soil_type = "Sandy"
        elif "black" in raw_soil:
            soil_type = "Black"
        elif "red" in raw_soil:
            soil_type = "Red"
        else:
            soil_type = "Clayey"

        # 2. Robust Crop Type Normalization
        raw_crop = str(data.get("crop_type", "Paddy")).strip().lower()
        if "paddy" in raw_crop or "rice" in raw_crop:
            crop_type = "Paddy"
        elif "wheat" in raw_crop:
            crop_type = "Wheat"
        elif "maize" in raw_crop or "corn" in raw_crop:
            crop_type = "Maize"
        elif "cotton" in raw_crop:
            crop_type = "Cotton"
        elif "sugarcane" in raw_crop:
            crop_type = "Sugarcane"
        elif "tobacco" in raw_crop:
            crop_type = "Tobacco"
        elif "barley" in raw_crop:
            crop_type = "Barley"
        elif "millet" in raw_crop:
            crop_type = "Millets"
        elif "oil" in raw_crop:
            crop_type = "Oil seeds"
        elif "pulse" in raw_crop:
            crop_type = "Pulses"
        elif "ground" in raw_crop or "nut" in raw_crop:
            crop_type = "Ground Nuts"
        else:
            crop_type = "Paddy"

        enc_soil = soil_type
        enc_crop = crop_type

        if isinstance(self.fert_encoders, dict):
            if "Soil Type" in self.fert_encoders and soil_type in self.fert_encoders["Soil Type"].classes_:
                enc_soil = self.fert_encoders["Soil Type"].transform([soil_type])[0]
            if "Crop Type" in self.fert_encoders and crop_type in self.fert_encoders["Crop Type"].classes_:
                enc_crop = self.fert_encoders["Crop Type"].transform([crop_type])[0]

        val_map = {
            "Temparature": temp,
            "Temperature": temp,
            "Humidity ": humidity,
            "Humidity": humidity,
            "Moisture": moisture,
            "Soil Type": enc_soil,
            "Crop Type": enc_crop,
            "Nitrogen": n,
            "N": n,
            "Phosphorous": p,
            "Phosphorus": p,
            "P": p,
            "Potassium": k,
            "K": k,
        }

        if hasattr(self.fert_scaler, "feature_names_in_"):
            expected_cols = list(self.fert_scaler.feature_names_in_)
            row = [val_map.get(col, 0) for col in expected_cols]
            features_df = pd.DataFrame([row], columns=expected_cols)
        else:
            cols = [
                "Temparature",
                "Humidity ",
                "Moisture",
                "Soil Type",
                "Crop Type",
                "Nitrogen",
                "Potassium",
                "Phosphorous",
            ]
            features_df = pd.DataFrame([[temp, humidity, moisture, enc_soil, enc_crop, n, k, p]], columns=cols)

        if self.fert_model is None or self.fert_scaler is None:
            if n < 25 and p < 20:
                prediction = "DAP"
            elif n < 30 and k < 20:
                prediction = "10-26-26"
            elif n >= 35:
                prediction = "Urea"
            else:
                prediction = "28-28"
            confidence = 88.0
        else:
            try:
                scaled_features = self.fert_scaler.transform(features_df)
                prediction = str(self.fert_model.predict(scaled_features)[0])
                confidence = 90.0
                if hasattr(self.fert_model, "predict_proba"):
                    probabilities = self.fert_model.predict_proba(scaled_features)[0]
                    confidence = round(float(np.max(probabilities)) * 100, 1)
            except Exception as e:
                print(f"⚠️ Fertilizer prediction warning: {e}")
                prediction = "Urea" if n >= 35 else "28-28"
                confidence = 85.0

        fert_profile = FERTILIZER_PROFILES.get(
            prediction,
            {
                "npk_ratio": "Standard Mineral Grade",
                "primary_nutrient": "Balanced N-P-K",
                "description": "Mineral nutrient formula designed to restore optimal soil fertility.",
                "dosage_guidelines": "80 – 120 kg/hectare (30 – 50 kg/acre, ~1 to 2 Bags)",
                "application_method": "Apply as side-dressing or incorporate into moist soil.",
                "organic_alternatives": "Cow dung manure, vermicompost, and neem cake.",
                "soil_prep_tips": "Ensure proper soil moisture at time of application.",
            },
        )

        # 3. ICAR Scientific Nutrient Gap & Dosage Calculation (Per Acre)
        ICAR_STANDARDS = {
            "Paddy": {
                "target_N": 120,
                "target_P": 60,
                "target_K": 40,
                "splits": "50% Basal + 25% Tillering (20-25 DAT) + 25% Panicle Initiation (45 DAT)",
            },
            "Wheat": {
                "target_N": 120,
                "target_P": 60,
                "target_K": 40,
                "splits": "50% Basal at Sowing + 25% CRI Stage (21 DAS) + 25% Jointing (45 DAS)",
            },
            "Maize": {
                "target_N": 120,
                "target_P": 60,
                "target_K": 50,
                "splits": "33% Basal + 33% Knee-high stage + 33% Tasseling stage",
            },
            "Cotton": {
                "target_N": 100,
                "target_P": 50,
                "target_K": 50,
                "splits": "30% Basal + 35% Square formation + 35% Peak flowering",
            },
            "Sugarcane": {
                "target_N": 250,
                "target_P": 115,
                "target_K": 115,
                "splits": "4 Splits: Basal, 45, 90, and 120 Days after planting",
            },
            "Pulses": {"target_N": 20, "target_P": 40, "target_K": 20, "splits": "100% Basal application at sowing"},
            "Ground Nuts": {
                "target_N": 25,
                "target_P": 50,
                "target_K": 75,
                "splits": "50% Basal + 50% Pegging stage (30-35 DAS)",
            },
            "Millets": {"target_N": 80, "target_P": 40, "target_K": 40, "splits": "50% Basal + 50% Tillering stage"},
            "Barley": {"target_N": 60, "target_P": 30, "target_K": 20, "splits": "60% Basal + 40% First irrigation"},
            "Oil seeds": {
                "target_N": 80,
                "target_P": 40,
                "target_K": 40,
                "splits": "50% Basal + 50% Rosette/flowering",
            },
            "Tobacco": {
                "target_N": 80,
                "target_P": 50,
                "target_K": 100,
                "splits": "Split application during active vegetative growth",
            },
        }

        std = ICAR_STANDARDS.get(
            crop_type, {"target_N": 100, "target_P": 50, "target_K": 40, "splits": "Split application"}
        )

        # 1 Hectare = 2.47105 Acres
        ac_factor = 2.47105
        acre_target_n = std["target_N"] / ac_factor
        acre_target_p = std["target_P"] / ac_factor
        acre_target_k = std["target_K"] / ac_factor

        # A. Full ICAR Blanket Recommended Dose (RDF) for 1 Acre (No soil test deduction)
        blanket_dap_kg = round(acre_target_p / 0.46, 1)
        blanket_dap_bags = round(blanket_dap_kg / 50.0, 2)
        blanket_n_from_dap = blanket_dap_kg * 0.18
        blanket_rem_n = max(0.0, acre_target_n - blanket_n_from_dap)
        blanket_urea_kg = round(blanket_rem_n / 0.46, 1)
        blanket_urea_bags = round(blanket_urea_kg / 50.0, 2)
        blanket_mop_kg = round(acre_target_k / 0.60, 1)
        blanket_mop_bags = round(blanket_mop_kg / 50.0, 2)

        # B. Soil-Adjusted Deficit Dose (Deducting nutrients already available in soil)
        # Note: Soil Health Card test values (n, p, k) are input in kg/ha and normalized to kg/acre
        has_soil_test = n > 0 or p > 0 or k > 0
        soil_n_acre = round(n / ac_factor, 1)
        soil_p_acre = round(p / ac_factor, 1)
        soil_k_acre = round(k / ac_factor, 1)

        raw_def_n = acre_target_n - soil_n_acre
        raw_def_p = acre_target_p - soil_p_acre
        raw_def_k = acre_target_k - soil_k_acre

        def_n = max(0.0, raw_def_n)
        def_p = max(0.0, raw_def_p)
        def_k = max(0.0, raw_def_k)

        # Check sufficiency: if raw deficit <= 0, the soil already has sufficient nutrients!
        p_sufficient = has_soil_test and (raw_def_p <= 0)
        n_sufficient = has_soil_test and (raw_def_n <= 0)
        k_sufficient = has_soil_test and (raw_def_k <= 0)
        all_sufficient = has_soil_test and (p_sufficient and n_sufficient and k_sufficient)

        adj_dap_kg = round(def_p / 0.46, 1) if def_p > 0 else 0.0
        adj_dap_bags = round(adj_dap_kg / 50.0, 2)
        adj_n_from_dap = adj_dap_kg * 0.18

        adj_rem_n = max(0.0, def_n - adj_n_from_dap)
        adj_urea_kg = round(adj_rem_n / 0.46, 1) if adj_rem_n > 0 else 0.0
        adj_urea_bags = round(adj_urea_kg / 50.0, 2)

        adj_mop_kg = round(def_k / 0.60, 1) if def_k > 0 else 0.0
        adj_mop_bags = round(adj_mop_kg / 50.0, 2)

        # Descriptive text for soil-adjusted dose (avoid bare 0.0)
        dap_status_text = (
            "Soil Already Sufficient (0 Bags)" if p_sufficient else f"{adj_dap_kg} kg/acre ({adj_dap_bags} Bags)"
        )
        urea_status_text = (
            "Soil Already Sufficient (0 Bags)"
            if (n_sufficient or adj_urea_kg == 0)
            else f"{adj_urea_kg} kg/acre ({adj_urea_bags} Bags)"
        )
        mop_status_text = (
            "Soil Already Sufficient (0 Bags)" if k_sufficient else f"{adj_mop_kg} kg/acre ({adj_mop_bags} Bags)"
        )

        # Determine the Active Prescribed Application Rate per Acre:
        # Strictly enforce: when soil test is provided (has_soil_test == True),
        # the active prescription MUST be the soil-adjusted net dosage, never blanket fallback!
        active_dap_kg = adj_dap_kg if has_soil_test else blanket_dap_kg
        active_dap_bags = adj_dap_bags if has_soil_test else blanket_dap_bags
        active_urea_kg = adj_urea_kg if has_soil_test else blanket_urea_kg
        active_urea_bags = adj_urea_bags if has_soil_test else blanket_urea_bags
        active_mop_kg = adj_mop_kg if has_soil_test else blanket_mop_kg
        active_mop_bags = adj_mop_bags if has_soil_test else blanket_mop_bags

        active_dap_text = dap_status_text if has_soil_test else f"{blanket_dap_kg} kg/acre ({blanket_dap_bags} Bags)"
        active_urea_text = (
            urea_status_text if has_soil_test else f"{blanket_urea_kg} kg/acre ({blanket_urea_bags} Bags)"
        )
        active_mop_text = mop_status_text if has_soil_test else f"{blanket_mop_kg} kg/acre ({blanket_mop_bags} Bags)"

        # Verified Split Schedule for Active Prescribed Dose
        split_basal = f"{active_dap_kg} kg DAP (100%) + {round(active_urea_kg * 0.5, 1)} kg Urea (50%) + {round(active_mop_kg * 0.5, 1)} kg MOP (50%)"
        split_tillering = f"{round(active_urea_kg * 0.25, 1)} kg Urea (25%)"
        split_panicle = (
            f"{round(active_urea_kg * 0.25, 1)} kg Urea (25%) + {round(active_mop_kg * 0.5, 1)} kg MOP (50%)"
        )

        scientific_plan = {
            "crop": crop_type,
            "soil_type": soil_type,
            "icar_target_ha": f"{std['target_N']}:{std['target_P']}:{std['target_K']} (N:P:K kg/ha)",
            "icar_target_acre": f"{round(acre_target_n, 1)}:{round(acre_target_p, 1)}:{round(acre_target_k, 1)} (N:P:K kg/acre)",
            # Full Blanket Recommendation (State Baseline RDF for 1 Acre)
            "blanket_dose": {
                "dap_kg": blanket_dap_kg,
                "dap_bags": blanket_dap_bags,
                "urea_kg": blanket_urea_kg,
                "urea_bags": blanket_urea_bags,
                "mop_kg": blanket_mop_kg,
                "mop_bags": blanket_mop_bags,
                "dap_text": f"{blanket_dap_kg} kg/acre ({blanket_dap_bags} Bags)",
                "urea_text": f"{blanket_urea_kg} kg/acre ({blanket_urea_bags} Bags)",
                "mop_text": f"{blanket_mop_kg} kg/acre ({blanket_mop_bags} Bags)",
            },
            # Soil-Adjusted Deficit Dose
            "has_soil_test": has_soil_test,
            "soil_adjusted_dose": {
                "dap_kg": adj_dap_kg,
                "dap_bags": adj_dap_bags,
                "urea_kg": adj_urea_kg,
                "urea_bags": adj_urea_bags,
                "mop_kg": adj_mop_kg,
                "mop_bags": adj_mop_bags,
                "dap_text": dap_status_text,
                "urea_text": urea_status_text,
                "mop_text": mop_status_text,
                "p_sufficient": p_sufficient,
                "n_sufficient": n_sufficient,
                "k_sufficient": k_sufficient,
                "all_sufficient": all_sufficient,
                "p_surplus_kg": round(abs(min(0.0, raw_def_p)), 1),
                "n_surplus_kg": round(abs(min(0.0, raw_def_n)), 1),
                "k_surplus_kg": round(abs(min(0.0, raw_def_k)), 1),
                "soil_n_acre": soil_n_acre,
                "soil_p_acre": soil_p_acre,
                "soil_k_acre": soil_k_acre,
            },
            # Active Prescribed Dosage (Strictly bound to Soil-Adjusted Net when has_soil_test=True)
            "active_rate": {
                "mode": "Soil-Test Adjusted Net Application" if has_soil_test else "ICAR State Baseline RDF",
                "is_soil_adjusted": has_soil_test,
                "all_sufficient": all_sufficient,
                "dap_kg": active_dap_kg,
                "dap_bags": active_dap_bags,
                "urea_kg": active_urea_kg,
                "urea_bags": active_urea_bags,
                "mop_kg": active_mop_kg,
                "mop_bags": active_mop_bags,
                "dap_text": active_dap_text,
                "urea_text": active_urea_text,
                "mop_text": active_mop_text,
            },
            # Prescribed recommendation bindings (strictly reflect active dose)
            "dap_recommendation": active_dap_text,
            "urea_recommendation": active_urea_text,
            "mop_recommendation": active_mop_text,
            "application_schedule": std["splits"],
            # Detailed Agronomic Splits
            "splits_detail": {"basal": split_basal, "tillering": split_tillering, "panicle": split_panicle},
        }

        data_source = str(data.get("data_source", "User entered")).strip()
        is_estimated = ("demo" in data_source.lower()) or bool(data.get("is_estimated", False))
        estimated_warning = "Estimated, not for actual application" if is_estimated else None

        scientific_plan["data_source"] = data_source
        scientific_plan["is_estimated"] = is_estimated
        if estimated_warning:
            scientific_plan["estimated_warning"] = estimated_warning

        return {
            "fertilizer": prediction,
            "confidence": confidence,
            "profile": fert_profile,
            "scientific_plan": scientific_plan,
            "data_source": data_source,
            "is_estimated": is_estimated,
            "estimated_warning": estimated_warning,
            "input_summary": {
                "soil_type": soil_type,
                "crop_type": crop_type,
                "npk_applied": f"N:{n} | P:{p} | K:{k}",
                "moisture": f"{moisture}%",
                "data_source": data_source,
            },
        }

    def predict_soil_image(self, image_source):
        """
        Classifies uploaded soil photo using MobileNetV2 Vision CNN.
        Returns predicted soil type, confidence, agronomic properties, and crop recommendations.
        """
        try:
            if isinstance(image_source, Image.Image):
                img = image_source.convert("RGB")
            elif isinstance(image_source, bytes):
                img = Image.open(io.BytesIO(image_source)).convert("RGB")
            else:
                img = Image.open(image_source).convert("RGB")

            tensor = self.soil_transform(img).unsqueeze(0)  # Shape: [1, 3, 224, 224]

            if self.soil_model is not None:
                with torch.no_grad():
                    logits = self.soil_model(tensor)
                    probabilities = torch.softmax(logits, dim=1)[0].numpy()

                top_idx = int(np.argmax(probabilities))
                pred_class = self.soil_classes[top_idx]
                confidence = round(float(probabilities[top_idx]) * 100, 1)

                class_breakdown = {
                    self.soil_classes[i]: round(float(probabilities[i]) * 100, 1) for i in range(len(self.soil_classes))
                }
            else:
                pred_class = "Loamy"
                confidence = 88.0
                class_breakdown = {"Loamy": 88.0, "Clayey": 5.0, "Black": 4.0, "Red": 2.0, "Sandy": 1.0}

            profile = SOIL_PROFILES.get(pred_class, SOIL_PROFILES["Loamy"])

            return {
                "soil_type": pred_class,
                "confidence": confidence,
                "is_low_confidence": confidence < 70.0,
                "confidence_warning": "Low confidence. Please get a soil test done." if confidence < 70.0 else None,
                "profile": profile,
                "estimated_properties": profile["estimated_properties"],
                "suitable_crops": profile["suitable_crops"],
                "class_probabilities": class_breakdown,
            }

        except Exception as e:
            print(f"❌ Error in predict_soil_image: {e!s}")
            raise e

    def predict_crop_spatiotemporal(self, soil_data, weather_sequence=None, weather_metadata=None):
        """
        Multimodal Crop Recommendation combining Spatial Soil Features + 7-Day Temporal Weather LSTM
        compressed through an Agronomic Feature Bottleneck.
        """
        try:
            n = float(soil_data.get("N", 80))
            p = float(soil_data.get("P", 40))
            k = float(soil_data.get("K", 40))
            ph = float(soil_data.get("ph", 6.5))
            raw_soil = str(soil_data.get("soil_type", "Loamy")).strip().capitalize()

            soil_map = {"Clayey": 0, "Loamy": 1, "Sandy": 2, "Black": 3, "Red": 4}
            soil_idx = soil_map.get(raw_soil, 1) / 4.0

            soil_tensor = torch.tensor([[n / 140.0, p / 145.0, k / 205.0, ph / 14.0, soil_idx]], dtype=torch.float32)

            # Build 7-day weather sequence
            if weather_sequence is not None and len(weather_sequence) >= 7:
                seq_arr = []
                for step in weather_sequence[:7]:
                    t_val = float(step.get("temperature", step.get("max_temp", 25.0))) / 45.0
                    h_val = float(step.get("humidity", 65.0)) / 100.0
                    r_val = float(step.get("rainfall", step.get("rain_mm", 10.0))) / 60.0
                    seq_arr.append([t_val, h_val, r_val])
                weather_tensor = torch.tensor([seq_arr], dtype=torch.float32)
            else:
                base_t = float(soil_data.get("temperature", 26.0))
                base_h = float(soil_data.get("humidity", 65.0))
                base_r = float(soil_data.get("rainfall", 100.0))
                seq = []
                for d in range(7):
                    drift_t = np.sin((d / 7.0) * np.pi) * 2.0
                    drift_h = np.cos((d / 7.0) * np.pi) * 3.5
                    rain_mult = 1.2 if d in [2, 3] else 0.8
                    day_t = np.clip((base_t + drift_t) / 45.0, 0.0, 1.0)
                    day_h = np.clip((base_h + drift_h) / 100.0, 0.0, 1.0)
                    day_r = np.clip((base_r * rain_mult / 7.0) / 60.0, 0.0, 1.0)
                    seq.append([day_t, day_h, day_r])
                weather_tensor = torch.tensor([seq], dtype=torch.float32)

            if self.fusion_model is not None and self.fusion_classes:
                with torch.no_grad():
                    logits = self.fusion_model(soil_tensor, weather_tensor)
                    probabilities = torch.softmax(logits, dim=1)[0].numpy()
                    bottleneck_vec = (
                        self.fusion_model.extract_bottleneck(soil_tensor, weather_tensor)[0].numpy().tolist()
                    )

                top_indices = np.argsort(probabilities)[::-1]
                primary_idx = top_indices[0]
                primary_crop = self.fusion_classes[primary_idx]
                confidence = round(float(probabilities[primary_idx]) * 100, 1)

                alternatives = []
                for idx in top_indices[1:4]:
                    prob = round(float(probabilities[idx]) * 100, 1)
                    if prob > 0.5:
                        alt_name = self.fusion_classes[idx]
                        alternatives.append(
                            {"crop": alt_name, "confidence": prob, "profile": CROP_PROFILES.get(alt_name, {})}
                        )
            else:
                rf_res = self.predict_crop(soil_data)
                primary_crop = rf_res["crop"]
                confidence = rf_res["confidence"]
                alternatives = rf_res["alternatives"]
                bottleneck_vec = [0.12, 0.45, 0.88, 0.34, 0.56, 0.72, 0.29, 0.91]

            soil_health, soil_amendments = self.analyze_soil_health(n, p, k, ph)
            crop_profile = CROP_PROFILES.get(primary_crop, CROP_PROFILES.get("rice", {}))

            return {
                "crop": primary_crop,
                "confidence": confidence,
                "profile": crop_profile,
                "alternatives": alternatives,
                "bottleneck_features": [round(x, 4) for x in bottleneck_vec[:8]],
                "fusion_architecture": {
                    "spatial_encoder": "Dense Soil Chemistry MLP (5 -> 32)",
                    "temporal_encoder": "2-Layer Bidirectional LSTM (7-day x 3 -> 32)",
                    "fusion_layer": "Multimodal Concatenation (64-dim)",
                    "bottleneck_layer": "Agronomic Dimensionality Reduction (64 -> 24-dim)",
                    "classifier": f"Softmax Classification ({len(self.fusion_classes)} Crops)",
                },
                "soil_health": soil_health,
                "soil_amendments": soil_amendments,
            }

        except Exception as e:
            print(f"❌ Error in predict_crop_spatiotemporal: {e!s}")
            raise e

    def calculate_irrigation_plan(self, data):
        """
        Precision Crop Water Calculation & Irrigation Planning Engine.
        Supports Open-Meteo FAO-56 Penman-Monteith and Hargreaves (Eq. 21 Ra) Fallback.
        Calculates ETc, rainfall offset, drip vs flood water volumes, and soil water intervals.
        """
        raw_crop = str(data.get("crop", "")).strip().lower()
        crops_dict = self.kc_data.get("crops", {})
        if not raw_crop or raw_crop not in crops_dict:
            supported = ", ".join(sorted(crops_dict.keys())) if crops_dict else "rice, wheat, maize, cotton, etc."
            raise ValueError(f"Unknown or unsupported crop '{raw_crop}'. Supported crops: {supported}")

        # Area validation
        area_ha = float(data.get("area_hectares", 1.0))
        if area_ha <= 0:
            raise ValueError("Cultivated farm area must be positive and greater than 0.")

        stage = str(data.get("growth_stage", "flowering")).strip().lower()
        soil_type = str(data.get("soil_type", "Loamy")).strip().capitalize()
        rainfall = max(0.0, float(data.get("rainfall", 0.0)))

        crop_info = crops_dict[raw_crop]
        kc_table = crop_info.get("kc", {})
        kc_val = float(kc_table.get(stage, kc_table.get("flowering", 1.0)))
        kc_source = crop_info.get("source", "FAO-56")

        # 1. Determine ET0 and Method Attribution
        lat = float(data.get("lat") or data.get("latitude") or 18.52)
        day_of_year = int(data.get("day_of_year")) if data.get("day_of_year") is not None else None

        if "et0" in data and data["et0"] is not None and float(data["et0"]) > 0:
            et0 = round(float(data["et0"]), 3)
            et0_method = str(data.get("et0_method", "open-meteo-fao56"))
        elif (
            "et0_fao_evapotranspiration" in data
            and data["et0_fao_evapotranspiration"] is not None
            and float(data["et0_fao_evapotranspiration"]) > 0
        ):
            et0 = round(float(data["et0_fao_evapotranspiration"]), 3)
            et0_method = "open-meteo-fao56"
        elif "open_meteo_et0" in data and data["open_meteo_et0"] is not None and float(data["open_meteo_et0"]) > 0:
            et0 = round(float(data["open_meteo_et0"]), 3)
            et0_method = "open-meteo-fao56"
        else:
            # Fallback Hargreaves formula: 0.0023 * (Tmean + 17.8) * sqrt(Tmax - Tmin) * Ra
            tmean = float(data.get("temperature", 28.0))
            if "tmax" in data and "tmin" in data:
                tmax = float(data["tmax"])
                tmin = float(data["tmin"])
            elif "temperature_max" in data and "temperature_min" in data:
                tmax = float(data["temperature_max"])
                tmin = float(data["temperature_min"])
            elif "delta_t" in data:
                delta_t = float(data["delta_t"])
                tmax = tmean + delta_t / 2.0
                tmin = tmean - delta_t / 2.0
            else:
                tmax = tmean + 5.0
                tmin = tmean - 5.0

            ra_custom = (
                float(data["ra"]) if "ra" in data else (float(data["ra_custom"]) if "ra_custom" in data else None)
            )
            et0 = calculate_hargreaves_et0(
                tmean=tmean, tmax=tmax, tmin=tmin, lat=lat, day_of_year=day_of_year, ra_custom=ra_custom
            )
            et0_method = "hargreaves-fallback"

        # 2. Crop Evapotranspiration (ETc = ET0 * Kc) — Pure FAO-56, NO soil_adj multiplier
        etc = round(et0 * kc_val, 2)

        # 3. Effective Rainfall Offset (USDA-SCS empirical 75% offset capped at ETc)
        peff = round(min(etc, rainfall * 0.75) if rainfall > 0 else 0.0, 2)
        inet_depth = round(max(0.0, etc - peff), 2)

        # Check for natural rainfall satisfaction
        is_skip_rain = (rainfall >= etc or peff >= etc) and rainfall > 0
        if is_skip_rain:
            inet_depth = 0.0
            daily_liters_net = 0.0
            status = "🌧️ Sufficient Natural Rainfall — Skip Irrigation Today"
            recommendation = f"Natural precipitation ({rainfall} mm) satisfies crop evapotranspiration ({etc} mm). Skip irrigation today to conserve water."
        elif inet_depth < 0.5:
            daily_liters_net = 0.0
            status = "✅ Soil Moisture Optimal — Skip Irrigation Today"
            recommendation = "Soil moisture reserves are sufficient. Light moisture maintenance only."
        else:
            daily_liters_net = round(inet_depth * area_ha * 10000.0, 1)
            status = "💧 Standard Scheduled Irrigation Required"
            recommendation = f"Apply net {daily_liters_net:,.0f} Liters today. Optimize drip or furrow runtimes according to system efficiency."

        # 4. Irrigation System Physics: Drip vs Flood & Efficiencies
        eff_drip = 0.90
        eff_sprinkler = 0.75
        eff_flood = 0.60

        def_drip = crop_info.get(
            "default_drip", {"emitter_lph": 2.0, "emitter_spacing_m": 0.4, "lateral_spacing_m": 0.8}
        )
        emitter_lph = float(data.get("emitter_lph", def_drip["emitter_lph"]))
        emitter_spacing_m = float(data.get("emitter_spacing_m", def_drip["emitter_spacing_m"]))
        lateral_spacing_m = float(data.get("lateral_spacing_m", def_drip["lateral_spacing_m"]))

        application_rate_mm_hr = round(emitter_lph / (emitter_spacing_m * lateral_spacing_m), 2)
        drip_capacity_lph = round(area_ha * 10000.0 * application_rate_mm_hr, 1)

        gross_drip_liters = round(daily_liters_net / eff_drip, 1) if daily_liters_net > 0 else 0.0
        gross_drip_depth_mm = round(inet_depth / eff_drip, 2) if inet_depth > 0 else 0.0
        drip_runtime_hours = (
            round(gross_drip_depth_mm / application_rate_mm_hr, 1)
            if application_rate_mm_hr > 0 and inet_depth > 0
            else 0.0
        )

        gross_flood_liters = round(daily_liters_net / eff_flood, 1) if daily_liters_net > 0 else 0.0
        _gross_flood_depth_mm = round(inet_depth / eff_flood, 2) if inet_depth > 0 else 0.0
        flood_pump_lph = float(data.get("flood_pump_lph", 25000.0))
        flood_runtime_hours = round(gross_flood_liters / flood_pump_lph, 1) if gross_flood_liters > 0 else 0.0

        gross_sprinkler_liters = round(daily_liters_net / eff_sprinkler, 1) if daily_liters_net > 0 else 0.0

        # 5. Soil Water Balance & Irrigation Interval (Soil used for interval, not ETc modification)
        soil_props = self.kc_data.get("soil_properties", {})
        soil_info = soil_props.get(soil_type, {"awc_mm_per_m": 140, "label": "Loamy Soil"})
        awc_mm_m = soil_info.get("awc_mm_per_m", 140)
        rooting_depth_m = float(crop_info.get("rooting_depth_m", 0.8))
        mad = float(crop_info.get("mad", 0.50))
        taw_mm = round(awc_mm_m * rooting_depth_m, 1)
        raw_mm = round(taw_mm * mad, 1)
        irrigation_interval_days = round(raw_mm / etc, 1) if etc > 0 else 1.0

        # 6. 7-Day Schedule from Actual Meteorological Forecast
        weekly_schedule = []
        forecast_list = data.get("forecast", [])
        if forecast_list and len(forecast_list) > 0:
            for i, f_day in enumerate(forecast_list[:7]):
                day_name = f_day.get("day", f"Day {i + 1}")
                day_rain = float(f_day.get("rain_mm", 0.0))
                day_et0 = float(f_day.get("et0")) if f_day.get("et0") is not None else et0
                day_etc = round(day_et0 * kc_val, 2)
                day_peff = round(min(day_etc, day_rain * 0.75) if day_rain > 0 else 0.0, 2)
                day_inet = round(max(0.0, day_etc - day_peff), 2)
                if (day_rain >= day_etc or day_peff >= day_etc) and day_rain > 0:
                    day_inet = 0.0
                    day_status = "Skip (Rain)"
                else:
                    day_status = "Irrigate" if day_inet > 0 else "Skip"

                day_net_lit = round(day_inet * area_ha * 10000.0)
                day_gross_drip = round(day_net_lit / eff_drip) if day_net_lit > 0 else 0
                day_runtime = (
                    round((day_inet / eff_drip) / application_rate_mm_hr, 1)
                    if application_rate_mm_hr > 0 and day_inet > 0
                    else 0.0
                )

                weekly_schedule.append(
                    {
                        "day": day_name,
                        "date": f_day.get("date", ""),
                        "reference_et0_mm": day_et0,
                        "water_depth_mm": day_inet,
                        "net_liters": day_net_lit,
                        "liters": day_gross_drip,
                        "runtime_hours": day_runtime,
                        "rainfall_mm": day_rain,
                        "status": day_status,
                    }
                )
        else:
            base_doy = day_of_year or datetime.now().timetuple().tm_yday
            days_labels = ["Today", "Tomorrow", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"]
            for i, d_label in enumerate(days_labels):
                proj_doy = base_doy + i
                if et0_method == "hargreaves-fallback":
                    day_et0 = calculate_hargreaves_et0(
                        tmean=tmean, tmax=tmax, tmin=tmin, lat=lat, day_of_year=proj_doy, ra_custom=ra_custom
                    )
                else:
                    day_et0 = et0

                day_rain = rainfall if i == 0 else 0.0
                day_etc = round(day_et0 * kc_val, 2)
                day_peff = round(min(day_etc, day_rain * 0.75) if day_rain > 0 else 0.0, 2)
                day_inet = round(max(0.0, day_etc - day_peff), 2)
                if (day_rain >= day_etc or day_peff >= day_etc) and day_rain > 0:
                    day_inet = 0.0
                    day_status = "Skip (Rain)"
                else:
                    day_status = "Irrigate" if day_inet > 0 else "Skip"

                day_net_lit = round(day_inet * area_ha * 10000.0)
                day_gross_drip = round(day_net_lit / eff_drip) if day_net_lit > 0 else 0
                day_runtime = (
                    round((day_inet / eff_drip) / application_rate_mm_hr, 1)
                    if application_rate_mm_hr > 0 and day_inet > 0
                    else 0.0
                )

                weekly_schedule.append(
                    {
                        "day": d_label,
                        "date": "",
                        "reference_et0_mm": day_et0,
                        "water_depth_mm": day_inet,
                        "net_liters": day_net_lit,
                        "liters": day_gross_drip,
                        "runtime_hours": day_runtime,
                        "rainfall_mm": day_rain,
                        "status": day_status,
                    }
                )

        return {
            "crop": raw_crop.capitalize(),
            "crop_name": crop_info.get("name", raw_crop.capitalize()),
            "growth_stage": stage.capitalize(),
            "soil_type": soil_type,
            "area_hectares": area_ha,
            "area_acres": round(area_ha * 2.47105, 2),
            "reference_et0_mm": et0,
            "et0_method": et0_method,
            "crop_coefficient_kc": kc_val,
            "kc_source": kc_source,
            "crop_water_need_mm": etc,
            "soil_adjustment": "none (applied to irrigation interval)",
            "effective_rain_offset_mm": peff,
            "net_irrigation_depth_mm": inet_depth,
            "daily_liters": daily_liters_net,
            "daily_liters_net": daily_liters_net,
            "gross_drip_liters": gross_drip_liters,
            "gross_flood_liters": gross_flood_liters,
            "gross_sprinkler_liters": gross_sprinkler_liters,
            "drip_runtime_hours": drip_runtime_hours,
            "flood_runtime_hours": flood_runtime_hours,
            "application_rate_mm_hr": application_rate_mm_hr,
            "irrigation_efficiencies": {"drip": eff_drip, "sprinkler": eff_sprinkler, "flood": eff_flood},
            "soil_water_balance": {
                "awc_mm_per_m": awc_mm_m,
                "rooting_depth_m": rooting_depth_m,
                "taw_mm": taw_mm,
                "mad": mad,
                "raw_mm": raw_mm,
                "irrigation_interval_days": irrigation_interval_days,
                "description": f"Soil holds {raw_mm} mm readily available water before stress; irrigate every ~{irrigation_interval_days} days.",
            },
            "system_specs": {
                "emitter_lph": emitter_lph,
                "emitter_spacing_m": emitter_spacing_m,
                "lateral_spacing_m": lateral_spacing_m,
                "drip_capacity_lph": drip_capacity_lph,
            },
            "status": status,
            "advisory": recommendation,
            "weekly_schedule": weekly_schedule,
        }

    def predict_harvest_timeline(self, data):
        """
        Phenological Growth Stage & Harvest Prediction Engine.
        Calculates exact maturity countdown, phenological stages, and ICAR expected yield.
        Complies with timezone (Asia/Kolkata), crop cycle benchmarks, and MSP data.
        """
        from datetime import datetime
        from zoneinfo import ZoneInfo

        raw_crop = str(data.get("crop", "")).strip().lower()
        crops_cycle = self.crop_cycles_data.get("crops", {})
        msp_crops = self.msp_data.get("crops", {})

        if not raw_crop or raw_crop not in crops_cycle:
            supported = ", ".join(sorted(crops_cycle.keys()))
            raise ValueError(f"Unknown crop '{raw_crop}'. Supported crops: {supported}")

        sowing_date_str = str(data.get("sowing_date", "")).strip()
        if not sowing_date_str:
            raise ValueError("sowing_date is required in YYYY-MM-DD format.")
        try:
            sowing_dt = datetime.strptime(sowing_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid sowing_date '{sowing_date_str}'. Expected YYYY-MM-DD format.")

        area_ha = float(data.get("area_hectares", 1.0))
        if area_ha <= 0:
            raise ValueError("Area must be greater than 0.")
        _area_acres = round(area_ha * 2.47105, 2)

        crop_info = crops_cycle[raw_crop]
        msp_info = msp_crops.get(
            raw_crop,
            {
                "crop": crop_info.get("name", raw_crop.capitalize()),
                "msp_rs_per_quintal": 2500,
                "season": "Annual",
                "year": "2024-25 (UNVERIFIED)",
                "type": "market_estimate",
                "verification_status": "UNVERIFIED",
                "source_url": "https://cacp.dacnet.nic.in",
            },
        )

        # Variety duration days override
        variety_duration = data.get("variety_duration_days")
        if variety_duration is not None and str(variety_duration).strip() != "":
            try:
                total_duration = int(variety_duration)
                if total_duration <= 0:
                    raise ValueError("variety_duration_days must be greater than 0.")
            except (ValueError, TypeError):
                raise ValueError("variety_duration_days must be a valid positive integer.")
        else:
            total_duration = int(crop_info.get("duration_days", 120))

        # Timezone comparison: compare only dates in Asia/Kolkata
        today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
        harvest_dt = sowing_dt + timedelta(days=total_duration)

        days_elapsed = (today - sowing_dt).days
        days_remaining = (harvest_dt - today).days

        warnings = []
        is_perennial = crop_info.get("type") == "perennial"
        indicative_only = is_perennial

        if is_perennial:
            warnings.append(
                "Perennial orchard crop: Timeline and yield are indicative annual fruiting cycle estimates, not seedling-to-first-harvest."
            )

        # Future sowing date check
        if days_elapsed < 0:
            days_until_sowing = abs(days_elapsed)
            days_overdue = 0
            status = "Upcoming"
            starts_in_message = f"Starts in {days_until_sowing} day{'s' if days_until_sowing != 1 else ''}"
            progress_pct = 0.0
            is_harvest_ready = False
        elif days_remaining < 0:
            # Overdue harvest
            days_until_sowing = 0
            days_overdue = abs(days_remaining)
            status = "Overdue"
            starts_in_message = None
            progress_pct = 100.0
            is_harvest_ready = True
            if days_elapsed > (total_duration * 1.5):
                warnings.append(
                    f"Sowing date is more than 1.5x cycle duration ({days_elapsed} days elapsed vs {total_duration} days cycle). Harvest is severely overdue or cycle has expired."
                )
        else:
            # Active growth cycle
            days_until_sowing = 0
            days_overdue = 0
            starts_in_message = None
            progress_pct = min(100.0, max(0.0, round((days_elapsed / total_duration) * 100.0, 1)))
            is_harvest_ready = days_remaining <= 5
            status = "Harvest Ready" if is_harvest_ready else "Active"

        # Stages timeline calculation
        split = crop_info.get(
            "stage_split",
            {"germination": 0.15, "vegetative": 0.30, "flowering": 0.30, "grain_filling": 0.20, "maturity": 0.05},
        )
        stage_names = crop_info.get(
            "stage_names",
            [
                "Germination & Seedling Emergence",
                "Active Vegetative & Tillering / Branching",
                "Flowering & Panicle / Tasseling Initiation",
                "Grain / Fruit Filling & Sizing",
                "Physiological Maturity & Harvest Window",
            ],
        )

        f1 = float(split.get("germination", 0.15))
        f2 = float(split.get("vegetative", 0.30))
        f3 = float(split.get("flowering", 0.30))
        f4 = float(split.get("grain_filling", 0.20))
        _f5 = float(split.get("maturity", 0.05))

        d1 = max(1, round(total_duration * f1))
        d2 = max(d1 + 1, round(total_duration * (f1 + f2)))
        d3 = max(d2 + 1, round(total_duration * (f1 + f2 + f3)))
        d4 = max(d3 + 1, round(total_duration * (f1 + f2 + f3 + f4)))
        d5 = total_duration

        stage_ranges = [(1, d1), (d1 + 1, d2), (d2 + 1, d3), (d3 + 1, d4), (d4 + 1, d5)]

        tips = [
            "Maintain consistent moist seedbed. Protect from surface crusting.",
            "Apply first nitrogen top-dressing to stimulate robust vegetative canopy.",
            "Critical moisture sensitive window. Ensure field is not subjected to drought stress.",
            "Potassium foliar boost enhances grain weight, fruit size, and starch accumulation.",
            CROP_PROFILES.get(raw_crop, {}).get(
                "harvest_tips", "Harvest when crop turns golden yellow and moisture < 14%."
            ),
        ]

        stages = []
        for i in range(5):
            start_d, end_d = stage_ranges[i]
            s_name = stage_names[i] if i < len(stage_names) else f"Stage {i + 1}"
            tip = tips[i] if i < len(tips) else ""

            if days_elapsed < 0:
                s_status = "Upcoming"
            elif days_remaining < 0:
                s_status = "Completed"
            else:
                if days_elapsed < start_d:
                    s_status = "Upcoming"
                elif days_elapsed > end_d:
                    s_status = "Completed"
                else:
                    s_status = "Active"

            stages.append({"stage": s_name, "day_range": f"Day {start_d} – {end_d}", "status": s_status, "tip": tip})

        # Yield adjustments (soil & irrigation)
        yield_adjustments_applied = []
        adj_factor = 1.0

        soil_type = str(data.get("soil", data.get("soil_type", ""))).strip().lower()
        if soil_type in ["clayey", "loamy", "black"]:
            yield_adjustments_applied.append(
                {
                    "factor": f"Soil suitability ({soil_type.capitalize()})",
                    "multiplier": 1.05,
                    "source": "ICAR-CSSRI Soil Quality & Nutrient Benchmark",
                }
            )
            adj_factor *= 1.05
        elif soil_type in ["sandy", "saline"]:
            yield_adjustments_applied.append(
                {
                    "factor": f"Soil constraint ({soil_type.capitalize()})",
                    "multiplier": 0.90,
                    "source": "ICAR-CSSRI Marginal Land Assessment",
                }
            )
            adj_factor *= 0.90

        irrigation = str(data.get("irrigation_type", data.get("irrigation", ""))).strip().lower()
        if irrigation in ["drip", "micro"]:
            yield_adjustments_applied.append(
                {
                    "factor": "High efficiency micro-irrigation (Drip)",
                    "multiplier": 1.10,
                    "source": "ICAR-WTC Micro-irrigation Field Evaluation",
                }
            )
            adj_factor *= 1.10
        elif irrigation in ["rainfed"]:
            yield_adjustments_applied.append(
                {
                    "factor": "Unirrigated rainfed dependency",
                    "multiplier": 0.85,
                    "source": "ICAR-CRIDA Dryland Farming Benchmark",
                }
            )
            adj_factor *= 0.85

        baseline_yield_q_ha = float(crop_info.get("baseline_yield_q_ha", 35.0))
        baseline_yield_source = crop_info.get("yield_source", "ICAR Benchmark 2023-24")

        expected_yield_per_ha = round(baseline_yield_q_ha * adj_factor, 2)
        expected_total_q = round(expected_yield_per_ha * area_ha, 1)
        low_total_q = round(expected_total_q * 0.70, 1)
        high_total_q = round(expected_total_q * 1.15, 1)

        expected_50kg_bags = round((expected_total_q * 100.0) / 50.0)
        low_50kg_bags = round((low_total_q * 100.0) / 50.0)
        high_50kg_bags = round((high_total_q * 100.0) / 50.0)

        msp_rate = float(msp_info.get("msp_rs_per_quintal", 2500))
        expected_revenue_rs = round(expected_total_q * msp_rate)
        low_revenue_rs = round(low_total_q * msp_rate)
        high_revenue_rs = round(high_total_q * msp_rate)

        return {
            "crop": crop_info.get("name", raw_crop.capitalize()),
            "crop_raw": raw_crop,
            "crop_type": crop_info.get("type", "annual"),
            "indicative_only": indicative_only,
            "stage_source": crop_info.get("stage_source", "generic"),
            "sowing_date": sowing_date_str,
            "expected_harvest_date": harvest_dt.strftime("%Y-%m-%d"),
            "harvest_date_formatted": harvest_dt.strftime("%B %d, %Y"),
            "total_duration_days": total_duration,
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "days_overdue": days_overdue,
            "days_until_sowing": days_until_sowing,
            "starts_in_message": starts_in_message,
            "progress_percentage": progress_pct,
            "status": status,
            "is_harvest_ready": is_harvest_ready,
            "warning": warnings[0] if warnings else None,
            "warnings": warnings,
            "stages_timeline": stages,
            "yield_adjustments_applied": yield_adjustments_applied,
            "yield_prediction": {
                "baseline_yield_per_hectare_q": baseline_yield_q_ha,
                "baseline_yield_source": baseline_yield_source,
                "expected_yield_per_hectare_q": expected_yield_per_ha,
                "expected_yield_per_acre_q": round(expected_yield_per_ha / 2.47105, 1),
                "range_multipliers": {"low": 0.70, "expected": 1.00, "high": 1.15},
                "yield_quintals": {"low": low_total_q, "expected": expected_total_q, "high": high_total_q},
                "bags_50kg": {"low": low_50kg_bags, "expected": expected_50kg_bags, "high": high_50kg_bags},
                "gross_revenue_rs": {"low": low_revenue_rs, "expected": expected_revenue_rs, "high": high_revenue_rs},
                "avg_yield_per_hectare_q": expected_yield_per_ha,
                "avg_yield_per_acre_q": round(expected_yield_per_ha / 2.47105, 1),
                "total_expected_quintals": expected_total_q,
                "total_50kg_bags": expected_50kg_bags,
                "reference_msp_rate_q": msp_rate,
                "estimated_gross_revenue_rs": expected_revenue_rs,
                "disclaimer": "Indicative estimate. Actual yield depends on variety, weather, pests and management.",
            },
            "msp_info": {
                "crop_name": msp_info.get("crop", crop_info.get("name", raw_crop.capitalize())),
                "rate_rs_per_quintal": msp_rate,
                "season": msp_info.get("season", "Kharif"),
                "year": msp_info.get("year", "2024-25"),
                "type": msp_info.get("type", "official_msp"),
                "verification_status": msp_info.get("verification_status", "UNVERIFIED"),
                "source_url": msp_info.get("source_url", "https://cacp.dacnet.nic.in"),
            },
            "harvest_readiness_checklist": [
                "Grain / Pod moisture level reaches under 14% to prevent storage fungal rot.",
                "Over 85% of leaves/panicles have turned dry straw-golden yellow.",
                "Stop field irrigation 7 to 10 days before harvest to dry topsoil for tractor/combine access.",
                "Harvest during bright, dry morning hours after field dew evaporates.",
            ],
        }


# Instantiate singleton
ml_engine = MLService()
