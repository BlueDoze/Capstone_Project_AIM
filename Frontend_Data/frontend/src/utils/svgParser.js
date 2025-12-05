/**
 * SVG Parser Utility
 * 
 * Extracts node positions from SVG floor plans and builds navigation graphs
 * Based on the LeafletJS set_start_end.html implementation
 */

/**
 * Load and parse SVG file to extract node positions
 * 
 * @param {string} svgUrl - URL to the SVG floor plan
 * @param {Object} navigationGraph - Navigation graph definition from all_node_data.json
 * @param {Array} bounds - Leaflet bounds [[south, west], [north, east]]
 * @returns {Promise<Object>} - {nodePositions, nodeMetadata, graph}
 */
export async function parseSVGNodes(svgUrl, navigationGraph, bounds) {
  try {
    console.log(`🔍 Parsing SVG nodes from: ${svgUrl}`);
    
    // Fetch SVG content
    const response = await fetch(svgUrl);
    if (!response.ok) {
      throw new Error(`Failed to load SVG: ${response.statusText}`);
    }
    
    const svgText = await response.text();
    
    // Parse SVG into DOM
    const parser = new DOMParser();
    const svgDoc = parser.parseFromString(svgText, 'image/svg+xml');
    const svgElement = svgDoc.documentElement;
    
    // Check for parsing errors
    const parserError = svgDoc.querySelector('parsererror');
    if (parserError) {
      throw new Error('SVG parsing error');
    }
    
    // Get SVG viewBox for coordinate conversion
    const viewBox = svgElement.viewBox.baseVal || {
      x: 0,
      y: 0,
      width: svgElement.width.baseVal.value || 1000,
      height: svgElement.height.baseVal.value || 1000
    };
    
    console.log(`📐 SVG ViewBox:`, viewBox);
    console.log(`🗺️ Map Bounds:`, bounds);
    
    const nodePositions = {};
    const nodeMetadata = {};
    const graph = {};
    
    // Extract bounds
    const [[south, west], [north, east]] = bounds;
    
    // Process each node in the navigation graph
    Object.entries(navigationGraph).forEach(([nodeId, nodeData]) => {
      // Find the SVG element by ID
      const nodeElement = svgElement.getElementById(nodeId);
      
      if (nodeElement) {
        // Get node position from SVG (cx, cy for circles)
        const cx = parseFloat(nodeElement.getAttribute('cx'));
        const cy = parseFloat(nodeElement.getAttribute('cy'));
        
        if (isNaN(cx) || isNaN(cy)) {
          console.warn(`⚠️ Node ${nodeId} has invalid coordinates`);
          return;
        }
        
        // Convert SVG coordinates to lat/lng
        const latLng = svgToLatLng(cx, cy, viewBox, bounds);
        
        nodePositions[nodeId] = latLng;
        
        nodeMetadata[nodeId] = {
          connections: nodeData.connections || [],
          represents: nodeData.represents || null,
          svgPosition: { cx, cy }
        };
        
        console.log(`✓ Node ${nodeId}: [${latLng.lat.toFixed(6)}, ${latLng.lng.toFixed(6)}]`);
      } else {
        console.warn(`⚠️ Node ${nodeId} NOT FOUND in SVG`);
      }
    });
    
    // Build graph with distance calculations
    Object.entries(nodeMetadata).forEach(([nodeId, data]) => {
      if (!nodePositions[nodeId]) return;
      
      graph[nodeId] = {
        position: [nodePositions[nodeId].lat, nodePositions[nodeId].lng],
        connections: data.connections.filter(connId => nodePositions[connId]),
        metadata: data.represents
      };
    });
    
    console.log(`✅ SVG parsing complete!`);
    console.log(`   Nodes extracted: ${Object.keys(nodePositions).length}`);
    
    return {
      nodePositions,
      nodeMetadata,
      graph,
      nodes: graph // Alias for compatibility
    };
    
  } catch (error) {
    console.error('❌ Error parsing SVG:', error);
    return {
      nodePositions: {},
      nodeMetadata: {},
      graph: {},
      nodes: {}
    };
  }
}

