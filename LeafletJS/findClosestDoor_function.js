        // Find the closest door to the user's position
        function findClosestDoor(doorList, svgMap, overlay, userPosition) {
            if (!doorList || doorList.length === 0) return null;
            if (doorList.length === 1) return doorList[0];
            
            let closestDoor = null;
            let minDistance = Infinity;
            
            doorList.forEach(doorId => {
                const doorElement = svgMap.getElementById(doorId);
                if (doorElement) {
                    try {
                        const doorCenter = objectToLatLng(doorElement, svgMap, overlay);
                        const distance = userPosition.distanceTo(doorCenter);
                        
                        console.log(`📏 Door ${doorId} distance: ${distance.toFixed(2)}m`);
                        
                        if (distance < minDistance) {
                            minDistance = distance;
                            closestDoor = doorId;
                        }
                    } catch (error) {
                        console.warn(`⚠️ Could not calculate position for door ${doorId}:`, error);
                    }
                } else {
                    console.warn(`⚠️ Door element ${doorId} not found in SVG`);
                }
            });
            
            if (closestDoor) {
                console.log(`✅ Closest door: ${closestDoor} (${minDistance.toFixed(2)}m away)`);
            }
            
            return closestDoor || doorList[0]; // Fallback to first door if calculation fails
        }
