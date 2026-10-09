import requests
import json

BASE_API = "http://127.0.0.1:5000"
BASE_WEB = "http://localhost:5173"

print("=" * 70)
print("🚀 GSD COMPREHENSIVE END-TO-END VERIFICATION SUITE — 4 PILLARS & AI VISION")
print("=" * 70)

# 1. Frontend Web Server
r_web = requests.get(BASE_WEB)
print(f"1. [Frontend SPA] Port 5173 Status: {r_web.status_code} (OK)")
assert r_web.status_code == 200, "Frontend is not serving"

# 2. Backend Health Check
r_health = requests.get(f"{BASE_API}/health")
health_data = r_health.json()
print(f"2. [Backend Health] Status: {r_health.status_code} | Service: {health_data['service']} | Status: {health_data['status']}")
assert r_health.status_code == 200

# 3. Live Meteorological Service
r_weather = requests.get(f"{BASE_API}/api/weather?location=Coimbatore")
w_data = r_weather.json().get('data', {})
print(f"3. [Weather Service] Coimbatore: {w_data.get('temperature')}°C, Humidity: {w_data.get('humidity')}%, Rain: {w_data.get('rainfall')}mm")
print(f"   5-Day Daily Forecast Length: {len(w_data.get('forecast', []))} Days")
assert r_weather.status_code == 200

# 4. Standard Crop Recommendation (Random Forest)
crop_payload = {"N": 90, "P": 42, "K": 43, "ph": 6.5, "location": "Coimbatore"}
r_crop = requests.post(f"{BASE_API}/api/recommend/crop", json=crop_payload)
crop_res = r_crop.json()
print(f"4. [Crop RF] Primary Crop: {crop_res['crop'].upper()} | Confidence: {crop_res['confidence']}%")
assert r_crop.status_code == 200
assert len(crop_res.get('top_crops', [])) == 3
print(f"   🌾 Top-3 Crops: {[c['crop'] + ' (' + str(c['confidence']) + '%)' for c in crop_res['top_crops']]}")

# 5. Spatio-Temporal LSTM & Feature Bottleneck Fusion (Experimental Flag)
fusion_payload = {"N": 85, "P": 48, "K": 40, "ph": 6.4, "soil_type": "Clayey", "location": "Coimbatore"}
r_fusion = requests.post(f"{BASE_API}/api/recommend/crop/spatiotemporal-fusion", json=fusion_payload)
fusion_res = r_fusion.json()
bottleneck_sample = fusion_res['bottleneck_features'][:4]
print(f"5. [Spatio-Temporal LSTM Fusion] Predicted: {fusion_res['crop'].upper()} | Confidence: {fusion_res['confidence']}%")
print(f"   🧪 Experimental Flag: {fusion_res.get('is_experimental')} | Notice: {fusion_res.get('production_notice')[:60]}...")
print(f"   🧬 24-dim Bottleneck Latent Sample: {bottleneck_sample}...")
print(f"   🧬 Temporal Encoder: {fusion_res['fusion_architecture']['temporal_encoder']}")
print(f"   🧬 Bottleneck Layer: {fusion_res['fusion_architecture']['bottleneck_layer']}")
assert r_fusion.status_code == 200
assert fusion_res.get('is_experimental') is True

# 6. Soil Image Classification (MobileNetV2 CNN Vision) with Real Image
img_path = "ml_models/datasets/soil_images/Black/Black_Soil_100.jpg"
with open(img_path, "rb") as f:
    r_soil = requests.post(f"{BASE_API}/api/classify/soil-image", files={"image": f})
soil_res = r_soil.json()
print(f"6. [Soil CNN Vision] Classified: {soil_res['soil_type']} Soil | Confidence: {soil_res['confidence']}%")
print(f"   Estimated NPK: {soil_res['estimated_properties']}")
print(f"   Recommended Crops for this soil: {soil_res['suitable_crops'][:3]}")
assert r_soil.status_code == 200
assert soil_res['soil_type'] == "Black"

# 7. Fertilizer Recommendation & ICAR 50kg Bags Stoichiometry
fert_payload = {
    "temperature": 26, "humidity": 60, "moisture": 62,
    "soil_type": "Black", "crop_type": "Cotton",
    "N": 75, "P": 32, "K": 48
}
r_fert = requests.post(f"{BASE_API}/api/recommend/fertilizer", json=fert_payload)
fert_res = r_fert.json()
plan = fert_res["scientific_plan"]["active_rate"]
print(f"7. [Fertilizer & ICAR Engine] Recommended: {fert_res['fertilizer']}")
print(f"   - DAP Requirement:  {plan['dap_kg']} kg ({plan['dap_bags']} Bags)")
print(f"   - Urea Requirement: {plan['urea_kg']} kg ({plan['urea_bags']} Bags)")
print(f"   - MOP Requirement:  {plan['mop_kg']} kg ({plan['mop_bags']} Bags)")
assert r_fert.status_code == 200

# 8. Irrigation Planning (FAO-56 Penman-Monteith Hydrology Engine)
irr_payload = {
    "crop": "rice",
    "growth_stage": "flowering",
    "soil_type": "Clayey",
    "area": 2,
    "area_unit": "acres",
    "temperature": 30,
    "humidity": 60,
    "rainfall": 0
}
r_irr = requests.post(f"{BASE_API}/api/irrigation/plan", json=irr_payload)
irr_res = r_irr.json()
print(f"8. [Irrigation Planning FAO-56] Crop: {irr_res['crop']} ({irr_res['growth_stage']})")
print(f"   - Net Irrigation Depth: {irr_res['net_irrigation_depth_mm']} mm/day")
print(f"   - Daily Volume:         {irr_res['daily_liters']:,.0f} Liters")
print(f"   - Drip Runtime:         {irr_res['drip_runtime_hours']} Hours")
print(f"   - Weekly Schedule:      {len(irr_res['weekly_schedule'])} Days Projected")
assert r_irr.status_code == 200
assert irr_res['daily_liters'] > 0

# 9. Harvest Prediction & Phenological Timeline Engine
harvest_payload = {
    "crop": "rice",
    "sowing_date": "2026-08-15",
    "area": 2,
    "area_unit": "acres"
}
r_harvest = requests.post(f"{BASE_API}/api/harvest/predict", json=harvest_payload)
harvest_res = r_harvest.json()
print(f"9. [Harvest & Phenology Timeline] Crop: {harvest_res['crop']}")
print(f"   - Harvest Target Date:  {harvest_res['harvest_date_formatted']} ({harvest_res['days_remaining']} Days Remaining)")
print(f"   - Growth Progress:      {harvest_res['progress_percentage']}% ({harvest_res['days_elapsed']} of {harvest_res['total_duration_days']} Days)")
print(f"   - Phenological Stages:  {len(harvest_res['stages_timeline'])} Biological Stages Tracked")
print(f"   - Expected Yield:       {harvest_res['yield_prediction']['total_expected_quintals']} Quintals ({harvest_res['yield_prediction']['total_50kg_bags']} Bags)")
print(f"   - Gross Revenue Est:    ₹{harvest_res['yield_prediction']['estimated_gross_revenue_rs']:,}")
assert r_harvest.status_code == 200
assert len(harvest_res['stages_timeline']) == 5
assert harvest_res['yield_prediction']['total_expected_quintals'] > 0

print("=" * 70)
print("🏆 ALL 9 END-TO-END MODULES FULLY TESTED & VERIFIED (100% SUCCESS)!")
print("=" * 70)
