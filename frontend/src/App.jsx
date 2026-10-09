import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import DashboardView from './components/DashboardView';
import CropView from './components/CropView';
import FertilizerView from './components/FertilizerView';
import IrrigationView from './components/IrrigationView';
import HarvestView from './components/HarvestView';
import WeatherView from './components/WeatherView';
import LocationModal from './components/LocationModal';
import { getWeatherData, checkHealth } from './services/api';
import './App.css';


export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [locationName, setLocationName] = useState('Coimbatore, Tamil Nadu');
  const [weatherData, setWeatherData] = useState(null);
  const [recommendation, setRecommendation] = useState({
    crop: 'rice',
    confidence: 99.55,
    profile: {
      season: 'Kharif (Monsoon)',
      duration: '105 – 150 Days',
      water_need: 'High (Flooded / Submerged)',
      ideal_ph: '5.5 – 6.8',
      harvest_tips: 'Harvest when 80-85% of the panicles turn golden yellow.'
    }
  });

  const [serverStatus, setServerStatus] = useState('checking');
  const [detectingGPS, setDetectingGPS] = useState(false);
  const [isLocationModalOpen, setIsLocationModalOpen] = useState(false);

  // Initial load: health check & default weather (parallelized for 0s load)
  useEffect(() => {
    let isMounted = true;
    const initApp = async () => {
      try {
        const [health, weather] = await Promise.all([
          checkHealth(),
          getWeatherData('Coimbatore')
        ]);
        if (!isMounted) return;
        setServerStatus(health.status === 'online' ? 'online' : 'offline');
        if (weather && weather.success) {
          setWeatherData(weather.data);
        }
      } catch (err) {
        if (!isMounted) return;
        console.error('App init notice:', err);
        setServerStatus('offline');
      }
    };
    initApp();
    return () => { isMounted = false; };
  }, []);

  // Handle Location Switch
  const handleLocationSelect = async (loc) => {
    setLocationName(loc);
    try {
      const weather = await getWeatherData(loc);
      if (weather.success) {
        setWeatherData(weather.data);
      }
    } catch (err) {
      console.error('Weather fetch error:', err);
    }
  };

  // GPS Auto-detect handler
  const handleDetectGPS = () => {
    if (!navigator.geolocation) {
      alert("GPS is not supported by your browser. Please search your district name.");
      return;
    }

    setDetectingGPS(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        try {
          const res = await getWeatherData('GPS Farm Location', latitude, longitude);
          if (res.success) {
            setWeatherData(res.data);
            setLocationName(res.data.city || `GPS Farm (${latitude.toFixed(2)}°, ${longitude.toFixed(2)}°)`);
          }
        } catch (err) {
          console.error('GPS weather fetch error:', err);
        } finally {
          setDetectingGPS(false);
        }
      },
      (err) => {
        console.warn('GPS location denied:', err.message);
        setDetectingGPS(false);
      },
      { timeout: 8000 }
    );
  };

  return (
    <div className="app-layout">
      {/* 1. Left Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        onTabSelect={setActiveTab}
      />

      {/* 2. Main Content Wrapper */}
      <div className="main-wrapper">
        {/* Top Header Bar */}
        <Header
          locationName={locationName}
          weatherData={weatherData}
          onOpenLocationModal={() => setIsLocationModalOpen(true)}
          onDetectGPS={handleDetectGPS}
          detectingGPS={detectingGPS}
        />

        {/* Dynamic Screen View */}
        <main>
          {activeTab === 'dashboard' && (
            <DashboardView
              locationName={locationName}
              weatherData={weatherData}
              recommendation={recommendation}
              onNavigateTab={setActiveTab}
            />
          )}

          {activeTab === 'crop' && (
            <CropView
              activeLocation={locationName}
              onCropAnalyzed={(data) => {
                setRecommendation(data);
              }}
            />
          )}

          {activeTab === 'fertilizer' && (
            <FertilizerView
              initialCrop={recommendation?.crop}
            />
          )}

          {activeTab === 'irrigation' && (
            <IrrigationView
              activeLocation={locationName}
              initialCrop={recommendation?.crop}
            />
          )}

          {activeTab === 'harvest' && (
            <HarvestView
              initialCrop={recommendation?.crop}
            />
          )}

          {activeTab === 'weather' && (
            <WeatherView
              weatherData={weatherData}
              onSearchCity={handleLocationSelect}
              onDetectGPS={handleDetectGPS}
              detectingGPS={detectingGPS}
            />
          )}
        </main>
      </div>

      {/* Location Modal */}
      <LocationModal
        isOpen={isLocationModalOpen}
        onClose={() => setIsLocationModalOpen(false)}
        onSelectLocation={handleLocationSelect}
        onDetectGPS={handleDetectGPS}
        detectingGPS={detectingGPS}
      />
    </div>
  );
}