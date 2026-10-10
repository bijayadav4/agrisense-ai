import React, { useState, useEffect } from 'react';
import { 
  Sprout, 
  Sparkles, 
  TrendingUp, 
  RefreshCw,
  AlertCircle,
  AlertTriangle,
  CloudSun,
  Droplets,
  Printer,
  Info,
  MapPin,
  Edit3,
  RotateCcw,
  Camera,
  CheckCircle2
} from 'lucide-react';
import { getCropRecommendation, getCropFusionRecommendation, classifySoilImage, getSoilSuitability } from '../services/api';

const SOIL_SUITABILITY_DEFAULT = {
  Black: {
    soil_name: "Black Soil (Regur)",
    suitable_crops: ["Cotton", "Wheat", "Sugarcane", "Gram", "Soybean", "Jowar", "Sunflower"],
    general_guidance: "High clay content with deep cracking and high moisture retention. Well suited for cotton and rabi crops. Requires controlled drainage to prevent waterlogging.",
    source: "UNVERIFIED"
  },
  Red: {
    soil_name: "Red Soil",
    suitable_crops: ["Groundnut", "Millets (Ragi, Bajra)", "Pulses", "Tobacco", "Potato", "Oilseeds"],
    general_guidance: "Porous and friable with high aeration. Lower in natural organic matter, nitrogen, and phosphorus; responds exceptionally well to organic compost and balanced NPK.",
    source: "UNVERIFIED"
  },
  Sandy: {
    soil_name: "Sandy Soil",
    suitable_crops: ["Watermelon", "Muskmelon", "Groundnut", "Gram", "Bajra", "Mothbeans"],
    general_guidance: "High drainage rate and low water holding capacity. Quick to warm up in summer. Drip irrigation and split fertilizer doses are recommended to avoid leaching.",
    source: "UNVERIFIED"
  },
  Clayey: {
    soil_name: "Clayey Soil",
    suitable_crops: ["Rice (Paddy)", "Wheat", "Gram", "Jute", "Sugarcane"],
    general_guidance: "Dense heavy soil with high nutrient and water holding capacity. Excellent for submerged paddy wetlands; requires careful tillage when moisture is optimal.",
    source: "UNVERIFIED"
  },
  Loamy: {
    soil_name: "Loamy Soil",
    suitable_crops: ["Wheat", "Sugarcane", "Cotton", "Jute", "Pulses", "Vegetables", "Maize"],
    general_guidance: "Ideal balanced agricultural soil with good drainage, aeration, and moisture retention. Highly versatile for multi-crop intensive rotations.",
    source: "UNVERIFIED"
  }
};

