import React, { useState } from 'react';
import { 
  FlaskConical, 
  Sparkles, 
  TrendingUp, 
  Leaf, 
  Calendar, 
  RefreshCw,
  AlertCircle,
  Package,
  Layers,
  Printer,
  ShoppingBag,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  Camera,
  Upload
} from 'lucide-react';
import { getFertilizerRecommendation, classifySoilImage } from '../services/api';
import LandUnitConverter from './LandUnitConverter';


const SOIL_TYPES = ['Clayey', 'Loamy', 'Sandy', 'Black', 'Red'];
const CROP_TYPES = [
  'Paddy', 'Wheat', 'Maize', 'Sugarcane', 'Cotton', 'Tobacco', 
  'Barley', 'Millets', 'Oil seeds', 'Pulses', 'Ground Nuts'
];

const FERT_PRESETS = [
  { name: '🌾 Paddy on Clayey Soil', crop: 'Paddy', soil: 'Clayey', n: 40, p: 20, k: 15, moist: 70 },
  { name: '🌱 Wheat on Loamy Soil', crop: 'Wheat', soil: 'Loamy', n: 35, p: 15, k: 15, moist: 40 },
  { name: '🌽 Maize on Sandy Soil', crop: 'Maize', soil: 'Sandy', n: 37, p: 0, k: 0, moist: 38 },
  { name: '☁️ Cotton on Black Soil', crop: 'Cotton', soil: 'Black', n: 7, p: 30, k: 9, moist: 62 },
  { name: '🎋 Sugarcane on Loamy', crop: 'Sugarcane', soil: 'Loamy', n: 12, p: 36, k: 0, moist: 45 },
  { name: '🌿 High Nutrient Soil (N:210, P:214, K:310 kg/ha)', crop: 'Paddy', soil: 'Clayey', n: 210, p: 214, k: 310, moist: 70 },
  { name: '⚖️ Partial Deficit Soil (N:210, P:14, K:310 kg/ha)', crop: 'Paddy', soil: 'Clayey', n: 210, p: 14, k: 310, moist: 70 },
];

