import React, { useState } from 'react';
import { 
  CloudSun, 
  Thermometer, 
  Droplets, 
  CloudRain, 
  Wind, 
  Navigation, 
  Search, 
  AlertTriangle, 
  CheckCircle2, 
  Calendar 
} from 'lucide-react';

const POPULAR_CITIES = [
  'Coimbatore, Tamil Nadu', 'Pune, Maharashtra', 'Nagpur, Maharashtra', 
  'Ludhiana, Punjab', 'Karnal, Haryana', 'Jaipur, Rajasthan',
  'Hyderabad, Telangana', 'Bengaluru, Karnataka', 'Patna, Bihar'
];

export default function WeatherView({ locationName, weatherData, onSearchCity, onDetectGPS, detectingGPS }) {
  const [cityInput, setCityInput] = useState('');

  const temp = weatherData?.temperature !== undefined ? weatherData.temperature : '--';
  const feelsLike = weatherData?.feels_like !== undefined ? weatherData.feels_like : null;
  const humidity = weatherData?.humidity !== undefined ? weatherData.humidity : '--';
  const rainfall = weatherData?.rainfall !== undefined ? weatherData.rainfall : 0.0;
  const precipChance = weatherData?.precipitation_chance !== undefined ? weatherData.precipitation_chance : null;
  const windSpeed = weatherData?.wind_speed !== undefined ? weatherData.wind_speed : '--';
  const condition = weatherData?.condition || 'Updating...';
  const displayLocation = locationName || weatherData?.city || 'Select Location';
  const isFallback = Boolean(weatherData?.forecast_source && weatherData.forecast_source.toLowerCase().includes('fallback'));

  const handleSearch = (e) => {
    e.preventDefault();
    if (cityInput.trim()) {
      onSearchCity(cityInput.trim());
      setCityInput('');
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Title Card with GPS and Search */}
      <div className="dashboard-card">
        <div className="card-title-row">
          <div className="card-title-left">
            <div className="logo-icon-wrap" style={{ color: '#0284c7', background: '#e0f2fe', borderColor: '#bae6fd' }}>
              <CloudSun size={24} />
            </div>
            <div>
              <h3>🌤️ Live Agro-Meteorological Weather & Climate</h3>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                Real-time micro-climate monitoring, rain forecasts, and farm spray advisories
              </span>
            </div>
          </div>
        </div>

        {/* Location Selector Controls */}
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '10px' }}>
          <button
            type="button"
            onClick={onDetectGPS}
            disabled={detectingGPS}
            className="btn-primary-green"
            style={{ width: 'auto', background: '#0284c7', padding: '10px 20px', fontSize: '0.9rem' }}
          >
            <Navigation size={16} />
            <span>{detectingGPS ? 'Locating Farm GPS...' : '📍 Auto-Detect My Farm GPS'}</span>
          </button>

          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px', flexGrow: 1, minWidth: '240px' }}>
            <input
              type="text"
              placeholder="Search agricultural district or city..."
              value={cityInput}
              onChange={(e) => setCityInput(e.target.value)}
              className="form-input-white"
            />
            <button type="submit" className="btn-primary-green" style={{ width: 'auto', padding: '10px 18px' }}>
              <Search size={16} />
              <span>Search</span>
            </button>
          </form>
        </div>

        {/* Popular City Chips */}
        <div style={{ marginTop: '10px' }}>
          <div className="preset-chips-strip">
            {POPULAR_CITIES.map((c, idx) => (
              <button
                key={idx}
                type="button"
                className="chip-btn"
                onClick={() => onSearchCity(c)}
              >
                📍 {c.split(',')[0]}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Weather Metrics */}
      <div className="dashboard-card">
        <div className="card-title-row">
          <div className="card-title-left">
            <span style={{ fontSize: '1.2rem' }}>📍</span>
            <h3>Current Climate in {displayLocation}</h3>
          </div>
          <span className="badge-tag badge-blue" style={{ fontSize: '0.85rem' }}>{condition}</span>
        </div>

        {/* Fallback Regional Baseline Notice */}
        {isFallback && (
          <div style={{
            margin: '0 0 16px 0',
            padding: '8px 14px',
            borderRadius: '8px',
            background: '#fef3c7',
            border: '1px solid #fde68a',
            color: '#92400e',
            fontSize: '0.82rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontWeight: 600
          }}>
            <AlertTriangle size={16} style={{ flexShrink: 0, color: '#d97706' }} />
            <span>Regional baseline, not live — Telemetry using agro-climatic baseline averages.</span>
          </div>
        )}

        <div className="weather-metrics-grid">
          <div className="weather-metric-tile">
            <div className="metric-icon-wrap red">
              <Thermometer size={18} />
            </div>
            <span className="metric-val">{temp}°C</span>
            <span className="metric-lbl">
              Air Temp {feelsLike ? `(Feels ${feelsLike}°C)` : ''}
            </span>
          </div>

          <div className="weather-metric-tile">
            <div className="metric-icon-wrap blue">
              <Droplets size={18} />
            </div>
            <span className="metric-val">{humidity}%</span>
            <span className="metric-lbl">Relative Humidity</span>
          </div>

          <div className="weather-metric-tile">
            <div className="metric-icon-wrap cyan">
              <CloudRain size={18} />
            </div>
            <span className="metric-val">
              {precipChance !== null ? `${precipChance}%` : `${rainfall} mm`}
            </span>
            <span className="metric-lbl">
              Precipitation {rainfall > 0 ? `(${rainfall} mm)` : 'Chance'}
            </span>
          </div>

          <div className="weather-metric-tile">
            <div className="metric-icon-wrap wind">
              <Wind size={18} />
            </div>
            <span className="metric-val">{windSpeed} km/h</span>
            <span className="metric-lbl">Wind Speed</span>
          </div>
        </div>

        {/* 5-Day Regional Forecast */}
        <div style={{ marginTop: '16px' }}>
          <h4 style={{ fontSize: '0.9rem', color: 'var(--text-heading)', fontWeight: 700, marginBottom: '10px' }}>
            📅 5-Day Agro-Meteorological Forecast:
          </h4>
          <div className="forecast-strip" style={{ border: 'none', paddingTop: 0 }}>
            {weatherData?.forecast && weatherData.forecast.length > 0 ? (
              weatherData.forecast.map((f, idx) => (
                <div key={idx} className="forecast-day-tile">
                  <span className="forecast-day-name">{f.day}</span>
                  <span className="forecast-weather-icon">{f.icon || '⛅'}</span>
                  <span className="forecast-temp-range">{Math.round(f.max_temp)}° / {Math.round(f.min_temp)}°C</span>
                  <span style={{ fontSize: '0.72rem', color: (f.rain_chance > 40 || f.rain_mm > 0) ? '#0284c7' : '#16a34a' }}>
                    {f.rain_chance !== undefined ? `${f.rain_chance}% rain` : (f.rain_mm > 0 ? `${f.rain_mm} mm` : (f.condition || 'Clear'))}
                  </span>
                </div>
              ))
            ) : (
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Loading live regional forecast...</span>
            )}
          </div>
        </div>
      </div>

      {/* Weather Advisories */}
      <div className="dashboard-card">
        <div className="card-title-row">
          <div className="card-title-left">
            <h3>Field Operation Advisories for {displayLocation}</h3>
          </div>
        </div>

        <div className="alerts-list">
          {weatherData?.advisory && weatherData.advisory.length > 0 ? (
            weatherData.advisory.map((adv, idx) => (
              <div 
                key={idx} 
                className={`alert-row ${adv.includes('Warning') || adv.includes('High') ? 'warning' : 'success'}`}
              >
                {adv.includes('Warning') || adv.includes('High') ? (
                  <AlertTriangle size={18} color="#d97706" style={{ flexShrink: 0 }} />
                ) : (
                  <CheckCircle2 size={18} color="#16a34a" style={{ flexShrink: 0 }} />
                )}
                <div>{adv}</div>
              </div>
            ))
          ) : (
            <div className="alert-row success">
              <CheckCircle2 size={18} color="#16a34a" style={{ flexShrink: 0 }} />
              <div>Optimal conditions for regular field work and farm operations.</div>
            </div>
          )}
        </div>
      </div>

    </div>
  );
}
