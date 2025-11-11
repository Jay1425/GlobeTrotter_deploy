/**
 * Itinerary Manager for GlobeTrotter
 * Handles itinerary section management and interactions
 */

class ItineraryManager {
    constructor() {
        this.sectionCounter = 0;
        this.tripId = null;
        this.cities = new Map();
        this.activities = new Map();
        this.initialize();
    }

    initialize() {
        // Get trip ID and initial section count
        const rootEl = document.getElementById('itinerary-root');
        this.tripId = rootEl?.dataset.tripId;
        this.sectionCounter = parseInt(rootEl?.dataset.sectionCount || '0', 10);

        // Initialize datepickers
        this.initializeDatepickers();

        // Setup event listeners
        this.setupEventListeners();

        // Initialize cities autocomplete
        this.initializeCitySearch();
    }

    initializeDatepickers() {
        // Initialize date range pickers for each section
        document.querySelectorAll('.date-range-picker').forEach(picker => {
            flatpickr(picker, {
                mode: "range",
                dateFormat: "Y-m-d",
                minDate: "today",
                onChange: (dates) => {
                    if (dates.length === 2) {
                        const sectionId = picker.closest('.section-card').dataset.section;
                        this.updateSectionDates(sectionId, dates[0], dates[1]);
                    }
                }
            });
        });
    }

    setupEventListeners() {
        // Add section button
        document.getElementById('add-section-btn')?.addEventListener('click', () => {
            this.addNewSection();
        });

        // Save button
        document.querySelector('.btn-primary')?.addEventListener('click', () => {
            this.saveItinerary();
        });

        // Handle section removal
        document.addEventListener('click', (e) => {
            if (e.target.closest('.remove-btn')) {
                const section = e.target.closest('.section-card');
                if (section) {
                    this.removeSection(section.dataset.section);
                }
            }
        });
    }

    initializeCitySearch() {
        const cityInputs = document.querySelectorAll('.city-search-input');
        cityInputs.forEach(input => {
            const autocomplete = new google.maps.places.Autocomplete(input, {
                types: ['(cities)'],
                componentRestrictions: { country: 'in' }
            });

            autocomplete.addListener('place_changed', () => {
                const place = autocomplete.getPlace();
                if (!place.geometry) return;

                const sectionId = input.closest('.section-card').dataset.section;
                this.updateSectionCity(sectionId, place);
            });
        });
    }

