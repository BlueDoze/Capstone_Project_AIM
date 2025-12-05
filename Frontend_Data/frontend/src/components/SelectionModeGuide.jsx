import React, { useState } from 'react';
import { X, MapPin, Navigation, CheckCircle } from 'lucide-react';

/**
 * SelectionModeGuide Component
 * 
 * Interactive guide/tutorial overlay for the tap-to-navigate feature
 * Shows users how to use the interactive mobile map selection mode
 */
export default function SelectionModeGuide({ onClose, onSkip }) {
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    {
      icon: <MapPin size={48} className="text-green-500" />,
      title: "Set Your Starting Point",
      description: "Tap anywhere on the map to mark where you are currently located. A green marker (A) will appear.",
      tips: ["You can tap on any hallway, room, or corridor", "Zoom in for more precise positioning"]
    },
    {
      icon: <Navigation size={48} className="text-red-500" />,
      title: "Choose Your Destination",
      description: "Tap on the map again to set where you want to go. A red marker (B) will appear at your destination.",
      tips: ["Tap near your target room or location", "The system will find the nearest accessible point"]
    },
    {
      icon: <CheckCircle size={48} className="text-blue-500" />,
      title: "Get Directions",
      description: "The route will automatically calculate and display on the map with turn-by-turn directions.",
      tips: ["Follow the blue path on the map", "Swipe through step-by-step instructions", "Use the restart button to try a different route"]
    }
  ];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onClose();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const step = steps[currentStep];

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        animation: 'fadeIn 0.3s ease-out'
      }}
      onClick={onClose}
    >
      <div 
        style={{
          backgroundColor: 'white',
          borderRadius: '16px',
          maxWidth: '500px',
          width: '100%',
          padding: '32px',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
          position: 'relative',
          animation: 'slideUp 0.3s ease-out'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            color: '#666',
            padding: '4px'
          }}
        >
          <X size={24} />
        </button>

        {/* Icon */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          {step.icon}
        </div>

        {/* Title */}
        <h2 style={{
          fontSize: '24px',
          fontWeight: 'bold',
          color: '#2c3e50',
          textAlign: 'center',
          marginBottom: '16px'
        }}>
          {step.title}
        </h2>

        {/* Description */}
        <p style={{
          fontSize: '16px',
          color: '#555',
          textAlign: 'center',
          marginBottom: '24px',
          lineHeight: '1.6'
        }}>
          {step.description}
        </p>

        {/* Tips */}
        <div style={{
          backgroundColor: '#f8f9fa',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '24px'
        }}>
          <h4 style={{
            fontSize: '14px',
            fontWeight: '600',
            color: '#2c3e50',
            marginBottom: '8px'
          }}>
            💡 Tips:
          </h4>
          <ul style={{
            listStyle: 'none',
            padding: 0,
            margin: 0
          }}>
            {step.tips.map((tip, idx) => (
              <li key={idx} style={{
                fontSize: '14px',
                color: '#666',
                marginBottom: '4px',
                paddingLeft: '20px',
                position: 'relative'
              }}>
                <span style={{
                  position: 'absolute',
                  left: '0',
                  color: '#3498db'
                }}>•</span>
                {tip}
              </li>
            ))}
          </ul>
        </div>

        {/* Progress dots */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '8px',
          marginBottom: '24px'
        }}>
          {steps.map((_, idx) => (
            <div
              key={idx}
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: idx === currentStep ? '#3498db' : '#ddd',
                transition: 'background-color 0.3s ease'
              }}
            />
          ))}
        </div>

        {/* Navigation buttons */}
        <div style={{
          display: 'flex',
          gap: '12px',
          justifyContent: 'space-between'
        }}>
          {currentStep > 0 && (
            <button
              onClick={handlePrevious}
              style={{
                flex: 1,
                padding: '12px 24px',
                borderRadius: '8px',
                border: '2px solid #3498db',
                backgroundColor: 'white',
                color: '#3498db',
                fontSize: '16px',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              Previous
            </button>
          )}
          
          {currentStep === 0 && onSkip && (
            <button
              onClick={onSkip}
              style={{
                flex: 1,
                padding: '12px 24px',
                borderRadius: '8px',
                border: '2px solid #95a5a6',
                backgroundColor: 'white',
                color: '#7f8c8d',
                fontSize: '16px',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              Skip Tutorial
            </button>
          )}

          <button
            onClick={handleNext}
            style={{
              flex: 1,
              padding: '12px 24px',
              borderRadius: '8px',
              border: 'none',
              backgroundColor: '#3498db',
              color: 'white',
              fontSize: '16px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            {currentStep === steps.length - 1 ? "Get Started" : "Next"}
          </button>
        </div>
      </div>

      {/* CSS Animations */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        button:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        button:active {
          transform: translateY(0);
        }
      `}</style>
    </div>
  );
}
