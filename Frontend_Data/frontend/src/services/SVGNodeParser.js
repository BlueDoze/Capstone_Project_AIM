/**
 * SVGNodeParser.js
 * 
 * Parse SVG floor plans to extract navigation nodes and convert coordinates
 * Ported from set_start_end.html lines 514-602
 */

/**
 * Convert SVG circle coordinates to geographic lat/lng
 * @param {SVGCircleElement} nodeElement - SVG circle element
 * @param {SVGSVGElement} svgMap - Parent SVG document
 * @param {Object} overlayBounds - Leaflet bounds {north, south, east, west}
 * @returns {Object} - {lat, lng} geographic coordinates
 */
export function nodeToLatLng(nodeElement, svgMap, overlayBounds) {
  if (!nodeElement || !svgMap || !overlayBounds) {
    console.error('❌ Missing required parameters for nodeToLatLng');
    return null;
  }

  // Get SVG coordinates
  const cx = parseFloat(nodeElement.getAttribute('cx'));
  const cy = parseFloat(nodeElement.getAttribute('cy'));

  if (isNaN(cx) || isNaN(cy)) {
    console.error('❌ Invalid cx/cy attributes on node');
    return null;
  }

  // Create SVG point for transformation
  const svgPoint = svgMap.createSVGPoint();
  svgPoint.x = cx;
  svgPoint.y = cy;

  // Transform through any applied transforms (including rotation)
  const ctm = nodeElement.getCTM();
  const transformedPoint = svgPoint.matrixTransform(ctm);

  // Get the SVG element's bounding box in screen space
  const svgRect = svgMap.getBoundingClientRect();

  // Calculate normalized position within the SVG (0 to 1)
  const normX = transformedPoint.x / svgRect.width;
  const normY = transformedPoint.y / svgRect.height;

  // Map to geographic coordinates
  const west = overlayBounds.west || overlayBounds.getWest?.();
  const east = overlayBounds.east || overlayBounds.getEast?.();
  const north = overlayBounds.north || overlayBounds.getNorth?.();
  const south = overlayBounds.south || overlayBounds.getSouth?.();

  const lng = west + normX * (east - west);
  const lat = north - normY * (north - south); // Y is inverted in screen coordinates

  return { lat, lng };
}

/**
 * Parse SVG document for navigation nodes and convert to geographic coordinates
 * @param {String} svgContent - SVG file content as string
 * @param {Object} overlayBounds - Leaflet bounds {north, south, east, west}
 * @returns {Object} - {nodePositions: {nodeId: {lat, lng}}, nodeSVGData: {nodeId: {cx, cy}}}
 */
export function parseSVGNodes(svgContent, overlayBounds) {
  if (!svgContent || !overlayBounds) {
    console.error('❌ Missing SVG content or bounds');
    return { nodePositions: {}, nodeSVGData: {} };
  }

  try {
    // Parse SVG string to DOM
    const parser = new DOMParser();
    const svgDoc = parser.parseFromString(svgContent, 'image/svg+xml');
    const svgMap = svgDoc.documentElement;

    if (svgMap.nodeName !== 'svg') {
      console.error('❌ Invalid SVG document');
      return { nodePositions: {}, nodeSVGData: {} };
    }

    const nodePositions = {};
    const nodeSVGData = {};

    // Find all circles with IDs (navigation nodes)
    const circles = svgMap.querySelectorAll('circle[id]');
    console.log(`🔍 Found ${circles.length} SVG circles with IDs`);

    circles.forEach(circle => {
      const nodeId = circle.getAttribute('id');
      
      // Skip circles that are not navigation nodes (e.g., visual decorations)
      if (nodeId.startsWith('_') || nodeId.includes('decoration')) {
        return;
      }

      const geoPos = nodeToLatLng(circle, svgMap, overlayBounds);
      
      if (geoPos) {
        nodePositions[nodeId] = geoPos;
        nodeSVGData[nodeId] = {
          cx: parseFloat(circle.getAttribute('cx')),
          cy: parseFloat(circle.getAttribute('cy')),
          r: parseFloat(circle.getAttribute('r')) || 5
        };
      }
    });

    console.log(`✅ Parsed ${Object.keys(nodePositions).length} navigation nodes from SVG`);
    
    return { nodePositions, nodeSVGData };
  } catch (error) {
    console.error('❌ Error parsing SVG:', error);
    return { nodePositions: {}, nodeSVGData: {} };
  }
}

/**
 * Build navigation graph from JSON definition and SVG coordinates
 * Ported from set_start_end.html lines 547-602
 * 
 * @param {String} svgContent - SVG file content
 * @param {Object} graphDefinition - Navigation graph from all_node_data.json
 * @param {Object} overlayBounds - Leaflet bounds
 * @returns {Object} - {graph, nodePositions, nodeMetadata}
 */
