import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 6000,
});

// Client-side In-Memory Caches for 0-second Instant Response
const weatherCache = new Map();
const cropCache = new Map();
const fertilizerCache = new Map();
let lastHealthCheck = null;
let lastHealthCheckTime = 0;

const WEATHER_TTL_MS = 5 * 60 * 1000;      // 5 minutes
const PREDICT_TTL_MS = 10 * 60 * 1000;     // 10 minutes
const HEALTH_TTL_MS = 30 * 1000;           // 30 seconds

// 1. Instant Health Check
export const checkHealth = async () => {
  const now = Date.now();
  if (lastHealthCheck && (now - lastHealthCheckTime < HEALTH_TTL_MS)) {
    return lastHealthCheck;
  }
  try {
    const response = await api.get('/health');
    lastHealthCheck = response.data;
    lastHealthCheckTime = now;
    return response.data;
  } catch (error) {
    return { status: 'offline', error: error.message };
  }
};

// 2. Weather Data with Instant 0ms Memory Cache
export const getWeatherData = async (location = 'New Delhi', lat = null, lon = null, options = {}) => {
  const signal = options?.signal;
  const skipCache = Boolean(options?.skipCache);
  const cacheKey = `${String(location).trim().toLowerCase()}_${lat}_${lon}`;
  const now = Date.now();
  
  if (!skipCache && weatherCache.has(cacheKey)) {
    const cached = weatherCache.get(cacheKey);
    if (now - cached.timestamp < WEATHER_TTL_MS) {
      return cached.data;
    }
  }

  let url = `/api/weather?location=${encodeURIComponent(location)}`;
  if (lat !== null && lon !== null) {
    url += `&lat=${lat}&lon=${lon}`;
  }

  const response = await api.get(url, { signal });
  if (response.data && response.data.success) {
    weatherCache.set(cacheKey, { data: response.data, timestamp: now });
  }
  return response.data;
};

export const clearPredictionCaches = () => {
  weatherCache.clear();
  cropCache.clear();
  fertilizerCache.clear();
};

// 3. Crop Recommendation with Instant Sub-millisecond Cache
export const getCropRecommendation = async (payload) => {
  const cacheKey = JSON.stringify(payload);
  const now = Date.now();

  if (cropCache.has(cacheKey)) {
    const cached = cropCache.get(cacheKey);
    if (now - cached.timestamp < PREDICT_TTL_MS) {
      return cached.data;
    }
  }

  const response = await api.post('/api/recommend/crop', payload);
  if (response.data && response.data.success) {
    cropCache.set(cacheKey, { data: response.data, timestamp: now });
  }
  return response.data;
};
export const recommendCrop = getCropRecommendation;

// 4. Fertilizer Recommendation with Instant Sub-millisecond Cache
export const getFertilizerRecommendation = async (payload) => {
  const cacheKey = JSON.stringify(payload);
  const now = Date.now();

  if (fertilizerCache.has(cacheKey)) {
    const cached = fertilizerCache.get(cacheKey);
    if (now - cached.timestamp < PREDICT_TTL_MS) {
      return cached.data;
    }
  }

  const response = await api.post('/api/recommend/fertilizer', payload);
  if (response.data && response.data.success) {
    fertilizerCache.set(cacheKey, { data: response.data, timestamp: now });
  }
  return response.data;
};

// 5. Soil Image Classification (MobileNetV2 CNN Vision)
export const classifySoilImage = async (imageFile) => {
  const formData = new FormData();
  formData.append('image', imageFile);

  const response = await api.post('/api/classify/soil-image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// 6. Spatio-Temporal LSTM & Feature Bottleneck Crop Recommendation
export const getCropFusionRecommendation = async (payload) => {
  const response = await api.post('/api/recommend/crop/spatiotemporal-fusion', payload);
  return response.data;
};

// 7. Irrigation Planning (FAO-56 Penman-Monteith)
export const getIrrigationPlan = async (payload) => {
  const response = await api.post('/api/irrigation/plan', payload);
  return response.data;
};

// 8. Phenological Growth & Harvest Timeline Prediction
export const getHarvestPrediction = async (payload) => {
  const response = await api.post('/api/harvest/predict', payload);
  return response.data;
};

// 9. Generate Official Farmer Advisory Report Card PDF
export const downloadReportCardPdf = async (payload) => {
  const response = await api.post('/api/report/generate', payload, {
    responseType: 'blob'
  });
  return response.data;
};

// 10. General Agronomic Soil Crop Suitability Guidance (Source: UNVERIFIED)
export const getSoilSuitability = async () => {
  const response = await api.get('/api/soil-crop-suitability');
  return response.data;
};

export default api;