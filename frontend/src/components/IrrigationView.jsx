import React, { useState, useEffect } from 'react';
import { 
  Droplets, 
  Sun, 
  CloudRain, 
  Calendar, 
  Clock, 
  Layers, 
  MapPin, 
  AlertCircle, 
  CheckCircle2, 
  RefreshCw, 
  ArrowRight,
  Gauge,
  Sparkles,
  Info,
  Settings,
  ShieldCheck
} from 'lucide-react';
import { getIrrigationPlan, getWeatherData } from '../services/api';

const CROP_OPTIONS = [
  { value: 'rice', label: '🌾 Paddy / Rice' },
  { value: 'wheat', label: '🌾 Wheat' },
  { value: 'maize', label: '🌽 Maize (Corn)' },
  { value: 'cotton', label: '🌱 Cotton' },
  { value: 'sugarcane', label: '🎋 Sugarcane' },
  { value: 'chickpea', label: '🫘 Chickpea (Gram)' },
  { value: 'pigeonpeas', label: '🫘 Pigeonpeas (Tur)' },
  { value: 'kidneybeans', label: '🫘 Kidney Beans (Rajma)' },
  { value: 'mothbeans', label: '🌱 Mothbeans' },
  { value: 'mungbean', label: '🌱 Green Gram (Moong)' },
  { value: 'blackgram', label: '🌱 Black Gram (Urad)' },
  { value: 'lentil', label: '🫘 Lentil (Masoor)' },
  { value: 'pomegranate', label: '🍎 Pomegranate' },
  { value: 'banana', label: '🍌 Banana' },
  { value: 'mango', label: '🥭 Mango' },
  { value: 'grapes', label: '🍇 Grapes' },
  { value: 'watermelon', label: '🍉 Watermelon' },
  { value: 'muskmelon', label: '🍈 Muskmelon' },
  { value: 'apple', label: '🍎 Apple' },
  { value: 'orange', label: '🍊 Orange' },
  { value: 'papaya', label: '🪴 Papaya' },
  { value: 'coconut', label: '🥥 Coconut' },
  { value: 'jute', label: '🌿 Jute' },
  { value: 'coffee', label: '☕ Coffee' },
  { value: 'chilli', label: '🌶️ Chilli' }
];

const GROWTH_STAGES = [
  { value: 'initial', label: '🌱 Initial / Germination Stage' },
  { value: 'vegetative', label: '🌿 Active Vegetative Canopy Growth' },
  { value: 'flowering', label: '🌸 Flowering & Fruit / Pod Initiation' },
  { value: 'ripening', label: '🌾 Ripening & Maturation' }
];

const SOIL_TYPES = [
  { value: 'Clayey', label: 'Clayey Soil (AWC: 170 mm/m, High Retention)' },
  { value: 'Black', label: 'Black / Vertisol Soil (AWC: 160 mm/m, Heavy Holding)' },
  { value: 'Loamy', label: 'Loamy Soil (AWC: 140 mm/m, Balanced Drainage)' },
  { value: 'Red', label: 'Red / Alfisol Soil (AWC: 110 mm/m, Medium Drainage)' },
  { value: 'Sandy', label: 'Sandy Soil (AWC: 70 mm/m, Rapid Percolation)' }
];

const LAND_UNITS = [
  { value: 'acres', label: 'Acres' },
  { value: 'cents', label: 'Cents (100 Cents = 1 Acre)' },
  { value: 'gunthas', label: 'Gunthas (40 Gunthas = 1 Acre)' },
  { value: 'hectares', label: 'Hectares' }
];

