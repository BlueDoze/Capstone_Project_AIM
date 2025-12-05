import React, { useState, useRef, useEffect } from 'react';
import { Send, Map as MapIcon, X, Navigation, Building2, Calendar, Moon, Sun, MessageSquare } from 'lucide-react';
import { MapContainer, TileLayer, GeoJSON, Polyline, useMap } from 'react-leaflet';
import MapNavigator from './components/MapNavigator';
import 'leaflet/dist/leaflet.css';

// Component to fit map bounds when data loads
function FitBounds({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [bounds, map]);
  return null;
}

export default function FanshaweNavigator() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I\'m Fanshawe Navigator. How can I help you find your way around campus today?' }
  ]);
  const [input, setInput] = useState('');
  const [showMap, setShowMap] = useState(false);
  const [geoJsonData, setGeoJsonData] = useState(null);
  const [mapBounds, setMapBounds] = useState(null);
  const [loading, setLoading] = useState(false);
  const [routeData, setRouteData] = useState(null);
  const [originBuilding, setOriginBuilding] = useState(null);
  const [destBuilding, setDestBuilding] = useState(null);
  const [buildingInfo, setBuildingInfo] = useState(null);
  const [darkMode, setDarkMode] = useState(false);
  const [sidebarVisible, setSidebarVisible] = useState(false);
  const [showIndoorMap, setShowIndoorMap] = useState(false);
  const [mapAction, setMapAction] = useState(null);
  const messagesEndRef = useRef(null);

  // Use relative URL since Flask serves the React app (same origin)
  const API_URL = '';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load GeoJSON data when map opens
  useEffect(() => {
    if (showMap && !geoJsonData) {
      loadGeoJSON();
    }
  }, [showMap]);

  const loadGeoJSON = async () => {
    try {
      const response = await fetch(`${API_URL}/api/geojson`);
      const data = await response.json();
      setGeoJsonData(data);
      
      // Calculate bounds
      if (data.features && data.features.length > 0) {
        const coordinates = data.features
          .filter(f => f.geometry && f.geometry.coordinates)
          .map(f => {
            if (f.geometry.type === 'Point') {
              return [[f.geometry.coordinates[1], f.geometry.coordinates[0]]];
            } else if (f.geometry.type === 'Polygon') {
              return f.geometry.coordinates[0].map(c => [c[1], c[0]]);
            }
            return [];
          })
          .flat();
        
        if (coordinates.length > 0) {
          const lats = coordinates.map(c => c[0]);
          const lngs = coordinates.map(c => c[1]);
          setMapBounds([
            [Math.min(...lats), Math.min(...lngs)],
            [Math.max(...lats), Math.max(...lngs)]
          ]);
        }
      }
    } catch (error) {
      console.error('Error loading GeoJSON:', error);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    const userInput = input;
    setInput('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mensagem: userInput })
      });

      const data = await response.json();

      // Add bot response
      const botResponse = {
        role: 'assistant',
        content: data.reply || data.resposta || 'Sorry, I couldn\'t process that request.'
      };
      setMessages(prev => [...prev, botResponse]);

      // Handle indoor navigation mapAction
      if (data.mapAction && data.mapAction.type === 'SHOW_ROUTE') {
        setMapAction(data.mapAction);
        // Removed: setShowIndoorMap(true); - Don't auto-open, let user click button
      }

      // If there's route data, handle it
      if (data.tipo === 'navegacao' && data.origem && data.destino) {
        try {
          const routeResponse = await fetch(`${API_URL}/api/calcular-rota`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              origem: data.origem,
              destino: data.destino
            })
          });
          const routeResult = await routeResponse.json();
          setRouteData(routeResult);
          
          // Automatically open map when route is calculated
          if (!showMap) {
            setShowMap(true);
          }
        } catch (error) {
          console.error('Error calculating route:', error);
        }
      }

      // If asking about building info, optionally show map
      if (data.tipo === 'info_predio') {
        // Could auto-open map here if desired
      }

    } catch (error) {
      console.error('Error sending message:', error);
      const errorResponse = {
        role: 'assistant',
        content: 'Sorry, there was an error processing your request. Please try again.'
      };
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleMap = () => {
    setShowMap(!showMap);
  };

  // Style for GeoJSON features
  const getFeatureStyle = (feature) => {
    const isCollege = feature.properties.name?.includes('Fanshawe') || 
                     feature.properties.amenity === 'college';
    
    // Check if this is part of a route
    let fillColor = isCollege ? '#764ba2' : '#bdc3c7';
    let fillOpacity = isCollege ? 0.3 : 0.1;
    
    if (routeData && feature.properties.ref) {
      if (feature.properties.ref === routeData.origem) {
        fillColor = '#27ae60'; // Green for origin
        fillOpacity = 0.7;
      } else if (feature.properties.ref === routeData.destino) {
        fillColor = '#e74c3c'; // Red for destination
        fillOpacity = 0.7;
      }
    }

    return {
      color: isCollege ? '#667eea' : '#95a5a6',
      weight: isCollege ? 3 : 2,
      fillOpacity: fillOpacity,
      fillColor: fillColor
    };
  };

  // Handle feature click
  const onEachFeature = (feature, layer) => {
    if (feature.properties) {
      const props = feature.properties;
      const nome = props.name || props.nome || 'Building';
      const ref = props.ref;

      // CLICK - Detailed info
      layer.on('click', async () => {
        if (ref) {
          try {
            const response = await fetch(`${API_URL}/api/predios/${ref}/info`);
            const data = await response.json();

            if (data.success && data.info) {
              setBuildingInfo(data);
            }
          } catch (error) {
            console.error('Error fetching building info:', error);
          }
        }
      });

      // Hover effects - only visual
      layer.on('mouseover', function() {
        this.setStyle({
          weight: 5,
          fillOpacity: 0.5
        });
      });

      layer.on('mouseout', function() {
        this.setStyle(getFeatureStyle(feature));
      });
    }
  };

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-100 transition-colors duration-200">
        {/* Header */}
        <div className="h-16 border-b border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 flex items-center transition-colors duration-200">
          <div className="max-w-full px-4 md:max-w-2xl md:px-6 lg:max-w-3xl lg:px-8 mx-auto w-full flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img 
                src="/Fanshawe_Icons/Pressbooks_Icon_Fanshawe-NorthStar_Red-removebg-preview.png" 
                alt="Fanshawe Logo" 
                className="w-10 h-10"
              />
              <h1 className="text-xl font-bold text-fanshawe-red">Fanshawe Navigator</h1>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-all duration-200"
                aria-label="Toggle Dark Mode"
              >
                {darkMode ? <Sun size={20} /> : <Moon size={20} />}
              </button>
              <button
                onClick={() => {
                  setMessages([
                    { role: 'assistant', content: 'Hello! I\'m Fanshawe Navigator. How can I help you find your way around campus today?' }
                  ]);
                  setRouteData(null);
                }}
                className="bg-fanshawe-red hover:bg-fanshawe-red-dark text-white px-4 py-2 rounded-lg transition-all duration-200"
              >
                New Chat
              </button>
            </div>
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Messages Area - Scrollable */}
          <div className="flex-1 overflow-y-auto p-6 relative">
            {/* Watermark background - Fixed position */}
            <div 
              className="fixed inset-0 flex items-center justify-center pointer-events-none"
              style={{
                backgroundImage: 'url(/Fanshawe_Icons/Fanshawe-removebg-preview.png)',
                backgroundPosition: 'center',
                backgroundRepeat: 'no-repeat',
                backgroundSize: '50%',
                opacity: darkMode ? 0.02 : 0.05,
                zIndex: 0
              }}
            />
            <div className="max-w-full px-4 md:max-w-2xl md:px-6 lg:max-w-3xl lg:px-8 mx-auto space-y-6 relative z-10">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[95%] sm:max-w-[90%] md:max-w-[85%] lg:max-w-[80%] rounded-lg p-4 shadow-md transition-all duration-200 ${
                      msg.role === 'user'
                        ? 'bg-fanshawe-red text-white border border-fanshawe-red-dark'
                        : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 border border-gray-300 dark:border-gray-600'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    
                    {/* Open Indoor Navigation Map Button */}
                    {msg.role === 'assistant' && idx === messages.length - 1 && mapAction && mapAction.type === 'OPEN_MAP' && (
                      <button
                        onClick={() => setShowIndoorMap(true)}
                        className="mt-3 w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-200 flex items-center justify-center gap-2 shadow-md"
                      >
                        <span className="text-xl">🗺️</span>
                        <span>View Indoor Navigation</span>
                      </button>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 border border-gray-300 dark:border-gray-600 rounded-lg p-4 shadow-md flex items-center gap-3 transition-all duration-200">
                    <img 
                      src="/Fanshawe_Icons/Pressbooks_Icon_Fanshawe-NorthStar_Red-removebg-preview.png" 
                      alt="Loading" 
                      className="w-6 h-6 animate-spin"
                    />
                    <p className="text-gray-600 dark:text-gray-400 font-semibold">Thinking...</p>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area with Quick Actions - Fixed at Bottom */}
          <div className="p-4 transition-colors duration-200 bg-gray-50 dark:bg-gray-900">
            <div className="max-w-full px-4 md:max-w-2xl md:px-6 lg:max-w-3xl lg:px-8 mx-auto space-y-3">
              {/* Input Bar - Gemini Style Pill */}
              <div className="flex items-center gap-3 bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 rounded-full shadow-xl px-6 py-4 transition-all duration-200 focus-within:border-fanshawe-red focus-within:ring-2 focus-within:ring-fanshawe-red">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={loading}
                  placeholder="Ask about campus locations, buildings, directions..."
                  className="flex-1 bg-transparent text-gray-800 dark:text-gray-100 focus:outline-none placeholder-gray-500 dark:placeholder-gray-400"
                />
                <button
                  onClick={handleSend}
                  disabled={loading}
                  className="bg-fanshawe-red hover:bg-fanshawe-red-dark text-white p-2 rounded-full transition-all duration-200 disabled:opacity-50 flex-shrink-0"
                  aria-label="Send Message"
                >
                  <Send size={20} />
                </button>
              </div>

              {/* Quick Action Chips - Single Row */}
              <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
                <button
                  onClick={toggleMap}
                  className="flex items-center gap-2 px-4 py-2 rounded-full border-2 border-gray-300 dark:border-gray-600 bg-transparent hover:bg-gray-100 dark:hover:bg-gray-700 text-sm transition-all duration-200 whitespace-nowrap flex-shrink-0"
                >
                  <MapIcon size={16} />
                  <span>Show Campus Map</span>
                </button>
                <button
                  onClick={() => {
                    setShowIndoorMap(true);
                    setMapAction({ type: 'INTERACTIVE_MODE', mode: 'selection' });
                  }}
                  className="flex items-center gap-2 px-4 py-2 rounded-full border-2 border-fanshawe-red dark:border-fanshawe-red bg-transparent hover:bg-fanshawe-red hover:text-white dark:hover:bg-fanshawe-red-dark text-sm transition-all duration-200 whitespace-nowrap flex-shrink-0"
                >
                  <Navigation size={16} />
                  <span>Indoor Navigation</span>
                </button>
                <button
                  onClick={() => setInput("How do I get from building A to building B?")}
                  className="flex items-center gap-2 px-4 py-2 rounded-full border-2 border-gray-300 dark:border-gray-600 bg-transparent hover:bg-gray-100 dark:hover:bg-gray-700 text-sm transition-all duration-200 whitespace-nowrap flex-shrink-0"
                >
                  <Navigation size={16} />
                  <span>Campus Navigation</span>
                </button>
                <button
                  onClick={() => setInput("What's in building A?")}
                  className="flex items-center gap-2 px-4 py-2 rounded-full border-2 border-gray-300 dark:border-gray-600 bg-transparent hover:bg-gray-100 dark:hover:bg-gray-700 text-sm transition-all duration-200 whitespace-nowrap flex-shrink-0"
                >
                  <Building2 size={16} />
                  <span>Building Information</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Map Modal */}
        {showMap && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={toggleMap}
          >
            <div 
              className="bg-white dark:bg-gray-800 rounded-lg w-[90%] h-[90%] flex flex-col border-2 border-gray-400 dark:border-gray-600 transition-colors duration-200"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-center p-4 border-b border-gray-300 dark:border-gray-700">
                <h3 className="text-xl font-bold text-gray-800 dark:text-gray-100">Campus Map</h3>
                <button
                  onClick={toggleMap}
                  className="text-gray-800 dark:text-gray-100 hover:text-gray-600 dark:hover:text-gray-400 transition-colors"
                >
                  <X size={24} />
                </button>
              </div>
              <div className="flex-1 overflow-hidden relative">
                {geoJsonData ? (
                  <>
                    <MapContainer
                      center={[43.0125, -81.2002]}
                      zoom={16}
                      style={{ height: '100%', width: '100%' }}
                      className="z-0"
                    >
                      <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      />
                      <GeoJSON 
                        data={geoJsonData} 
                        style={getFeatureStyle}
                        onEachFeature={onEachFeature}
                      />
                      {mapBounds && <FitBounds bounds={mapBounds} />}
                    </MapContainer>
                    
                    {/* Building Info Popup */}
                    {buildingInfo && (
                      <div className="absolute top-4 right-4 bg-white dark:bg-gray-800 rounded-lg shadow-2xl p-6 max-w-md z-10 border-2 border-fanshawe-red transition-colors duration-200">
                        <div className="flex justify-between items-start mb-4">
                          <h4 className="text-xl font-bold text-fanshawe-red">
                            {buildingInfo.info.nome}
                          </h4>
                          <button
                            onClick={() => setBuildingInfo(null)}
                            className="text-gray-500 dark:text-gray-400 hover:text-fanshawe-red transition-colors"
                          >
                            <X size={20} />
                          </button>
                        </div>
                        
                        <div className="space-y-3 text-gray-700 dark:text-gray-300">
                          {buildingInfo.info.descricao && (
                            <p className="text-sm">{buildingInfo.info.descricao}</p>
                          )}
                          
                          {buildingInfo.info.andares && buildingInfo.info.andares.length > 0 && (
                            <div>
                              <p className="font-semibold text-sm">🏢 Floors:</p>
                              <p className="text-sm">{buildingInfo.info.andares.join(', ')}</p>
                            </div>
                          )}
                          
                          {buildingInfo.info.facilidades && buildingInfo.info.facilidades.length > 0 && (
                            <div>
                              <p className="font-semibold text-sm">✨ Facilities:</p>
                              <ul className="text-sm list-disc list-inside">
                                {buildingInfo.info.facilidades.map((fac, idx) => (
                                  <li key={idx}>{fac}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {buildingInfo.info.salas_principais && buildingInfo.info.salas_principais.length > 0 && (
                            <div>
                              <p className="font-semibold text-sm">📚 Main Rooms:</p>
                              <ul className="text-sm list-disc list-inside">
                                {buildingInfo.info.salas_principais.slice(0, 5).map((sala, idx) => (
                                  <li key={idx}>
                                    {sala.numero} - {sala.tipo} (Floor {sala.andar})
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {buildingInfo.info.horario_funcionamento && (
                            <div>
                              <p className="font-semibold text-sm">🕐 Hours:</p>
                              <p className="text-sm">{buildingInfo.info.horario_funcionamento}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <p className="text-gray-800 dark:text-gray-100">Loading map...</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Indoor Navigation Map Modal */}
        {showIndoorMap && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4"
            onClick={() => {
              setShowIndoorMap(false);
              setMapAction(null);
            }}
          >
            <div 
              className="bg-white dark:bg-gray-800 rounded-lg w-full h-full max-w-7xl max-h-[95vh] flex flex-col shadow-2xl border-2 border-gray-400 dark:border-gray-600 overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-center px-6 py-4 border-b-2 border-gray-300 dark:border-gray-700 bg-gradient-to-r from-fanshawe-red to-red-600 flex-shrink-0">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  <Navigation size={24} />
                  Indoor Navigation - Building {mapAction?.building || 'M'}
                </h3>
                <button
                  onClick={() => {
                    setShowIndoorMap(false);
                    setMapAction(null);
                  }}
                  className="text-white hover:text-gray-200 transition-colors bg-white bg-opacity-20 rounded-full p-2 hover:bg-opacity-30"
                >
                  <X size={24} />
                </button>
              </div>
              <div className="flex-1 overflow-hidden relative">
                <MapNavigator
                  building={mapAction?.building || 'M'}
                  initialFloor={mapAction?.floor || '1'}
                  mapAction={mapAction}
                  onNavigationComplete={() => {
                    setShowIndoorMap(false);
                    setMapAction(null);
                  }}
                  className="absolute inset-0"
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