export function buildNavigationGraph(svgContent, graphDefinition, overlayBounds) {
  console.log("🔨 Building navigation graph...");

  if (!svgContent || !graphDefinition || !overlayBounds) {
    console.error('❌ Missing required parameters for graph building');
    return { graph: {}, nodePositions: {}, nodeMetadata: {} };
  }

  try {
    const parser = new DOMParser();
    const svgDoc = parser.parseFromString(svgContent, 'image/svg+xml');
    const svgMap = svgDoc.documentElement;

    const graph = {};
    const nodePositions = {};
    const nodeMetadata = {};

    // Parse all nodes defined in the graph
    Object.entries(graphDefinition).forEach(([nodeId, nodeData]) => {
      const nodeElement = svgMap.getElementById(nodeId);

      if (nodeElement && nodeElement.nodeName === 'circle') {
        const geoPosition = nodeToLatLng(nodeElement, svgMap, overlayBounds);
        
        if (geoPosition) {
          nodePositions[nodeId] = geoPosition;

          nodeMetadata[nodeId] = {
            connections: nodeData.connections || [],
            represents: nodeData.represents || null,
            svgPosition: {
              cx: parseFloat(nodeElement.getAttribute('cx')),
              cy: parseFloat(nodeElement.getAttribute('cy'))
            }
          };

          console.log(`✓ Node ${nodeId}: ${geoPosition.lat.toFixed(6)}, ${geoPosition.lng.toFixed(6)}`);
        } else {
          console.warn(`⚠️ Could not convert node ${nodeId} to lat/lng`);
        }
      } else {
        console.error(`✗ Node ${nodeId} NOT FOUND in SVG or not a circle!`);
      }
    });

    // Build graph with connections
    Object.entries(nodeMetadata).forEach(([nodeId, data]) => {
      if (!nodePositions[nodeId]) return;

      graph[nodeId] = {
        connections: data.connections.filter(connectedId => {
          if (!nodePositions[connectedId]) {
            console.warn(`⚠️ Connected node ${connectedId} not found in positions`);
            return false;
          }
          return true;
        }),
        represents: data.represents
      };
    });

    console.log("✅ Navigation graph built!");
    console.log(`   Nodes: ${Object.keys(nodePositions).length}`);
    console.log(`   Connections: ${Object.values(graph).reduce((sum, node) => sum + node.connections.length, 0)}`);

    return { graph, nodePositions, nodeMetadata };
  } catch (error) {
    console.error('❌ Error building navigation graph:', error);
    return { graph: {}, nodePositions: {}, nodeMetadata: {} };
  }
}

/**
 * Fetch and parse SVG floor plan from server
 * @param {String} building - Building ID (e.g., "M", "H")
 * @param {String} floor - Floor number
 * @returns {Promise<String>} - SVG content as string
 */
export async function fetchSVGFloorPlan(building, floor) {
  try {
    const svgUrl = `/leaflet-assets/Floorplans/Building ${building}/${building}${floor}.svg`;
    console.log(`📥 Fetching SVG: ${svgUrl}`);
    
    const response = await fetch(svgUrl);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const svgContent = await response.text();
    console.log(`✅ SVG loaded (${svgContent.length} bytes)`);
    
    return svgContent;
  } catch (error) {
    console.error(`❌ Failed to fetch SVG for Building ${building} Floor ${floor}:`, error);
    return null;
  }
}

/**
 * Load complete navigation data for a building floor
 * Combines JSON graph definition with SVG coordinate parsing
 * 
 * @param {String} building - Building ID
 * @param {String} floor - Floor number
 * @param {Object} graphDefinition - Navigation graph from all_node_data.json
 * @param {Object} overlayBounds - Leaflet bounds for the floor
 * @returns {Promise<Object>} - Complete navigation data
 */
export async function loadFloorNavigationData(building, floor, graphDefinition, overlayBounds) {
  console.log(`📂 Loading navigation data for Building ${building} Floor ${floor}`);

  const svgContent = await fetchSVGFloorPlan(building, floor);
  
  if (!svgContent) {
    console.error('❌ Failed to load SVG content');
    return null;
  }

  const navData = buildNavigationGraph(svgContent, graphDefinition, overlayBounds);

  return {
    ...navData,
    building,
    floor,
    svgContent
  };
}

export default {
  nodeToLatLng,
  parseSVGNodes,
  buildNavigationGraph,
  fetchSVGFloorPlan,
  loadFloorNavigationData
};
