import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { MapPin, Ruler, Calculator, CheckCircle2, Info } from 'lucide-react';

/**
 * 1. DATA STRUCTURE: South Indian States & Regional Land Unit Multipliers to Hectares
 */
const SOUTH_INDIA_LAND_UNITS = {
  'Tamil Nadu': [
    { label: 'Cent', unit: 'cent', multiplier: 0.004047 },
    { label: 'Acre', unit: 'acre', multiplier: 0.404686 },
    { label: 'Hectare', unit: 'hectare', multiplier: 1.0 }
  ],
  'Kerala': [
    { label: 'Cent', unit: 'cent', multiplier: 0.004047 },
    { label: 'Acre', unit: 'acre', multiplier: 0.404686 },
    { label: 'Hectare', unit: 'hectare', multiplier: 1.0 }
  ],
  'Karnataka': [
    { label: 'Guntha / Gunta', unit: 'guntha', multiplier: 0.010117 }, // 40 Gunthas = 1 Acre
    { label: 'Acre', unit: 'acre', multiplier: 0.404686 },
    { label: 'Hectare', unit: 'hectare', multiplier: 1.0 }
  ],
  'Andhra Pradesh': [
    { label: 'Guntha', unit: 'guntha', multiplier: 0.010117 },
    { label: 'Cent', unit: 'cent', multiplier: 0.004047 },
    { label: 'Acre', unit: 'acre', multiplier: 0.404686 },
    { label: 'Hectare', unit: 'hectare', multiplier: 1.0 }
  ]
};

