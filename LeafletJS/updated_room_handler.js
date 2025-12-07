                                if (pathResult.path && pathResult.path.length > 0) {
                                    // Get the overlay for this building
                                    const buildingOverlay = window.currentOverlays.find(overlay => {
                                        return overlay.getElement().querySelector(`#${buildingName}`);
                                    }) || window.currentOverlays[0];
                                    
                                    // Find the closest door to the user's position
                                    const finalDoorId = findClosestDoor(doorList, svgMap, buildingOverlay, window.userPosition);
                                    
                                    console.log(`🚪 Selected door for ${roomId}: ${finalDoorId}`);
                                    
                                    drawPathOnMap(pathResult.path, graphData.nodePositions, map, svgMap, true, finalDoorId, buildingOverlay);
                                }
