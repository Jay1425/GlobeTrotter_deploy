/**
 * Google Maps Integration for GlobeTrotter
 * API Key: AIzaSyBD5kYDTg0BYcJbuPGFP5f4JqWWL7mJyzA
 */

class GlobeTrotterMaps {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.map = null;
        this.markers = [];
        this.directionsService = null;
        this.directionsRenderer = null;
        this.infoWindow = null;
    }

    // Initialize Google Maps
    async initMap(containerId, options = {}) {
        const defaultOptions = {
            zoom: 6,
            center: { lat: 20.5937, lng: 78.9629 }, // Center of India
            mapTypeId: 'roadmap',
            styles: [
                {
                    featureType: 'poi',
                    elementType: 'labels',
                    stylers: [{ visibility: 'off' }]
                }
            ]
        };

        const mapOptions = { ...defaultOptions, ...options };
        
        this.map = new google.maps.Map(document.getElementById(containerId), mapOptions);
        this.directionsService = new google.maps.DirectionsService();
        this.directionsRenderer = new google.maps.DirectionsRenderer({
            suppressMarkers: true,
            polylineOptions: {
                strokeColor: '#667eea',
                strokeWeight: 4,
                strokeOpacity: 0.8
            }
        });
        this.directionsRenderer.setMap(this.map);
        this.infoWindow = new google.maps.InfoWindow();

        return this.map;
    }

    // Add markers for cities with custom info
    addCityMarker(city, options = {}) {
        if (!city.coordinates || !city.coordinates.lat || !city.coordinates.lng) {
            console.warn('City missing coordinates:', city.name);
            return null;
        }

        const markerOptions = {
            position: { lat: city.coordinates.lat, lng: city.coordinates.lng },
            map: this.map,
            title: city.name,
            icon: {
                url: this.getCityMarkerIcon(city.costIndex),
                scaledSize: new google.maps.Size(40, 40),
                anchor: new google.maps.Point(20, 40)
            },
            ...options
        };

        const marker = new google.maps.Marker(markerOptions);

        // Create info window content
        const infoContent = this.createCityInfoWindow(city);
        
        marker.addListener('click', () => {
            this.infoWindow.setContent(infoContent);
            this.infoWindow.open(this.map, marker);
        });

        this.markers.push(marker);
        return marker;
    }

    // Get marker icon based on cost index
    getCityMarkerIcon(costIndex) {
        const icons = {
            low: 'https://maps.google.com/mapfiles/ms/icons/green-dot.png',
            medium: 'https://maps.google.com/mapfiles/ms/icons/yellow-dot.png',
            high: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png'
        };
        return icons[costIndex] || icons.medium;
    }

    // Create info window content for cities
    createCityInfoWindow(city) {
        const stars = '★'.repeat(city.popularity) + '☆'.repeat(5 - city.popularity);
        
        return `
            <div class="city-info-window" style="max-width: 300px; font-family: 'Inter', sans-serif;">
                <div class="flex items-center justify-between mb-2">
                    <h3 class="text-lg font-bold text-gray-800">${city.name}</h3>
                    <span class="cost-badge cost-${city.costIndex}" style="
                        padding: 2px 8px; 
                        border-radius: 12px; 
                        font-size: 0.75rem; 
                        font-weight: 600;
                        background: ${this.getCostBadgeColor(city.costIndex)};
                        color: white;
                    ">${city.costIndex.toUpperCase()}</span>
                </div>
                <p class="text-gray-600 mb-2">${city.country}${city.region ? ', ' + city.region : ''}</p>
                <div class="flex items-center mb-2">
                    <span class="text-yellow-500 mr-2">${stars}</span>
                    <span class="text-sm text-gray-500">(${city.popularity}/5)</span>
                </div>
                ${city.description ? `<p class="text-gray-700 text-sm mb-3">${city.description}</p>` : ''}
                ${city.attractions && city.attractions.length ? `
                    <div class="mb-3">
                        <h4 class="font-semibold text-gray-800 mb-1">Top Attractions:</h4>
                        <ul class="text-sm text-gray-600">
                            ${city.attractions.slice(0, 3).map(attraction => `<li>• ${attraction}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                <div class="flex gap-2">
                    <button onclick="addCityToTrip('${city.id}')" class="bg-indigo-600 text-white px-3 py-1 rounded text-sm hover:bg-indigo-700 transition-colors">
                        Add to Trip
                    </button>
                    <button onclick="viewCityDetails('${city.id}')" class="bg-gray-200 text-gray-700 px-3 py-1 rounded text-sm hover:bg-gray-300 transition-colors">
                        View Details
                    </button>
                </div>
            </div>
        `;
    }

    // Get cost badge color
    getCostBadgeColor(costIndex) {
        const colors = {
            low: '#10B981',    // Green
            medium: '#F59E0B', // Yellow
            high: '#EF4444'    // Red
        };
        return colors[costIndex] || colors.medium;
    }

    // Display trip route with multiple cities
    displayTripRoute(cities) {
        if (cities.length < 2) {
            console.warn('Need at least 2 cities to display route');
            return;
        }

        // Clear existing markers and routes
        this.clearMarkers();
        this.directionsRenderer.setDirections({ routes: [] });

        // Add markers for all cities
        cities.forEach((city, index) => {
            this.addCityMarker(city, {
                label: {
                    text: (index + 1).toString(),
                    color: 'white',
                    fontWeight: 'bold'
                }
            });
        });

        // Create route waypoints
        if (cities.length === 2) {
            this.displayDirectRoute(cities[0], cities[1]);
        } else {
            this.displayMultiCityRoute(cities);
        }

        // Fit map to show all cities
        this.fitMapToCities(cities);
    }

    // Display direct route between two cities
    displayDirectRoute(startCity, endCity) {
        const request = {
            origin: { lat: startCity.coordinates.lat, lng: startCity.coordinates.lng },
            destination: { lat: endCity.coordinates.lat, lng: endCity.coordinates.lng },
            travelMode: google.maps.TravelMode.DRIVING,
            region: 'IN'
        };

        this.directionsService.route(request, (result, status) => {
            if (status === 'OK') {
                this.directionsRenderer.setDirections(result);
                this.displayRouteInfo(result.routes[0]);
            } else {
                console.error('Directions request failed:', status);
            }
        });
    }

    // Display multi-city route
    displayMultiCityRoute(cities) {
        if (cities.length < 3) return;

        const waypoints = cities.slice(1, -1).map(city => ({
            location: { lat: city.coordinates.lat, lng: city.coordinates.lng },
            stopover: true
        }));

        const request = {
            origin: { lat: cities[0].coordinates.lat, lng: cities[0].coordinates.lng },
            destination: { lat: cities[cities.length - 1].coordinates.lat, lng: cities[cities.length - 1].coordinates.lng },
            waypoints: waypoints,
            travelMode: google.maps.TravelMode.DRIVING,
            optimizeWaypoints: true,
            region: 'IN'
        };

        this.directionsService.route(request, (result, status) => {
            if (status === 'OK') {
                this.directionsRenderer.setDirections(result);
                this.displayRouteInfo(result.routes[0]);
            } else {
                console.error('Multi-city directions failed:', status);
            }
        });
    }

    // Display route information
    displayRouteInfo(route) {
        const leg = route.legs[0];
        const totalDistance = route.legs.reduce((sum, leg) => sum + leg.distance.value, 0);
        const totalDuration = route.legs.reduce((sum, leg) => sum + leg.duration.value, 0);

        const routeInfo = document.getElementById('route-info');
        if (routeInfo) {
            routeInfo.innerHTML = `
                <div class="route-summary bg-white p-4 rounded-lg shadow-lg">
                    <h4 class="font-bold text-gray-800 mb-2">Route Summary</h4>
                    <div class="flex justify-between text-sm">
                        <span>Total Distance: <strong>${(totalDistance / 1000).toFixed(0)} km</strong></span>
                        <span>Estimated Duration: <strong>${Math.round(totalDuration / 3600)}h ${Math.round((totalDuration % 3600) / 60)}m</strong></span>
                    </div>
                </div>
            `;
        }
    }

    // Fit map bounds to show all cities
    fitMapToCities(cities) {
        if (cities.length === 0) return;

        const bounds = new google.maps.LatLngBounds();
        cities.forEach(city => {
            if (city.coordinates) {
                bounds.extend({ lat: city.coordinates.lat, lng: city.coordinates.lng });
            }
        });

        this.map.fitBounds(bounds);
        
        // Ensure minimum zoom level
        google.maps.event.addListenerOnce(this.map, 'bounds_changed', () => {
            if (this.map.getZoom() > 15) {
                this.map.setZoom(15);
            }
        });
    }

    // Clear all markers
    clearMarkers() {
        this.markers.forEach(marker => marker.setMap(null));
        this.markers = [];
    }

    // Search nearby places
    searchNearbyPlaces(city, type = 'tourist_attraction') {
        if (!city.coordinates) return;

        const service = new google.maps.places.PlacesService(this.map);
        const request = {
            location: { lat: city.coordinates.lat, lng: city.coordinates.lng },
            radius: 50000, // 50km radius
            type: type
        };

        service.nearbySearch(request, (results, status) => {
            if (status === google.maps.places.PlacesServiceStatus.OK) {
                this.displayNearbyPlaces(results.slice(0, 10));
            }
        });
    }

    // Display nearby places as markers
    displayNearbyPlaces(places) {
        places.forEach(place => {
            const marker = new google.maps.Marker({
                position: place.geometry.location,
                map: this.map,
                title: place.name,
                icon: {
                    url: 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                    scaledSize: new google.maps.Size(25, 25)
                }
            });

            marker.addListener('click', () => {
                this.infoWindow.setContent(`
                    <div style="max-width: 200px;">
                        <h4 class="font-bold">${place.name}</h4>
                        <p class="text-sm text-gray-600">${place.vicinity}</p>
                        <div class="flex items-center mt-1">
                            <span class="text-yellow-500">${'★'.repeat(Math.round(place.rating || 0))}</span>
                            <span class="text-sm text-gray-500 ml-1">(${place.rating || 'N/A'})</span>
                        </div>
                    </div>
                `);
                this.infoWindow.open(this.map, marker);
            });

            this.markers.push(marker);
        });
    }
}

// Global functions for info window actions
window.addCityToTrip = function(cityId) {
    // Implement add to trip functionality
    console.log('Adding city to trip:', cityId);
    // You can call your existing API here
};

window.viewCityDetails = function(cityId) {
    // Implement view details functionality
    console.log('Viewing city details:', cityId);
    window.location.href = `/city/${cityId}`;
};

// Export for use in other files
window.GlobeTrotterMaps = GlobeTrotterMaps;
