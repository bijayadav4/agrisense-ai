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
import { getWeatherData, checkHealth, getHarvestPrediction, recommendCrop } from './services/api';
import './App.css';


export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [locationName, setLocationName] = useState('Coimbatore, Tamil Nadu');
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

  // Initial load: health check & default weather (parallelized for 0s load)
  useEffect(() => {
    let isMounted = true;
    const initApp = async () => {
      try {
        const [health, weather, cropRes] = await Promise.all([
          checkHealth(),
          getWeatherData('Coimbatore'),
          recommendCrop({
            N: 85,
            P: 48,
            K: 40,
            ph: 6.4,
            temperature: 25,
            humidity: 80,
            rainfall: 200,
            location: 'Coimbatore',
            data_source: 'Demo input (fixed weather)',
            is_estimated: true
          }).catch(() => null)
        ]);
        if (!isMounted) return;
        setServerStatus(health.status === 'online' ? 'online' : 'offline');
        if (weather && weather.success) {
          setWeatherData(weather.data);
        }
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

  // Re-fetch weather whenever locationName changes
  useEffect(() => {
    if (!locationName) return;
    let isMounted = true;
    const updateWeather = async () => {
      try {
        const res = await getWeatherData(locationName);
        if (isMounted && res && res.success) {
          setWeatherData(res.data);
        }
      } catch (err) {
        console.error('Weather re-fetch error:', err);
      }
    };
    updateWeather();
    return () => { isMounted = false; };
  }, [locationName]);

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

  // Handle Location Switch
  const handleLocationSelect = async (loc) => {
    setLocationName(loc);
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
              farmArea={farmArea}
              farmAreaUnit={farmAreaUnit}
              harvestInfo={harvestInfo}
              onNavigateTab={setActiveTab}
            />
          )}

          {activeTab === 'crop' && (
            <CropView
              activeLocation={locationName}
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
              initialCrop={recommendation?.crop}
              soilData={soilData}
              onUpdateSoil={handleUpdateSoil}
            />
          )}

          {activeTab === 'irrigation' && (
            <IrrigationView
              activeLocation={locationName}
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