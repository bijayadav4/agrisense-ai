import React, { useState, useEffect } from 'react';
import { 
  Calendar, 
  Clock, 
  Sprout, 
  TrendingUp, 
  CheckCircle2, 
  AlertCircle, 
  AlertTriangle,
  DollarSign, 
  Package, 
  Sparkles, 
  Layers, 
  ArrowRight,
  ShieldCheck,
  CalendarDays,
  Info,
  Sliders,
  HelpCircle
} from 'lucide-react';
import { getHarvestPrediction } from '../services/api';

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
  { value: 'apple', label: '🍏 Apple' },
  { value: 'orange', label: '🍊 Orange' },
  { value: 'papaya', label: '🪴 Papaya' },
  { value: 'coconut', label: '🥥 Coconut' },
  { value: 'jute', label: '🌿 Jute' },
  { value: 'coffee', label: '☕ Coffee' },
  { value: 'chilli', label: '🌶️ Chilli' }
];

const LAND_UNITS = [
  { value: 'acres', label: 'Acres' },
  { value: 'cents', label: 'Cents (100 Cents = 1 Acre)' },
  { value: 'gunthas', label: 'Gunthas (40 Gunthas = 1 Acre)' },
  { value: 'hectares', label: 'Hectares' }
];

export default function HarvestView({ 
  initialCrop = 'rice',
  farmArea = 2,
  farmAreaUnit = 'acres',
  harvestInfo,
  onUpdateHarvestInfo,
  onUpdateFarmArea,
  onUpdateFarmAreaUnit
}) {
  // Default sowing date: 45 days ago for realistic active progression
  const defaultSowingDate = () => {
    const d = new Date();
    d.setDate(d.getDate() - 45);
    return d.toISOString().split('T')[0];
  };

  const [crop, setCrop] = useState(initialCrop || 'rice');
  const [sowingDate, setSowingDate] = useState(defaultSowingDate());
  const [area, setArea] = useState(farmArea);
  const [areaUnit, setAreaUnit] = useState(farmAreaUnit);
  const [varietyDurationDays, setVarietyDurationDays] = useState('');

  const [loading, setLoading] = useState(false);
  const [harvestResult, setHarvestResult] = useState(harvestInfo);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (farmArea) setArea(farmArea);
  }, [farmArea]);

  useEffect(() => {
    if (farmAreaUnit) setAreaUnit(farmAreaUnit);
  }, [farmAreaUnit]);

  useEffect(() => {
    if (harvestInfo) setHarvestResult(harvestInfo);
  }, [harvestInfo]);

  useEffect(() => {
    if (!harvestInfo) {
      handlePredictHarvest();
    }
  }, []);

  const handlePredictHarvest = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setErrorMsg('');

    try {
      const payload = {
        crop,
        sowing_date: sowingDate,
        area: parseFloat(area) || 1,
        area_unit: areaUnit
      };

      if (varietyDurationDays && parseInt(varietyDurationDays, 10) > 0) {
        payload.variety_duration_days = parseInt(varietyDurationDays, 10);
      }

      const res = await getHarvestPrediction(payload);
      if (res && res.success) {
        setHarvestResult(res);
        if (onUpdateHarvestInfo) onUpdateHarvestInfo(res);
      } else {
        setErrorMsg(res?.error || 'Failed to predict harvest timeline');
      }
    } catch (err) {
      console.error('Harvest predict error:', err);
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
          background: 'linear-gradient(135deg, #15803d 0%, #166534 50%, #14532d 100%)',
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
            <CalendarDays size={14} /> Phenological Life-Cycle & Harvest Yield Engine
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 800, margin: '0 0 6px 0', color: '#ffffff' }}>
            📅 Harvest Prediction & Phenological Timeline
          </h2>
          <p style={{ margin: 0, fontSize: '14px', color: '#dcfce7', maxWidth: '780px', lineHeight: 1.5 }}>
            Track crop biological growth stages in real-time, get exact harvest readiness countdowns, and predict total farm yields with Low / Expected / High scenario ranges.
          </p>
        </div>
      </div>

      {/* 2. Main 2-Column Grid */}
      <div className="responsive-two-col" style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 400px) minmax(0, 1fr)', gap: '24px', alignItems: 'start' }}>
        
        {/* Left Form: Sowing Date & Land */}
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
          <div style={{ marginBottom: '18px', paddingBottom: '12px', borderBottom: '1px solid var(--border-subtle)' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sprout size={18} color="var(--primary-green)" /> Crop Sowing Information
            </h3>
          </div>

          <form onSubmit={handlePredictHarvest} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
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

            {/* Sowing Date */}
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
                Crop Sowing / Transplant Date
              </label>
              <input
                type="date"
                value={sowingDate}
                onChange={(e) => setSowingDate(e.target.value)}
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
                required
              />
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                Pick past planting date or future date for upcoming scheduled sowing
              </span>
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

            {/* Optional Variety Duration */}
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
                Custom Variety Duration (Optional)
              </label>
              <input
                type="number"
                min="30"
                max="450"
                value={varietyDurationDays}
                onChange={(e) => setVarietyDurationDays(e.target.value)}
                placeholder="e.g. 110 (Default: Crop average)"
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
              />
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                Specify days if planting an early or late maturity seed hybrid
              </span>
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
                <>Computing Life Cycle...</>
              ) : (
                <>
                  <Calendar size={16} /> Predict Harvest & Yield
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right Content: Timeline & Yield Cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', minWidth: 0 }}>
          {harvestResult ? (
            <>
              {/* Status Banner (Upcoming / Overdue / Active) */}
              {harvestResult.status === 'Upcoming' && (
                <div 
                  style={{
                    background: '#eff6ff',
                    border: '1px solid #bfdbfe',
                    borderRadius: 'var(--radius-xl)',
                    padding: '20px 24px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '16px'
                  }}
                >
                  <div style={{ background: '#3b82f6', color: '#ffffff', padding: '10px', borderRadius: '50%' }}>
                    <Calendar size={24} />
                  </div>
                  <div>
                    <div style={{ fontSize: '18px', fontWeight: 800, color: '#1e40af' }}>
                      🌱 {harvestResult.starts_in_message || `Starts in ${harvestResult.days_until_sowing} days`}
                    </div>
                    <div style={{ fontSize: '13px', color: '#1e3a8a', marginTop: '2px' }}>
                      Sowing scheduled for <strong>{harvestResult.sowing_date}</strong>. Growth timeline will activate once sowing date commences.
                    </div>
                  </div>
                </div>
              )}

              {harvestResult.status === 'Overdue' && (
                <div 
                  style={{
                    background: '#fff1f2',
                    border: '1px solid #fecdd3',
                    borderRadius: 'var(--radius-xl)',
                    padding: '20px 24px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '16px'
                  }}
                >
                  <div style={{ background: '#e11d48', color: '#ffffff', padding: '10px', borderRadius: '50%' }}>
                    <AlertTriangle size={24} />
                  </div>
                  <div>
                    <div style={{ fontSize: '18px', fontWeight: 800, color: '#9f1239' }}>
                      ⚠️ Harvest Overdue by {harvestResult.days_overdue} Days!
                    </div>
                    <div style={{ fontSize: '13px', color: '#881337', marginTop: '2px' }}>
                      Maturity cycle concluded on <strong>{harvestResult.harvest_date_formatted}</strong>. Immediate harvest recommended to avoid pod shattering, lodging, or field grain spoilage.
                    </div>
                  </div>
                </div>
              )}

              {/* Warnings Banner (e.g. > 1.5x cycle) */}
              {harvestResult.warning && (
                <div style={{ background: '#fffbeb', border: '1px solid #fde68a', color: '#92400e', padding: '12px 18px', borderRadius: 'var(--radius-lg)', fontSize: '13px', display: 'flex', gap: '10px', alignItems: 'center' }}>
                  <AlertCircle size={18} style={{ flexShrink: 0 }} />
                  <span>{harvestResult.warning}</span>
                </div>
              )}

              {/* Perennial Notice */}
              {harvestResult.indicative_only && (
                <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534', padding: '12px 18px', borderRadius: 'var(--radius-lg)', fontSize: '13px', display: 'flex', gap: '10px', alignItems: 'center' }}>
                  <Info size={18} style={{ flexShrink: 0 }} />
                  <div>
                    <strong>Perennial Orchard Crop Notice:</strong> Timeline and yields reflect indicative annual fruiting/bearing benchmarks rather than initial seedling establishment.
                  </div>
                </div>
              )}

              {/* Maturity Countdown Banner */}
              <div 
                style={{
                  background: harvestResult.status === 'Upcoming' ? '#f8fafc' : (harvestResult.is_harvest_ready ? 'var(--accent-amber-light)' : 'var(--primary-green-light)'),
                  border: `1px solid ${harvestResult.status === 'Upcoming' ? '#cbd5e1' : (harvestResult.is_harvest_ready ? 'var(--accent-amber)' : 'var(--primary-green-border)')}`,
                  borderRadius: 'var(--radius-xl)',
                  padding: '22px 26px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '16px'
                }}
              >
                <div>
                  <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Crop Maturity Status: <strong>{harvestResult.status}</strong>
                  </span>
                  <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text-heading)', marginTop: '2px' }}>
                    {harvestResult.status === 'Upcoming' 
                      ? `⏳ Starts in ${harvestResult.days_until_sowing} Days` 
                      : (harvestResult.status === 'Overdue' 
                          ? `⚠️ ${harvestResult.days_overdue} Days Overdue`
                          : (harvestResult.is_harvest_ready ? '🎉 Ready for Harvest!' : `⏳ ${harvestResult.days_remaining} Days Remaining`))}
                  </div>
                  <div style={{ fontSize: '13px', color: 'var(--text-main)', marginTop: '4px' }}>
                    Expected Harvest Date: <strong>{harvestResult.harvest_date_formatted}</strong> (Cycle: {harvestResult.total_duration_days} Days)
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '32px', fontWeight: 800, color: 'var(--primary-green)' }}>
                    {harvestResult.progress_percentage}%
                  </div>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>
                    {harvestResult.days_elapsed > 0 ? `${harvestResult.days_elapsed} of ${harvestResult.total_duration_days} Days Elapsed` : `Sowing pending (${Math.abs(harvestResult.days_elapsed)}d)`}
                  </span>
                </div>

                {/* Progress bar */}
                <div style={{ width: '100%', height: '8px', background: 'rgba(0,0,0,0.08)', borderRadius: '4px', overflow: 'hidden', marginTop: '6px' }}>
                  <div 
                    style={{ 
                      width: `${harvestResult.progress_percentage}%`, 
                      height: '100%', 
                      background: harvestResult.status === 'Overdue' ? '#e11d48' : 'var(--primary-green)',
                      borderRadius: '4px',
                      transition: 'width 0.6s cubic-bezier(0.4, 0, 0.2, 1)'
                    }} 
                  />
                </div>
              </div>

              {/* Yield Range & Financial Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
                {/* 1. Total Quintals with Range */}
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
                    Expected Crop Yield
                  </span>
                  <div style={{ fontSize: '26px', fontWeight: 800, color: 'var(--primary-green)', margin: '6px 0 2px 0' }}>
                    {harvestResult.yield_prediction.total_expected_quintals} <span style={{ fontSize: '15px', fontWeight: 600 }}>Quintals</span>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-main)', marginTop: '4px', fontWeight: 600 }}>
                    Range: {harvestResult.yield_prediction.yield_quintals?.low} – {harvestResult.yield_prediction.yield_quintals?.high} Q
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
                    Base: {harvestResult.yield_prediction.baseline_yield_per_hectare_q} Q/ha
                  </span>
                </div>

                {/* 2. Total 50kg Farmer Bags with Range */}
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
                    Bags Count (50 kg)
                  </span>
                  <div style={{ fontSize: '26px', fontWeight: 800, color: '#0284c7', margin: '6px 0 2px 0' }}>
                    {harvestResult.yield_prediction.total_50kg_bags} <span style={{ fontSize: '15px', fontWeight: 600 }}>Bags</span>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-main)', marginTop: '4px', fontWeight: 600 }}>
                    Range: {harvestResult.yield_prediction.bags_50kg?.low} – {harvestResult.yield_prediction.bags_50kg?.high} Bags
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
                    Standard farm transport sacks
                  </span>
                </div>

                {/* 3. Reference MSP / Market Rate */}
                <div 
                  style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '18px 20px',
                    boxShadow: 'var(--shadow-card)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      Govt. MSP Benchmark
                    </span>
                    <span style={{ fontSize: '10px', fontWeight: 700, background: '#fef3c7', color: '#92400e', padding: '2px 6px', borderRadius: '8px' }}>
                      {harvestResult.msp_info?.year || '2024-25'}
                    </span>
                  </div>
                  <div style={{ fontSize: '26px', fontWeight: 800, color: '#f59e0b', margin: '6px 0 2px 0' }}>
                    ₹{harvestResult.yield_prediction.reference_msp_rate_q?.toLocaleString()} <span style={{ fontSize: '14px', fontWeight: 600 }}>/ Q</span>
                  </div>
                  <span style={{ fontSize: '12px', color: 'var(--text-dim)', display: 'block' }}>
                    {harvestResult.msp_info?.type === 'official_msp' ? 'Official CACP benchmark' : 'Agmarknet market estimate'}
                  </span>
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                    Status: {harvestResult.msp_info?.verification_status || 'UNVERIFIED'}
                  </span>
                </div>

                {/* 4. Est Gross Revenue with Range */}
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
                    Est. Gross Revenue
                  </span>
                  <div style={{ fontSize: '26px', fontWeight: 800, color: '#16a34a', margin: '6px 0 2px 0' }}>
                    ₹{harvestResult.yield_prediction.estimated_gross_revenue_rs?.toLocaleString()}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-main)', marginTop: '4px', fontWeight: 600 }}>
                    Range: ₹{harvestResult.yield_prediction.gross_revenue_rs?.low?.toLocaleString()} – ₹{harvestResult.yield_prediction.gross_revenue_rs?.high?.toLocaleString()}
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
                    Valuation at baseline rates
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
              <Calendar size={44} style={{ margin: '0 auto 12px auto', opacity: 0.5 }} />
              <h4 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                Enter Sowing Information
              </h4>
              <p style={{ fontSize: '13px', maxWidth: '380px', margin: '0 auto' }}>
                Set your crop and planting date to predict harvest maturity and expected farm yields.
              </p>
            </div>
          )}
        </div>

      </div>

      {/* 3. Full-Width Timeline & Agronomy (Entire Page Fitting on Scroll) */}
      {harvestResult && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', marginTop: '24px', width: '100%' }}>
          {/* Yield Card Disclaimer & Source */}
          <div 
            style={{
              background: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: 'var(--radius-lg)',
              padding: '12px 18px',
              display: 'flex',
              alignItems: 'flex-start',
              justifyContent: 'space-between',
              gap: '12px',
              flexWrap: 'wrap',
              fontSize: '12px',
              color: 'var(--text-muted)'
            }}
          >
            <div>
              ⚠️ <strong>Disclaimer:</strong> {harvestResult.yield_prediction.disclaimer || "Indicative estimate. Actual yield depends on variety, weather, pests and management."}
            </div>
            <div>
              📚 <strong>Benchmark:</strong> {harvestResult.yield_prediction.baseline_yield_source || "ICAR Research Benchmark"}
            </div>
          </div>

          {/* 5 Phenological Stages Timeline Stepper */}
          <div 
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-xl)',
              padding: '24px',
              boxShadow: 'var(--shadow-card)'
            }}
          >
            <div style={{ marginBottom: '18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Layers size={18} color="var(--primary-green)" /> 5 Phenological Growth Stages & Field Agronomy
              </h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {harvestResult.stage_source === 'generic' ? (
                  <span 
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      padding: '3px 10px',
                      borderRadius: '12px',
                      background: '#fef3c7',
                      color: '#92400e',
                      border: '1px solid #fde68a'
                    }}
                  >
                    Approximate (Generic Phenology)
                  </span>
                ) : (
                  <span 
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      padding: '3px 10px',
                      borderRadius: '12px',
                      background: '#dcfce7',
                      color: '#166534',
                      border: '1px solid #bbf7d0'
                    }}
                  >
                    Crop-Specific Benchmark
                  </span>
                )}
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {harvestResult.stages_timeline?.map((st, idx) => {
                const isCompleted = st.status === 'Completed';
                const isActive = st.status === 'Active';
                const isUpcoming = st.status === 'Upcoming';

                let circleBg = 'var(--border-color)';
                let circleColor = 'var(--text-muted)';
                let cardBg = 'transparent';
                let cardBorder = 'var(--border-subtle)';

                if (isCompleted) {
                  circleBg = 'var(--primary-green)';
                  circleColor = '#ffffff';
                  cardBg = 'var(--bg-card-subtle)';
                } else if (isActive) {
                  circleBg = '#0284c7';
                  circleColor = '#ffffff';
                  cardBg = 'var(--primary-green-light)';
                  cardBorder = 'var(--primary-green-border)';
                } else {
                  circleBg = '#cbd5e1';
                  circleColor = '#64748b';
                }

                return (
                  <div 
                    key={st.stage}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '14px',
                      padding: '14px 16px',
                      borderRadius: 'var(--radius-md)',
                      background: cardBg,
                      border: `1px solid ${cardBorder}`,
                      position: 'relative'
                    }}
                  >
                    {/* Step indicator circle */}
                    <div 
                      style={{
                        width: '28px',
                        height: '28px',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 700,
                        fontSize: '12px',
                        background: circleBg,
                        color: circleColor,
                        flexShrink: 0,
                        marginTop: '2px'
                      }}
                    >
                      {isCompleted ? <CheckCircle2 size={16} /> : (idx + 1)}
                    </div>

                    {/* Content */}
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', flexWrap: 'wrap' }}>
                        <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-heading)' }}>
                          {st.stage}
                        </span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                            {st.day_range}
                          </span>
                          <span 
                            style={{
                              fontSize: '11px',
                              fontWeight: 700,
                              padding: '2px 8px',
                              borderRadius: '12px',
                              background: isCompleted ? '#dcfce7' : (isActive ? '#e0f2fe' : '#f1f5f9'),
                              color: isCompleted ? '#166534' : (isActive ? '#0369a1' : '#64748b')
                            }}
                          >
                            {st.status}
                          </span>
                        </div>
                      </div>
                      <div style={{ fontSize: '12.5px', color: 'var(--text-muted)', marginTop: '4px', lineHeight: 1.4 }}>
                        💡 {st.tip}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Harvest Readiness Checklist */}
          <div 
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-xl)',
              padding: '20px 24px',
              boxShadow: 'var(--shadow-card)'
            }}
          >
            <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-heading)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldCheck size={18} color="var(--primary-green)" /> Field Readiness Protocol Before Harvesting
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' }}>
              {harvestResult.harvest_readiness_checklist?.map((item, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', fontSize: '13px', color: 'var(--text-main)', lineHeight: 1.4 }}>
                  <CheckCircle2 size={16} color="var(--primary-green)" style={{ flexShrink: 0, marginTop: '2px' }} />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