    addNewSection() {
        this.sectionCounter++;
        const sectionsContainer = document.getElementById('itinerary-sections');
        
        const newSection = document.createElement('div');
        newSection.className = 'section-card animate-slideInScale';
        newSection.setAttribute('data-section', this.sectionCounter);
        newSection.style.animationDelay = '0.1s';
        
        newSection.innerHTML = `
            <div class="remove-btn tooltip" data-tooltip="Remove section" onclick="itineraryManager.removeSection(${this.sectionCounter})">
                <i class="fas fa-times text-sm"></i>
            </div>
            
            <div class="sequence-controls flex items-center mb-4">
                <div class="w-8 h-8 bg-indigo-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                    ${this.sectionCounter}
                </div>
                <div class="ml-4 flex-1">
                    <input type="text" class="city-search-input w-full p-2 border border-gray-200 rounded-lg focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 outline-none transition-all" 
                           placeholder="Search for a city...">
                </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div class="info-box">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center">
                            <i class="fas fa-calendar text-indigo-500 mr-2"></i>
                            <span class="font-semibold text-gray-700">Date Range</span>
                        </div>
                        <input type="text" class="date-range-picker text-gray-600 bg-transparent border-none outline-none text-right w-36" 
                               placeholder="Select dates">
                    </div>
                </div>
                
                <div class="info-box">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center">
                            <i class="fas fa-rupee-sign text-green-500 mr-2"></i>
                            <span class="font-semibold text-gray-700">Budget</span>
                        </div>
                        <input type="number" class="budget-input text-gray-600 bg-transparent border-none outline-none text-right w-24" 
                               placeholder="₹0" onchange="itineraryManager.updateSectionBudget(${this.sectionCounter}, this.value)">
                    </div>
                </div>
            </div>
            
            <div class="activities-container">
                <h4 class="text-lg font-semibold text-gray-800 mb-3">Activities</h4>
                <div class="activities-list space-y-2"></div>
                <button class="add-activity-btn mt-3 px-4 py-2 text-sm text-indigo-600 border border-indigo-200 rounded-lg hover:bg-indigo-50 transition-colors"
                        onclick="itineraryManager.showActivitySearch(${this.sectionCounter})">
                    <i class="fas fa-plus mr-2"></i>Add Activity
                </button>
            </div>
        `;
        
        sectionsContainer.appendChild(newSection);
        
        // Initialize new city search
        this.initializeCitySearch();
        
        // Initialize new datepicker
        this.initializeDatepickers();
        
        // Scroll to new section
        newSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    removeSection(sectionId) {
        const section = document.querySelector(`[data-section="${sectionId}"]`);
        if (section) {
            section.style.transform = 'translateX(-100%)';
            section.style.opacity = '0';
            setTimeout(() => {
                section.remove();
                this.updateSequenceNumbers();
                this.updateTotalBudget();
            }, 300);
        }
    }

    updateSequenceNumbers() {
        document.querySelectorAll('.section-card').forEach((section, index) => {
            const number = index + 1;
            section.setAttribute('data-section', number);
            const sequenceNumber = section.querySelector('.sequence-controls .bg-indigo-600');
            if (sequenceNumber) {
                sequenceNumber.textContent = number;
            }
        });
        this.sectionCounter = document.querySelectorAll('.section-card').length;
    }

    updateSectionCity(sectionId, place) {
        const section = document.querySelector(`[data-section="${sectionId}"]`);
        if (!section) return;

        const cityData = {
            placeId: place.place_id,
            name: place.name,
            coordinates: {
                lat: place.geometry.location.lat(),
                lng: place.geometry.location.lng()
            },
            formatted_address: place.formatted_address
        };

        this.cities.set(sectionId, cityData);

        // Update city search input with formatted name
        const input = section.querySelector('.city-search-input');
        if (input) {
            input.value = place.formatted_address;
        }

        // Fetch and populate nearby attractions
        this.fetchNearbyAttractions(sectionId, cityData.coordinates);
    }

    async fetchNearbyAttractions(sectionId, coordinates) {
        const service = new google.maps.places.PlacesService(document.createElement('div'));
        
        const request = {
            location: coordinates,
            radius: '50000',
            type: ['tourist_attraction']
        };

        service.nearbySearch(request, (results, status) => {
            if (status === google.maps.places.PlacesServiceStatus.OK) {
                const attractions = results.slice(0, 10).map(place => ({
                    id: place.place_id,
                    name: place.name,
                    rating: place.rating,
                    photos: place.photos?.length > 0 ? [place.photos[0].getUrl()] : [],
                    vicinity: place.vicinity
                }));

                // Store attractions for this section
                this.activities.set(sectionId, attractions);

                // Show activity suggestions
                this.showActivitySuggestions(sectionId, attractions);
            }
        });
    }

    showActivitySuggestions(sectionId, attractions) {
        const section = document.querySelector(`[data-section="${sectionId}"]`);
        if (!section) return;

        const container = section.querySelector('.activities-list');
        if (!container) return;

        container.innerHTML = attractions.map(attraction => `
            <div class="activity-suggestion p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                 onclick="itineraryManager.addActivity(${sectionId}, '${attraction.id}')">
                <div class="flex items-center justify-between">
                    <div>
                        <h5 class="font-medium text-gray-800">${attraction.name}</h5>
                        <p class="text-sm text-gray-600">${attraction.vicinity}</p>
                    </div>
                    <div class="flex items-center text-sm text-gray-500">
                        <span class="text-yellow-500 mr-1">${'★'.repeat(Math.round(attraction.rating || 0))}</span>
                        <span>${attraction.rating || 'N/A'}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    addActivity(sectionId, activityId) {
        const section = document.querySelector(`[data-section="${sectionId}"]`);
        if (!section) return;

        const activities = this.activities.get(sectionId) || [];
        const activity = activities.find(a => a.id === activityId);
        if (!activity) return;

        const activityList = section.querySelector('.activities-list');
        const existingActivity = activityList.querySelector(`[data-activity-id="${activityId}"]`);
        
        if (existingActivity) {
            existingActivity.classList.add('bg-red-50');
            setTimeout(() => {
                existingActivity.classList.remove('bg-red-50');
            }, 1000);
            return;
        }

        const activityEl = document.createElement('div');
        activityEl.className = 'selected-activity p-3 bg-white border border-gray-200 rounded-lg animate-fadeInUp';
        activityEl.setAttribute('data-activity-id', activityId);
        
        activityEl.innerHTML = `
            <div class="flex items-center justify-between">
                <div>
                    <h5 class="font-medium text-gray-800">${activity.name}</h5>
                    <p class="text-sm text-gray-600">${activity.vicinity}</p>
                </div>
                <button class="text-red-500 hover:text-red-700 transition-colors"
                        onclick="itineraryManager.removeActivity(${sectionId}, '${activityId}')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Insert at the top of the list
        activityList.insertBefore(activityEl, activityList.firstChild);
    }

    removeActivity(sectionId, activityId) {
        const section = document.querySelector(`[data-section="${sectionId}"]`);
        if (!section) return;

        const activity = section.querySelector(`[data-activity-id="${activityId}"]`);
        if (activity) {
            activity.style.transform = 'translateX(-100%)';
            activity.style.opacity = '0';
            setTimeout(() => {
                activity.remove();
            }, 300);
        }
    }

    updateSectionDates(sectionId, startDate, endDate) {
        const section = document.querySelector(`[data-section="${sectionId}"]`);
        if (!section) return;

        // Update any UI elements that show the dates
        const dateDisplay = section.querySelector('.date-display');
        if (dateDisplay) {
            const formattedStart = startDate.toLocaleDateString();
            const formattedEnd = endDate.toLocaleDateString();
            dateDisplay.textContent = `${formattedStart} - ${formattedEnd}`;
        }
    }

    updateSectionBudget(sectionId, budget) {
        const budgetValue = parseFloat(budget) || 0;
        console.log(`Section ${sectionId} budget updated: ₹${budgetValue}`);
        this.updateTotalBudget();
    }

    updateTotalBudget() {
        const budgetInputs = document.querySelectorAll('.budget-input');
        let totalBudget = 0;

        budgetInputs.forEach(input => {
            const value = parseFloat(input.value) || 0;
            totalBudget += value;
        });

        // Update total budget display
        const totalBudgetDisplay = document.querySelector('.text-3xl.font-bold.text-indigo-600');
        if (totalBudgetDisplay) {
            totalBudgetDisplay.textContent = `₹${totalBudget.toLocaleString('en-IN')}`;
        }
    }

    async saveItinerary() {
        if (!this.tripId) {
            showNotification('No trip ID found', 'error');
            return;
        }

        const sections = [];
        document.querySelectorAll('.section-card').forEach(section => {
            const sectionId = section.dataset.section;
            const cityData = this.cities.get(sectionId);
            const dateRange = section.querySelector('.date-range-picker').value;
            const budget = parseFloat(section.querySelector('.budget-input').value) || 0;
            
            const activities = Array.from(section.querySelectorAll('.selected-activity'))
                .map(activity => ({
                    id: activity.dataset.activityId,
                    name: activity.querySelector('h5').textContent,
                    location: activity.querySelector('p').textContent
                }));

            sections.push({
                order: parseInt(sectionId),
                city: cityData,
                dateRange,
                budget,
                activities
            });
        });

        const saveBtn = document.querySelector('.btn-primary');
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Saving...';
        saveBtn.disabled = true;

        try {
            const response = await fetch(`/api/trips/${this.tripId}/itinerary`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sections })
            });

            const data = await response.json();
            
            if (data.ok) {
                showNotification('Itinerary saved successfully!', 'success');
                
                // Update route visualization if available
                if (window.tripRouteVisualizer) {
                    window.tripRouteVisualizer.displayTripRoute();
                }
            } else {
                throw new Error(data.message || 'Failed to save itinerary');
            }
        } catch (error) {
            console.error('Error saving itinerary:', error);
            showNotification('Failed to save itinerary', 'error');
        } finally {
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
        }
    }

    showActivitySearch(sectionId) {
        const section = document.querySelector(`[data-section="${sectionId}"]`);
        if (!section) return;

        const cityData = this.cities.get(sectionId);
        if (!cityData) {
            showNotification('Please select a city first', 'error');
            return;
        }

        // Show the activity suggestions
        const attractions = this.activities.get(sectionId) || [];
        this.showActivitySuggestions(sectionId, attractions);
    }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    window.itineraryManager = new ItineraryManager();
});
