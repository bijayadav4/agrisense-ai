import React, { useState } from 'react';
import { 
  MapPin, 
  X, 
  Navigation, 
  Search, 
  CheckCircle2, 
  RefreshCw 
} from 'lucide-react';

const POPULAR_DISTRICTS = [
  'Coimbatore, Tamil Nadu',
  'Pune, Maharashtra',
  'Nagpur, Maharashtra',
  'Nashik, Maharashtra',
  'Mumbai, Maharashtra',
  'Ludhiana, Punjab',
  'Karnal, Haryana',
  'Jaipur, Rajasthan',
  'Bengaluru, Karnataka',
  'Hyderabad, Telangana',
  'Vijayawada, Andhra Pradesh',
  'Lucknow, Uttar Pradesh',
  'Patna, Bihar',
  'Indore, Madhya Pradesh',
  'Ahmedabad, Gujarat'
];

export default function LocationModal({ isOpen, onClose, onSelectLocation, onDetectGPS, detectingGPS }) {
  const [searchInput, setSearchInput] = useState('');

  if (!isOpen) return null;

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchInput.trim()) {
      onSelectLocation(searchInput.trim());
      onClose();
    }
  };

  const handleDistrictPick = (loc) => {
    onSelectLocation(loc);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content-card animate-modal" style={{ maxWidth: '580px' }} onClick={(e) => e.stopPropagation()}>
        <button type="button" className="modal-close-btn" onClick={onClose}>
          <X size={20} />
        </button>

        {/* Modal Title */}
        <div className="modal-title-row">
          <div className="logo-icon-wrap">
            <MapPin size={24} />
          </div>
          <div>
            <h2>📍 Farm Location & Micro-Climate</h2>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Select your agricultural district or auto-detect your farm coordinates
            </span>
          </div>
        </div>

        {/* GPS Auto-Detect Button */}
        <button
          type="button"
          onClick={() => {
            onDetectGPS();
            onClose();
          }}
          disabled={detectingGPS}
          className="btn-primary-green"
          style={{ background: '#0284c7' }}
        >
          {detectingGPS ? (
            <>
              <RefreshCw size={18} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
              <span>Locating Farm Coordinates...</span>
            </>
          ) : (
            <>
              <Navigation size={18} />
              <span>📍 Auto-Detect My Farm GPS Coordinates</span>
            </>
          )}
        </button>

        {/* Search Bar */}
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            placeholder="Type city or district name..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="form-input-white"
            style={{ flexGrow: 1 }}
          />
          <button type="submit" className="btn-primary-green" style={{ width: 'auto', padding: '10px 20px' }}>
            <Search size={16} />
            <span>Set</span>
          </button>
        </form>

        {/* District Grid */}
        <div>
          <label style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-heading)', display: 'block', marginBottom: '8px' }}>
            Popular Agricultural Regions:
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', maxHeight: '240px', overflowY: 'auto' }}>
            {POPULAR_DISTRICTS.map((dist) => (
              <button
                key={dist}
                type="button"
                className="chip-btn"
                onClick={() => handleDistrictPick(dist)}
                style={{ textAlign: 'left', padding: '8px 12px', borderRadius: '8px' }}
              >
                📍 {dist}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
