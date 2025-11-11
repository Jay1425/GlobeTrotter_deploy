/**
 * Enhanced City Search with Google Maps Integration
 * Extends the existing city search functionality with interactive maps
 */

class CitySearchWithMaps {
    constructor() {
        this.mapManager = null;
        this.selectedCities = [];
        this.currentSearchResults = [];
        this.initializeMapIntegration();
    }

    async initializeMapIntegration() {
        // Wait for Google Maps to load
        if (typeof google !== 'undefined') {
            this.setupMapsIntegration();
        } else {
            // Load Google Maps API if not already loaded
            this.loadGoogleMapsAPI();
        }
    }

    loadGoogleMapsAPI() {
        const script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyBD5kYDTg0BYcJbuPGFP5f4JqWWL7mJyzA&libraries=places&callback=initCitySearchMaps`;
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);
        
        // Set global callback
        window.initCitySearchMaps = () => {
            this.setupMapsIntegration();
        };
    }

    setupMapsIntegration() {
        this.mapManager = new GlobeTrotterMaps('AIzaSyBD5kYDTg0BYcJbuPGFP5f4JqWWL7mJyzA');
        
        // Initialize map in city search page
        if (document.getElementById('city-search-map')) {
            this.initializeCitySearchMap();
        }

        // Enhance existing search functionality
        this.enhanceSearchWithMaps();
    }

    async initializeCitySearchMap() {
        await this.mapManager.initMap('city-search-map', {
            zoom: 6,
            center: { lat: 20.5937, lng: 78.9629 } // Center of India
        });

        // Load and display all available cities
        this.loadAllCitiesOnMap();
    }

    async loadAllCitiesOnMap() {
        try {
            const response = await fetch('/api/search/cities?limit=100');
            const data = await response.json();
            
            if (data.cities) {
                data.cities.forEach(city => {
                    this.mapManager.addCityMarker(city);
                });
                
                // Fit map to show all cities
                this.mapManager.fitMapToCities(data.cities);
                this.currentSearchResults = data.cities;
            }
        } catch (error) {
            console.error('Failed to load cities on map:', error);
        }
    }

    enhanceSearchWithMaps() {
        // Hook into existing search functionality
        const originalSearch = window.searchCities;
        
        window.searchCities = async (query, filters) => {
            // Call original search function
            if (originalSearch) {
                await originalSearch(query, filters);
            }
            
            // Update map with search results
            this.updateMapWithSearchResults(query, filters);
        };

        // Add map toggle button to search results
        this.addMapToggleButton();
    }

    async updateMapWithSearchResults(query, filters) {
        if (!this.mapManager) return;

        try {
            // Build search params
            const params = new URLSearchParams();
            if (query) params.append('query', query);
            if (filters.country) params.append('country', filters.country);
            if (filters.cost) params.append('cost_filter', filters.cost);
            params.append('limit', '50');

            const response = await fetch(`/api/search/cities?${params}`);
            const data = await response.json();
            
            if (data.cities) {
                // Clear existing markers
                this.mapManager.clearMarkers();
                
                // Add markers for search results
                data.cities.forEach(city => {
                    this.mapManager.addCityMarker(city);
                });
                
                // Fit map to show results
                if (data.cities.length > 0) {
                    this.mapManager.fitMapToCities(data.cities);
                }
                
                this.currentSearchResults = data.cities;
                this.updateSearchResultsCount(data.cities.length);
            }
        } catch (error) {
            console.error('Failed to update map with search results:', error);
        }
    }

    addMapToggleButton() {
        const searchContainer = document.querySelector('.search-container');
        if (!searchContainer) return;

        const mapToggleContainer = document.createElement('div');
        mapToggleContainer.className = 'map-toggle-container mt-4';
        mapToggleContainer.innerHTML = `
            <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-gray-800">Search Results</h3>
                <button id="toggle-map-view" class="flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
                    <i class="fas fa-map-marker-alt"></i>
                    <span>Show Map</span>
                </button>
            </div>
        `;

        // Insert after search form
        const searchForm = document.querySelector('.search-form');
        if (searchForm) {
            searchForm.parentNode.insertBefore(mapToggleContainer, searchForm.nextSibling);
        }

        // Add map container (initially hidden)
        const mapContainer = document.createElement('div');
        mapContainer.innerHTML = `
            <div id="city-search-map-container" class="hidden mt-6">
                <div class="bg-white rounded-xl shadow-lg overflow-hidden">
                    <div class="p-4 border-b border-gray-200">
                        <div class="flex items-center justify-between">
                            <h4 class="font-semibold text-gray-800">City Locations</h4>
                            <div id="map-results-count" class="text-sm text-gray-600"></div>
                        </div>
                    </div>
                    <div id="city-search-map" style="height: 500px; width: 100%;"></div>
                    <div id="route-info" class="p-4"></div>
                </div>
            </div>
        `;
        
        mapToggleContainer.appendChild(mapContainer);

        // Add toggle functionality
        this.setupMapToggle();
    }

    setupMapToggle() {
        const toggleButton = document.getElementById('toggle-map-view');
        const mapContainer = document.getElementById('city-search-map-container');
        
        if (!toggleButton || !mapContainer) return;

        let mapVisible = false;

        toggleButton.addEventListener('click', async () => {
            mapVisible = !mapVisible;
            
            if (mapVisible) {
                mapContainer.classList.remove('hidden');
                toggleButton.innerHTML = `
                    <i class="fas fa-list"></i>
                    <span>Show List</span>
                `;
                
                // Initialize map if not already done
                if (!this.mapManager?.map) {
                    await this.initializeCitySearchMap();
                } else {
                    // Update with current search results
                    this.mapManager.clearMarkers();
                    this.currentSearchResults.forEach(city => {
                        this.mapManager.addCityMarker(city);
                    });
                    if (this.currentSearchResults.length > 0) {
                        this.mapManager.fitMapToCities(this.currentSearchResults);
                    }
                }
            } else {
                mapContainer.classList.add('hidden');
                toggleButton.innerHTML = `
                    <i class="fas fa-map-marker-alt"></i>
                    <span>Show Map</span>
                `;
            }
        });
    }

    updateSearchResultsCount(count) {
        const countElement = document.getElementById('map-results-count');
        if (countElement) {
            countElement.textContent = `${count} cities found`;
        }
    }

    // Add city selection for trip planning
    enableCitySelection() {
        const mapElement = document.getElementById('city-search-map');
        if (!mapElement) return;

        // Add selection controls
        const selectionControls = document.createElement('div');
        selectionControls.className = 'selected-cities-panel bg-white p-4 border-t border-gray-200';
        selectionControls.innerHTML = `
            <div class="flex items-center justify-between mb-3">
                <h4 class="font-semibold text-gray-800">Selected Cities (<span id="selected-count">0</span>)</h4>
                <button id="clear-selection" class="text-red-600 hover:text-red-700 text-sm">
                    <i class="fas fa-times mr-1"></i>Clear All
                </button>
            </div>
            <div id="selected-cities-list" class="flex flex-wrap gap-2 mb-3"></div>
            <button id="plan-route" class="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 transition-colors disabled:bg-gray-400" disabled>
                <i class="fas fa-route mr-2"></i>Plan Route
            </button>
        `;

        mapElement.parentNode.appendChild(selectionControls);

        // Setup selection functionality
        this.setupCitySelection();
    }

    setupCitySelection() {
        const selectedCitiesList = document.getElementById('selected-cities-list');
        const selectedCount = document.getElementById('selected-count');
        const planRouteBtn = document.getElementById('plan-route');
        const clearSelectionBtn = document.getElementById('clear-selection');

        // Override marker click to enable selection
        const originalAddCityMarker = this.mapManager.addCityMarker.bind(this.mapManager);
        
        this.mapManager.addCityMarker = (city, options = {}) => {
            const marker = originalAddCityMarker(city, options);
            
            if (marker) {
                marker.addListener('click', () => {
                    this.toggleCitySelection(city);
                    this.updateSelectionUI();
                });
            }
            
            return marker;
        };

        // Clear selection handler
        clearSelectionBtn?.addEventListener('click', () => {
            this.selectedCities = [];
            this.updateSelectionUI();
            this.mapManager.directionsRenderer.setDirections({ routes: [] });
        });

        // Plan route handler
        planRouteBtn?.addEventListener('click', () => {
            if (this.selectedCities.length >= 2) {
                this.mapManager.displayTripRoute(this.selectedCities);
            }
        });
    }

    toggleCitySelection(city) {
        const existingIndex = this.selectedCities.findIndex(c => c.id === city.id);
        
        if (existingIndex >= 0) {
            // Remove from selection
            this.selectedCities.splice(existingIndex, 1);
        } else {
            // Add to selection
            this.selectedCities.push(city);
        }
    }

    updateSelectionUI() {
        const selectedCitiesList = document.getElementById('selected-cities-list');
        const selectedCount = document.getElementById('selected-count');
        const planRouteBtn = document.getElementById('plan-route');

        if (selectedCount) {
            selectedCount.textContent = this.selectedCities.length;
        }

        if (selectedCitiesList) {
            selectedCitiesList.innerHTML = this.selectedCities.map((city, index) => `
                <div class="flex items-center space-x-2 bg-indigo-100 px-3 py-1 rounded-full text-sm">
                    <span class="bg-indigo-600 text-white w-5 h-5 rounded-full flex items-center justify-center text-xs">${index + 1}</span>
                    <span>${city.name}</span>
                    <button onclick="removeCityFromSelection('${city.id}')" class="text-indigo-700 hover:text-indigo-900">
                        <i class="fas fa-times text-xs"></i>
                    </button>
                </div>
            `).join('');
        }

        if (planRouteBtn) {
            planRouteBtn.disabled = this.selectedCities.length < 2;
        }
    }
}

// Global function for removing cities from selection
window.removeCityFromSelection = function(cityId) {
    if (window.citySearchWithMaps) {
        const city = window.citySearchWithMaps.selectedCities.find(c => c.id === cityId);
        if (city) {
            window.citySearchWithMaps.toggleCitySelection(city);
            window.citySearchWithMaps.updateSelectionUI();
        }
    }
};

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('city-search-container')) {
        window.citySearchWithMaps = new CitySearchWithMaps();
    }
});
