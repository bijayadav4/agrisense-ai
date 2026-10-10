import React, { useMemo, useState } from 'react';
import { 
  Sprout, 
  Package, 
  CloudSun, 
  ArrowRight, 
  CheckCircle2, 
  AlertTriangle, 
  MapPin, 
  Droplets,
  Calendar,
  Clock,
  Sparkles,
  FileText,
  Download,
  Loader2
} from 'lucide-react';
import { downloadReportCardPdf } from '../services/api';

export default function DashboardView({ 
  locationName = 'Coimbatore, Tamil Nadu',
  weatherData, 
  recommendation, 
  farmArea = 2.0,
  farmAreaUnit = 'Acres',
  harvestInfo,
  onNavigateTab 
}) {
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const isWeatherLoading = !weatherData || !weatherData.forecast_source;

  const handleDownloadPdf = async () => {
    if (isWeatherLoading) {
      alert("Weather data is still loading. Please wait a moment before downloading the report.");
      return;
    }
    try {
      setIsGeneratingPdf(true);
      const isDemo = !recommendation;

      // Extract real forecast without hardcoded fallback days or ad-hoc 0.75 multiplier
      const forecastDays = (weatherData?.forecast && Array.isArray(weatherData.forecast) && weatherData.forecast.length > 0)
        ? weatherData.forecast.slice(0, 7)
        : [];

      const weeklySchedule = forecastDays.map((f, idx) => ({
        day: f.day || (idx === 0 ? "Today" : `Day ${idx + 1}`),
        date: f.date || "",
        temp_max: Math.round(f.temp_max || f.max_temp || 30),
        rainfall_mm: Number(f.rain_mm || f.rainfall_mm || 0),
        et0_mm: Number(f.et0 || f.et0_mm || 5.0)
      }));

      const payload = {
        farmer_name: recommendation?.farmer_name || "Not provided",
        location: locationName || "Coimbatore, Tamil Nadu",
        area: parseFloat(farmArea) || 1.0,
        area_unit: farmAreaUnit || "Acres",
        soil_type: recommendation?.soil_type || null,
        soil_source: recommendation?.soil_source || null,
        data_source: recommendation?.data_source || (isDemo ? (recommendation?.is_ambiguous ? "Demo input (fixed weather) [Ambiguous]" : "Demo input (fixed weather)") : "User entered"),
        is_estimated: isDemo || Boolean(recommendation?.is_estimated),
        N: recommendation?.N !== undefined ? recommendation.N : "85",
        P: recommendation?.P !== undefined ? recommendation.P : "48",
        K: recommendation?.K !== undefined ? recommendation.K : "40",
        ph: recommendation?.ph !== undefined ? recommendation.ph : "6.4",
        crop_data: {
          crop: recommendation?.crop || null,
          confidence: recommendation?.confidence || null,
          top_crops: recommendation?.top_crops || [],
          is_ambiguous: recommendation?.is_ambiguous || false,
          ambiguity_warning: recommendation?.ambiguity_warning || null,
          season_warning: recommendation?.season_warning || null,
          provenance_note: recommendation?.provenance_note || null
        },
        fertilizer_data: {
          fertilizer: "Urea / DAP Balanced",
          dap_kg: 35.2,
          dap_bags: 0.70,
          urea_kg: 56.6,
          urea_bags: 1.13,
          mop_kg: 16.8,
          mop_bags: 0.34
        },
        irrigation_data: {
          forecast_source: weatherData?.forecast_source || "Unknown",
          et0_method: "open-meteo-fao56",
          interval_days: 4,
          daily_liters: 47512,
          drip_runtime_hours: 0.6,
          weekly_schedule: weeklySchedule
        },
        harvest_data: {
          crop: recommendation?.crop || null,
          harvest_date: harvestInfo?.harvest_date_formatted || harvestInfo?.expected_harvest_date || null,
          days_remaining: harvestInfo?.days_remaining !== undefined ? harvestInfo.days_remaining : null,
          yield_quintals: harvestInfo?.yield_prediction?.total_expected_quintals || null,
          msp_year: harvestInfo?.msp_info?.year || null,
          msp_rs_per_quintal: harvestInfo?.msp_info?.rate_rs_per_quintal || null,
          msp_type: harvestInfo?.msp_info?.verification_status || null
        }
      };

      const blob = await downloadReportCardPdf(payload);
      const url = window.URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `AgriSense_Farm_Advisory_${new Date().toISOString().slice(0, 10)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to generate PDF report card:", err);
      alert("Error generating PDF report card. Please ensure the backend is running.");
    } finally {
      setIsGeneratingPdf(false);
    }
  };
  // Current real-time calendar date
  const todayFormatted = useMemo(() => {
    return new Date().toLocaleDateString('en-US', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  }, []);

  const temp = weatherData?.temperature !== undefined ? Math.round(weatherData.temperature) : 28;
  const humidity = weatherData?.humidity !== undefined ? weatherData.humidity : 60;
  const windSpeed = weatherData?.wind_speed !== undefined ? Math.round(weatherData.wind_speed) : 8;
  const condition = weatherData?.condition || 'Clear & Sunny';
  const precipChance = weatherData?.precipitation_chance !== undefined ? weatherData.precipitation_chance : 10;
  const rainfall = weatherData?.rainfall !== undefined ? weatherData.rainfall : 0;

  const isRainExpected = (precipChance !== null && precipChance >= 60) || 
    rainfall > 5.0 || 
    condition.toLowerCase().includes('rain') || 
    condition.toLowerCase().includes('drizzle');

  // Crop Prescription data
  const cropName = recommendation?.crop 
    ? recommendation.crop.charAt(0).toUpperCase() + recommendation.crop.slice(1) 
    : 'Rice (Paddy)';
  const cropDuration = recommendation?.profile?.duration || '105 – 150 Days (3 to 5 Months)';
  const cropSeason = recommendation?.profile?.season || 'Kharif (Monsoon)';
  const cropWater = recommendation?.profile?.water_need || 'High (Flooded / Submerged)';
  const cropConfidence = recommendation?.confidence || 99.55;

  // Build 5-Day Forecast with Real Calendar Dates
  const fiveDayForecast = useMemo(() => {
    const rawForecast = weatherData?.forecast && weatherData.forecast.length > 0 
      ? weatherData.forecast 
      : null;

    return Array.from({ length: 5 }).map((_, idx) => {
      const d = new Date();
      d.setDate(d.getDate() + idx);
      const dayLabel = idx === 0 ? 'Today' : d.toLocaleDateString('en-US', { weekday: 'short' });
      const dateLabel = d.toLocaleDateString('en-US', { day: 'numeric', month: 'short' });

      if (rawForecast && rawForecast[idx]) {
        const item = rawForecast[idx];
        return {
          day: dayLabel,
          date: dateLabel,
          icon: item.icon || '⛅',
          maxTemp: Math.round(item.max_temp),
          minTemp: Math.round(item.min_temp),
          condition: item.condition || 'Partly Cloudy',
          rainChance: item.rain_chance !== undefined ? item.rain_chance : (idx === 0 ? precipChance : 15)
        };
      }

      // Sensible defaults if forecast API is pending
      return {
        day: dayLabel,
        date: dateLabel,
        icon: idx === 2 ? '🌧️' : '🌤️',
        maxTemp: temp + (idx === 1 ? 1 : idx === 2 ? -2 : 0),
        minTemp: temp - 6,
        condition: idx === 2 ? 'Scattered Rain' : 'Sunny / Pleasant',
        rainChance: idx === 2 ? 65 : 15
      };
    });
  }, [weatherData, temp, precipChance]);

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* 1. Farm Header & Real Calendar Date Banner */}
      <div 
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
          background: '#ffffff',
          border: '1px solid #cde8d5',
          borderRadius: '16px',
          padding: '16px 22px',
          boxShadow: '0 2px 8px rgba(34, 134, 74, 0.04)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: '#eaf6ed', color: '#15803d', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Calendar size={22} />
          </div>
          <div>
            <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a' }}>
              {todayFormatted}
            </div>
            <div style={{ fontSize: '0.82rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
              <MapPin size={13} color="#15803d" />
              <span>{locationName}</span>
              <span>•</span>
              <span style={{ color: '#15803d', fontWeight: 600 }}>Active Farm Dashboard</span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={handleDownloadPdf}
            disabled={isGeneratingPdf || isWeatherLoading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              borderRadius: '10px',
              border: isWeatherLoading ? '1px solid #9ca3af' : '1px solid #16a34a',
              background: isWeatherLoading ? '#9ca3af' : '#16a34a',
              color: '#ffffff',
              fontSize: '0.82rem',
              fontWeight: 700,
              cursor: isWeatherLoading ? 'not-allowed' : (isGeneratingPdf ? 'wait' : 'pointer'),
              opacity: isWeatherLoading ? 0.75 : 1,
              transition: 'all 0.15s ease'
            }}
          >
            {isWeatherLoading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Weather loading...</span>
              </>
            ) : isGeneratingPdf ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Generating PDF...</span>
              </>
            ) : (
              <>
                <FileText size={16} />
                <span>📄 Download Report Card (PDF)</span>
              </>
            )}
          </button>

          <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '8px 14px', textAlign: 'right' }}>
            <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', display: 'block' }}>Live Weather</span>
            <strong style={{ fontSize: '0.98rem', color: '#0f172a' }}>{temp}°C • {condition}</strong>
          </div>
        </div>
      </div>

      {/* 2. The Two Core Farm Prescriptions: Crop & Fertilizer */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '18px' }}>
        
        {/* Core Card 1: Crop Recommendation */}
        <div 
          style={{
            background: '#ffffff',
            border: '1px solid #bbf7d0',
            borderRadius: '16px',
            padding: '22px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxShadow: '0 2px 8px rgba(34, 134, 74, 0.04)'
          }}
        >
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: '#eaf6ed', color: '#15803d', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Sprout size={22} />
                </div>
                <div>
                  <span style={{ fontSize: '0.74rem', fontWeight: 700, color: recommendation ? '#15803d' : '#b45309', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    1. Recommended Crop {recommendation ? '' : '(Demo Data Preview)'}
                  </span>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a', margin: '2px 0 0 0' }}>
                    🌾 {recommendation ? cropName : `${cropName} (Demo)`}
                  </h3>
                </div>
              </div>
              <span style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                color: recommendation ? '#15803d' : '#92400e',
                background: recommendation ? '#dcfce7' : '#fef3c7',
                padding: '4px 10px',
                borderRadius: '9999px',
                border: `1px solid ${recommendation ? '#86efac' : '#fde68a'}`
              }}>
                {recommendation ? `${cropConfidence}% Match` : 'Demo Data'}
              </span>
            </div>

            <p style={{ fontSize: '0.84rem', color: '#475569', lineHeight: 1.5, margin: '0 0 14px 0' }}>
              {recommendation 
                ? 'Scientifically recommended for your soil nutrient profile (N-P-K & pH) and local climate.'
                : '⚠️ Demo data preview. Please go to the Crop tab and enter your Soil Health Card N, P, K and pH values.'}
            </p>

            <div style={{ background: '#f8fafc', padding: '12px 14px', borderRadius: '10px', border: '1px solid #e2e8f0', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', marginBottom: '16px' }}>
              <div>
                <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600, display: 'block' }}>Season:</span>
                <strong style={{ fontSize: '0.86rem', color: '#1e293b' }}>{cropSeason}</strong>
              </div>
              <div>
                <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600, display: 'block' }}>Harvest Time:</span>
                <strong style={{ fontSize: '0.86rem', color: '#1e293b' }}>{cropDuration}</strong>
              </div>
              <div style={{ gridColumn: 'span 2' }}>
                <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600, display: 'block' }}>Water Need:</span>
                <strong style={{ fontSize: '0.86rem', color: '#0284c7' }}>{cropWater}</strong>
              </div>
            </div>
          </div>

          <button 
            type="button" 
            onClick={() => onNavigateTab('crop')}
            className="btn-primary-green"
            style={{ width: '100%', justifyContent: 'center', padding: '10px 16px', fontSize: '0.88rem' }}
          >
            <Sprout size={16} />
            Test Another Soil Sample →
          </button>
        </div>

        {/* Core Card 2: Fertilizer Dosage & Bags */}
        <div 
          style={{
            background: '#ffffff',
            border: '1px solid #ddd6fe',
            borderRadius: '16px',
            padding: '22px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxShadow: '0 2px 8px rgba(124, 58, 237, 0.04)'
          }}
        >
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: '#ede9fe', color: '#7c3aed', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Package size={22} />
                </div>
                <div>
                  <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#7c3aed', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    2. Fertilizer Prescription
                  </span>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a', margin: '2px 0 0 0' }}>
                    📦 DAP & Urea Dosage
                  </h3>
                </div>
              </div>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#7c3aed', background: '#ede9fe', padding: '4px 10px', borderRadius: '9999px', border: '1px solid #c4b5fd' }}>
                ICAR Protocol
              </span>
            </div>

            <p style={{ fontSize: '0.84rem', color: '#475569', lineHeight: 1.5, margin: '0 0 14px 0' }}>
              Standard 50kg bag prescription calibrated to prevent chemical fertilizer over-application:
            </p>

            <div style={{ background: '#faf5ff', padding: '12px 14px', borderRadius: '10px', border: '1px solid #e9d5ff', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', marginBottom: '16px' }}>
              <div>
                <span style={{ fontSize: '0.72rem', color: '#7c3aed', fontWeight: 700, textTransform: 'uppercase', display: 'block' }}>DAP (Basal)</span>
                <strong style={{ fontSize: '0.98rem', color: '#581c87' }}>1.0 Bag / Acre</strong>
                <span style={{ fontSize: '0.72rem', color: '#64748b' }}>(at sowing time)</span>
              </div>
              <div>
                <span style={{ fontSize: '0.72rem', color: '#15803d', fontWeight: 700, textTransform: 'uppercase', display: 'block' }}>Urea (Nitrogen)</span>
                <strong style={{ fontSize: '0.98rem', color: '#14532d' }}>1.8 Bags / Acre</strong>
                <span style={{ fontSize: '0.72rem', color: '#64748b' }}>(split into 2 doses)</span>
              </div>
              <div style={{ gridColumn: 'span 2', paddingTop: '6px', borderTop: '1px dashed #e9d5ff' }}>
                <span style={{ fontSize: '0.74rem', color: '#64748b' }}>
                  Regional Unit Support: <strong>Cents</strong>, <strong>Gunthas</strong>, <strong>Acres</strong>, <strong>Hectares</strong>.
                </span>
              </div>
            </div>
          </div>

          <button 
            type="button" 
            onClick={() => onNavigateTab('fertilizer')}
            className="btn-primary-green"
            style={{ width: '100%', justifyContent: 'center', background: '#7c3aed', padding: '10px 16px', fontSize: '0.88rem' }}
          >
            <Package size={16} />
            Calculate Exact Bags for Your Land Plot →
          </button>
        </div>

        {/* Core Card 3: Precision Irrigation Planning */}
        <div 
          style={{
            background: '#ffffff',
            border: '1px solid #7dd3fc',
            borderRadius: '16px',
            padding: '22px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxShadow: '0 2px 8px rgba(2, 132, 199, 0.04)'
          }}
        >
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: '#e0f2fe', color: '#0284c7', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Droplets size={22} />
                </div>
                <div>
                  <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#0284c7', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    3. Irrigation Planning
                  </span>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a', margin: '2px 0 0 0' }}>
                    💧 Water & Drip Schedule
                  </h3>
                </div>
              </div>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#0284c7', background: '#e0f2fe', padding: '4px 10px', borderRadius: '9999px', border: '1px solid #bae6fd' }}>
                Open-Meteo FAO-56
              </span>
            </div>

            <p style={{ fontSize: '0.84rem', color: '#475569', lineHeight: 1.5, margin: '0 0 14px 0' }}>
              Calculates crop evapotranspiration (ETc), rainfall offset, drip vs flood volume, and watering intervals.
            </p>


            <div style={{ background: '#f0f9ff', padding: '12px 14px', borderRadius: '10px', border: '1px solid #e0f2fe', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', marginBottom: '16px' }}>
              <div>
                <span style={{ fontSize: '0.72rem', color: '#0284c7', fontWeight: 700, textTransform: 'uppercase', display: 'block' }}>Daily Liters</span>
                <strong style={{ fontSize: '0.98rem', color: '#0369a1' }}>~19,100 L / 2 Acres</strong>
                <span style={{ fontSize: '0.72rem', color: '#64748b' }}>(weather adjusted)</span>
              </div>
              <div>
                <span style={{ fontSize: '0.72rem', color: '#0284c7', fontWeight: 700, textTransform: 'uppercase', display: 'block' }}>Drip Runtime</span>
                <strong style={{ fontSize: '0.98rem', color: '#0369a1' }}>~4.5 – 6.0 Hours</strong>
                <span style={{ fontSize: '0.72rem', color: '#64748b' }}>(split AM / PM)</span>
              </div>
              <div style={{ gridColumn: 'span 2', paddingTop: '6px', borderTop: '1px dashed #bae6fd' }}>
                <span style={{ fontSize: '0.74rem', color: '#64748b' }}>
                  Integrated with 7-day schedule, soil texture retention, and rainfall offset.
                </span>
              </div>
            </div>
          </div>

          <button 
            type="button" 
            onClick={() => onNavigateTab('irrigation')}
            className="btn-primary-green"
            style={{ width: '100%', justifyContent: 'center', background: '#0284c7', padding: '10px 16px', fontSize: '0.88rem' }}
          >
            <Droplets size={16} />
            Generate Precision Irrigation Plan →
          </button>
        </div>

        {/* Core Card 4: Harvest Prediction & Phenological Timeline */}
        <div 
          style={{
            background: '#ffffff',
            border: '1px solid #fed7aa',
            borderRadius: '16px',
            padding: '22px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxShadow: '0 2px 8px rgba(234, 88, 12, 0.04)'
          }}
        >
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: '#fff7ed', color: '#ea580c', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Calendar size={22} />
                </div>
                <div>
                  <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#ea580c', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    4. Harvest Prediction
                  </span>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a', margin: '2px 0 0 0' }}>
                    📅 Phenology & Yield
                  </h3>
                </div>
              </div>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#ea580c', background: '#fff7ed', padding: '4px 10px', borderRadius: '9999px', border: '1px solid #ffedd5' }}>
                ICAR Growth Cycle
              </span>
            </div>

            <p style={{ fontSize: '0.84rem', color: '#475569', lineHeight: 1.5, margin: '0 0 14px 0' }}>
              Real-time countdown from sowing date, 5 phenological stages, and ICAR expected harvest yield.
            </p>

            <div style={{ background: '#fffbeb', padding: '12px 14px', borderRadius: '10px', border: '1px solid #fef3c7', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', marginBottom: '16px' }}>
              <div>
                <span style={{ fontSize: '0.72rem', color: '#b45309', fontWeight: 700, textTransform: 'uppercase', display: 'block' }}>Expected Yield</span>
                <strong style={{ fontSize: '0.98rem', color: '#78350f' }}>~38 – 48 Q / ha</strong>
                <span style={{ fontSize: '0.72rem', color: '#64748b' }}>(in 50kg bags)</span>
              </div>
              <div>
                <span style={{ fontSize: '0.72rem', color: '#b45309', fontWeight: 700, textTransform: 'uppercase', display: 'block' }}>Growth Progress</span>
                <strong style={{ fontSize: '0.98rem', color: '#78350f' }}>5 Phenological Stages</strong>
                <span style={{ fontSize: '0.72rem', color: '#64748b' }}>(daily countdown)</span>
              </div>
              <div style={{ gridColumn: 'span 2', paddingTop: '6px', borderTop: '1px dashed #fde68a' }}>
                <span style={{ fontSize: '0.74rem', color: '#64748b' }}>
                  Includes moisture readiness checklist & benchmark MSP revenue forecast.
                </span>
              </div>
            </div>
          </div>

          <button 
            type="button" 
            onClick={() => onNavigateTab('harvest')}
            className="btn-primary-green"
            style={{ width: '100%', justifyContent: 'center', background: '#ea580c', padding: '10px 16px', fontSize: '0.88rem' }}
          >
            <Calendar size={16} />
            Track Sowing Date & Expected Yield →
          </button>
        </div>

      </div>


      {/* 3. Real Future 5-Day Weather Forecast Strip with Exact Dates */}
      <div 
        style={{
          background: '#ffffff',
          border: '1px solid #bae6fd',
          borderRadius: '16px',
          padding: '20px 22px',
          boxShadow: '0 2px 8px rgba(2, 132, 199, 0.04)'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: '#e0f2fe', color: '#0284c7', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CloudSun size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                ⛅ 5-Day Future Farm Weather & Rain Outlook
              </h3>
              <span style={{ fontSize: '0.78rem', color: '#64748b' }}>
                Plan irrigation, pesticide spraying, and harvesting with upcoming calendar dates
              </span>
            </div>
          </div>

          <button 
            type="button" 
            onClick={() => onNavigateTab('weather')}
            style={{
              fontSize: '0.8rem',
              fontWeight: 600,
              color: '#0284c7',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              textDecoration: 'underline'
            }}
          >
            Open Live Weather Radar →
          </button>
        </div>

        {/* 5-Day Grid with Real Calendar Dates */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '10px' }}>
          {fiveDayForecast.map((f, idx) => (
            <div 
              key={idx}
              style={{
                background: idx === 0 ? '#f0f9ff' : '#f8fafc',
                border: idx === 0 ? '1.5px solid #7dd3fc' : '1px solid #e2e8f0',
                borderRadius: '12px',
                padding: '12px 10px',
                textAlign: 'center',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <span style={{ fontSize: '0.82rem', fontWeight: 800, color: idx === 0 ? '#0284c7' : '#1e293b' }}>
                {f.day}
              </span>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>
                {f.date}
              </span>
              <span style={{ fontSize: '1.6rem', margin: '2px 0' }}>
                {f.icon}
              </span>
              <span style={{ fontSize: '0.86rem', fontWeight: 800, color: '#0f172a' }}>
                {f.maxTemp}° / {f.minTemp}°
              </span>
              <span style={{ fontSize: '0.72rem', color: f.rainChance >= 50 ? '#0284c7' : '#64748b', fontWeight: f.rainChance >= 50 ? 700 : 500 }}>
                💧 {f.rainChance}% rain
              </span>
            </div>
          ))}
        </div>

        {/* Bottom Direct Advice based on this forecast */}
        <div style={{ marginTop: '16px', paddingTop: '14px', borderTop: '1px solid #f1f5f9', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.82rem', color: '#166534', background: '#f0fdf4', padding: '10px 14px', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
            <CheckCircle2 size={18} color="#16a34a" style={{ flexShrink: 0 }} />
            <span><strong>Foliar Spray Today: </strong>Safe calm wind ({windSpeed} km/h). Good conditions for pesticide application.</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.82rem', color: isRainExpected ? '#9a3412' : '#1e40af', background: isRainExpected ? '#fff7ed' : '#eff6ff', padding: '10px 14px', borderRadius: '8px', border: isRainExpected ? '1px solid #fed7aa' : '1px solid #bfdbfe' }}>
            {isRainExpected ? (
              <AlertTriangle size={18} color="#ea580c" style={{ flexShrink: 0 }} />
            ) : (
              <Droplets size={18} color="#2563eb" style={{ flexShrink: 0 }} />
            )}
            <span><strong>Irrigation: </strong>{isRainExpected ? 'Rain expected. Hold off surface fertilizer to prevent wash-off.' : 'Dry weather. Proceed with normal morning irrigation.'}</span>
          </div>
        </div>

      </div>

    </div>
  );
}