export default function FertilizerView({ initialCrop }) {
  const [formData, setFormData] = useState({
    temperature: 26,
    humidity: 60,
    moisture: 40,
    soil_type: 'Clayey',
    crop_type: initialCrop && CROP_TYPES.includes(initialCrop.charAt(0).toUpperCase() + initialCrop.slice(1)) 
      ? initialCrop.charAt(0).toUpperCase() + initialCrop.slice(1) 
      : 'Paddy',
    N: '',
    P: '',
    K: '',
  });

  const [dataSource, setDataSource] = useState('User entered');
  const [farmHectares, setFarmHectares] = useState(0);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [soilDetecting, setSoilDetecting] = useState(false);
  const [soilDetectionResult, setSoilDetectionResult] = useState(null);
  const [soilDetectionError, setSoilDetectionError] = useState('');
  const [soilSource, setSoilSource] = useState('user-selected');

  const handleSoilImageUpload = async (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;

    setSoilDetecting(true);
    setSoilDetectionError('');
    try {
      const res = await classifySoilImage(file);
      if (res && res.success) {
        setSoilDetectionResult(res);
        setSoilSource('ai-detected');
        // Photo upload sets ONLY soil_type (never moisture or NPK)
        setFormData(prev => ({
          ...prev,
          soil_type: res.soil_type
        }));
      } else {
        setSoilDetectionError(res.error || 'Failed to classify soil image');
      }
    } catch (err) {
      console.error('Soil classification error:', err);
      setSoilDetectionError(err.response?.data?.error || err.message || 'Error processing soil image');
    } finally {
      setSoilDetecting(false);
    }
  };

  const handleSoilOverrideChange = (newType) => {
    setFormData(prev => ({ ...prev, soil_type: newType }));
    setSoilSource('user-selected');
  };

  const handlePresetSelect = (preset) => {
    setFormData((prev) => ({
      ...prev,
      crop_type: preset.crop,
      soil_type: preset.soil,
      N: Number(preset.n),
      P: Number(preset.p),
      K: Number(preset.k),
      moisture: Number(preset.moist)
    }));
    setDataSource('Demo estimated');
  };

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    if (['N', 'P', 'K'].includes(name)) {
      setDataSource('User entered');
    }
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? (value === '' ? '' : Number(value)) : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const data = await getFertilizerRecommendation({
        temperature: Number(formData.temperature),
        humidity: Number(formData.humidity),
        moisture: Number(formData.moisture),
        soil_type: formData.soil_type,
        crop_type: formData.crop_type,
        N: Number(formData.N),
        P: Number(formData.P),
        K: Number(formData.K),
        data_source: dataSource,
        is_estimated: dataSource === 'Demo estimated'
      });

      if (data.success) {
        setResult({
          ...data,
          data_source: dataSource,
          is_estimated: dataSource === 'Demo estimated'
        });
      } else {
        setError(data.error || 'Fertilizer calculation failed.');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to connect to AgriSense server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Title Card & Input Form */}
      <div className="dashboard-card" style={{ padding: '24px', borderRadius: '16px' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', paddingBottom: '16px', borderBottom: '1px solid #f1f5f9' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: '#ecfdf5', color: '#16a34a', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid #bbf7d0' }}>
              <FlaskConical size={24} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.35rem', fontWeight: 800, color: '#0f172a' }}>
                🌾 Fertilizer Calculator & Dosage Plan
              </h3>
              <p style={{ margin: '2px 0 0 0', fontSize: '0.84rem', color: '#64748b' }}>
                Simple, accurate fertilizer recommendations for your farm size and soil
              </p>
            </div>
          </div>
          {result && (
            <button type="button" onClick={() => window.print()} className="btn-view-advice" style={{ padding: '6px 14px', fontSize: '0.82rem' }}>
              <Printer size={15} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
              Print Plan
            </button>
          )}
        </div>

        {/* Demo Presets (Estimated, Not Measured) */}
        <div style={{ margin: '14px 0', padding: '10px 14px', background: '#f8fafc', borderRadius: '10px', border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#475569' }}>
              🧪 Demo presets (Estimated values, not measured):
            </span>
            {FERT_PRESETS.slice(0, 5).map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handlePresetSelect(p)}
                style={{
                  fontSize: '0.76rem',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  background: formData.crop_type === p.crop ? '#dcfce7' : '#ffffff',
                  color: formData.crop_type === p.crop ? '#166534' : '#334155',
                  border: `1px solid ${formData.crop_type === p.crop ? '#86efac' : '#cbd5e1'}`,
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s'
                }}
              >
                {p.name.split(' on ')[0]}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
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
            <button
              type="button"
              onClick={() => handlePresetSelect(FERT_PRESETS[5])}
              style={{ fontSize: '0.74rem', padding: '3px 8px', borderRadius: '4px', background: '#ffffff', border: '1px solid #cbd5e1', color: '#059669', cursor: 'pointer', fontWeight: 600 }}
              title="Test with High Nutrient Soil"
            >
              🌿 Rich Soil
            </button>
            <button
              type="button"
              onClick={() => handlePresetSelect(FERT_PRESETS[6])}
              style={{ fontSize: '0.74rem', padding: '3px 8px', borderRadius: '4px', background: '#ffffff', border: '1px solid #cbd5e1', color: '#d97706', cursor: 'pointer', fontWeight: 600 }}
              title="Test with Partial Deficit Soil"
            >
              ⚖️ Deficit Soil
            </button>
          </div>
        </div>

        {/* Step-by-Step Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          
          {/* STEP 1: Crop & Land Size */}
          <div style={{ background: '#ffffff', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <span style={{ background: '#16a34a', color: '#ffffff', width: '22px', height: '22px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 800 }}>1</span>
              <strong style={{ fontSize: '0.95rem', color: '#0f172a' }}>
                Select Crop & Farm Size
              </strong>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '14px', marginBottom: '12px' }}>
              <div className="form-field-white">
                <label style={{ fontSize: '0.82rem', fontWeight: 700, color: '#334155' }}>
                  🌾 Crop Cultivated
                </label>
                <select
                  name="crop_type"
                  value={formData.crop_type}
                  onChange={handleChange}
                  className="form-select-white"
                  style={{ fontWeight: 600, fontSize: '0.92rem' }}
                >
                  {CROP_TYPES.map((crop) => (
                    <option key={crop} value={crop}>{crop}</option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <span style={{ fontSize: '0.78rem', color: '#64748b' }}>
                  Selected Crop: <strong>{formData.crop_type}</strong>
                </span>
                <span style={{ fontSize: '0.74rem', color: '#16a34a', marginTop: '2px' }}>
                  ICAR Blanket RDF & ML Model calibrated for {formData.crop_type}
                </span>
              </div>
            </div>

            {/* Regional Land Unit Converter */}
            <LandUnitConverter onHectareChange={setFarmHectares} />
          </div>

          {/* STEP 2: Soil Type & Moisture */}
          <div style={{ background: '#ffffff', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ background: '#16a34a', color: '#ffffff', width: '22px', height: '22px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 800 }}>2</span>
                <strong style={{ fontSize: '0.95rem', color: '#0f172a' }}>
                  Select Soil Type
                </strong>
              </div>

              <label style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '5px 12px',
                borderRadius: '8px',
                background: '#f0fdf4',
                border: '1px solid #86efac',
                color: '#15803d',
                fontSize: '0.78rem',
                fontWeight: 700,
                cursor: soilDetecting ? 'wait' : 'pointer',
                transition: 'all 0.15s ease'
              }}>
                <Camera size={14} />
                <span>{soilDetecting ? 'Analyzing Image...' : '📷 Detect from Photo (CNN Vision)'}</span>
                <input 
                  type="file" 
                  accept="image/*" 
                  onChange={handleSoilImageUpload} 
                  style={{ display: 'none' }} 
                  disabled={soilDetecting} 
                />
              </label>
            </div>

            {/* AI Vision Detection Success Notification */}
            {soilDetectionResult && (
              <div style={{
                marginBottom: '14px',
                padding: '10px 14px',
                borderRadius: '8px',
                background: '#f8fafc',
                border: '1px solid #bbf7d0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '10px'
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.86rem', fontWeight: 800, color: '#166534' }}>
                      🌱 AI Detected: {soilDetectionResult.soil_type} Soil
                    </span>
                    <span style={{ background: '#dcfce7', color: '#15803d', padding: '1px 8px', borderRadius: '12px', fontSize: '0.72rem', fontWeight: 700 }}>
                      {soilDetectionResult.confidence}% Confidence
                    </span>
                    {(soilDetectionResult.confidence < 70 || soilDetectionResult.soil_type?.toLowerCase() === 'loamy') && (
                      <span style={{ background: '#fef3c7', border: '1px solid #fde68a', color: '#92400e', padding: '2px 8px', borderRadius: '12px', fontSize: '0.72rem', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        {soilDetectionResult.soil_type?.toLowerCase() === 'loamy'
                          ? '⚠️ Is class ki detection kamzor hai (Loamy precision ~38.5%), soil type manually confirm karein'
                          : '⚠️ Is class ki detection kamzor hai, soil type manually confirm karein'}
                      </span>
                    )}
                  </div>
                  <span style={{ fontSize: '0.74rem', color: '#475569', display: 'block', marginTop: '2px' }}>
                    Photo se NPK ya moisture nahi nikalte; kripya Soil Health Card ya lab test ke values neeche daalein.
                  </span>

                  {/* Soil type badlein manual override */}
                  <div style={{ marginTop: '8px', paddingTop: '6px', borderTop: '1px dashed #cbd5e1', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#334155' }}>
                      🔄 Soil type badlein:
                    </label>
                    <select
                      value={formData.soil_type}
                      onChange={(e) => handleSoilOverrideChange(e.target.value)}
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
                    {soilSource === 'user-selected' && (
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
                <button
                  type="button"
                  onClick={() => setSoilDetectionResult(null)}
                  style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '0.9rem' }}
                >
                  ✕
                </button>
              </div>
            )}

            {soilDetectionError && (
              <div style={{ marginBottom: '12px', padding: '8px 12px', borderRadius: '8px', background: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', fontSize: '0.76rem' }}>
                ⚠️ {soilDetectionError}
              </div>
            )}


            {/* Visual 5-Soil Cards Selector */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: '10px', marginBottom: '14px' }}>
              {[
                { type: 'Clayey', icon: '🟫', desc: 'Heavy, wet' },
                { type: 'Loamy', icon: '🪴', desc: 'Fertile mix' },
                { type: 'Sandy', icon: '🏖️', desc: 'Fast drain' },
                { type: 'Black', icon: '⬛', desc: 'Regur / Cotton' },
                { type: 'Red', icon: '🔴', desc: 'Iron rich' }
              ].map((s) => {
                const isSelected = formData.soil_type === s.type;
                return (
                  <button
                    key={s.type}
                    type="button"
                    onClick={() => handleSoilOverrideChange(s.type)}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      padding: '10px 8px',
                      borderRadius: '10px',
                      border: `2px solid ${isSelected ? '#16a34a' : '#e2e8f0'}`,
                      background: isSelected ? '#f0fdf4' : '#ffffff',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      boxShadow: isSelected ? '0 2px 4px rgba(22, 163, 74, 0.15)' : 'none'
                    }}
                  >
                    <span style={{ fontSize: '1.4rem' }}>{s.icon}</span>
                    <span style={{ fontSize: '0.84rem', fontWeight: 800, color: isSelected ? '#166534' : '#1e293b', marginTop: '4px' }}>
                      {s.type}
                    </span>
                    <span style={{ fontSize: '0.68rem', color: isSelected ? '#15803d' : '#64748b', marginTop: '1px' }}>
                      {s.desc}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Soil Moisture Slider */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', background: '#f8fafc', padding: '10px 14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.1rem' }}>💧</span>
                <div>
                  <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#334155', display: 'block' }}>
                    Soil Moisture Level
                  </span>
                  <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                    Normal standing field moisture for {formData.crop_type}
                  </span>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: '1 1 200px', maxWidth: '300px' }}>
                <input
                  type="range"
                  name="moisture"
                  min="0"
                  max="100"
                  value={formData.moisture}
                  onChange={handleChange}
                  style={{ flex: 1, accentColor: '#16a34a' }}
                />
                <span style={{ fontSize: '0.86rem', fontWeight: 800, color: '#166534', minWidth: '42px', textAlign: 'right' }}>
                  {formData.moisture}%
                </span>
              </div>
            </div>
          </div>

          {/* STEP 3: Soil Test Lab Values (Mandatory N-P-K) */}
          <div style={{ background: '#ffffff', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ background: '#16a34a', color: '#ffffff', width: '22px', height: '22px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 800 }}>3</span>
                <strong style={{ fontSize: '0.95rem', color: '#0f172a' }}>
                  Soil Health Card / Lab Test (Mandatory N-P-K)
                </strong>
              </div>
              <span style={{
                fontSize: '0.74rem',
                color: (formData.N !== '' && formData.P !== '' && formData.K !== '') ? '#166534' : '#b45309',
                background: (formData.N !== '' && formData.P !== '' && formData.K !== '') ? '#dcfce7' : '#fef3c7',
                padding: '3px 8px',
                borderRadius: '6px',
                fontWeight: 600
              }}>
                {(formData.N !== '' && formData.P !== '' && formData.K !== '') ? `Filled (${dataSource})` : 'Lab values required'}
              </span>
            </div>

            <p style={{ fontSize: '0.78rem', color: '#64748b', margin: '0 0 12px 0' }}>
              Soil Health Card ke lab N, P, K values (kg/ha) daalein. AgriSense aapke soil reserves ko credit karke exact deficit fertilizer dose nikalega.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
              <div className="form-field-white">
                <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                  <span style={{ fontWeight: 700, color: '#166534' }}>🌿 Nitrogen (N)</span>
                  <span style={{ color: '#64748b', fontSize: '0.72rem' }}>kg/ha</span>
                </label>
                <input
                  type="number"
                  name="N"
                  value={formData.N}
                  onChange={handleChange}
                  className="form-input-white"
                  placeholder="e.g. 40"
                  required
                />
              </div>

              <div className="form-field-white">
                <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                  <span style={{ fontWeight: 700, color: '#8b5cf6' }}>🌱 Phosphorus (P)</span>
                  <span style={{ color: '#64748b', fontSize: '0.72rem' }}>kg/ha</span>
                </label>
                <input
                  type="number"
                  name="P"
                  value={formData.P}
                  onChange={handleChange}
                  className="form-input-white"
                  placeholder="e.g. 20"
                  required
                />
              </div>

              <div className="form-field-white">
                <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                  <span style={{ fontWeight: 700, color: '#0284c7' }}>🌾 Potassium (K)</span>
                  <span style={{ color: '#64748b', fontSize: '0.72rem' }}>kg/ha</span>
                </label>
                <input
                  type="number"
                  name="K"
                  value={formData.K}
                  onChange={handleChange}
                  className="form-input-white"
                  placeholder="e.g. 15"
                  required
                />
              </div>
            </div>
          </div>

          {!(formData.N !== '' && formData.P !== '' && formData.K !== '') && (
            <div style={{ padding: '8px 12px', borderRadius: '6px', background: '#eff6ff', border: '1px solid #bfdbfe', color: '#1e40af', fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <AlertCircle size={16} style={{ flexShrink: 0 }} />
              <span>Soil Health Card ya lab test ke N, P, K values daalein (ya upar Demo Presets use karein).</span>
            </div>
          )}

          {/* Action Submit Button */}
          <button 
            type="submit" 
            disabled={loading || formData.N === '' || formData.P === '' || formData.K === ''} 
            className="btn-primary-green"
            style={{
              background: '#16a34a',
              padding: '14px 20px',
              fontSize: '1.05rem',
              fontWeight: 800,
              borderRadius: '12px',
              boxShadow: '0 4px 12px rgba(22, 163, 74, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              cursor: (loading || formData.N === '' || formData.P === '' || formData.K === '') ? 'not-allowed' : 'pointer',
              opacity: (formData.N !== '' && formData.P !== '' && formData.K !== '') ? 1 : 0.65,
              border: 'none',
              color: '#ffffff',
              transition: 'all 0.2s ease'
            }}
          >
            {loading ? (
              <>
                <RefreshCw size={20} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
                <span>Calculating Fertilizer Needs (ICAR + AI Model)...</span>
              </>
            ) : (
              <>
                <Sparkles size={20} />
                <span>Calculate Recommended Fertilizer & Dosage</span>
              </>
            )}
          </button>
        </form>

        {error && (
          <div style={{ padding: '12px 14px', background: '#fef2f2', border: '1px solid #fee2e2', borderRadius: '10px', color: '#dc2626', display: 'flex', alignItems: 'center', gap: '8px', marginTop: '14px' }}>
            <AlertCircle size={18} />
            <span style={{ fontSize: '0.88rem' }}>{error}</span>
          </div>
        )}
      </div>

      {/* Output */}
      {result && (() => {
        const acres = farmHectares > 0 ? farmHectares * 2.47105 : 1.0;
        const isAdjusted = Boolean(
          result.scientific_plan?.has_soil_test && 
          result.scientific_plan?.soil_adjusted_dose
        );

        const isAllSufficient = Boolean(
          isAdjusted && result.scientific_plan.soil_adjusted_dose.all_sufficient
        );

        const dapPerAcreKg = isAdjusted
          ? Number(result.scientific_plan.soil_adjusted_dose.dap_kg)
          : Number(result.scientific_plan.blanket_dose?.dap_kg || 52.8);

        const ureaPerAcreKg = isAdjusted
          ? Number(result.scientific_plan.soil_adjusted_dose.urea_kg)
          : Number(result.scientific_plan.blanket_dose?.urea_kg || 85.0);

        const mopPerAcreKg = isAdjusted
          ? Number(result.scientific_plan.soil_adjusted_dose.mop_kg)
          : Number(result.scientific_plan.blanket_dose?.mop_kg || 27.0);

        const dapPerAcreBags = isAdjusted
          ? Number(result.scientific_plan.soil_adjusted_dose.dap_bags)
          : Number(result.scientific_plan.blanket_dose?.dap_bags || 1.06);

        const ureaPerAcreBags = isAdjusted
          ? Number(result.scientific_plan.soil_adjusted_dose.urea_bags)
          : Number(result.scientific_plan.blanket_dose?.urea_bags || 1.70);

        const mopPerAcreBags = isAdjusted
          ? Number(result.scientific_plan.soil_adjusted_dose.mop_bags)
          : Number(result.scientific_plan.blanket_dose?.mop_bags || 0.54);

        // Total Farm Calculations across total acreage
        const dapTotalKg = (dapPerAcreKg * acres).toFixed(1);
        const dapTotalBags = (dapTotalKg / 50.0).toFixed(1);

        const ureaTotalKg = (ureaPerAcreKg * acres).toFixed(1);
        const ureaTotalBags = (ureaTotalKg / 50.0).toFixed(1);

        const mopTotalKg = (mopPerAcreKg * acres).toFixed(1);
        const mopTotalBags = (mopTotalKg / 50.0).toFixed(1);

        const isDapSufficient = isAdjusted && (result.scientific_plan.soil_adjusted_dose?.p_sufficient || dapPerAcreKg === 0);
        const isUreaSufficient = isAdjusted && (result.scientific_plan.soil_adjusted_dose?.n_sufficient || ureaPerAcreKg === 0);
        const isMopSufficient = isAdjusted && (result.scientific_plan.soil_adjusted_dose?.k_sufficient || mopPerAcreKg === 0);

        return (
          <div className="result-box-green animate-fade-in" style={{ background: '#f8fafc', borderColor: '#cbd5e1', padding: '24px' }}>
            {/* Header Banner */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', paddingBottom: '16px', borderBottom: '1px solid #e2e8f0' }}>
              <div>
                <span style={{ fontSize: '0.8rem', color: '#16a34a', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  FARMER ADVISORY PLAN
                </span>
                <h3 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0f172a', margin: '4px 0 0 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>🌾 {result.scientific_plan?.crop || formData.crop_type} Fertilizer Plan</span>
                  <span style={{ fontSize: '0.95rem', fontWeight: 600, color: '#64748b', background: '#f1f5f9', padding: '2px 10px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                    {farmHectares > 0 ? `${acres.toFixed(2)} Acres (${farmHectares} ha)` : '1.00 Acre Baseline'}
                  </span>
                </h3>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                {isAllSufficient ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#ecfdf5', color: '#065f46', border: '1px solid #a7f3d0', padding: '6px 14px', borderRadius: '9999px', fontSize: '0.84rem', fontWeight: 700 }}>
                    <CheckCircle2 size={16} color="#059669" />
                    <span>Soil Test Applied • 100% Fertilizer Saved (0 Bags Needed)</span>
                  </div>
                ) : isAdjusted ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#ecfdf5', color: '#065f46', border: '1px solid #a7f3d0', padding: '6px 14px', borderRadius: '9999px', fontSize: '0.84rem', fontWeight: 700 }}>
                    <CheckCircle2 size={16} color="#059669" />
                    <span>Soil Lab Test Credited (N:{formData.N} P:{formData.P} K:{formData.K})</span>
                  </div>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#f0fdf4', color: '#166534', border: '1px solid #bbf7d0', padding: '6px 14px', borderRadius: '9999px', fontSize: '0.84rem', fontWeight: 600 }}>
                    <Sparkles size={16} color="#16a34a" />
                    <span>ICAR Standard Blanket Recommendation</span>
                  </div>
                )}
                
                <button
                  type="button"
                  onClick={() => window.print()}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#ffffff', border: '1px solid #cbd5e1', padding: '6px 12px', borderRadius: '8px', fontSize: '0.82rem', fontWeight: 600, color: '#475569', cursor: 'pointer' }}
                >
                  <Printer size={15} />
                  <span>Print Plan</span>
                </button>
              </div>
            </div>

            {/* Data Source Badge & Warning */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px', flexWrap: 'wrap' }}>
              <span style={{
                fontSize: '0.74rem',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: '4px',
                background: (result.data_source === 'Demo estimated' || result.is_estimated) ? '#fef3c7' : '#f0fdf4',
                color: (result.data_source === 'Demo estimated' || result.is_estimated) ? '#92400e' : '#15803d',
                border: `1px solid ${(result.data_source === 'Demo estimated' || result.is_estimated) ? '#fde68a' : '#86efac'}`
              }}>
                Data Source: {result.data_source || 'User entered'}
              </span>
            </div>

            {(result.is_estimated || result.data_source === 'Demo estimated') && (
              <div style={{
                marginTop: '12px',
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
                <AlertCircle size={18} style={{ flexShrink: 0, color: '#d97706' }} />
                <span>
                  ⚠️ Estimated values, lab test se confirm karein. <strong>(Estimated, not for actual application)</strong>
                </span>
              </div>
            )}

            {/* If 100% Sufficient Alert */}
            {isAllSufficient && (
              <div style={{ marginTop: '16px', padding: '14px 18px', background: '#ecfdf5', border: '1.5px solid #6ee7b7', borderRadius: '12px', display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                <div style={{ fontSize: '1.5rem', lineHeight: 1 }}>🎉</div>
                <div>
                  <h4 style={{ margin: '0 0 4px 0', color: '#065f46', fontSize: '1.05rem', fontWeight: 800 }}>
                    Excellent News! Your Soil Already Has Abundant Nutrients
                  </h4>
                  <p style={{ margin: 0, color: '#047857', fontSize: '0.88rem', lineHeight: 1.5 }}>
                    Your soil laboratory test shows high reserves of Nitrogen, Phosphorus, and Potassium that fully satisfy crop requirements across all {acres.toFixed(2)} Acres. 
                    <strong> You do NOT need to buy any chemical fertilizer bags for this season.</strong> This saves money and prevents nutrient toxicity.
                  </p>
                </div>
              </div>
            )}

            {/* SECTION 1: WHAT TO BUY (SHOPPING LIST) */}
            <div style={{ marginTop: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                <h4 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: '#1e293b', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShoppingBag size={20} color="#16a34a" />
                  <span>What to Buy for Your Farm ({farmHectares > 0 ? `${acres.toFixed(2)} Acres` : '1 Acre Baseline'})</span>
                </h4>
                <span style={{ fontSize: '0.8rem', color: '#64748b' }}>50 kg per bag standard</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
                {/* DAP Card */}
                <div style={{
                  background: isDapSufficient ? '#f0fdf4' : '#ffffff',
                  border: `2px solid ${isDapSufficient ? '#86efac' : '#e2e8f0'}`,
                  borderRadius: '12px',
                  padding: '16px 18px',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                  position: 'relative'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#8b5cf6', background: '#ede9fe', padding: '2px 8px', borderRadius: '4px', textTransform: 'uppercase' }}>
                        Phosphorus & Root
                      </span>
                      <h5 style={{ margin: '6px 0 0 0', fontSize: '1.15rem', fontWeight: 800, color: '#1e293b' }}>
                        DAP Fertilizer
                      </h5>
                    </div>
                    {isDapSufficient ? (
                      <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#166534', background: '#dcfce7', padding: '3px 8px', borderRadius: '6px' }}>
                        Sufficient
                      </span>
                    ) : (
                      <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#64748b' }}>
                        {dapPerAcreBags} b/ac
                      </span>
                    )}
                  </div>

                  <div style={{ marginTop: '12px', marginBottom: '8px' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 900, color: isDapSufficient ? '#166534' : '#0f172a', lineHeight: 1.1 }}>
                      {isDapSufficient ? '0 Bags' : `${dapTotalBags} Bags`}
                    </div>
                    <div style={{ fontSize: '0.82rem', color: isDapSufficient ? '#15803d' : '#64748b', marginTop: '4px', fontWeight: 500 }}>
                      {isDapSufficient 
                        ? '✅ Soil reserve has enough P₂O₅' 
                        : `Total: ${dapTotalKg} kg (${dapPerAcreKg} kg/acre)`}
                    </div>
                  </div>

                  <div style={{ borderTop: '1px dashed #e2e8f0', paddingTop: '8px', marginTop: '10px', fontSize: '0.76rem', color: '#475569' }}>
                    <strong>When:</strong> 100% applied at sowing / transplanting
                  </div>
                </div>

                {/* Urea Card */}
                <div style={{
                  background: isUreaSufficient ? '#f0fdf4' : '#ffffff',
                  border: `2px solid ${isUreaSufficient ? '#86efac' : '#e2e8f0'}`,
                  borderRadius: '12px',
                  padding: '16px 18px',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                  position: 'relative'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#16a34a', background: '#dcfce7', padding: '2px 8px', borderRadius: '4px', textTransform: 'uppercase' }}>
                        Nitrogen & Green Growth
                      </span>
                      <h5 style={{ margin: '6px 0 0 0', fontSize: '1.15rem', fontWeight: 800, color: '#1e293b' }}>
                        Urea Fertilizer
                      </h5>
                    </div>
                    {isUreaSufficient ? (
                      <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#166534', background: '#dcfce7', padding: '3px 8px', borderRadius: '6px' }}>
                        Sufficient
                      </span>
                    ) : (
                      <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#64748b' }}>
                        {ureaPerAcreBags} b/ac
                      </span>
                    )}
                  </div>

                  <div style={{ marginTop: '12px', marginBottom: '8px' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 900, color: isUreaSufficient ? '#166534' : '#0f172a', lineHeight: 1.1 }}>
                      {isUreaSufficient ? '0 Bags' : `${ureaTotalBags} Bags`}
                    </div>
                    <div style={{ fontSize: '0.82rem', color: isUreaSufficient ? '#15803d' : '#64748b', marginTop: '4px', fontWeight: 500 }}>
                      {isUreaSufficient 
                        ? '✅ Soil reserve has enough N' 
                        : `Total: ${ureaTotalKg} kg (${ureaPerAcreKg} kg/acre)`}
                    </div>
                  </div>

                  <div style={{ borderTop: '1px dashed #e2e8f0', paddingTop: '8px', marginTop: '10px', fontSize: '0.76rem', color: '#475569' }}>
                    <strong>When:</strong> Split in 3 equal parts across crop growth
                  </div>
                </div>

                {/* MOP (Potash) Card */}
                <div style={{
                  background: isMopSufficient ? '#f0fdf4' : '#ffffff',
                  border: `2px solid ${isMopSufficient ? '#86efac' : '#e2e8f0'}`,
                  borderRadius: '12px',
                  padding: '16px 18px',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                  position: 'relative'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#0284c7', background: '#e0f2fe', padding: '2px 8px', borderRadius: '4px', textTransform: 'uppercase' }}>
                        Potassium & Grain Quality
                      </span>
                      <h5 style={{ margin: '6px 0 0 0', fontSize: '1.15rem', fontWeight: 800, color: '#1e293b' }}>
                        MOP (Potash)
                      </h5>
                    </div>
                    {isMopSufficient ? (
                      <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#166534', background: '#dcfce7', padding: '3px 8px', borderRadius: '6px' }}>
                        Sufficient
                      </span>
                    ) : (
                      <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#64748b' }}>
                        {mopPerAcreBags} b/ac
                      </span>
                    )}
                  </div>

                  <div style={{ marginTop: '12px', marginBottom: '8px' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 900, color: isMopSufficient ? '#166534' : '#0f172a', lineHeight: 1.1 }}>
                      {isMopSufficient ? '0 Bags' : `${mopTotalBags} Bags`}
                    </div>
                    <div style={{ fontSize: '0.82rem', color: isMopSufficient ? '#15803d' : '#64748b', marginTop: '4px', fontWeight: 500 }}>
                      {isMopSufficient 
                        ? '✅ Soil reserve has enough K₂O' 
                        : `Total: ${mopTotalKg} kg (${mopPerAcreKg} kg/acre)`}
                    </div>
                  </div>

                  <div style={{ borderTop: '1px dashed #e2e8f0', paddingTop: '8px', marginTop: '10px', fontSize: '0.76rem', color: '#475569' }}>
                    <strong>When:</strong> 50% at sowing + 50% at panicle stage
                  </div>
                </div>
              </div>
            </div>

            {/* SECTION 2: APPLICATION TIMELINE */}
            <div style={{ marginTop: '24px', background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '18px 20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                <h4 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 800, color: '#1e293b', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Clock size={18} color="#0284c7" />
                  <span>When & How to Apply (Growth Stage Schedule)</span>
                </h4>
                <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  Soil Type: {formData.soil_type} Soil
                  {soilSource === 'user-selected' ? (
                    <span style={{ background: '#fef3c7', color: '#92400e', border: '1px solid #fde68a', padding: '1px 6px', borderRadius: '4px', fontSize: '0.68rem', fontWeight: 700 }}>
                      user-selected
                    </span>
                  ) : (
                    <span style={{ background: '#dcfce7', color: '#15803d', padding: '1px 6px', borderRadius: '4px', fontSize: '0.68rem', fontWeight: 700 }}>
                      AI-detected
                    </span>
                  )}
                </span>
              </div>

              {isAllSufficient ? (
                <div style={{ padding: '12px 14px', background: '#f0fdf4', borderRadius: '8px', color: '#166534', fontSize: '0.88rem' }}>
                  ✅ <strong>No chemical fertilizer schedule needed:</strong> Continue regular field irrigation and weeding. Soil organic matter is self-sufficient.
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
                  {/* Step 1 */}
                  <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                      <span style={{ background: '#3b82f6', color: '#ffffff', width: '24px', height: '24px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 800 }}>1</span>
                      <strong style={{ fontSize: '0.9rem', color: '#0f172a' }}>Day 0 (At Sowing / Basal)</strong>
                    </div>
                    <p style={{ fontSize: '0.78rem', color: '#64748b', margin: '0 0 8px 0' }}>
                      Mix into soil during last ploughing / transplanting:
                    </p>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1e293b', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {!isDapSufficient && <div>• DAP: {dapTotalBags} Bags ({dapTotalKg} kg) - 100%</div>}
                      {!isUreaSufficient && <div>• Urea: {(ureaTotalBags * 0.5).toFixed(1)} Bags ({(ureaTotalKg * 0.5).toFixed(1)} kg) - 50%</div>}
                      {!isMopSufficient && <div>• MOP: {(mopTotalBags * 0.5).toFixed(1)} Bags ({(mopTotalKg * 0.5).toFixed(1)} kg) - 50%</div>}
                    </div>
                  </div>

                  {/* Step 2 */}
                  <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                      <span style={{ background: '#10b981', color: '#ffffff', width: '24px', height: '24px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 800 }}>2</span>
                      <strong style={{ fontSize: '0.9rem', color: '#0f172a' }}>Day 20–25 (Tillering Stage)</strong>
                    </div>
                    <p style={{ fontSize: '0.78rem', color: '#64748b', margin: '0 0 8px 0' }}>
                      Broadcast evenly with standing thin layer of water:
                    </p>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1e293b', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {!isUreaSufficient ? (
                        <div>• Urea: {(ureaTotalBags * 0.25).toFixed(1)} Bags ({(ureaTotalKg * 0.25).toFixed(1)} kg) - 25%</div>
                      ) : (
                        <div style={{ color: '#166534' }}>• No top-dressing required (Soil sufficient)</div>
                      )}
                    </div>
                  </div>

                  {/* Step 3 */}
                  <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                      <span style={{ background: '#8b5cf6', color: '#ffffff', width: '24px', height: '24px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 800 }}>3</span>
                      <strong style={{ fontSize: '0.9rem', color: '#0f172a' }}>Day 40–45 (Panicle Initiation)</strong>
                    </div>
                    <p style={{ fontSize: '0.78rem', color: '#64748b', margin: '0 0 8px 0' }}>
                      Final dose before flowering for grain filling:
                    </p>
                    <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1e293b', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {!isUreaSufficient && <div>• Urea: {(ureaTotalBags * 0.25).toFixed(1)} Bags ({(ureaTotalKg * 0.25).toFixed(1)} kg) - 25%</div>}
                      {!isMopSufficient && <div>• MOP: {(mopTotalBags * 0.5).toFixed(1)} Bags ({(mopTotalKg * 0.5).toFixed(1)} kg) - 50%</div>}
                      {isUreaSufficient && isMopSufficient && <div style={{ color: '#166534' }}>• Soil sufficient — no final chemical top-dressing needed</div>}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* SECTION 3: COLLAPSIBLE TECHNICAL RESEARCH ACCORDION */}
            <div style={{ marginTop: '20px' }}>
              <button
                type="button"
                onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 16px',
                  background: showTechnicalDetails ? '#f1f5f9' : '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '10px',
                  cursor: 'pointer',
                  fontSize: '0.88rem',
                  fontWeight: 700,
                  color: '#334155',
                  transition: 'all 0.2s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>🔬</span>
                  <span>View Agronomic Research Details (ICAR Targets, Soil Deficit Math, ML Model Match)</span>
                </div>
                {showTechnicalDetails ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>

              {showTechnicalDetails && (
                <div style={{ marginTop: '12px', padding: '16px', background: '#ffffff', borderRadius: '10px', border: '1px solid #cbd5e1' }} className="animate-fade-in">
                  {/* ML Grade Row */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px', paddingBottom: '12px', borderBottom: '1px solid #f1f5f9', marginBottom: '12px' }}>
                    <div>
                      <span style={{ fontSize: '0.74rem', color: '#7c3aed', fontWeight: 700, textTransform: 'uppercase' }}>
                        Machine Learning Classification Model
                      </span>
                      <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#7c3aed' }}>
                        🧪 Prescribed Grade: {result.fertilizer}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span style={{ background: '#ede9fe', color: '#6d28d9', border: '1px solid #c4b5fd', fontSize: '0.84rem', padding: '4px 10px', borderRadius: '6px', fontWeight: 700 }}>
                        {result.confidence}% Match
                      </span>
                      <span style={{ fontSize: '0.72rem', color: '#64748b', display: 'block', marginTop: '2px' }}>
                        Trained on 100% accurate Random Forest
                      </span>
                    </div>
                  </div>

                  {/* ICAR Standard Blanket Matrix */}
                  {result.scientific_plan && (
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px', marginBottom: '8px' }}>
                        <strong style={{ fontSize: '0.88rem', color: '#1e293b' }}>
                          🏛️ ICAR Standard Blanket RDF Targets:
                        </strong>
                        <span style={{ fontSize: '0.76rem', color: '#4338ca', fontWeight: 600 }}>
                          Target: {result.scientific_plan.icar_target_ha} ({result.scientific_plan.icar_target_acre})
                        </span>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '10px', marginBottom: '14px' }}>
                        <div style={{ background: '#fdf4ff', padding: '10px 12px', borderRadius: '8px', border: '1px solid #f5d0fe' }}>
                          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#a21caf', textTransform: 'uppercase' }}>DAP Blanket</span>
                          <div style={{ fontSize: '0.98rem', fontWeight: 800, color: '#86198f', marginTop: '2px' }}>
                            {result.scientific_plan.blanket_dose?.dap_text || "52.8 kg/acre (1.05 Bags)"}
                          </div>
                        </div>

                        <div style={{ background: '#f0fdf4', padding: '10px 12px', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
                          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#15803d', textTransform: 'uppercase' }}>Urea Blanket</span>
                          <div style={{ fontSize: '0.98rem', fontWeight: 800, color: '#166534', marginTop: '2px' }}>
                            {result.scientific_plan.blanket_dose?.urea_text || "85.0 kg/acre (1.70 Bags)"}
                          </div>
                        </div>

                        <div style={{ background: '#eff6ff', padding: '10px 12px', borderRadius: '8px', border: '1px solid #bfdbfe' }}>
                          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#1d4ed8', textTransform: 'uppercase' }}>MOP Blanket</span>
                          <div style={{ fontSize: '0.98rem', fontWeight: 800, color: '#1e40af', marginTop: '2px' }}>
                            {result.scientific_plan.blanket_dose?.mop_text || "27.0 kg/acre (0.55 Bags)"}
                          </div>
                        </div>
                      </div>

                      {/* Soil Test Deductions */}
                      {result.scientific_plan.has_soil_test && (
                        <div style={{ padding: '12px 14px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '12px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '6px', marginBottom: '8px' }}>
                            <strong style={{ fontSize: '0.84rem', color: '#334155' }}>
                              🌱 Soil Lab Test Conversions & Deductions (kg/ha → kg/acre):
                            </strong>
                            <span style={{ fontSize: '0.72rem', color: '#166534', background: '#dcfce7', padding: '2px 8px', borderRadius: '4px', border: '1px solid #86efac', fontWeight: 700 }}>
                              Input: N:{formData.N} | P:{formData.P} | K:{formData.K} kg/ha
                            </span>
                          </div>

                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '8px' }}>
                            <div style={{ background: '#ffffff', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
                              <span style={{ fontSize: '0.72rem', color: '#64748b' }}>Net DAP Rate</span>
                              <div style={{ fontSize: '0.92rem', fontWeight: 700, color: result.scientific_plan.soil_adjusted_dose?.p_sufficient ? '#166534' : '#0f172a' }}>
                                {result.scientific_plan.soil_adjusted_dose?.dap_text}
                              </div>
                              {result.scientific_plan.soil_adjusted_dose?.p_sufficient && (
                                <span style={{ fontSize: '0.68rem', color: '#15803d', display: 'block', marginTop: '2px' }}>
                                  Surplus: +{result.scientific_plan.soil_adjusted_dose?.p_surplus_kg} kg/ac P₂O₅
                                </span>
                              )}
                            </div>

                            <div style={{ background: '#ffffff', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
                              <span style={{ fontSize: '0.72rem', color: '#64748b' }}>Net Urea Rate</span>
                              <div style={{ fontSize: '0.92rem', fontWeight: 700, color: result.scientific_plan.soil_adjusted_dose?.n_sufficient ? '#166534' : '#0f172a' }}>
                                {result.scientific_plan.soil_adjusted_dose?.urea_text}
                              </div>
                              {result.scientific_plan.soil_adjusted_dose?.n_sufficient && (
                                <span style={{ fontSize: '0.68rem', color: '#15803d', display: 'block', marginTop: '2px' }}>
                                  Surplus: +{result.scientific_plan.soil_adjusted_dose?.n_surplus_kg} kg/ac N
                                </span>
                              )}
                            </div>

                            <div style={{ background: '#ffffff', padding: '8px 10px', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
                              <span style={{ fontSize: '0.72rem', color: '#64748b' }}>Net MOP Rate</span>
                              <div style={{ fontSize: '0.92rem', fontWeight: 700, color: result.scientific_plan.soil_adjusted_dose?.k_sufficient ? '#166534' : '#0f172a' }}>
                                {result.scientific_plan.soil_adjusted_dose?.mop_text}
                              </div>
                              {result.scientific_plan.soil_adjusted_dose?.k_sufficient && (
                                <span style={{ fontSize: '0.68rem', color: '#15803d', display: 'block', marginTop: '2px' }}>
                                  Surplus: +{result.scientific_plan.soil_adjusted_dose?.k_surplus_kg} kg/ac K₂O
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Organic Alternatives */}
                  {result.profile?.organic_alternatives && (
                    <div style={{ background: '#f0fdf4', padding: '10px 14px', borderRadius: '8px', border: '1px solid #bbf7d0', fontSize: '0.84rem', marginTop: '10px' }}>
                      <strong style={{ color: '#166534', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                        <Leaf size={14} />
                        Organic / Bio-fertilizer Options:
                      </strong>
                      <p style={{ color: '#14532d', margin: 0, fontSize: '0.8rem' }}>{result.profile.organic_alternatives}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })()}

    </div>
  );
}
