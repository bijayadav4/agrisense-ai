import React from 'react';
import { 
  Home, 
  Sprout, 
  FlaskConical, 
  CloudSun,
  Droplets,
  Calendar
} from 'lucide-react';

export default function Sidebar({ activeTab, onTabSelect }) {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home },
    { id: 'crop', label: 'Crop Recommendation', icon: Sprout },
    { id: 'fertilizer', label: 'Fertilizer Calculator', icon: FlaskConical },
    { id: 'irrigation', label: 'Irrigation Planning', icon: Droplets },
    { id: 'harvest', label: 'Harvest Prediction', icon: Calendar },
    { id: 'weather', label: 'Weather & Forecast', icon: CloudSun },
  ];


  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        {/* Brand Logo */}
        <div className="sidebar-logo">
          <div className="logo-icon-wrap">
            <Sprout size={26} />
          </div>
          <div className="logo-text">
            <h1>AgriSense AI</h1>
            <span>Smart Farming Assistant</span>
          </div>
        </div>

        {/* Phase 2 Sidebar Menu */}
        <nav className="sidebar-menu" aria-label="Sidebar Menu">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabSelect(item.id)}
                className={`sidebar-item ${isActive ? 'active' : ''}`}
                type="button"
              >
                <Icon size={19} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