export default function LandUnitConverter({ onHectareChange, initialArea = '' }) {
  const states = useMemo(() => Object.keys(SOUTH_INDIA_LAND_UNITS), []);

  // State management
  const [selectedState, setSelectedState] = useState('Tamil Nadu');
  const [selectedUnit, setSelectedUnit] = useState(SOUTH_INDIA_LAND_UNITS['Tamil Nadu'][0].unit);
  const [areaInput, setAreaInput] = useState(initialArea);

  // Available units for the currently selected state
  const availableUnits = useMemo(() => {
    return SOUTH_INDIA_LAND_UNITS[selectedState] || [];
  }, [selectedState]);

  // When state changes, reset selectedUnit to the first valid unit for that state
  const handleStateChange = (e) => {
    const newState = e.target.value;
    setSelectedState(newState);
    const firstUnit = SOUTH_INDIA_LAND_UNITS[newState]?.[0]?.unit || 'acre';
    setSelectedUnit(firstUnit);
  };

  /**
   * 3. LOGIC: calculateHectares
   * Multiplies user area by selected unit's multiplier and rounds to 3 decimal places.
   */
  const calculateHectares = useCallback((val, unitKey, stateKey) => {
    const numericVal = parseFloat(val);
    if (isNaN(numericVal) || numericVal <= 0) {
      return 0;
    }
    const unitsList = SOUTH_INDIA_LAND_UNITS[stateKey] || [];
    const activeUnitObj = unitsList.find((u) => u.unit === unitKey) || unitsList[0];
    const multiplier = activeUnitObj ? activeUnitObj.multiplier : 1.0;
    
    // Round output to 3 decimal places
    const converted = numericVal * multiplier;
    return Number(converted.toFixed(3));
  }, []);

  // Compute standard hectares
  const standardHectares = useMemo(() => {
    return calculateHectares(areaInput, selectedUnit, selectedState);
  }, [areaInput, selectedUnit, selectedState, calculateHectares]);

  // 4. INTEGRATION: Notify parent whenever converted standard hectare changes
  useEffect(() => {
    if (typeof onHectareChange === 'function') {
      onHectareChange(standardHectares);
    }
  }, [standardHectares, onHectareChange]);

  const activeUnitConfig = availableUnits.find((u) => u.unit === selectedUnit);

  return (
    <div className="w-full bg-slate-50/70 rounded-2xl border border-slate-200 p-4 mb-4 transition-all">
      {/* Sleek Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 mb-3 border-b border-slate-200/80">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-emerald-100 text-emerald-800 rounded-lg">
            <Ruler className="w-4 h-4" size={16} />
          </div>
          <span className="text-sm font-bold text-slate-800">
            Farm Area & Regional Unit
          </span>
        </div>
        <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
          <MapPin size={12} /> South India Standards (Cent = 0.004047 ha)
        </span>
      </div>

      {/* Grid Inputs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
        {/* State */}
        <div className="flex flex-col gap-1">
          <label htmlFor="state-select" className="text-xs font-semibold text-slate-600">
            State
          </label>
          <select
            id="state-select"
            value={selectedState}
            onChange={handleStateChange}
            className="w-full px-3 py-2 text-xs sm:text-sm bg-white border border-slate-300 rounded-xl text-slate-800 font-medium focus:ring-2 focus:ring-emerald-500 focus:outline-none cursor-pointer"
          >
            {states.map((st) => (
              <option key={st} value={st}>
                {st}
              </option>
            ))}
          </select>
        </div>

        {/* Unit */}
        <div className="flex flex-col gap-1">
          <label htmlFor="unit-select" className="text-xs font-semibold text-slate-600">
            Measurement Unit
          </label>
          <select
            id="unit-select"
            value={selectedUnit}
            onChange={(e) => setSelectedUnit(e.target.value)}
            className="w-full px-3 py-2 text-xs sm:text-sm bg-white border border-slate-300 rounded-xl text-slate-800 font-medium focus:ring-2 focus:ring-emerald-500 focus:outline-none cursor-pointer"
          >
            {availableUnits.map((u) => (
              <option key={u.unit} value={u.unit}>
                {u.label} (×{u.multiplier})
              </option>
            ))}
          </select>
        </div>

        {/* Area Input */}
        <div className="flex flex-col gap-1">
          <label htmlFor="area-input" className="text-xs font-semibold text-slate-600">
            Enter Area in {activeUnitConfig?.label || 'Units'}
          </label>
          <input
            id="area-input"
            type="number"
            min="0"
            step="any"
            placeholder={selectedUnit === 'cent' ? 'e.g. 50 or 100' : 'e.g. 1, 2, 5'}
            value={areaInput}
            onChange={(e) => setAreaInput(e.target.value)}
            className="w-full px-3 py-2 text-xs sm:text-sm bg-white border border-slate-300 rounded-xl text-slate-900 font-bold focus:ring-2 focus:ring-emerald-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Quick Presets & Result in One Clean Row */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-200/60">
        <div className="flex items-center flex-wrap gap-1.5">
          <span className="text-[11px] font-semibold text-slate-500 mr-1">Quick Presets:</span>
          <button
            type="button"
            onClick={() => { setSelectedUnit('cent'); setAreaInput('25'); }}
            className="text-[11px] px-2 py-0.5 rounded-md bg-white border border-slate-200 hover:border-emerald-500 hover:bg-emerald-50 text-slate-700 font-medium transition cursor-pointer"
          >
            25 Cents (¼ ac)
          </button>
          <button
            type="button"
            onClick={() => { setSelectedUnit('cent'); setAreaInput('50'); }}
            className="text-[11px] px-2 py-0.5 rounded-md bg-white border border-slate-200 hover:border-emerald-500 hover:bg-emerald-50 text-slate-700 font-medium transition cursor-pointer"
          >
            50 Cents (½ ac)
          </button>
          <button
            type="button"
            onClick={() => { setSelectedUnit('acre'); setAreaInput('1'); }}
            className="text-[11px] px-2 py-0.5 rounded-md bg-white border border-slate-200 hover:border-emerald-500 hover:bg-emerald-50 text-slate-700 font-medium transition cursor-pointer"
          >
            1 Acre
          </button>
          <button
            type="button"
            onClick={() => { setSelectedUnit('acre'); setAreaInput('2'); }}
            className="text-[11px] px-2 py-0.5 rounded-md bg-white border border-slate-200 hover:border-emerald-500 hover:bg-emerald-50 text-slate-700 font-medium transition cursor-pointer"
          >
            2 Acres
          </button>
          <button
            type="button"
            onClick={() => { setSelectedUnit('acre'); setAreaInput('5'); }}
            className="text-[11px] px-2 py-0.5 rounded-md bg-white border border-slate-200 hover:border-emerald-500 hover:bg-emerald-50 text-slate-700 font-medium transition cursor-pointer"
          >
            5 Acres
          </button>
        </div>

        {/* Subtle Converted Display */}
        <div className="flex items-center gap-1.5 text-xs text-slate-600 font-medium ml-auto">
          <span>Converted:</span>
          <span className="font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
            {standardHectares.toFixed(3)} ha
          </span>
          {areaInput && parseFloat(areaInput) > 0 && (
            <span className="text-[11px] text-slate-500">
              ({(standardHectares * 2.47105).toFixed(2)} ac)
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