export default function CropView({ activeLocation, weatherData, soilData, onUpdateSoil, onCropAnalyzed }) {
  // 1. Soil nutrient parameters (default empty, required from Soil Health Card or Demo button)
  const [formData, setFormData] = useState({
    N: '',
    P: '',
    K: '',
    ph: ''
  });

  const [dataSource, setDataSource] = useState('Lab test / User entered');
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 2. Soil Photo Classification & Global State Sync
  const [soilDetecting, setSoilDetecting] = useState(false);
  const [soilDetectionError, setSoilDetectionError] = useState('');
  const [suitabilityMap, setSuitabilityMap] = useState(SOIL_SUITABILITY_DEFAULT);

  const activeSoilType = soilData?.soil_type || 'Loamy';

  // Load backend suitability catalog on mount (with bundled fallback)
  useEffect(() => {
    let isMounted = true;
    const fetchSuitability = async () => {
      try {
        const res = await getSoilSuitability();
        if (isMounted && res && res.success && res.data) {
          setSuitabilityMap(res.data);
        }
      } catch (err) {
        // Fallback already pre-set to SOIL_SUITABILITY_DEFAULT
      }
    };
    fetchSuitability();
    return () => { isMounted = false; };
  }, []);

  const handleSoilPhotoUpload = async (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;

    setSoilDetecting(true);
    setSoilDetectionError('');
    try {
      const res = await classifySoilImage(file);
      if (res && res.success) {
        if (onUpdateSoil) {
          onUpdateSoil(res.soil_type || 'Loamy', res.confidence, 'ai-detected');
        }
        // Note: Photo upload NEVER auto-populates N, P, K, or pH
      } else {
        setSoilDetectionError(res.error || 'Failed to analyze soil photo');
      }
    } catch (err) {
      console.error('Soil classification error:', err);
      setSoilDetectionError(err.response?.data?.error || err.message || 'Error processing photo');
    } finally {
      setSoilDetecting(false);
    }
  };

  const handleSoilTypeDropdownChange = (e) => {
    const newType = e.target.value;
    if (onUpdateSoil) {
      onUpdateSoil(newType, null, 'user-selected');
    }
  };

  const showWeakDetectionWarning = 
    soilData?.source === 'ai-detected' && 
    (activeSoilType.toLowerCase() === 'loamy' || (soilData?.confidence && soilData.confidence < 70));

  // 3. 30-Day Meteorological Auto-Fill & Manual Override Toggle
  const [isManualClimate, setIsManualClimate] = useState(false);
  const [manualClimate, setManualClimate] = useState({
    temperature: '',
    humidity: '',
    rainfall: ''
  });

  const autoTemp = weatherData?.temperature_last_30_days ?? weatherData?.temperature ?? 27.0;
  const autoHumidity = weatherData?.humidity_last_30_days ?? weatherData?.humidity ?? 65;
  const autoRainfall = weatherData?.rainfall_last_30_days ?? 85.0;

  useEffect(() => {
    if (!isManualClimate) {
      setManualClimate({
        temperature: autoTemp,
        humidity: autoHumidity,
        rainfall: autoRainfall
      });
    }
  }, [autoTemp, autoHumidity, autoRainfall, isManualClimate]);

  // 4. Experimental ST-LSTM Fusion Prototype (Gated behind VITE_SHOW_EXPERIMENTAL)
  const showExperimental = import.meta.env.VITE_SHOW_EXPERIMENTAL === 'true';
  const [useFusionModel, setUseFusionModel] = useState(false);

  const handleNutrientChange = (e) => {
    const { name, value } = e.target;
    setDataSource('Lab test / User entered');
    setFormData((prev) => ({
      ...prev,
      [name]: value === '' ? '' : Number(value)
    }));
  };

  const handleClimateChange = (e) => {
    const { name, value } = e.target;
    setManualClimate((prev) => ({
      ...prev,
      [name]: value === '' ? '' : Number(value)
    }));
  };

  const handleFillDemoData = () => {
    setFormData({
      N: 85,
      P: 48,
      K: 40,
      ph: 6.4
    });
    setDataSource('Demo estimated');
    setError('');
  };

  const isFormComplete = 
    formData.N !== '' && 
    formData.P !== '' && 
    formData.K !== '' && 
    formData.ph !== '';

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isFormComplete) {
      setError('Please enter N, P, K and pH values from your Soil Health Card or lab test.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const effTemp = isManualClimate && manualClimate.temperature !== '' ? Number(manualClimate.temperature) : Number(autoTemp);
      const effHumidity = isManualClimate && manualClimate.humidity !== '' ? Number(manualClimate.humidity) : Number(autoHumidity);
      const effRainfall = isManualClimate && manualClimate.rainfall !== '' ? Number(manualClimate.rainfall) : Number(autoRainfall);

      // Clean payload: soil_type is strictly NOT sent to crop recommendation model
      const payload = {
        N: Number(formData.N),
        P: Number(formData.P),
        K: Number(formData.K),
        ph: Number(formData.ph),
        temperature: effTemp,
        humidity: effHumidity,
        rainfall: effRainfall,
        location: activeLocation || 'Coimbatore, Tamil Nadu',
        data_source: dataSource,
        is_estimated: dataSource === 'Demo estimated'
      };

      const data = (showExperimental && useFusionModel)
        ? await getCropFusionRecommendation(payload)
        : await getCropRecommendation(payload);

      if (data && data.success) {
        const enriched = {
          ...data,
          data_source: dataSource,
          is_estimated: dataSource === 'Demo estimated',
          N: formData.N,
          P: formData.P,
          K: formData.K,
          ph: formData.ph,
          effective_weather: {
            temperature: effTemp,
            humidity: effHumidity,
            rainfall: effRainfall
          }
        };
        setRecommendation(enriched);
        if (onCropAnalyzed) {
          onCropAnalyzed(enriched);
        }
      } else {
        setError(data?.error || 'Failed to predict crop recommendation.');
      }
    } catch (err) {
      console.error('Crop recommendation error:', err);
      setError(err.response?.data?.error || 'Failed to connect to AgriSense server.');
    } finally {
      setLoading(false);
    }
  };

  const suitabilityInfo = suitabilityMap[activeSoilType] || SOIL_SUITABILITY_DEFAULT[activeSoilType] || SOIL_SUITABILITY_DEFAULT.Loamy;

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* 1. Card Header & Title */}
      <div className="dashboard-card">
        <div className="card-title-row">
          <div className="card-title-left">
            <div className="logo-icon-wrap">
              <Sprout size={24} />
            </div>
            <div>
              <h3>🌾 Soil Data Collection &amp; AI Crop Recommendation</h3>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                Pillar 1: Random Forest Classifier (99.52% ± 0.25% 5-fold CV across 23 Indian Crops)
              </span>
            </div>
          </div>
          {recommendation && (
            <button 
              type="button" 
              onClick={() => window.print()} 
              className="btn-view-advice" 
              style={{ padding: '6px 14px', fontSize: '0.82rem' }}
            >
              <Printer size={15} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
              Print Report
            </button>
          )}
        </div>

        {/* 2. Experimental ST-LSTM Prototype Banner (Visible ONLY when VITE_SHOW_EXPERIMENTAL=true) */}
        {showExperimental && (
          <div style={{
            marginTop: '12px',
            padding: '10px 14px',
            borderRadius: '10px',
            background: useFusionModel ? '#fefce8' : '#f8fafc',
            border: `1px solid ${useFusionModel ? '#fde047' : '#e2e8f0'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '10px',
            transition: 'all 0.2s ease'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.2rem' }}>🧪</span>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <strong style={{ fontSize: '0.86rem', color: useFusionModel ? '#854d0e' : '#1e293b' }}>
                    Experimental prototype (synthetic weather sequence, not evaluated)
                  </strong>
                  <span style={{ fontSize: '0.68rem', background: '#fef3c7', color: '#92400e', border: '1px solid #fde68a', padding: '1px 6px', borderRadius: '4px', fontWeight: 700 }}>
                    Research Prototype
                  </span>
                </div>
                <span style={{ fontSize: '0.73rem', color: '#64748b', display: 'block', marginTop: '1px' }}>
                  A simple Bi-LSTM prototype with synthetic temporal sequences. Not Mohan Sir's paper architecture.
                </span>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setUseFusionModel(!useFusionModel)}
              style={{
                padding: '5px 14px',
                borderRadius: '20px',
                border: `1px solid ${useFusionModel ? '#ca8a04' : '#cbd5e1'}`,
                background: useFusionModel ? '#ca8a04' : '#ffffff',
                color: useFusionModel ? '#ffffff' : '#475569',
                fontSize: '0.78rem',
                fontWeight: 800,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {useFusionModel ? '🧪 Prototype Active' : 'Enable Experimental Prototype'}
            </button>
          </div>
        )}

        {/* 3. Soil photo (optional) Card */}
        <div style={{
          marginTop: '12px',
          padding: '12px 16px',
          borderRadius: '10px',
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Camera size={16} color="var(--primary-green)" />
              <strong style={{ fontSize: '0.86rem', color: '#1e293b' }}>
                📷 Soil photo (optional)
              </strong>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '5px 12px',
                borderRadius: '6px',
                background: '#f0fdf4',
                border: '1px solid #86efac',
                color: '#15803d',
                fontSize: '0.76rem',
                fontWeight: 700,
                cursor: soilDetecting ? 'wait' : 'pointer',
                transition: 'all 0.15s ease'
              }}>
                {soilDetecting ? (
                  <>
                    <RefreshCw size={13} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
                    <span>Analyzing soil photo...</span>
                  </>
                ) : (
                  <>
                    <Camera size={13} />
                    <span>Upload Photo</span>
                  </>
                )}
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleSoilPhotoUpload}
                  style={{ display: 'none' }}
                  disabled={soilDetecting}
                />
              </label>
            </div>
          </div>

          <p style={{ margin: 0, fontSize: '0.78rem', color: '#64748b' }}>
            ℹ️ This soil type is used in Fertilizer and Irrigation. Crop prediction uses N, P, K, pH and weather.
          </p>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '8px',
            padding: '8px 12px',
            borderRadius: '6px',
            background: '#f8fafc',
            border: '1px solid #e2e8f0'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.80rem', fontWeight: 600, color: '#334155' }}>
                Current Soil Type: <strong style={{ color: 'var(--primary-green)' }}>{activeSoilType} Soil</strong>
              </span>
              {soilData?.source === 'ai-detected' && soilData?.confidence && (
                <span style={{
                  fontSize: '0.70rem',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: '4px',
                  background: '#dcfce7',
                  color: '#15803d',
                  border: '1px solid #86efac'
                }}>
                  AI-detected ({soilData.confidence}%)
                </span>
              )}
              {soilData?.source === 'user-selected' && (
                <span style={{
                  fontSize: '0.70rem',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: '4px',
                  background: '#fef3c7',
                  color: '#92400e',
                  border: '1px solid #fde68a'
                }}>
                  user-selected
                </span>
              )}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#475569' }}>
                Change soil type:
              </label>
              <select
                value={activeSoilType}
                onChange={handleSoilTypeDropdownChange}
                style={{
                  padding: '4px 8px',
                  borderRadius: '6px',
                  border: '1px solid #cbd5e1',
                  fontSize: '0.76rem',
                  background: '#ffffff',
                  color: '#1e293b',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                {['Black', 'Clayey', 'Loamy', 'Red', 'Sandy'].map((st) => (
                  <option key={st} value={st}>{st} Soil</option>
                ))}
              </select>
            </div>
          </div>

          {showWeakDetectionWarning && (
            <div style={{
              padding: '8px 12px',
              borderRadius: '6px',
              background: '#fffbeb',
              border: '1px solid #fde68a',
              color: '#92400e',
              fontSize: '0.76rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}>
              <AlertTriangle size={15} style={{ flexShrink: 0, color: '#d97706' }} />
              <span>
                {activeSoilType.toLowerCase() === 'loamy'
                  ? '⚠️ Detection for this soil type is weak (Loamy precision ~38.5%). Please confirm the soil type yourself.'
                  : '⚠️ Detection for this soil type is weak (confidence < 70%). Please confirm the soil type yourself.'}
              </span>
            </div>
          )}

          {soilDetectionError && (
            <div style={{ padding: '6px 10px', borderRadius: '6px', background: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', fontSize: '0.74rem' }}>
              ⚠️ {soilDetectionError}
            </div>
          )}
        </div>

        {/* 4. Location & 30-Day Weather Summary (Single Source of Truth from Header) */}
        <div style={{
          marginTop: '12px',
          padding: '12px 16px',
          borderRadius: '10px',
          background: '#f8fafc',
          border: '1px solid #e2e8f0',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <MapPin size={16} color="var(--primary-green)" />
              <span style={{ fontSize: '0.86rem', fontWeight: 700, color: '#1e293b' }}>
                Farm Location: <span style={{ color: 'var(--primary-green)' }}>{activeLocation || 'Coimbatore, Tamil Nadu'}</span>
              </span>
              <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                (Synced with header)
              </span>
            </div>

            {/* Quick Demo Data Fill Button */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                type="button"
                onClick={handleFillDemoData}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '5px',
                  padding: '5px 12px',
                  borderRadius: '6px',
                  background: '#f0fdf4',
                  border: '1px solid #86efac',
                  color: '#15803d',
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
                title="Fill demo soil parameters (N=85, P=48, K=40, pH=6.4)"
              >
                <Sparkles size={13} />
                <span>⚡ Fill demo data</span>
              </button>
            </div>
          </div>

          {/* 30-Day Weather Stats Indicator */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '8px',
            padding: '8px 12px',
            borderRadius: '6px',
            background: '#ffffff',
            border: '1px solid #e2e8f0'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CloudSun size={16} color="#0284c7" />
              <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#334155' }}>
                Last 30 days: Temp {autoTemp}°C, Humidity {autoHumidity}%, Rainfall {autoRainfall} mm
              </span>
            </div>
            <button
              type="button"
              onClick={() => setIsManualClimate(!isManualClimate)}
              style={{
                background: 'none',
                border: 'none',
                color: '#0284c7',
                fontSize: '0.76rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '2px 6px'
              }}
            >
              {isManualClimate ? (
                <>
                  <RotateCcw size={12} />
                  <span>Reset to 30-day weather</span>
                </>
              ) : (
                <>
                  <Edit3 size={12} />
                  <span>Edit manually</span>
                </>
              )}
            </button>
          </div>

          {/* Editable Climate Inputs if Farmer Clicks 'Edit manually' */}
          {isManualClimate && (
            <div className="form-grid-modal" style={{ marginTop: '4px', paddingTop: '8px', borderTop: '1px dashed #cbd5e1' }}>
              <div className="form-field-white">
                <label style={{ fontSize: '0.76rem' }}>🌡️ Temperature (°C)</label>
                <input
                  type="number"
                  step="0.5"
                  name="temperature"
                  value={manualClimate.temperature}
                  onChange={handleClimateChange}
                  className="form-input-white"
                />
              </div>
              <div className="form-field-white">
                <label style={{ fontSize: '0.76rem' }}>💧 Humidity (%)</label>
                <input
                  type="number"
                  name="humidity"
                  min="10"
                  max="100"
                  value={manualClimate.humidity}
                  onChange={handleClimateChange}
                  className="form-input-white"
                />
              </div>
              <div className="form-field-white">
                <label style={{ fontSize: '0.76rem' }}>🌧️ 30-Day Rainfall (mm)</label>
                <input
                  type="number"
                  name="rainfall"
                  min="0"
                  max="1500"
                  value={manualClimate.rainfall}
                  onChange={handleClimateChange}
                  className="form-input-white"
                />
              </div>
            </div>
          )}
        </div>

        {/* Demo Data Amber Note Banner */}
        {dataSource === 'Demo estimated' && (
          <div style={{
            marginTop: '10px',
            padding: '8px 12px',
            borderRadius: '6px',
            background: '#fffbeb',
            border: '1px solid #fde68a',
            color: '#92400e',
            fontSize: '0.78rem',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <AlertTriangle size={15} style={{ flexShrink: 0, color: '#d97706' }} />
            <span>
              <strong>Source: Demo estimated</strong> — These are estimated values. For accurate recommendations, please use Soil Health Card or lab test values.
            </span>
          </div>
        )}

        {/* 5. Soil Nutrient Form (N, P, K, pH) */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '14px' }}>
          
          <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '10px', padding: '10px 14px', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.82rem', color: '#166534' }}>
            <Info size={18} style={{ flexShrink: 0, color: '#15803d' }} />
            <span>
              <strong>Soil Health Card Lab Standard: </strong>
              N-P-K values represent soil nutrient density in <strong>kg/ha</strong>. Fill all four fields: N, P, K and pH.
            </span>
          </div>

          <div className="form-grid-modal">
            <div className="form-field-white">
              <label>
                <span>🌿 Available Nitrogen (N)</span>
                <span style={{ color: formData.N !== '' ? 'var(--primary-green)' : '#94a3b8', fontWeight: 600 }}>
                  {formData.N !== '' ? `${formData.N} kg/ha` : '(Empty)'}
                </span>
              </label>
              <input
                type="number"
                name="N"
                value={formData.N}
                onChange={handleNutrientChange}
                placeholder="e.g. 85"
                className="form-input-white"
                min="0"
                max="300"
                required
              />
            </div>

            <div className="form-field-white">
              <label>
                <span>🌱 Available Phosphorus (P)</span>
                <span style={{ color: formData.P !== '' ? 'var(--primary-green)' : '#94a3b8', fontWeight: 600 }}>
                  {formData.P !== '' ? `${formData.P} kg/ha` : '(Empty)'}
                </span>
              </label>
              <input
                type="number"
                name="P"
                value={formData.P}
                onChange={handleNutrientChange}
                placeholder="e.g. 48"
                className="form-input-white"
                min="0"
                max="200"
                required
              />
            </div>

            <div className="form-field-white">
              <label>
                <span>🌾 Available Potassium (K)</span>
                <span style={{ color: formData.K !== '' ? 'var(--primary-green)' : '#94a3b8', fontWeight: 600 }}>
                  {formData.K !== '' ? `${formData.K} kg/ha` : '(Empty)'}
                </span>
              </label>
              <input
                type="number"
                name="K"
                value={formData.K}
                onChange={handleNutrientChange}
                placeholder="e.g. 40"
                className="form-input-white"
                min="0"
                max="300"
                required
              />
            </div>

            <div className="form-field-white">
              <label>
                <span>🧪 Soil Reaction (pH)</span>
                <span style={{ color: formData.ph !== '' ? 'var(--primary-green)' : '#94a3b8', fontWeight: 600 }}>
                  {formData.ph !== '' ? `${formData.ph} pH` : '(Empty)'}
                </span>
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="14"
                name="ph"
                value={formData.ph}
                onChange={handleNutrientChange}
                placeholder="e.g. 6.4"
                className="form-input-white"
                required
              />
            </div>
          </div>

          {!isFormComplete && (
            <div style={{ padding: '8px 12px', borderRadius: '6px', background: '#eff6ff', border: '1px solid #bfdbfe', color: '#1e40af', fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Info size={16} style={{ flexShrink: 0 }} />
              <span>The Recommend button works after you fill N, P, K and pH. To try a demo, click "⚡ Fill demo data" above.</span>
            </div>
          )}

          {/* Recommend Button: Enabled only when all 4 fields are filled */}
          <button
            type="submit"
            disabled={loading || !isFormComplete}
            className="btn-primary-green"
            style={{
              opacity: isFormComplete ? 1 : 0.6,
              cursor: isFormComplete ? 'pointer' : 'not-allowed'
            }}
          >
            {loading ? (
              <>
                <RefreshCw size={18} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
                <span>Analyzing Soil Nutrient Profile...</span>
              </>
            ) : (
              <>
                <Sparkles size={18} />
                <span>Recommend Best Crops for My Soil</span>
              </>
            )}
          </button>
        </form>

        {error && (
          <div style={{ padding: '12px', background: '#fef2f2', border: '1px solid #fee2e2', borderRadius: 'var(--radius-md)', color: '#dc2626', display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px' }}>
            <AlertCircle size={18} />
            <span style={{ fontSize: '0.88rem' }}>{error}</span>
          </div>
        )}
      </div>

      {/* 6. Recommendation Results Card */}
      {recommendation && (
        <div className="result-box-green animate-fade-in">
          <div className="result-hero-title-row">
            <div>
              <span style={{ fontSize: '0.78rem', color: 'var(--primary-green)', fontWeight: 700, textTransform: 'uppercase' }}>
                AI Recommendation Result
              </span>
              <h3 className="result-crop-big">🌾 {recommendation.crop.toUpperCase()}</h3>
            </div>
            <div className="badge-tag" style={{ background: '#dcfce7', color: '#15803d', border: '1px solid #86efac', fontSize: '0.92rem', padding: '6px 14px' }}>
              <TrendingUp size={16} />
              <span>{recommendation.confidence}% Suitability Match</span>
            </div>
          </div>

          {/* Data Source Badge */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px', flexWrap: 'wrap' }}>
            <span style={{
              fontSize: '0.74rem',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '4px',
              background: recommendation.is_estimated ? '#fef3c7' : '#f0fdf4',
              color: recommendation.is_estimated ? '#92400e' : '#15803d',
              border: `1px solid ${recommendation.is_estimated ? '#fde68a' : '#86efac'}`
            }}>
              Data source: {recommendation.is_estimated ? 'Demo estimated' : 'Lab test'}
            </span>
          </div>

          {/* Amber Note if Demo Estimated */}
          {recommendation.is_estimated && (
            <div style={{
              margin: '10px 0',
              padding: '10px 14px',
              borderRadius: '8px',
              background: '#fffbeb',
              border: '1px solid #fde68a',
              color: '#92400e',
              fontSize: '0.82rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <AlertTriangle size={18} style={{ flexShrink: 0, color: '#d97706' }} />
              <span>⚠️ Estimated values. Please confirm with a lab test.</span>
            </div>
          )}

          {/* Ambiguity Warning Banner */}
          {recommendation.is_ambiguous && (
            <div style={{
              margin: '12px 0',
              padding: '12px 16px',
              borderRadius: '8px',
              background: '#fffbeb',
              border: '1px solid #fde68a',
              color: '#92400e',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '10px'
            }}>
              <AlertCircle size={20} style={{ color: '#d97706', flexShrink: 0, marginTop: '2px' }} />
              <div style={{ fontSize: '0.84rem' }}>
                <strong style={{ display: 'block', marginBottom: '2px', color: '#b45309' }}>
                  ⚠️ Ambiguous Crop Suitability Warning (Confidence Gap &lt; 15%)
                </strong>
                <span>{recommendation.ambiguity_warning}</span>
              </div>
            </div>
          )}

          {/* Sowing Season Window Advisory Banner */}
          {recommendation.season_warning && (
            <div style={{
              margin: '10px 0',
              padding: '10px 14px',
              borderRadius: '8px',
              background: '#fff7ed',
              border: '1px solid #fed7aa',
              color: '#9a3412',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '10px'
            }}>
              <AlertTriangle size={18} style={{ color: '#ea580c', flexShrink: 0, marginTop: '2px' }} />
              <div style={{ fontSize: '0.82rem' }}>
                <strong style={{ display: 'block', marginBottom: '2px', color: '#c2410c' }}>
                  🗓️ Seasonal Sowing Advisory (Off-Season Alert)
                </strong>
                <span>{recommendation.season_warning}</span>
              </div>
            </div>
          )}

          {/* Top-3 Crops Probability Distribution */}
          {recommendation.top_crops && recommendation.top_crops.length > 0 && (
            <div style={{ marginTop: '12px', marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                  Top-3 Recommended Crops &amp; Probability Distribution:
                </span>
                {recommendation.confidence_gap !== undefined && (
                  <span style={{ fontSize: '0.72rem', color: recommendation.is_ambiguous ? '#b45309' : '#15803d', fontWeight: 700 }}>
                    Confidence Gap: {Math.round(recommendation.confidence_gap * 100)}%
                  </span>
                )}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '8px' }}>
                {recommendation.top_crops.map((item, idx) => (
                  <div key={idx} style={{
                    background: idx === 0 ? '#f0fdf4' : '#ffffff',
                    border: `1px solid ${idx === 0 ? '#86efac' : '#e2e8f0'}`,
                    padding: '8px 12px',
                    borderRadius: '8px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 700, textTransform: 'capitalize', fontSize: '0.88rem' }}>
                        #{item.rank} {item.crop}
                      </span>
                      <span style={{ fontSize: '0.82rem', fontWeight: 800, color: idx === 0 ? '#15803d' : '#475569' }}>
                        {item.confidence}%
                      </span>
                    </div>
                    <div style={{ height: '5px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%',
                        width: `${item.confidence}%`,
                        background: idx === 0 ? '#16a34a' : '#94a3b8',
                        borderRadius: '4px'
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Specs Grid */}
          <div className="result-specs-grid">
            <div className="result-spec-pill">
              <span className="lbl">Sowing Season</span>
              <span className="val">{recommendation.profile?.season || 'Kharif / Rabi'}</span>
            </div>
            <div className="result-spec-pill">
              <span className="lbl">Growth Duration</span>
              <span className="val">{recommendation.profile?.duration || '90 – 120 Days'}</span>
            </div>
            <div className="result-spec-pill">
              <span className="lbl">Water Requirement</span>
              <span className="val">{recommendation.profile?.water_need || 'Moderate'}</span>
            </div>
            <div className="result-spec-pill">
              <span className="lbl">Ideal Soil pH</span>
              <span className="val">{recommendation.profile?.ideal_ph || '6.0 – 7.5'}</span>
            </div>
          </div>

          {recommendation.profile?.harvest_tips && (
            <div style={{ background: '#f0fdf4', padding: '12px 16px', borderRadius: 'var(--radius-md)', border: '1px solid #bbf7d0', fontSize: '0.88rem', marginTop: '10px' }}>
              <strong style={{ color: 'var(--primary-green)', display: 'block', marginBottom: '4px' }}>
                🌾 Farmer Harvesting Tip:
              </strong>
              <p style={{ color: 'var(--text-main)', margin: 0 }}>{recommendation.profile.harvest_tips}</p>
            </div>
          )}

          {/* Soil Compatibility Note (General Guidance) */}
          <div style={{
            marginTop: '14px',
            padding: '12px 16px',
            borderRadius: '8px',
            background: '#f8fafc',
            border: '1px solid #cbd5e1',
            fontSize: '0.80rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '6px', marginBottom: '6px' }}>
              <strong style={{ color: '#0f766e', display: 'flex', alignItems: 'center', gap: '6px' }}>
                🌱 Soil Compatibility Note ({activeSoilType} Soil):
              </strong>
              <span style={{
                fontSize: '0.68rem',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: '4px',
                background: '#f1f5f9',
                color: '#475569',
                border: '1px solid #cbd5e1'
              }}>
                General guidance (source: UNVERIFIED)
              </span>
            </div>

            <p style={{ margin: '4px 0', color: '#334155', lineHeight: 1.4 }}>
              {suitabilityInfo?.general_guidance || 'Agronomic reference guidance for typical Indian agricultural soils.'}
            </p>

            <div style={{ marginTop: '6px', display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
              <span style={{ fontWeight: 600, color: '#475569', fontSize: '0.74rem' }}>
                Typically suitable crops on {activeSoilType} soil:
              </span>
              {suitabilityInfo?.suitable_crops?.map((c, idx) => (
                <span key={idx} style={{
                  background: '#ffffff',
                  border: '1px solid #e2e8f0',
                  padding: '1px 7px',
                  borderRadius: '12px',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  color: '#1e293b'
                }}>
                  {c}
                </span>
              ))}
            </div>

            <div style={{ marginTop: '6px', fontSize: '0.70rem', color: '#64748b', fontStyle: 'italic' }}>
              * This is general agronomic guidance only. Model Top-3 ranking is computed from your lab test NPK and weather.
            </div>
          </div>

          {/* Alternative Crops */}
          {recommendation.alternatives && recommendation.alternatives.length > 0 && (
            <div style={{ marginTop: '10px' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                Alternative Crops for Your Soil:
              </span>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px', marginTop: '8px' }}>
                {recommendation.alternatives.map((alt, idx) => (
                  <div key={idx} style={{ background: '#ffffff', padding: '10px 14px', borderRadius: 'var(--radius-md)', border: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{alt.crop}</span>
                    <span style={{ fontSize: '0.82rem', color: 'var(--primary-green)', fontWeight: 700 }}>{alt.confidence}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

    </div>
  );
}
