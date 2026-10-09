import React, { useState } from 'react';
import { 
  Sprout, 
  Sparkles, 
  TrendingUp, 
  RefreshCw,
  AlertCircle,
  AlertTriangle,
  CloudSun,
  Droplets,
  Calendar,
  Layers,
  Printer,
  Info,
  Camera
} from 'lucide-react';
import { getCropRecommendation, getCropFusionRecommendation, classifySoilImage } from '../services/api';


const DEMO_PRESETS = [
  { 
    name: '🌾 Rice / Paddy Wetland', 
    N: 85, P: 48, K: 40, ph: 6.4,
    temperature: 24.0, humidity: 82.0, rainfall: 220.0,
    desc: 'Demo Preset: Kharif Monsoon Submerged Wetland Soil'
  },
  { 
    name: '🌱 Wheat / Rabi Plains', 
    N: 95, P: 50, K: 40, ph: 6.6,
    temperature: 19.5, humidity: 58.0, rainfall: 72.0,
    desc: 'Demo Preset: Rabi Season Loamy Irrigated Plains'
  },
  { 
    name: '☁️ Cotton Black Soil', 
    N: 120, P: 45, K: 20, ph: 6.8,
    temperature: 24.5, humidity: 80.0, rainfall: 80.0,
    desc: 'Demo Preset: Warm Semi-Arid Black Soil'
  },
  { 
    name: '🫘 Pulse / Gram Arid Soil', 
    N: 30, P: 60, K: 25, ph: 7.5,
    temperature: 22.0, humidity: 50.0, rainfall: 50.0,
    desc: 'Demo Preset: Rabi Cool Drought-Hardy Soil'
  },
];

