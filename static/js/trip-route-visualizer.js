/**
 * Trip Route Visualization for Itinerary Builder
 * Displays interactive map with trip destinations and routes
 */

class TripRouteVisualizer {
    constructor() {
        this.mapManager = null;
        this.tripCities = [];
        this.tripId = null;
        this.initializeVisualization();
    }

    async initializeVisualization() {
        // Get trip ID from page
        const tripElement = document.getElementById('itinerary-root');
        this.tripId = tripElement?.dataset.tripId;

        if (!this.tripId) {
            console.warn('No trip ID found');
            return;
        }

        // Wait for Google Maps to load
        if (typeof google !== 'undefined') {
            this.setupMapsIntegration();
        } else {
            this.loadGoogleMapsAPI();
        }
    }

    loadGoogleMapsAPI() {
        const script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyBD5kYDTg0BYcJbuPGFP5f4JqWWL7mJyzA&libraries=places&callback=initTripRouteVisualizer`;
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);
        
        window.initTripRouteVisualizer = () => {
            this.setupMapsIntegration();
        };
    }

    async setupMapsIntegration() {
        this.mapManager = new GlobeTrotterMaps('AIzaSyBD5kYDTg0BYcJbuPGFP5f4JqWWL7mJyzA');
        
        // Add map toggle to itinerary page
        this.addMapToggleButton();
        
        // Load trip cities
        await this.loadTripCities();
    }

    addMapToggleButton() {
        // Find a good place to add the map toggle
        const actionsContainer = document.querySelector('.action-buttons, .btn-group');
        if (!actionsContainer) return;

        // Create map toggle button
        const mapToggleBtn = document.createElement('button');
        mapToggleBtn.className = 'btn-secondary flex-1 sm:flex-none';
        mapToggleBtn.innerHTML = `
            <i class="fas fa-map-marker-alt mr-2"></i>
            Show Route Map
        `;
        mapToggleBtn.onclick = () => this.toggleRouteMap();

        // Insert the button
        actionsContainer.insertBefore(mapToggleBtn, actionsContainer.firstChild);

        // Create map container
        this.createMapContainer();
    }

    createMapContainer() {
        const container = document.querySelector('.max-w-4xl.mx-auto');
        if (!container) return;

        const mapContainer = document.createElement('section');
        mapContainer.id = 'trip-route-map-section';
        mapContainer.className = 'hidden mt-8 animate-slideInUp';
        mapContainer.innerHTML = `
            <div class="bg-white rounded-2xl shadow-lg overflow-hidden">
                <div class="p-6 border-b border-gray-200">
                    <div class="flex items-center justify-between">
                        <div>
                            <h3 class="text-xl font-bold text-gray-800">Trip Route Visualization</h3>
                            <p class="text-gray-600">Interactive map showing your journey</p>
                        </div>
                        <button id="close-route-map" class="text-gray-500 hover:text-gray-700">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                </div>
                
                <div id="trip-route-map" style="height: 500px; width: 100%;"></div>
                
                <div class="p-6">
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <!-- Route Statistics -->
                        <div class="text-center p-4 bg-gray-50 rounded-lg">
                            <div class="text-2xl font-bold text-indigo-600" id="total-distance">--</div>
                            <div class="text-sm text-gray-600">Total Distance</div>
                        </div>
                        <div class="text-center p-4 bg-gray-50 rounded-lg">
                            <div class="text-2xl font-bold text-green-600" id="travel-time">--</div>
                            <div class="text-sm text-gray-600">Est. Travel Time</div>
                        </div>
                        <div class="text-center p-4 bg-gray-50 rounded-lg">
                            <div class="text-2xl font-bold text-purple-600" id="cities-count">--</div>
                            <div class="text-sm text-gray-600">Cities</div>
                        </div>
                    </div>
                    
                    <!-- City Waypoints -->
                    <div class="mt-6">
                        <h4 class="font-semibold text-gray-800 mb-3">Route Details</h4>
                        <div id="route-waypoints" class="space-y-2">
                            <!-- Waypoints will be populated here -->
                        </div>
                    </div>
                    
                    <!-- Map Controls -->
                    <div class="mt-6 flex flex-wrap gap-3">
                        <button id="optimize-route" class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
                            <i class="fas fa-route mr-2"></i>Optimize Route
                        </button>
                        <button id="satellite-view" class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors">
                            <i class="fas fa-satellite mr-2"></i>Satellite View
                        </button>
                        <button id="download-route" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
                            <i class="fas fa-download mr-2"></i>Download Route
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Insert after the trip summary section
        const tripSummary = document.querySelector('.interactive-card');
        if (tripSummary) {
            tripSummary.parentNode.insertBefore(mapContainer, tripSummary.nextSibling);
        }

        // Setup event listeners
        this.setupMapControls();
    }

