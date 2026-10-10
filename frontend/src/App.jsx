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
import { getWeatherData, checkHealth, getHarvestPrediction, recommendCrop, clearPredictionCaches } from './services/api';
import './App.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [location, setLocation] = useState({
    name: 'New Delhi',
    lat: 28.6139,
    lon: 77.2090
  });
  const [weatherData, setWeatherData] = useState(null);
  const [farmArea, setFarmArea] = useState(2.0);
  const [farmAreaUnit, setFarmAreaUnit] = useState('Acres');
  const [harvestInfo, setHarvestInfo] = useState(null);
  const [recommendation, setRecommendation] = useState(null);

  const [serverStatus, setServerStatus] = useState('checking');
  const [detectingGPS, setDetectingGPS] = useState(false);
  const [isLocationModalOpen, setIsLocationModalOpen] = useState(false);

  // Sync harvest predictions with active crop and farm area
  useEffect(() => {
    let isMounted = true;
    const fetchHarvest = async () => {
      try {
        const cropName = (recommendation?.crop || 'rice').toLowerCase();
        const todayStr = new Date().toISOString().split('T')[0];
        const res = await getHarvestPrediction({
          crop: cropName,
          sowing_date: todayStr,
          area: parseFloat(farmArea) || 1.0,
          area_unit: farmAreaUnit
        });
        if (isMounted && res && res.success) {
          setHarvestInfo(res);
        }
      } catch (err) {
        console.error('Harvest fetch notice:', err);
      }
    };
    fetchHarvest();
    return () => { isMounted = false; };
  }, [recommendation?.crop, farmArea, farmAreaUnit]);

  // Initial load: health check & initial demo crop recommendation
  useEffect(() => {
    let isMounted = true;
    const initApp = async () => {
      try {
        const [health, cropRes] = await Promise.all([
          checkHealth(),
          recommendCrop({
            N: 85,
            P: 48,
            K: 40,
            ph: 6.4,
            temperature: 25,
            humidity: 80,
            rainfall: 200,
            location: location.name,
            data_source: 'Demo input (fixed weather)',
            is_estimated: true
          }).catch(() => null)
        ]);
        if (!isMounted) return;
        setServerStatus(health.status === 'online' ? 'online' : 'offline');
        if (cropRes && cropRes.success) {
          setRecommendation(cropRes);
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

  // Unified single source of truth for weather with AbortController stale guard
  useEffect(() => {
    if (!location.name && location.lat === null) return;
    const controller = new AbortController();

    const fetchWeather = async () => {
      try {
        clearPredictionCaches();
        const res = await getWeatherData(location.name, location.lat, location.lon, {
          signal: controller.signal
        });
        if (res && res.success) {
          setWeatherData(res.data);
        }
      } catch (err) {
        if (err.name === 'CanceledError' || err.code === 'ERR_CANCELED' || err.message === 'canceled') {
          return;
        }
        console.error('Weather fetch error:', err);
      }
    };

    fetchWeather();

    return () => {
      controller.abort();
    };
  }, [location.lat, location.lon, location.name]);

  const [soilData, setSoilData] = useState({
    soil_type: 'Loamy',
    confidence: null,
    source: 'user-selected'
  });

  const handleUpdateSoil = (soilType, confidence = null, source = 'user-selected') => {
    setSoilData({
      soil_type: soilType,
      confidence: confidence,
      source: source
    });
  };

  // Handle Location Switch (Single update, no duplicate fetches)
  const handleLocationSelect = (loc) => {
    if (typeof loc === 'string') {
      setLocation({
        name: loc.trim(),
        lat: null,
        lon: null
      });
    } else if (loc && typeof loc === 'object') {
      setLocation({
        name: loc.name || loc.city || 'Unknown',
        lat: loc.lat ?? null,
        lon: loc.lon ?? null
      });
    }
  };

  // GPS Auto-detect handler (Single fetch flow via unified state)
  const handleDetectGPS = () => {
    if (!navigator.geolocation) {
      alert("GPS is not supported by your browser. Please search your district name.");
      return;
    }

    setDetectingGPS(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        setLocation({
          name: `GPS Farm (${latitude.toFixed(2)}°, ${longitude.toFixed(2)}°)`,
          lat: latitude,
          lon: longitude
        });
        setDetectingGPS(false);
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
          locationName={location.name}
          weatherData={weatherData}
          onOpenLocationModal={() => setIsLocationModalOpen(true)}
          onDetectGPS={handleDetectGPS}
          detectingGPS={detectingGPS}
        />

        {/* Dynamic Screen View */}
        <main>
          {activeTab === 'dashboard' && (
            <DashboardView
              locationName={location.name}
              weatherData={weatherData}
              recommendation={recommendation}
              farmArea={farmArea}
              farmAreaUnit={farmAreaUnit}
              harvestInfo={harvestInfo}
              onNavigateTab={setActiveTab}
            />
          )}

          {activeTab === 'crop' && (
            <CropView
              activeLocation={location.name}
              weatherData={weatherData}
              soilData={soilData}
              onUpdateSoil={handleUpdateSoil}
              onCropAnalyzed={(data) => {
                setRecommendation(data);
              }}
            />
          )}

          {activeTab === 'fertilizer' && (
            <FertilizerView
              activeLocation={location.name}
              weatherData={weatherData}
              initialCrop={recommendation?.crop}
              soilData={soilData}
              onUpdateSoil={handleUpdateSoil}
            />
          )}

          {activeTab === 'irrigation' && (
            <IrrigationView
              activeLocation={location.name}
              weatherData={weatherData}
              initialCrop={recommendation?.crop}
              soilData={soilData}
              farmArea={farmArea}
              farmAreaUnit={farmAreaUnit}
              onUpdateFarmArea={setFarmArea}
              onUpdateFarmAreaUnit={setFarmAreaUnit}
              onUpdateSoil={handleUpdateSoil}
            />
          )}

          {activeTab === 'harvest' && (
            <HarvestView
              activeLocation={location.name}
              weatherData={weatherData}
              initialCrop={recommendation?.crop}
              farmArea={farmArea}
              farmAreaUnit={farmAreaUnit}
              harvestInfo={harvestInfo}
              onUpdateHarvestInfo={setHarvestInfo}
              onUpdateFarmArea={setFarmArea}
              onUpdateFarmAreaUnit={setFarmAreaUnit}
            />
          )}

          {activeTab === 'weather' && (
            <WeatherView
              locationName={location.name}
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