import React, { useState } from 'react';
import { X } from 'lucide-react';

/**
 * StartupModal Component
 * 
 * Two-step modal for setting initial user position:
 * Step 1: Select current floor
 * Step 2: Choose GPS or manual position selection
 * 
 * Based on LeafletJS set_start_end.html implementation
 */
export default function StartupModal({ 
  building = 'M',
  onComplete,
  onClose,
  availableFloors = ['1', '2', '3']
}) {
  const [step, setStep] = useState(1);
  const [selectedFloor, setSelectedFloor] = useState(availableFloors[0] || '1');
  const [isWaitingForClick, setIsWaitingForClick] = useState(false);

  const handleFloorNext = () => {
    setStep(2);
  };

  const handleUseGPS = () => {
    onComplete({
      method: 'gps',
      floor: selectedFloor,
      building: building
    });
  };

  const handleManualSelect = () => {
    setStep(3);
    setIsWaitingForClick(true);
    
    // Signal to parent that we're waiting for map click
    onComplete({
      method: 'manual',
      floor: selectedFloor,
      building: building,
      waitingForClick: true
    });
  };

  const handleSkip = () => {
    // Use default position
    onComplete({
      method: 'default',
      floor: selectedFloor,
      building: building,
      position: { lat: 43.0143425, lng: -81.19856355 } // M building default
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-80 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 relative">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
        >
          <X size={24} />
        </button>

        <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">
          Welcome to Campus Navigation
        </h2>

        {/* Step 1: Floor Selection */}
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-700 mb-4">
                Step 1: Select Your Current Floor
              </h3>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-600 mb-2">
                  Building {building} - Floor:
                </label>
                <select
                  value={selectedFloor}
                  onChange={(e) => setSelectedFloor(e.target.value)}
                  className="w-full text-lg p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {availableFloors.map(floor => (
                    <option key={floor} value={floor}>
                      Floor {floor}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <button
              onClick={handleFloorNext}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              Next
            </button>

            <button
              onClick={handleSkip}
              className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-6 rounded-lg transition-colors text-sm"
            >
              Skip & Use Default Position
            </button>
          </div>
        )}

        {/* Step 2: Position Method Selection */}
        {step === 2 && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-700 mb-4">
                Step 2: Set Your Starting Position
              </h3>
              <p className="text-sm text-gray-600 mb-6">
                Choose how to set your current location on floor {selectedFloor}:
              </p>
            </div>

            <button
              onClick={handleUseGPS}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-6 rounded-lg transition-colors flex items-center justify-center gap-3"
            >
              <span className="text-2xl">🛰️</span>
              <span>Use GPS</span>
            </button>

            <button
              onClick={handleManualSelect}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-4 px-6 rounded-lg transition-colors flex items-center justify-center gap-3"
            >
              <span className="text-2xl">📍</span>
              <span>Select Manually on Map</span>
            </button>

            <button
              onClick={() => setStep(1)}
              className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-6 rounded-lg transition-colors text-sm"
            >
              ← Back
            </button>
          </div>
        )}

        {/* Step 3: Waiting for Manual Click */}
        {step === 3 && (
          <div className="space-y-6 text-center">
            <div className="animate-pulse">
              <div className="text-6xl mb-4">📍</div>
              <h3 className="text-lg font-semibold text-gray-700 mb-2">
                Click on the map to set your position
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                The floor plan for floor {selectedFloor} is now visible.
                <br />
                Click where you are currently located.
              </p>
              <p className="text-xs text-gray-400">
                Your marker will appear after you click.
              </p>
            </div>

            <button
              onClick={() => setStep(2)}
              className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-6 rounded-lg transition-colors text-sm"
            >
              ← Back
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
