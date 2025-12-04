import React, { useState, useEffect } from 'react';
import { Building, ChevronDown, Navigation, MapPin } from 'lucide-react';

/**
 * FloorSelector Component
 * 
 * Allows users to select different floors within a building
 * Displays available floors and highlights the current selection
 */
export default function FloorSelector({
  building,
  currentFloor,
  availableFloors = [],
  onFloorChange,
  className = '',
}) {
  const [isOpen, setIsOpen] = useState(false);

  if (!availableFloors || availableFloors.length === 0) {
    return null;
  }

  return (
    <div className={`floor-selector ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="floor-selector-button"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '12px 16px',
          background: 'white',
          border: '2px solid #667eea',
          borderRadius: '8px',
          cursor: 'pointer',
          fontSize: '14px',
          fontWeight: '600',
          color: '#667eea',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        }}
      >
        <Building size={20} />
        <span>
          {building} - Floor {currentFloor}
        </span>
        <ChevronDown
          size={16}
          style={{
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.2s',
          }}
        />
      </button>

      {isOpen && (
        <div
          className="floor-selector-dropdown"
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            marginTop: '8px',
            background: 'white',
            border: '2px solid #667eea',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            zIndex: 1000,
            minWidth: '200px',
          }}
        >
          {availableFloors.map((floor) => (
            <button
              key={floor.level}
              onClick={() => {
                onFloorChange(floor.level);
                setIsOpen(false);
              }}
              className="floor-option"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: 'none',
                background: currentFloor === floor.level ? '#667eea' : 'white',
                color: currentFloor === floor.level ? 'white' : '#333',
                fontSize: '14px',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'background 0.2s',
                borderBottom:
                  floor !== availableFloors[availableFloors.length - 1]
                    ? '1px solid #e0e0e0'
                    : 'none',
              }}
              onMouseEnter={(e) => {
                if (currentFloor !== floor.level) {
                  e.target.style.background = '#f5f5f5';
                }
              }}
              onMouseLeave={(e) => {
                if (currentFloor !== floor.level) {
                  e.target.style.background = 'white';
                }
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <MapPin size={16} />
                <span>
                  Floor {floor.level}
                  {floor.name && ` - ${floor.name}`}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * BuildingInfo Component
 * 
 * Displays information about the current building
 */
export function BuildingInfo({ building, info, className = '' }) {
  if (!info) return null;

  return (
    <div
      className={`building-info ${className}`}
      style={{
        background: 'white',
        padding: '16px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      }}
    >
      <h3 style={{ margin: '0 0 8px 0', fontSize: '18px', color: '#667eea' }}>
        Building {building}
      </h3>
      {info.name && (
        <p style={{ margin: '4px 0', fontSize: '14px', color: '#666' }}>
          {info.name}
        </p>
      )}
      {info.description && (
        <p style={{ margin: '8px 0 0 0', fontSize: '13px', color: '#888' }}>
          {info.description}
        </p>
      )}
    </div>
  );
}

/**
 * NavigationControls Component
 * 
 * Controls for starting/stopping navigation and showing current instructions
 */
export function NavigationControls({
  isNavigating,
  currentInstruction,
  onStartNavigation,
  onStopNavigation,
  onRecenter,
  className = '',
}) {
  return (
    <div
      className={`navigation-controls ${className}`}
      style={{
        background: 'white',
        padding: '16px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      }}
    >
      {isNavigating ? (
        <>
          {currentInstruction && (
            <div
              style={{
                marginBottom: '12px',
                padding: '12px',
                background: '#f0f4ff',
                borderRadius: '6px',
                borderLeft: '4px solid #667eea',
              }}
            >
              <p style={{ margin: 0, fontSize: '14px', color: '#333' }}>
                {currentInstruction}
              </p>
            </div>
          )}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={onRecenter}
              style={{
                flex: 1,
                padding: '10px',
                background: '#667eea',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
              }}
            >
              <Navigation size={16} />
              Recenter
            </button>
            <button
              onClick={onStopNavigation}
              style={{
                flex: 1,
                padding: '10px',
                background: '#e74c3c',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600',
              }}
            >
              Stop Navigation
            </button>
          </div>
        </>
      ) : (
        <button
          onClick={onStartNavigation}
          style={{
            width: '100%',
            padding: '12px',
            background: '#27ae60',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
          }}
        >
          <Navigation size={18} />
          Start Navigation
        </button>
      )}
    </div>
  );
}