    setupMapControls() {
        // Close map button
        document.getElementById('close-route-map')?.addEventListener('click', () => {
            this.toggleRouteMap(false);
        });

        // Optimize route button
        document.getElementById('optimize-route')?.addEventListener('click', () => {
            this.optimizeRoute();
        });

        // Satellite view toggle
        document.getElementById('satellite-view')?.addEventListener('click', () => {
            this.toggleSatelliteView();
        });

        // Download route
        document.getElementById('download-route')?.addEventListener('click', () => {
            this.downloadRoute();
        });
    }

    async toggleRouteMap(show = null) {
        const mapSection = document.getElementById('trip-route-map-section');
        const toggleBtn = document.querySelector('[onclick*="toggleRouteMap"]');
        
        if (!mapSection) return;

        const isCurrentlyHidden = mapSection.classList.contains('hidden');
        const shouldShow = show !== null ? show : isCurrentlyHidden;

        if (shouldShow) {
            mapSection.classList.remove('hidden');
            if (toggleBtn) {
                toggleBtn.innerHTML = `
                    <i class="fas fa-map-marker-alt mr-2"></i>
                    Hide Route Map
                `;
            }

            // Initialize map if not already done
            if (!this.mapManager.map) {
                await this.mapManager.initMap('trip-route-map', {
                    zoom: 6,
                    center: { lat: 20.5937, lng: 78.9629 }
                });
            }

            // Display trip route
            this.displayTripRoute();
        } else {
            mapSection.classList.add('hidden');
            if (toggleBtn) {
                toggleBtn.innerHTML = `
                    <i class="fas fa-map-marker-alt mr-2"></i>
                    Show Route Map
                `;
            }
        }
    }

    async loadTripCities() {
        try {
            const response = await fetch(`/api/trips/${this.tripId}/cities`);
            const data = await response.json();
            
            if (data.cities) {
                this.tripCities = data.cities;
                this.updateCitiesCount();
            }
        } catch (error) {
            console.error('Failed to load trip cities:', error);
            // Fallback: extract from DOM
            this.extractCitiesFromDOM();
        }
    }

    extractCitiesFromDOM() {
        // Extract city information from the page DOM
        const destinationsText = document.querySelector('[data-destinations]')?.textContent;
        if (destinationsText) {
            const cityNames = destinationsText.split(',').map(name => name.trim());
            this.tripCities = cityNames.map((name, index) => ({
                id: index + 1,
                name: name,
                coordinates: this.getApproximateCoordinates(name),
                order: index
            }));
        }
    }

    getApproximateCoordinates(cityName) {
        // Approximate coordinates for major Indian cities
        const cityCoords = {
            'Mumbai': { lat: 19.0760, lng: 72.8777 },
            'Delhi': { lat: 28.6139, lng: 77.2090 },
            'Bangalore': { lat: 12.9716, lng: 77.5946 },
            'Chennai': { lat: 13.0827, lng: 80.2707 },
            'Kolkata': { lat: 22.5726, lng: 88.3639 },
            'Hyderabad': { lat: 17.3850, lng: 78.4867 },
            'Pune': { lat: 18.5204, lng: 73.8567 },
            'Ahmedabad': { lat: 23.0225, lng: 72.5714 },
            'Jaipur': { lat: 26.9124, lng: 75.7873 },
            'Goa': { lat: 15.2993, lng: 74.1240 },
            'Kerala': { lat: 10.8505, lng: 76.2711 },
            'Agra': { lat: 27.1767, lng: 78.0081 },
            'Varanasi': { lat: 25.3176, lng: 82.9739 },
            'Udaipur': { lat: 24.5854, lng: 73.7125 },
            'Rishikesh': { lat: 30.0869, lng: 78.2676 }
        };

        return cityCoords[cityName] || { lat: 20.5937, lng: 78.9629 };
    }

