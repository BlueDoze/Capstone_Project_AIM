/**
 * NavigationNodesOverlay.jsx
 * 
 * Interactive navigation nodes overlay for floor plans
 * Shows clickable nodes with type-based styling
 */

import React, { useState } from 'react';
import { CircleMarker, Popup } from 'react-leaflet';

/**
 * Navigation Nodes Overlay Component
 * Renders navigation graph nodes as interactive markers
 * 
 * @param {Array} nodes - Array of node objects with {id, position: {lat, lng}, type, represents}
 * @param {Function} onNodeClick - Callback when node is clicked
 * @param {Array} highlightedNodes - Array of node IDs to highlight
 * @param {Boolean} showLabels - Whether to show node labels
 * @param {Boolean} visible - Whether nodes are visible
 */
export default function NavigationNodesOverlay({
  nodes = [],
  onNodeClick = null,
  highlightedNodes = [],
  showLabels = false,
  visible = true
}) {
  const [hoveredNode, setHoveredNode] = useState(null);

  if (!visible || !nodes || nodes.length === 0) {
    return null;
  }

  const getNodeColor = (node, isHighlighted, isHovered) => {
    if (isHighlighted) return '#e74c3c'; // Red for highlighted
    if (isHovered) return '#f39c12'; // Orange for hovered
    
    // Color by node type
    switch (node.type) {
      case 'room':
        return '#27ae60'; // Green
      case 'stairs':
        return '#f39c12'; // Orange
      case 'elevator':
        return '#9b59b6'; // Purple
      case 'entrance':
      case 'exit':
        return '#16a085'; // Teal
      case 'bathroom':
        return '#3498db'; // Blue
      case 'intersection':
      case 'turn':
        return '#95a5a6'; // Gray
      default:
        return '#3498db'; // Default blue
    }
  };

  const getNodeRadius = (isHighlighted, isHovered) => {
    if (isHighlighted) return 8;
    if (isHovered) return 6;
    return 4;
  };

  return (
    <>
      {nodes.map((node) => {
        const isHighlighted = highlightedNodes.includes(node.id);
        const isHovered = hoveredNode === node.id;
        const color = getNodeColor(node, isHighlighted, isHovered);
        const radius = getNodeRadius(isHighlighted, isHovered);

        if (!node.position || !node.position.lat || !node.position.lng) {
          return null;
        }

        return (
          <CircleMarker
            key={node.id}
            center={[node.position.lat, node.position.lng]}
            radius={radius}
            pathOptions={{
              color: '#ffffff',
              weight: 2,
              fillColor: color,
              fillOpacity: 0.8
            }}
            eventHandlers={{
              click: () => onNodeClick && onNodeClick(node),
              mouseover: () => setHoveredNode(node.id),
              mouseout: () => setHoveredNode(null)
            }}
          >
            {(showLabels || isHovered) && (
              <Popup>
                <div className="text-sm">
                  <strong>{node.name || node.id}</strong>
                  {node.type && (
                    <div className="text-xs text-gray-600">
                      Type: {node.type}
                    </div>
                  )}
                  {node.represents && (
                    <div className="text-xs text-gray-600">
                      Room: {node.represents}
                    </div>
                  )}
                  {onNodeClick && (
                    <div className="mt-2 text-xs text-blue-600 cursor-pointer">
                      Click to navigate →
                    </div>
                  )}
                </div>
              </Popup>
            )}
          </CircleMarker>
        );
      })}
    </>
  );
}

/**
 * Path Highlighting Component
 * Highlights nodes along a navigation path
 */
export function PathNodesOverlay({ path, nodePositions }) {
  if (!path || !nodePositions || path.length === 0) {
    return null;
  }

  return (
    <>
      {path.map((nodeId, index) => {
        const position = nodePositions[nodeId];
        if (!position) return null;

        let color = '#f1c40f'; // Yellow for middle nodes
        if (index === 0) color = '#27ae60'; // Green for start
        if (index === path.length - 1) color = '#e74c3c'; // Red for end

        return (
          <CircleMarker
            key={`path-${nodeId}`}
            center={[position.lat, position.lng]}
            radius={6}
            pathOptions={{
              color: '#ffffff',
              weight: 2,
              fillColor: color,
              fillOpacity: 0.9
            }}
          >
            <Popup>
              <div className="text-sm font-semibold">
                {index === 0 && '🟢 Start'}
                {index === path.length - 1 && '🔴 Destination'}
                {index > 0 && index < path.length - 1 && `Waypoint ${index}`}
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </>
  );
}