/**
 * Convert SVG coordinates to Leaflet lat/lng
 * Enhanced version that handles SVG transforms (rotation, scale, etc.)
 * Based on gps_toggle.html nodeToLatLng implementation
 * 
 * @param {number} svgX - X coordinate in SVG space
 * @param {number} svgY - Y coordinate in SVG space
 * @param {Object} viewBox - SVG viewBox {x, y, width, height}
 * @param {Array} bounds - Leaflet bounds [[south, west], [north, east]]
 * @returns {Object} - {lat, lng}
 */
function svgToLatLng(svgX, svgY, viewBox, bounds) {
  const [[south, west], [north, east]] = bounds;
  
  // Normalize SVG coordinates (0 to 1)
  const normX = (svgX - viewBox.x) / viewBox.width;
  const normY = (svgY - viewBox.y) / viewBox.height;
  
  // Map to geographic coordinates
  const lng = west + normX * (east - west);
  const lat = north - normY * (north - south); // Y is inverted in SVG
  
  return { lat, lng };
}

/**
 * Convert SVG node element to lat/lng with transform support
 * Handles rotation and other SVG transforms
 * Based on gps_toggle.html implementation
 * 
 * @param {Element} nodeElement - SVG circle or other element
 * @param {Element} svgElement - Parent SVG element
 * @param {Array} rotatedCorners - Array of 4 rotated corner points [{lat, lng}, ...]
 * @returns {Object} - {lat, lng}
 */
export function nodeToLatLngWithTransforms(nodeElement, svgElement, rotatedCorners) {
  try {
    // Create SVG point for coordinate transformation
    const svgPoint = svgElement.createSVGPoint();
    svgPoint.x = parseFloat(nodeElement.getAttribute('cx'));
    svgPoint.y = parseFloat(nodeElement.getAttribute('cy'));
    
    // Apply all transforms (including rotation)
    const ctm = nodeElement.getCTM();
    const transformedPoint = ctm ? svgPoint.matrixTransform(ctm) : svgPoint;
    
    // Get SVG dimensions
    const svgRect = svgElement.getBoundingClientRect();
    
    // Calculate normalized position (0 to 1)
    const normX = transformedPoint.x / svgRect.width;
    const normY = transformedPoint.y / svgRect.height;
    
    // Map to geographic coordinates using rotated corners
    if (rotatedCorners && rotatedCorners.length === 4) {
      const [topLeft, topRight, bottomRight, bottomLeft] = rotatedCorners;
      
      // Interpolate latitude
      const latTop = topLeft.lat + normX * (topRight.lat - topLeft.lat);
      const latBottom = bottomLeft.lat + normX * (bottomRight.lat - bottomLeft.lat);
      const lat = latTop + normY * (latBottom - latTop);
      
      // Interpolate longitude
      const lngTop = topLeft.lng + normX * (topRight.lng - topLeft.lng);
      const lngBottom = bottomLeft.lng + normX * (bottomRight.lng - bottomLeft.lng);
      const lng = lngTop + normY * (lngBottom - lngTop);
      
      return { lat, lng };
    }
    
    // Fallback to simple conversion if no rotated corners
    console.warn('No rotated corners provided, using simple conversion');
    const viewBox = svgElement.viewBox.baseVal || {
      x: 0,
      y: 0,
      width: svgElement.width.baseVal.value || 1000,
      height: svgElement.height.baseVal.value || 1000
    };
    
    return svgToLatLng(svgPoint.x, svgPoint.y, viewBox, 
      [[43.0139203, -81.1989228], [43.0147647, -81.1982043]]);
    
  } catch (error) {
    console.error('Error converting node to lat/lng:', error);
    return null;
  }
}

/**
 * Merge navigation graph with SVG-parsed positions
 * 
 * @param {Object} navigationGraph - Graph from all_node_data.json
 * @param {Object} svgParsedData - Data from parseSVGNodes
 * @returns {Object} - Enhanced navigation data with positions
 */
export function mergeNavigationData(navigationGraph, svgParsedData) {
  const enhancedGraph = {};
  
  Object.entries(navigationGraph).forEach(([nodeId, nodeData]) => {
    enhancedGraph[nodeId] = {
      ...nodeData,
      position: svgParsedData.graph[nodeId]?.position || null,
      geoPosition: svgParsedData.nodePositions[nodeId] || null
    };
  });
  
  return {
    navigationGraph: enhancedGraph,
    nodes: enhancedGraph, // Alias
    nodePositions: svgParsedData.nodePositions
  };
}