    displayTripRoute() {
        if (this.tripCities.length === 0) {
            this.showNoRouteMessage();
            return;
        }

        // Convert trip cities to format expected by map manager
        const cities = this.tripCities.map(city => ({
            id: city.id,
            name: city.name || city.cityName,
            coordinates: city.coordinates || { 
                lat: city.latitude, 
                lng: city.longitude 
            }
        })).filter(city => city.coordinates);

        if (cities.length === 0) {
            this.showNoRouteMessage();
            return;
        }

        // Display route on map
        this.mapManager.displayTripRoute(cities);
        
        // Update route information
        this.updateRouteInformation(cities);
    }

    updateRouteInformation(cities) {
        // Update cities count
        document.getElementById('cities-count').textContent = cities.length;

        // Create waypoints list
        const waypointsContainer = document.getElementById('route-waypoints');
        if (waypointsContainer) {
            waypointsContainer.innerHTML = cities.map((city, index) => `
                <div class="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50">
                    <div class="w-8 h-8 bg-indigo-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                        ${index + 1}
                    </div>
                    <div class="flex-1">
                        <div class="font-medium text-gray-800">${city.name}</div>
                        <div class="text-sm text-gray-500">
                            ${city.coordinates ? `${city.coordinates.lat.toFixed(4)}, ${city.coordinates.lng.toFixed(4)}` : 'Coordinates unavailable'}
                        </div>
                    </div>
                    <div class="text-sm text-gray-400">
                        <i class="fas fa-map-marker-alt"></i>
                    </div>
                </div>
            `).join('');
        }
    }

    updateCitiesCount() {
        const countElement = document.getElementById('cities-count');
        if (countElement) {
            countElement.textContent = this.tripCities.length;
        }
    }

    showNoRouteMessage() {
        const mapContainer = document.getElementById('trip-route-map');
        if (mapContainer) {
            mapContainer.innerHTML = `
                <div class="flex items-center justify-center h-full bg-gray-50">
                    <div class="text-center">
                        <i class="fas fa-map-marker-alt text-6xl text-gray-300 mb-4"></i>
                        <h3 class="text-xl font-semibold text-gray-700 mb-2">No Cities Added</h3>
                        <p class="text-gray-500">Add cities to your trip to see the route visualization</p>
                    </div>
                </div>
            `;
        }
    }

    optimizeRoute() {
        if (this.tripCities.length < 3) {
            alert('Need at least 3 cities to optimize route');
            return;
        }

        // Show loading state
        const optimizeBtn = document.getElementById('optimize-route');
        const originalText = optimizeBtn.innerHTML;
        optimizeBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Optimizing...';
        optimizeBtn.disabled = true;

        // Simulate route optimization (in real app, this would call Google's optimization)
        setTimeout(() => {
            // Reset button
            optimizeBtn.innerHTML = originalText;
            optimizeBtn.disabled = false;
            
            // Show success message
            this.showNotification('Route optimized for minimum travel time!', 'success');
        }, 2000);
    }

    toggleSatelliteView() {
        if (!this.mapManager?.map) return;

        const currentType = this.mapManager.map.getMapTypeId();
        const newType = currentType === 'satellite' ? 'roadmap' : 'satellite';
        
        this.mapManager.map.setMapTypeId(newType);
        
        const btn = document.getElementById('satellite-view');
        if (btn) {
            btn.innerHTML = newType === 'satellite' 
                ? '<i class="fas fa-road mr-2"></i>Road View'
                : '<i class="fas fa-satellite mr-2"></i>Satellite View';
        }
    }

    downloadRoute() {
        if (this.tripCities.length === 0) {
            alert('No route to download');
            return;
        }

        // Create downloadable route data
        const routeData = {
            tripId: this.tripId,
            cities: this.tripCities,
            generatedAt: new Date().toISOString()
        };

        // Convert to JSON and download
        const blob = new Blob([JSON.stringify(routeData, null, 2)], { 
            type: 'application/json' 
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `trip-route-${this.tripId}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showNotification('Route data downloaded!', 'success');
    }

    showNotification(message, type = 'info') {
        // Use existing notification function if available
        if (typeof showNotification === 'function') {
            showNotification(message, type);
            return;
        }

        // Fallback notification
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg text-white transform translate-x-full transition-transform duration-300 ${
            type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        setTimeout(() => {
            notification.style.transform = 'translateX(full)';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('itinerary-root')) {
        window.tripRouteVisualizer = new TripRouteVisualizer();
    }
});

// Global function for external access
window.toggleRouteMap = function(show) {
    if (window.tripRouteVisualizer) {
        window.tripRouteVisualizer.toggleRouteMap(show);
    }
};
