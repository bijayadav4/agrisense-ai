import React from 'react';
import { 
  MapPin, 
  Sun, 
  Navigation,
  PhoneCall,
  Headphones
} from 'lucide-react';

export default function Header({ locationName, weatherData, onOpenLocationModal, onDetectGPS, detectingGPS }) {
  const currentTemp = weatherData?.temperature !== undefined ? `${weatherData.temperature}°C` : '...';
  const currentCondition = weatherData?.condition || 'Updating...';
  const displayLocation = locationName || weatherData?.city || 'Select Location';

  return (
    <header className="top-header">
      {/* Location Selector & GPS Auto-detect */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div className="header-location" onClick={onOpenLocationModal} title="Click to Change Location or Search District">
          <div className="location-icon-wrap">
            <MapPin size={18} />
          </div>
          <div className="location-text">
            <h3>{displayLocation}</h3>
            <span>Farm Location (Click to change)</span>
          </div>
        </div>

        <button
          type="button"
          onClick={onDetectGPS}
          disabled={detectingGPS}
          className="chip-btn"
          style={{ padding: '6px 12px', fontSize: '0.78rem', color: 'var(--primary-green)', borderColor: 'var(--primary-green-border)', background: '#eaf6ed' }}
          title="Auto-detect using GPS"
        >
          <Navigation size={13} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
          <span>{detectingGPS ? 'Locating...' : '📍 GPS'}</span>
        </button>
      </div>

      {/* Center Weather Snippet */}
      <div className="header-weather-snippet">
        <span style={{ fontSize: '1.2rem', marginRight: '6px' }}>{weatherData?.icon || '🌤️'}</span>
        <div>
          <span className="weather-snippet-temp">{currentTemp}</span>
          <span className="weather-snippet-condition" style={{ marginLeft: '6px' }}>{currentCondition}</span>
        </div>
      </div>

      {/* Right Kisan Helpline Button */}
      <div className="header-helpline-section">
        <a 
          href="tel:18001801551" 
          className="kisan-helpline-badge"
          title="Call Kisan Call Centre (Toll Free: 1800-180-1551)"
        >
          <div className="helpline-icon-circle">
            <PhoneCall size={16} />
          </div>
          <div className="helpline-text-group">
            <span className="helpline-title">Kisan Helpline (Toll-Free)</span>
            <span className="helpline-number">1800-180-1551</span>
          </div>
        </a>
      </div>
    </header>
  );
}