export default function CropView({ activeLocation, onCropAnalyzed }) {
  const [formData, setFormData] = useState({
    N: '',
    P: '',
    K: '',
    ph: '',
    temperature: '',
    humidity: '',
    rainfall: '',
    useLiveWeather: false,
    location: activeLocation || 'Coimbatore, Tamil Nadu'
  });

  const [dataSource, setDataSource] = useState('User entered');
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [soilDetecting, setSoilDetecting] = useState(false);
  const [soilDetectionResult, setSoilDetectionResult] = useState(null);
  const [soilDetectionError, setSoilDetectionError] = useState('');
  const [useFusionModel, setUseFusionModel] = useState(false);
  const [manualSoilOverride, setManualSoilOverride] = useState(false);
  const [overrideSoilType, setOverrideSoilType] = useState('Loamy');

  const handleSoilPhotoUpload = async (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;

    setSoilDetecting(true);
    setSoilDetectionError('');
    try {
      const res = await classifySoilImage(file);
      if (res && res.success) {
        setSoilDetectionResult(res);
        setOverrideSoilType(res.soil_type || 'Loamy');
        setManualSoilOverride(false);
        // Photo upload NEVER auto-populates N, P, K, or pH
      } else {
        setSoilDetectionError(res.error || 'Failed to analyze soil photo');
      }
    } catch (err) {
      console.error('Soil photo classification error:', err);
      setSoilDetectionError(err.response?.data?.error || err.message || 'Error processing photo');
    } finally {
      setSoilDetecting(false);
    }
  };

  const handleSoilOverrideChange = (e) => {
    const val = e.target.value;
    setOverrideSoilType(val);
    setManualSoilOverride(true);
  };

  const handlePresetSelect = (preset) => {
    setFormData((prev) => ({
      ...prev,
      N: preset.N,
      P: preset.P,
      K: preset.K,
      ph: preset.ph,
      temperature: preset.temperature,
      humidity: preset.humidity,
      rainfall: preset.rainfall,
      useLiveWeather: false
    }));
    setDataSource('Demo estimated');
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    if (['N', 'P', 'K', 'ph'].includes(name)) {
      setDataSource('User entered');
    }
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : (type === 'number' ? (value === '' ? '' : Number(value)) : value)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const payload = {
        N: Number(formData.N),
        P: Number(formData.P),
        K: Number(formData.K),
        ph: Number(formData.ph),
        location: formData.location.trim(),
        data_source: dataSource,
        is_estimated: dataSource === 'Demo estimated'
      };

      // Only send custom climate if user explicitly opted out of live weather or selected a seasonal preset
      if (!formData.useLiveWeather) {
        payload.temperature = Number(formData.temperature);
        payload.humidity = Number(formData.humidity);
        payload.rainfall = Number(formData.rainfall);
      }

      const effectiveSoil = manualSoilOverride ? overrideSoilType : (soilDetectionResult?.soil_type || overrideSoilType);
      if (effectiveSoil) {
        payload.soil_type = effectiveSoil;
        payload.soil_source = manualSoilOverride ? 'user-selected' : (soilDetectionResult ? 'ai-detected' : 'user-selected');
      }

      const data = useFusionModel
        ? await getCropFusionRecommendation(payload)
        : await getCropRecommendation(payload);

      if (data.success) {
        const enriched = {
          ...data,
          data_source: dataSource,
          is_estimated: dataSource === 'Demo estimated',
          soil_type: effectiveSoil,
          soil_source: payload.soil_source,
          N: formData.N,
          P: formData.P,
          K: formData.K,
          ph: formData.ph
        };
        setRecommendation(enriched);
        if (onCropAnalyzed) {
          onCropAnalyzed(enriched);
        }
      } else {
        setError(data.error || 'Failed to predict crop recommendation.');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to connect to AgriSense server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Header Banner */}
      <div className="dashboard-card">
        <div className="card-title-row">
          <div className="card-title-left">
            <div className="logo-icon-wrap">
              <Sprout size={24} />
            </div>
            <div>
              <h3>🌾 Soil Data Collection & AI Crop Recommendation</h3>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                Pillar 1: Random Forest Classifier (99.52% ± 0.25% 5-fold CV, benchmark data across 23 Indian Crops)
              </span>
            </div>
          </div>
          {recommendation && (
            <button type="button" onClick={() => window.print()} className="btn-view-advice" style={{ padding: '6px 14px', fontSize: '0.82rem' }}>
              <Printer size={15} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
              Print Report
            </button>
          )}
        </div>

        {/* Spatio-Temporal LSTM & Feature Bottleneck Fusion Switch (Experimental Research Prototype) */}
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
                  Experimental: ST-LSTM Multimodal Fusion
                </strong>
                <span style={{ fontSize: '0.68rem', background: '#fef3c7', color: '#92400e', border: '1px solid #fde68a', padding: '1px 6px', borderRadius: '4px', fontWeight: 700 }}>
                  Non-Production Prototype
                </span>
              </div>
              <span style={{ fontSize: '0.73rem', color: '#64748b', display: 'block', marginTop: '1px' }}>
                {useFusionModel 
                  ? 'Active: Experimental research prototype using synthesized meteorological trajectories (not in primary pipeline).' 
                  : 'Optional prototype: Evaluates LSTM temporal sequences. Production uses Pillar 1 (Random Forest).'}
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
            {useFusionModel ? '🧪 Prototype Active' : 'Toggle Experimental Fusion'}
          </button>
        </div>

        {/* 1-Click Soil Presets & AI Photo Detector */}
        <div style={{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
            <label style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--primary-green)' }}>
              ⚡ 1-Click Field Presets or Auto-Detect from Photo:
            </label>

            <label style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '6px',
              background: '#f0fdf4',
              border: '1px solid #86efac',
              color: '#15803d',
              fontSize: '0.76rem',
              fontWeight: 700,
              cursor: soilDetecting ? 'wait' : 'pointer',
              transition: 'all 0.15s ease'
            }}>
              <Camera size={13} />
              <span>{soilDetecting ? 'Analyzing...' : '📷 Detect Soil Type from Photo'}</span>
              <input
                type="file"
                accept="image/*"
                onChange={handleSoilPhotoUpload}
                style={{ display: 'none' }}
                disabled={soilDetecting}
              />
            </label>
          </div>

          {soilDetectionResult && (
            <div style={{
              padding: '12px 14px',
              borderRadius: '8px',
              background: '#f8fafc',
              border: '1px solid #86efac',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              fontSize: '0.78rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
                <div>
                  <strong style={{ color: '#166534', fontSize: '0.86rem' }}>
                    Soil type detected: {soilDetectionResult.soil_type} (confidence {soilDetectionResult.confidence}%).
                  </strong>

                  {(soilDetectionResult.confidence < 70 || soilDetectionResult.soil_type?.toLowerCase() === 'loamy') && (
                    <div style={{ marginTop: '5px', padding: '4px 10px', borderRadius: '4px', background: '#fef3c7', border: '1px solid #fde68a', color: '#92400e', fontWeight: 600, fontSize: '0.74rem', display: 'flex', alignItems: 'center', gap: '5px' }}>
                      <AlertTriangle size={14} style={{ flexShrink: 0 }} />
                      <span>
                        {soilDetectionResult.soil_type?.toLowerCase() === 'loamy'
                          ? '⚠️ Is class ki detection kamzor hai (Loamy precision ~38.5%), soil type manually confirm karein.'
                          : '⚠️ Is class ki detection kamzor hai, soil type manually confirm karein.'}
                      </span>
                    </div>
                  )}

                  <span style={{ display: 'block', fontSize: '0.74rem', color: '#334155', marginTop: '6px' }}>
                    Photo se NPK ya pH nahi nikalte; kripya Soil Health Card ya lab test ke values neeche daalein.
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setSoilDetectionResult(null)}
                  style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1rem', padding: '2px 6px' }}
                >
                  ✕
                </button>
              </div>

              {/* Soil type badlein (Manual Override) */}
              <div style={{
                marginTop: '4px',
                paddingTop: '6px',
                borderTop: '1px dashed #cbd5e1',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                flexWrap: 'wrap'
              }}>
                <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#334155' }}>
                  🔄 Soil type badlein:
                </label>
                <select
                  value={overrideSoilType}
                  onChange={handleSoilOverrideChange}
                  style={{
                    padding: '3px 8px',
                    borderRadius: '6px',
                    border: '1px solid #94a3b8',
                    fontSize: '0.75rem',
                    background: '#ffffff',
                    color: '#1e293b',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  {['Black', 'Clayey', 'Loamy', 'Red', 'Sandy'].map(st => (
                    <option key={st} value={st}>{st} Soil</option>
                  ))}
                </select>
                {manualSoilOverride && (
                  <span style={{
                    background: '#fef3c7',
                    border: '1px solid #fde68a',
                    color: '#92400e',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '0.70rem',
                    fontWeight: 800
                  }}>
                    user-selected
                  </span>
                )}
              </div>
            </div>
          )}

          {soilDetectionError && (
            <div style={{ padding: '6px 10px', borderRadius: '6px', background: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', fontSize: '0.74rem' }}>
              ⚠️ {soilDetectionError}
            </div>
          )}

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px', marginTop: '4px' }}>
            <span style={{ fontSize: '0.76rem', fontWeight: 700, color: '#64748b' }}>
              🧪 Demo Presets (Estimated values, lab test se confirm karein):
            </span>
            <span style={{
              fontSize: '0.70rem',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '4px',
              background: dataSource === 'Demo estimated' ? '#fef3c7' : '#f0fdf4',
              color: dataSource === 'Demo estimated' ? '#92400e' : '#15803d',
              border: `1px solid ${dataSource === 'Demo estimated' ? '#fde68a' : '#86efac'}`
            }}>
              Source: {dataSource}
            </span>
          </div>

          <div className="preset-chips-strip">
            {DEMO_PRESETS.map((p, idx) => (
              <button
                key={idx}
                type="button"
                className="chip-btn"
                onClick={() => handlePresetSelect(p)}
                title={p.desc}
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>


        {/* Form Inputs */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '10px' }}>
          <div className="form-field-white">
            <label>
              <span>📍 Farm Location / District</span>
            </label>
            <input
              type="text"
              name="location"
              value={formData.location}
              onChange={handleChange}
              placeholder="e.g. Coimbatore, Ludhiana, Thanjavur"
              className="form-input-white"
              required
            />
          </div>

          {/* Educational Note on Soil Health Card Concentration Readings */}
          <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '10px', padding: '10px 14px', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.82rem', color: '#166534', marginTop: '2px', marginBottom: '4px' }}>
            <Info size={18} style={{ flexShrink: 0, color: '#15803d' }} />
            <span>
              <strong>Soil Health Card Lab Standard: </strong>
              The N-P-K values below represent your soil's natural nutrient density (measured in <strong>kg/ha</strong> per ICAR testing standards). Farm plot size is not needed for crop suitability.
            </span>
          </div>

          <div className="form-grid-modal">
            <div className="form-field-white">
              <label>
                <span>🌿 Available Nitrogen (N)</span>
                <span style={{ color: 'var(--primary-green)', fontWeight: 600 }}>
                  {formData.N !== '' ? `${formData.N} kg/ha` : '(Khali — lab test daalein)'}
                </span>
              </label>
              <input
                type="number"
                name="N"
                value={formData.N}
                onChange={handleChange}
                placeholder="e.g. 85"
                className="form-input-white"
                required
              />
            </div>

            <div className="form-field-white">
              <label>
                <span>🌱 Available Phosphorus (P)</span>
                <span style={{ color: 'var(--primary-green)', fontWeight: 600 }}>
                  {formData.P !== '' ? `${formData.P} kg/ha` : '(Khali — lab test daalein)'}
                </span>
              </label>
              <input
                type="number"
                name="P"
                value={formData.P}
                onChange={handleChange}
                placeholder="e.g. 48"
                className="form-input-white"
                required
              />
            </div>

            <div className="form-field-white">
              <label>
                <span>🌾 Available Potassium (K)</span>
                <span style={{ color: 'var(--primary-green)', fontWeight: 600 }}>
                  {formData.K !== '' ? `${formData.K} kg/ha` : '(Khali — lab test daalein)'}
                </span>
              </label>
              <input
                type="number"
                name="K"
                value={formData.K}
                onChange={handleChange}
                placeholder="e.g. 40"
                className="form-input-white"
                required
              />
            </div>

            <div className="form-field-white">
              <label>
                <span>🧪 Soil Reaction (pH)</span>
                <span style={{ color: 'var(--primary-green)', fontWeight: 600 }}>
                  {formData.ph !== '' ? `${formData.ph} pH` : '(Khali — lab test daalein)'}
                </span>
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="14"
                name="ph"
                value={formData.ph}
                onChange={handleChange}
                placeholder="e.g. 6.4"
                className="form-input-white"
                required
              />
            </div>
          </div>

          {/* Climate & Water Conditions Control */}
          <div style={{ background: '#f8fafc', padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CloudSun size={18} color="#0284c7" />
                <strong style={{ fontSize: '0.88rem', color: '#0f172a' }}>Crop Season & Climate Parameters</strong>
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.82rem', color: '#475569' }}>
                <input
                  type="checkbox"
                  name="useLiveWeather"
                  checked={formData.useLiveWeather}
                  onChange={handleChange}
                />
                <span>Sync with Live City Weather (Open-Meteo)</span>
              </label>
            </div>

            {!formData.useLiveWeather && (
              <div className="form-grid-modal" style={{ marginTop: '8px' }}>
                <div className="form-field-white">
                  <label>🌡️ Temperature (°C)</label>
                  <input
                    type="number"
                    step="0.5"
                    name="temperature"
                    value={formData.temperature}
                    onChange={handleChange}
                    placeholder="e.g. 24.0"
                    className="form-input-white"
                    required
                  />
                </div>
                <div className="form-field-white">
                  <label>💧 Humidity (%)</label>
                  <input
                    type="number"
                    name="humidity"
                    min="10"
                    max="100"
                    value={formData.humidity}
                    onChange={handleChange}
                    placeholder="e.g. 80"
                    className="form-input-white"
                    required
                  />
                </div>
                <div className="form-field-white">
                  <label>🌧️ Rainfall / Water Need (mm)</label>
                  <input
                    type="number"
                    name="rainfall"
                    min="10"
                    max="500"
                    value={formData.rainfall}
                    onChange={handleChange}
                    placeholder="e.g. 150"
                    className="form-input-white"
                    required
                  />
                </div>
              </div>
            )}
          </div>

          {!(formData.N !== '' && formData.P !== '' && formData.K !== '' && formData.ph !== '') && (
            <div style={{ padding: '8px 12px', borderRadius: '6px', background: '#eff6ff', border: '1px solid #bfdbfe', color: '#1e40af', fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Info size={16} style={{ flexShrink: 0 }} />
              <span>Soil Health Card ya lab test ke N, P, K, pH values daalein (ya upar se Demo Presets chunein).</span>
            </div>
          )}

          <button
            type="submit"
            disabled={
              loading ||
              formData.N === '' ||
              formData.P === '' ||
              formData.K === '' ||
              formData.ph === '' ||
              (!formData.useLiveWeather && (formData.temperature === '' || formData.humidity === '' || formData.rainfall === ''))
            }
            className="btn-primary-green"
            style={{
              opacity: (formData.N !== '' && formData.P !== '' && formData.K !== '' && formData.ph !== '' && (formData.useLiveWeather || (formData.temperature !== '' && formData.humidity !== '' && formData.rainfall !== ''))) ? 1 : 0.65
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

      {/* Recommendation Results Card */}
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

          {/* Data Source Badge & Amber Alert if Demo Estimated */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px', flexWrap: 'wrap' }}>
            <span style={{
              fontSize: '0.74rem',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '4px',
              background: recommendation.data_source === 'Demo estimated' ? '#fef3c7' : '#f0fdf4',
              color: recommendation.data_source === 'Demo estimated' ? '#92400e' : '#15803d',
              border: `1px solid ${recommendation.data_source === 'Demo estimated' ? '#fde68a' : '#86efac'}`
            }}>
              Data Source: {recommendation.data_source || 'User entered'}
            </span>
          </div>

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
              <span>⚠️ Estimated values, lab test se confirm karein.</span>
            </div>
          )}

          {/* Ambiguous Suitability Warning Banner */}
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

          {/* Wheat Provenance Limited Data Advisory */}
          {(recommendation.crop === 'wheat' || recommendation.provenance_note) && (
            <div style={{
              margin: '10px 0',
              padding: '8px 12px',
              borderRadius: '6px',
              background: '#fef3c7',
              border: '1px solid #fde68a',
              color: '#78350f',
              fontSize: '0.78rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}>
              <Info size={16} style={{ flexShrink: 0, color: '#b45309' }} />
              <span>
                <strong>Wheat Benchmark Advisory:</strong> Wheat recommendation is calibrated from ICAR synthetic parameter extension (limited benchmark data). Soil test verification advised.
              </span>
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
                    {item.crop === 'wheat' && (
                      <span style={{ fontSize: '0.68rem', color: '#b45309', fontWeight: 600 }}>
                        *limited data
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Multimodal Feature Bottleneck Display */}
          {recommendation.bottleneck_features && (
            <div style={{
              margin: '12px 0',
              padding: '10px 14px',
              borderRadius: '8px',
              background: '#f8fafc',
              border: '1px solid #cbd5e1',
              fontSize: '0.78rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px', flexWrap: 'wrap', gap: '6px' }}>
                <strong style={{ color: '#0f766e', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  🧬 Agronomic Feature Bottleneck Representation:
                </strong>
                <span style={{ fontSize: '0.72rem', background: '#ccfbf1', color: '#0f766e', padding: '1px 8px', borderRadius: '12px', fontWeight: 700 }}>
                  24-dim Latent Space
                </span>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {recommendation.bottleneck_features.map((val, idx) => (
                  <span key={idx} style={{
                    fontFamily: 'monospace',
                    fontSize: '0.74rem',
                    background: '#ffffff',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    border: '1px solid #e2e8f0',
                    color: '#334155'
                  }}>
                    z<sub>{idx+1}</sub>: {val}
                  </span>
                ))}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '6px' }}>
                Bi-LSTM 7-day weather dynamics fused with spatial soil chemistry through bottleneck feature compression.
              </div>
            </div>
          )}


          {/* Specs Grid */}
          <div className="result-specs-grid">
            <div className="result-spec-pill">
              <span className="lbl">Soil Type</span>
              <span className="val" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                {manualSoilOverride ? overrideSoilType : (soilDetectionResult?.soil_type || overrideSoilType || 'Loamy')}
                {manualSoilOverride ? (
                  <span style={{ fontSize: '0.68rem', background: '#fef3c7', color: '#92400e', border: '1px solid #fde68a', padding: '1px 6px', borderRadius: '4px', fontWeight: 700 }}>
                    user-selected
                  </span>
                ) : soilDetectionResult ? (
                  <span style={{ fontSize: '0.68rem', background: '#dcfce7', color: '#15803d', padding: '1px 6px', borderRadius: '4px', fontWeight: 700 }}>
                    AI-detected
                  </span>
                ) : null}
              </span>
            </div>
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
            <div style={{ background: '#f0fdf4', padding: '12px 16px', borderRadius: 'var(--radius-md)', border: '1px solid #bbf7d0', fontSize: '0.88rem' }}>
              <strong style={{ color: 'var(--primary-green)', display: 'block', marginBottom: '4px' }}>
                🌾 Farmer Harvesting Tip:
              </strong>
              <p style={{ color: 'var(--text-main)', margin: 0 }}>{recommendation.profile.harvest_tips}</p>
            </div>
          )}

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
