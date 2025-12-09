                console.log(`🎯 Step 2: Navigating on Floor ${dest.endFloor} from ${connectorNodeId} to ${dest.roomId}`);
                
                // Get destination node candidates
                const destNodeArray = endFloorData.roomToNode[dest.roomId];
                if (!destNodeArray || destNodeArray.length === 0) {
                    alert(`Could not find room ${dest.roomId} on Floor ${dest.endFloor}`);
                    floorInstructions.innerHTML = originalInstructions;
                    continueBtn.disabled = false;
                    continueBtn.style.opacity = '1';
                    return;
                }
                const destinationNodeId = destNodeArray[0];
                console.log(`📍 Destination node: ${destinationNodeId}`);
                
                // Find path from connector to destination node
                const path = findShortestPath(graphData.graph, connectorNodeId, destinationNodeId);
                if (!path || path.length === 0) {
                    alert(`Could not find path from ${connectorNodeId} to ${destinationNodeId} on Floor ${dest.endFloor}`);
                    floorInstructions.innerHTML = originalInstructions;
                    continueBtn.disabled = false;
                    continueBtn.style.opacity = '1';
                    return;
                }
                
                console.log(`✅ Found path on Floor ${dest.endFloor}:`, path);
                
                // Get the building overlay
                const buildingOverlay = window.buildingOverlays[dest.building];
                
                // Determine final object (door or room center) based on object type
                let finalObjectId = null;
                
                if (dest.objectType === 'room') {
                    // Get the room's door list
                    const doorList = endFloorData.objects?.rooms?.[dest.roomId];
                    
                    if (doorList && doorList.length > 0) {
                        // Find the closest door to the CONNECTOR POSITION (user's new starting point)
                        // NOT the original user position - this is the key difference for multi-floor
                        console.log(`🚪 Room ${dest.roomId} has ${doorList.length} door(s)`);
                        console.log(`📍 Finding closest door from connector position:`, connectorPos);
                        
                        let closestDoorId = null;
                        let minDistance = Infinity;
                        
                        doorList.forEach((doorId) => {
                            const doorElement = svgMap.getElementById(doorId);
                            if (doorElement) {
                                const doorCenter = objectToLatLng(doorElement, svgMap, buildingOverlay);
                                if (doorCenter) {
                                    // Calculate distance from CONNECTOR position (where user arrives on new floor)
                                    const distance = connectorPos.distanceTo(doorCenter);
                                    console.log(`   🚪 Door ${doorId}: ${distance.toFixed(2)}m from connector`);
                                    if (distance < minDistance) {
                                        minDistance = distance;
                                        closestDoorId = doorId;
                                    }
                                }
                            } else {
                                console.warn(`⚠️ Door ${doorId} not found in SVG`);
                            }
                        });
                        
                        finalObjectId = closestDoorId || doorList[0];
                        console.log(`✅ Selected closest door: ${finalObjectId} (${minDistance.toFixed(2)}m from connector)`);
                    } else {
                        // No doors defined, use room center
                        finalObjectId = dest.roomId;
                        console.log(`⚠️ No doors found for room ${dest.roomId}, using room center`);
                    }
                } else if (dest.objectType === 'exit') {
                    // For exits, use the exit center
                    finalObjectId = dest.roomId;
                    console.log(`✅ Using exit center: ${finalObjectId}`);
                }
                
                // Draw the path on the map
                drawPathOnMap(path, graphData.nodePositions, map, svgMap, true, finalObjectId, buildingOverlay);