export default function IrrigationView({ 
  activeLocation = 'Coimbatore', 
  initialCrop = 'rice', 
  soilData, 
  farmArea = 2,
  farmAreaUnit = 'acres',
  onUpdateFarmArea,
  onUpdateFarmAreaUnit,
  onUpdateSoil 
}) {
  const [crop, setCrop] = useState(initialCrop || 'rice');
  const [stage, setStage] = useState('vegetative');
  const [soilType, setSoilType] = useState(soilData?.soil_type || 'Loamy');
  const [area, setArea] = useState(farmArea);
  const [areaUnit, setAreaUnit] = useState(farmAreaUnit);
  const [temperature, setTemperature] = useState(28);
  const [humidity, setHumidity] = useState(60);
  const [rainfall, setRainfall] = useState(0);

  // Sync with global farmArea from App.jsx
  useEffect(() => {
    if (farmArea) setArea(farmArea);
  }, [farmArea]);

  useEffect(() => {
    if (farmAreaUnit) setAreaUnit(farmAreaUnit);
  }, [farmAreaUnit]);

  // Sync with global soil state from App.jsx
  useEffect(() => {
    if (soilData?.soil_type) {
      setSoilType(soilData.soil_type);
    }
  }, [soilData]);

  // Hardware Drip Parameters
  const [showAdvancedDrip, setShowAdvancedDrip] = useState(false);
  const [emitterLph, setEmitterLph] = useState(2.0);
  const [emitterSpacingM, setEmitterSpacingM] = useState(0.4);
  const [lateralSpacingM, setLateralSpacingM] = useState(0.8);

  const [loading, setLoading] = useState(false);
  const [weatherSyncing, setWeatherSyncing] = useState(false);
  const [planResult, setPlanResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  // Initial plan load
  useEffect(() => {
    handleCalculatePlan();
  }, []);

  const handleSyncWeather = async () => {
    setWeatherSyncing(true);
    try {
      const res = await getWeatherData(activeLocation);
      if (res && res.success) {
        setTemperature(Math.round(res.data.temperature || 28));
        setHumidity(Math.round(res.data.humidity || 60));
        setRainfall(Math.round(res.data.rainfall || 0));
      }
    } catch (err) {
      console.error('Weather sync error:', err);
    } finally {
      setWeatherSyncing(false);
    }
  };

  const handleCalculatePlan = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setErrorMsg('');

    try {
      const payload = {
        crop,
        growth_stage: stage,
        soil_type: soilType,
        area: parseFloat(area) || 1,
        area_unit: areaUnit,
        temperature: parseFloat(temperature) || 28,
        humidity: parseFloat(humidity) || 60,
        rainfall: parseFloat(rainfall) || 0,
        location: activeLocation,
        emitter_lph: parseFloat(emitterLph) || 2.0,
        emitter_spacing_m: parseFloat(emitterSpacingM) || 0.4,
        lateral_spacing_m: parseFloat(lateralSpacingM) || 0.8
      };

      const res = await getIrrigationPlan(payload);
      if (res && res.success) {
        setPlanResult(res);
      } else {
        setErrorMsg(res?.error || 'Failed to generate irrigation plan');
      }
    } catch (err) {
      console.error('Irrigation error:', err);
      setErrorMsg(err.response?.data?.error || err.message || 'Error communicating with server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* 1. Header Banner */}
      <div 
        style={{
          background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 50%, #075985 100%)',
          borderRadius: 'var(--radius-xl)',
          padding: '24px 28px',
          color: '#ffffff',
          boxShadow: 'var(--shadow-md)',
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '4px 12px', background: 'rgba(255,255,255,0.18)', borderRadius: '20px', fontSize: '12px', fontWeight: 600, marginBottom: '10px' }}>
            <Droplets size={14} /> Open-Meteo FAO-56 & Hargreaves Solar Evapotranspiration
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 800, margin: '0 0 6px 0', color: '#ffffff' }}>
            💧 Precision Irrigation & Water Planning
          </h2>
          <p style={{ margin: 0, fontSize: '14px', color: '#e0f2fe', maxWidth: '780px', lineHeight: 1.5 }}>
            Calculate exact crop evapotranspiration (ETc), rainfall offsets, and drip vs flood runtime hours customized to your crop growth stage and soil water retention capacity.
          </p>
        </div>
      </div>

      {/* 2. Main 2-Column Grid */}
      <div className="responsive-two-col" style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 400px) minmax(0, 1fr)', gap: '24px', alignItems: 'start' }}>
        
        {/* Left Form: Parameters */}
        <div 
          style={{
            minWidth: 0,
            boxSizing: 'border-box',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-xl)',
            padding: '24px',
            boxShadow: 'var(--shadow-card)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px', paddingBottom: '12px', borderBottom: '1px solid var(--border-subtle)' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={18} color="var(--primary-green)" /> Field & Crop Parameters
            </h3>
            <button
              type="button"
              onClick={handleSyncWeather}
              disabled={weatherSyncing}
              style={{
                background: 'var(--bg-card-subtle)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '4px 10px',
                fontSize: '12px',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
              title="Sync temperature & humidity with live district weather"
            >
              <RefreshCw size={12} className={weatherSyncing ? 'animate-spin' : ''} />
              {weatherSyncing ? 'Syncing...' : 'Sync Weather'}
            </button>
          </div>

          <form onSubmit={handleCalculatePlan} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Crop Select */}
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
                Select Cultivated Crop
              </label>
              <select
                value={crop}
                onChange={(e) => setCrop(e.target.value)}
                style={{
                  width: '100%',
                  minWidth: 0,
                  boxSizing: 'border-box',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-card)',
                  fontSize: '14px',
                  color: 'var(--text-main)'
                }}
              >
                {CROP_OPTIONS.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>

            {/* Growth Stage */}
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
                Phenological Growth Stage
              </label>
              <select
                value={stage}
                onChange={(e) => setStage(e.target.value)}
                style={{
                  width: '100%',
                  minWidth: 0,
                  boxSizing: 'border-box',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-card)',
                  fontSize: '14px',
                  color: 'var(--text-main)'
                }}
              >
                {GROWTH_STAGES.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>

            {/* Soil Type */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                <label style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>
                  Soil Texture (Change soil type)
                </label>
                <span style={{ background: '#fef3c7', color: '#92400e', border: '1px solid #fde68a', padding: '1px 6px', borderRadius: '4px', fontSize: '0.68rem', fontWeight: 700 }}>
                  user-selected
                </span>
              </div>
              <select
                value={soilType}
                onChange={(e) => {
                  const val = e.target.value;
                  setSoilType(val);
                  if (onUpdateSoil) onUpdateSoil(val, null, 'user-selected');
                }}
                style={{
                  width: '100%',
                  maxWidth: '100%',
                  minWidth: 0,
                  boxSizing: 'border-box',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-card)',
                  fontSize: '14px',
                  color: 'var(--text-main)'
                }}
              >
                {SOIL_TYPES.map((st) => (
                  <option key={st.value} value={st.value}>{st.label}</option>
                ))}
              </select>
            </div>

            {/* Farm Area & Unit */}
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
                Cultivated Farm Land Area
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)', gap: '0.75rem' }}>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  value={area}
                  onChange={(e) => {
                    setArea(e.target.value);
                    if (onUpdateFarmArea) onUpdateFarmArea(e.target.value);
                  }}
                  placeholder="2"
                  style={{
                    width: '100%',
                    minWidth: 0,
                    boxSizing: 'border-box',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-color)',
                    fontSize: '14px'
                  }}
                  required
                />
                <select
                  value={areaUnit}
                  onChange={(e) => {
                    setAreaUnit(e.target.value);
                    if (onUpdateFarmAreaUnit) onUpdateFarmAreaUnit(e.target.value);
                  }}
                  style={{
                    width: '100%',
                    maxWidth: '100%',
                    minWidth: 0,
                    boxSizing: 'border-box',
                    overflow: 'hidden',
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-color)',
                    background: 'var(--bg-card)',
                    fontSize: '13px',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}
                >
                  {LAND_UNITS.map((u) => (
                    <option key={u.value} value={u.value}>{u.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Weather Sync Controls */}
            <div style={{ background: 'var(--bg-card-subtle)', borderRadius: 'var(--radius-md)', padding: '12px', border: '1px solid var(--border-subtle)' }}>
              <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: '10px' }}>
                Environmental Parameters ({activeLocation})
              </span>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
                <div>
                  <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>Temp (°C)</label>
                  <input
                    type="number"
                    value={temperature}
                    onChange={(e) => setTemperature(e.target.value)}
                    style={{ width: '100%', minWidth: 0, boxSizing: 'border-box', padding: '6px 8px', fontSize: '13px', borderRadius: '6px', border: '1px solid var(--border-color)' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>Humidity (%)</label>
                  <input
                    type="number"
                    value={humidity}
                    onChange={(e) => setHumidity(e.target.value)}
                    style={{ width: '100%', minWidth: 0, boxSizing: 'border-box', padding: '6px 8px', fontSize: '13px', borderRadius: '6px', border: '1px solid var(--border-color)' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>Rain (mm)</label>
                  <input
                    type="number"
                    value={rainfall}
                    onChange={(e) => setRainfall(e.target.value)}
                    style={{ width: '100%', minWidth: 0, boxSizing: 'border-box', padding: '6px 8px', fontSize: '13px', borderRadius: '6px', border: '1px solid var(--border-color)' }}
                  />
                </div>
              </div>
            </div>

            {/* Optional Hardware Layout Section */}
            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
              <button
                type="button"
                onClick={() => setShowAdvancedDrip(!showAdvancedDrip)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--accent-blue)',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <Settings size={14} /> {showAdvancedDrip ? 'Hide Drip Hardware Specs' : 'Configure Drip Emitter Specs'}
              </button>

              {showAdvancedDrip && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', marginTop: '10px' }}>
                  <div>
                    <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>Emitter LPH</label>
                    <input
                      type="number"
                      step="0.1"
                      value={emitterLph}
                      onChange={(e) => setEmitterLph(e.target.value)}
                      style={{ width: '100%', minWidth: 0, boxSizing: 'border-box', padding: '6px 8px', fontSize: '13px', borderRadius: '6px', border: '1px solid var(--border-color)' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>Spacing (m)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={emitterSpacingM}
                      onChange={(e) => setEmitterSpacingM(e.target.value)}
                      style={{ width: '100%', minWidth: 0, boxSizing: 'border-box', padding: '6px 8px', fontSize: '13px', borderRadius: '6px', border: '1px solid var(--border-color)' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>Lateral (m)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={lateralSpacingM}
                      onChange={(e) => setLateralSpacingM(e.target.value)}
                      style={{ width: '100%', minWidth: 0, boxSizing: 'border-box', padding: '6px 8px', fontSize: '13px', borderRadius: '6px', border: '1px solid var(--border-color)' }}
                    />
                  </div>
                </div>
              )}
            </div>

            {errorMsg && (
              <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', padding: '10px 14px', borderRadius: 'var(--radius-md)', fontSize: '13px', display: 'flex', gap: '8px', alignItems: 'center' }}>
                <AlertCircle size={16} /> {errorMsg}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: '6px',
                background: 'var(--primary-green)',
                color: '#ffffff',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                padding: '13px 20px',
                fontSize: '14px',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                transition: 'background 0.2s'
              }}
            >
              {loading ? (
                <>
                  <RefreshCw size={16} className="animate-spin" /> Computing Hydrology Model...
                </>
              ) : (
                <>
                  <Droplets size={16} /> Compute Irrigation Schedule
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right Content: Hydrological & Irrigation Results */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', minWidth: 0 }}>
          {planResult ? (
            <>
              {/* Method Attribution & Dynamic Status Advisory Banner */}
              <div 
                style={{
                  background: planResult.daily_liters === 0 ? 'var(--accent-blue-light)' : 'var(--primary-green-light)',
                  border: `1px solid ${planResult.daily_liters === 0 ? 'var(--accent-blue)' : 'var(--primary-green-border)'}`,
                  borderRadius: 'var(--radius-xl)',
                  padding: '20px 24px',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '16px'
                }}
              >
                <div 
                  style={{
                    padding: '10px',
                    borderRadius: '12px',
                    background: planResult.daily_liters === 0 ? '#3b82f6' : 'var(--primary-green)',
                    color: '#ffffff',
                    marginTop: '2px'
                  }}
                >
                  <Droplets size={24} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', marginBottom: '4px' }}>
                    <div style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-heading)' }}>
                      {planResult.status}
                    </div>
                    <span style={{ fontSize: '11px', fontWeight: 700, background: '#ffffff', color: '#0369a1', padding: '2px 8px', borderRadius: '12px', border: '1px solid #bae6fd' }}>
                      {planResult.et0_method === 'open-meteo-fao56' ? '🛰️ Open-Meteo FAO-56' : '☀️ Hargreaves Solar (FAO-56 Eq. 21)'}
                    </span>
                  </div>
                  <div style={{ fontSize: '14px', color: 'var(--text-main)', lineHeight: 1.5 }}>
                    {planResult.advisory}
                  </div>
                </div>
              </div>

              {/* 4 Stat Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
                {/* 1. Daily Volume */}
                <div 
                  style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '18px 20px',
                    boxShadow: 'var(--shadow-card)'
                  }}
                >
                  <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Net Crop Water Demand
                  </span>
                  <div style={{ fontSize: '26px', fontWeight: 800, color: 'var(--primary-green)', margin: '6px 0 2px 0' }}>
                    {planResult.daily_liters.toLocaleString()} <span style={{ fontSize: '15px', fontWeight: 600 }}>L / day</span>
                  </div>
                  <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                    For {planResult.area_acres} Acres ({planResult.area_hectares} ha)
                  </span>
                </div>

                {/* 2. Net Water Depth */}
                <div 
                  style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '18px 20px',
                    boxShadow: 'var(--shadow-card)'
                  }}
                >
                  <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Crop Water Need (ETc)
                  </span>
                  <div style={{ fontSize: '26px', fontWeight: 800, color: '#0284c7', margin: '6px 0 2px 0' }}>
                    {planResult.crop_water_need_mm} <span style={{ fontSize: '15px', fontWeight: 600 }}>mm / day</span>
                  </div>
                  <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                    Rain Offset: {planResult.effective_rain_offset_mm} mm (Net: {planResult.net_irrigation_depth_mm} mm)
                  </span>
                </div>

                {/* 3. Drip Runtime */}
                <div 
                  style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '18px 20px',
                    boxShadow: 'var(--shadow-card)'
                  }}
                >
                  <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Drip Runtime (90% Eff)
                  </span>
                  <div style={{ fontSize: '26px', fontWeight: 800, color: '#f59e0b', margin: '6px 0 2px 0' }}>
                    {planResult.drip_runtime_hours} <span style={{ fontSize: '15px', fontWeight: 600 }}>Hours</span>
                  </div>
                  <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                    Application: {planResult.application_rate_mm_hr} mm/hr
                  </span>
                </div>

                {/* 4. Crop Factor Kc */}
                <div 
                  style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '18px 20px',
                    boxShadow: 'var(--shadow-card)'
                  }}
                >
                  <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Crop Factor Kc ({planResult.kc_source || 'FAO-56'})
                  </span>
                  <div style={{ fontSize: '26px', fontWeight: 800, color: '#8b5cf6', margin: '6px 0 2px 0' }}>
                    {planResult.crop_coefficient_kc}
                  </div>
                  <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                    Reference ET₀: {planResult.reference_et0_mm} mm/day
                  </span>
                </div>
              </div>
            </>
          ) : (
            <div 
              style={{
                background: 'var(--bg-card)',
                border: '1px dashed var(--border-color)',
                borderRadius: 'var(--radius-xl)',
                padding: '48px 24px',
                textAlign: 'center',
                color: 'var(--text-muted)'
              }}
            >
              <Droplets size={44} style={{ margin: '0 auto 12px auto', opacity: 0.5 }} />
              <h4 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                Configure Your Parameters
              </h4>
              <p style={{ fontSize: '13px', maxWidth: '380px', margin: '0 auto' }}>
                Select your crop, growth stage, soil type, and field dimensions to generate the precision irrigation schedule.
              </p>
            </div>
          )}
        </div>

      </div>

      {/* 3. Full-Width Deep-Dive Sections (Entire Page Fitting on Scroll) */}
      {planResult && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', marginTop: '24px', width: '100%' }}>
          {/* Drip vs Flood Efficiency Comparison Card */}
          <div 
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-xl)',
              padding: '22px 24px',
              boxShadow: 'var(--shadow-card)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Droplets size={18} color="#0284c7" /> Drip vs Surface Flood Irrigation Comparison
              </h3>
              <span style={{ fontSize: '12px', fontWeight: 700, color: '#16a34a', background: '#dcfce7', padding: '3px 10px', borderRadius: '12px' }}>
                Saves {((planResult.gross_flood_liters || 0) - (planResult.gross_drip_liters || 0)).toLocaleString()} Liters / day
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
              {/* Drip Option */}
              <div style={{ background: '#f0fdf4', border: '1.5px solid #86efac', borderRadius: '12px', padding: '14px 16px' }}>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#166534', textTransform: 'uppercase' }}>
                  💧 Precision Drip (90% Eff)
                </div>
                <div style={{ fontSize: '22px', fontWeight: 800, color: '#15803d', margin: '4px 0 2px 0' }}>
                  {(planResult.gross_drip_liters || 0).toLocaleString()} <span style={{ fontSize: '13px' }}>L</span>
                </div>
                <div style={{ fontSize: '12px', color: '#166534' }}>
                  Runtime: <strong>{planResult.drip_runtime_hours} hrs</strong> (Low evaporation)
                </div>
              </div>

              {/* Sprinkler Option */}
              <div style={{ background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: '12px', padding: '14px 16px' }}>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#0369a1', textTransform: 'uppercase' }}>
                  🌧️ Sprinkler (75% Eff)
                </div>
                <div style={{ fontSize: '22px', fontWeight: 800, color: '#0284c7', margin: '4px 0 2px 0' }}>
                  {(planResult.gross_sprinkler_liters || 0).toLocaleString()} <span style={{ fontSize: '13px' }}>L</span>
                </div>
                <div style={{ fontSize: '12px', color: '#0369a1' }}>
                  Moderate distribution loss
                </div>
              </div>

              {/* Flood Option */}
              <div style={{ background: '#fff7ed', border: '1px solid #fed7aa', borderRadius: '12px', padding: '14px 16px' }}>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#c2410c', textTransform: 'uppercase' }}>
                  🌊 Surface Furrow / Flood (60% Eff)
                </div>
                <div style={{ fontSize: '22px', fontWeight: 800, color: '#ea580c', margin: '4px 0 2px 0' }}>
                  {(planResult.gross_flood_liters || 0).toLocaleString()} <span style={{ fontSize: '13px' }}>L</span>
                </div>
                <div style={{ fontSize: '12px', color: '#c2410c' }}>
                  Tubewell 5HP: <strong>{planResult.flood_runtime_hours} hrs</strong> (High percolation)
                </div>
              </div>
            </div>
          </div>

          {/* Soil Water Balance & Irrigation Interval Card */}
          {planResult.soil_water_balance && (
            <div 
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-xl)',
                padding: '20px 24px',
                boxShadow: 'var(--shadow-card)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '16px'
              }}
            >
              <div>
                <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Soil Water Holding Capacity & Stress Threshold
                </span>
                <div style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-heading)', marginTop: '2px' }}>
                  Irrigate Every ~{planResult.soil_water_balance.irrigation_interval_days} Days
                </div>
                <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Root Depth: {planResult.soil_water_balance.rooting_depth_m}m | RAW: {planResult.soil_water_balance.raw_mm} mm before crop moisture stress occurs.
                </div>
              </div>
              <span style={{ fontSize: '11px', fontWeight: 700, background: '#f8fafc', border: '1px solid #e2e8f0', padding: '4px 10px', borderRadius: '8px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>Soil Adjustment: {planResult.soil_adjustment}</span>
                <span style={{ background: '#fef3c7', color: '#92400e', border: '1px solid #fde68a', padding: '1px 6px', borderRadius: '4px', fontSize: '0.65rem' }}>
                  user-selected
                </span>
              </span>
            </div>
          )}

          {/* 7-Day Actual Forecast Schedule Table */}
          <div 
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-xl)',
              padding: '24px',
              boxShadow: 'var(--shadow-card)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Calendar size={18} color="#0284c7" /> 7-Day Projected Irrigation Schedule
              </h3>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)', background: 'var(--bg-card-subtle)', padding: '4px 10px', borderRadius: '6px' }}>
                Calculated from daily meteorological forecast
              </span>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Schedule Day</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>ET₀ (mm)</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Rain (mm)</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Net Depth</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Drip Volume (90%)</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Runtime</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {planResult.weekly_schedule?.map((day, idx) => (
                    <tr 
                      key={day.day + idx}
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        background: idx === 0 ? 'var(--primary-green-light)' : 'transparent',
                        fontWeight: idx === 0 ? 700 : 400
                      }}
                    >
                      <td style={{ padding: '12px', color: idx === 0 ? 'var(--primary-green)' : 'var(--text-heading)' }}>
                        {day.day} {idx === 0 && '⚡'}
                      </td>
                      <td style={{ padding: '12px' }}>{day.reference_et0_mm} mm</td>
                      <td style={{ padding: '12px' }}>{day.rainfall_mm} mm</td>
                      <td style={{ padding: '12px' }}>{day.water_depth_mm} mm</td>
                      <td style={{ padding: '12px', fontWeight: 600 }}>{day.liters.toLocaleString()} L</td>
                      <td style={{ padding: '12px' }}>{day.runtime_hours} hrs</td>
                      <td style={{ padding: '12px' }}>
                        <span 
                          style={{
                            fontSize: '11px',
                            fontWeight: 700,
                            padding: '2px 8px',
                            borderRadius: '12px',
                            background: day.status?.includes('Skip') ? '#fef3c7' : '#dcfce7',
                            color: day.status?.includes('Skip') ? '#92400e' : '#166534'
                          }}
                        >
                          {day.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
