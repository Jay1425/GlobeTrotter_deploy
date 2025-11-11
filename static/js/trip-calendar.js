/**
 * Trip Calendar Manager
 * Handles calendar view and timeline view for trip itineraries
 */

class TripCalendar {
    constructor(tripId) {
        this.tripId = tripId;
        this.calendar = null;
        this.events = [];
        this.destinations = [];
        this.currentEditingActivity = null;
        this.isDragging = false;
        
        this.initialize();
    }

    async initialize() {
        try {
            // Load trip data
            await this.loadTripData();
            
            // Initialize FullCalendar
            this.initializeCalendar();
            
            // Setup view toggles
            this.setupViewToggles();
            
            // Setup modals
            this.setupModals();
            
            // Setup event listeners
            this.setupEventListeners();
            
        } catch (error) {
            console.error('Error initializing trip calendar:', error);
            this.showNotification('Failed to load trip data', 'error');
        }
    }

    async loadTripData() {
        try {
            // Load destinations
            const destinationsResponse = await fetch(`/api/trips/${this.tripId}/cities`);
            if (destinationsResponse.ok) {
                const destinationsData = await destinationsResponse.json();
                this.destinations = destinationsData.cities || [];
            }

            // Load trip details for date range
            const tripResponse = await fetch(`/api/trips/${this.tripId}`);
            if (tripResponse.ok) {
                const tripData = await tripResponse.json();
                this.trip = tripData.trip || {};
            }

            // Generate events from destinations
            this.generateEventsFromDestinations();
            
        } catch (error) {
            console.error('Error loading trip data:', error);
            throw error;
        }
    }

    generateEventsFromDestinations() {
        this.events = [];
        
        this.destinations.forEach((destination, index) => {
            if (destination.date_range) {
                const [startDate, endDate] = this.parseDateRange(destination.date_range);
                
                if (startDate && endDate) {
                    // Create destination event
                    this.events.push({
                        id: `dest-${destination.id}`,
                        title: `📍 ${destination.name}`,
                        start: startDate,
                        end: this.addDays(endDate, 1), // Add 1 day for multi-day display
                        backgroundColor: '#667eea',
                        borderColor: '#4338ca',
                        classNames: ['destination-event'],
                        extendedProps: {
                            type: 'destination',
                            destinationId: destination.id,
                            destination: destination
                        }
                    });

                    // Generate sample activities for demonstration
                    this.generateSampleActivities(destination, startDate, endDate);
                }
            }
        });
    }

    generateSampleActivities(destination, startDate, endDate) {
        const activities = [
            { name: 'Morning Exploration', type: 'sightseeing', time: '09:00', duration: 3 },
            { name: 'Local Lunch', type: 'food', time: '13:00', duration: 1 },
            { name: 'Afternoon Activity', type: 'activity', time: '15:00', duration: 2 },
            { name: 'Evening Relaxation', type: 'leisure', time: '18:00', duration: 2 }
        ];

        const currentDate = new Date(startDate);
        const lastDate = new Date(endDate);

        while (currentDate <= lastDate) {
            activities.forEach((activity, index) => {
                const activityStart = new Date(currentDate);
                const [hours, minutes] = activity.time.split(':');
                activityStart.setHours(parseInt(hours), parseInt(minutes), 0, 0);
                
                const activityEnd = new Date(activityStart);
                activityEnd.setHours(activityStart.getHours() + activity.duration);

                this.events.push({
                    id: `activity-${destination.id}-${currentDate.getTime()}-${index}`,
                    title: `${this.getActivityIcon(activity.type)} ${activity.name}`,
                    start: activityStart.toISOString(),
                    end: activityEnd.toISOString(),
                    backgroundColor: this.getActivityColor(activity.type),
                    borderColor: this.getActivityBorderColor(activity.type),
                    classNames: ['activity-event'],
                    extendedProps: {
                        type: 'activity',
                        activityType: activity.type,
                        destinationId: destination.id,
                        cost: Math.floor(Math.random() * 1000) + 100,
                        notes: `Sample activity in ${destination.name}`
                    }
                });
            });

            currentDate.setDate(currentDate.getDate() + 1);
        }
    }

    getActivityIcon(type) {
        const icons = {
            'sightseeing': '🏛️',
            'food': '🍽️',
            'activity': '🎯',
            'leisure': '🧘',
            'transport': '🚗',
            'shopping': '🛍️'
        };
        return icons[type] || '📍';
    }

    getActivityColor(type) {
        const colors = {
            'sightseeing': '#8b5cf6',
            'food': '#f59e0b',
            'activity': '#ef4444',
            'leisure': '#10b981',
            'transport': '#6b7280',
            'shopping': '#ec4899'
        };
        return colors[type] || '#667eea';
    }

    getActivityBorderColor(type) {
        const colors = {
            'sightseeing': '#7c3aed',
            'food': '#d97706',
            'activity': '#dc2626',
            'leisure': '#059669',
            'transport': '#4b5563',
            'shopping': '#be185d'
        };
        return colors[type] || '#4338ca';
    }

    parseDateRange(dateRange) {
        try {
            const parts = dateRange.split(' to ');
            if (parts.length === 2) {
                return [new Date(parts[0].trim()), new Date(parts[1].trim())];
            }
        } catch (error) {
            console.error('Error parsing date range:', dateRange, error);
        }
        return [null, null];
    }

    addDays(date, days) {
        const result = new Date(date);
        result.setDate(result.getDate() + days);
        return result;
    }

    initializeCalendar() {
        const calendarEl = document.getElementById('calendar');
        this.calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,listWeek'
            },
            events: this.events,
            editable: true,
            droppable: true,
            dayMaxEvents: 3,
            moreLinkClick: 'popover',
            
            // Event handlers
            eventDrop: (info) => this.handleEventDrop(info),
            eventResize: (info) => this.handleEventResize(info),
            eventClick: (info) => this.handleEventClick(info),
            dateClick: (info) => this.handleDateClick(info),
            
            // Styling
            eventDidMount: (info) => {
                info.el.setAttribute('title', info.event.title);
                info.el.style.cursor = 'pointer';
            }
        });

        this.calendar.render();
    }

    setupViewToggles() {
        const calendarViewBtn = document.getElementById('calendarView');
        const timelineViewBtn = document.getElementById('timelineView');
        const calendarContainer = document.getElementById('calendarViewContainer');
        const timelineContainer = document.getElementById('timelineViewContainer');

        calendarViewBtn.addEventListener('click', () => {
            this.switchToCalendarView();
        });

        timelineViewBtn.addEventListener('click', () => {
            this.switchToTimelineView();
        });
    }

    switchToCalendarView() {
        const calendarViewBtn = document.getElementById('calendarView');
        const timelineViewBtn = document.getElementById('timelineView');
        const calendarContainer = document.getElementById('calendarViewContainer');
        const timelineContainer = document.getElementById('timelineViewContainer');

        calendarContainer.classList.remove('hidden');
        timelineContainer.classList.add('hidden');
        
        calendarViewBtn.classList.add('active');
        timelineViewBtn.classList.remove('active');

        // Refresh calendar
        if (this.calendar) {
            setTimeout(() => this.calendar.updateSize(), 300);
        }
    }

    switchToTimelineView() {
        const calendarViewBtn = document.getElementById('calendarView');
        const timelineViewBtn = document.getElementById('timelineView');
        const calendarContainer = document.getElementById('calendarViewContainer');
        const timelineContainer = document.getElementById('timelineViewContainer');

        calendarContainer.classList.add('hidden');
        timelineContainer.classList.remove('hidden');
        
        timelineViewBtn.classList.add('active');
        calendarViewBtn.classList.remove('active');

        // Load timeline view
        this.loadTimelineView();
    }

    async loadTimelineView() {
        const timelineContent = document.getElementById('timelineContent');
        const timelineLoading = document.getElementById('timelineLoading');
        
        timelineLoading.style.display = 'block';
        timelineContent.innerHTML = '';

        try {
            // Generate timeline HTML
            const timelineHTML = this.generateTimelineHTML();
            timelineContent.innerHTML = timelineHTML;
            
            // Setup drag and drop for timeline
            this.setupTimelineDragDrop();
            
            // Setup activity interactions
            this.setupTimelineActivityInteractions();
            
        } catch (error) {
            console.error('Error loading timeline view:', error);
            timelineContent.innerHTML = '<div class="text-center text-red-600 py-8">Failed to load timeline view</div>';
        } finally {
            timelineLoading.style.display = 'none';
        }
    }

    generateTimelineHTML() {
        let html = '';
        
        // Group events by destination
        const destinationGroups = this.groupEventsByDestination();
        
        destinationGroups.forEach((group, index) => {
            const destination = group.destination;
            const activities = group.activities;
            
            html += `
                <div class="mb-8 animate-slideInUp" style="animation-delay: ${index * 0.1}s;">
                    <div class="timeline-dot" style="top: ${index * 20}px;"></div>
                    <div class="timeline-card" data-destination-id="${destination.id}">
                        <div class="flex justify-between items-start mb-6">
                            <div>
                                <h3 class="text-2xl font-bold text-gray-900 mb-2">${destination.name}</h3>
                                <p class="text-gray-600 mb-2">${destination.date_range || 'Date not set'}</p>
                                <div class="flex items-center gap-4 text-sm text-gray-500">
                                    <span class="flex items-center">
                                        <i class="fas fa-map-marker-alt mr-1 text-indigo-500"></i>
                                        ${destination.city || destination.name}
                                    </span>
                                    <span class="flex items-center">
                                        <i class="fas fa-rupee-sign mr-1 text-green-500"></i>
                                        ₹${destination.budget || 0}
                                    </span>
                                </div>
                            </div>
                            <div class="flex flex-col items-end gap-2">
                                <span class="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm font-medium">
                                    ${this.calculateDuration(destination.date_range)}
                                </span>
                                <button class="add-activity-btn px-3 py-1 text-xs bg-green-100 text-green-700 rounded-full hover:bg-green-200 transition-colors" data-destination-id="${destination.id}">
                                    <i class="fas fa-plus mr-1"></i>Add Activity
                                </button>
                            </div>
                        </div>
                        
                        <div class="activities-container space-y-3" data-destination-id="${destination.id}">
                            ${this.generateActivitiesHTML(activities)}
                        </div>
                    </div>
                </div>
            `;
        });
        
        if (html === '') {
            html = `
                <div class="text-center py-12 text-gray-500">
                    <i class="fas fa-calendar-times text-4xl mb-4"></i>
                    <h3 class="text-xl font-semibold mb-2">No destinations found</h3>
                    <p>Add some destinations to your trip to see them in the timeline.</p>
                </div>
            `;
        }
        
        return html;
    }

    generateActivitiesHTML(activities) {
        return activities.map(activity => {
            const startTime = new Date(activity.start).toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: true
            });
            const endTime = new Date(activity.end).toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: true
            });
            
            return `
                <div class="activity-card animate-fadeIn" 
                     draggable="true" 
                     data-activity-id="${activity.id}"
                     data-destination-id="${activity.extendedProps.destinationId}">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <h4 class="font-semibold text-gray-900 mb-1">${activity.title}</h4>
                            <p class="text-sm text-gray-600 mb-2">${startTime} - ${endTime}</p>
                            ${activity.extendedProps.notes ? `<p class="text-xs text-gray-500">${activity.extendedProps.notes}</p>` : ''}
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="text-sm font-medium text-green-600">₹${activity.extendedProps.cost || 0}</span>
                            <div class="flex gap-1">
                                <button class="edit-activity-btn p-1 text-gray-400 hover:text-indigo-600 transition-colors" 
                                        data-activity-id="${activity.id}" title="Edit">
                                    <i class="fas fa-edit text-xs"></i>
                                </button>
                                <button class="delete-activity-btn p-1 text-gray-400 hover:text-red-600 transition-colors" 
                                        data-activity-id="${activity.id}" title="Delete">
                                    <i class="fas fa-trash text-xs"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    groupEventsByDestination() {
        const groups = [];
        
        this.destinations.forEach(destination => {
            const destinationEvents = this.events.filter(event => 
                event.extendedProps && event.extendedProps.destinationId === destination.id
            );
            
            const activities = destinationEvents.filter(event => 
                event.extendedProps.type === 'activity'
            ).sort((a, b) => new Date(a.start) - new Date(b.start));
            
            groups.push({
                destination: destination,
                activities: activities
            });
        });
        
        return groups;
    }

    calculateDuration(dateRange) {
        if (!dateRange) return 'Duration not set';
        
        const [startDate, endDate] = this.parseDateRange(dateRange);
        if (startDate && endDate) {
            const days = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;
            return `${days} Day${days > 1 ? 's' : ''}`;
        }
        return 'Duration not set';
    }

    setupTimelineDragDrop() {
        const activityCards = document.querySelectorAll('.activity-card');
        const activityContainers = document.querySelectorAll('.activities-container');

        // Setup drag start
        activityCards.forEach(card => {
            card.addEventListener('dragstart', (e) => {
                this.isDragging = true;
                card.classList.add('dragging');
                e.dataTransfer.setData('text/plain', card.dataset.activityId);
            });

            card.addEventListener('dragend', (e) => {
                this.isDragging = false;
                card.classList.remove('dragging');
            });
        });

        // Setup drop zones
        activityContainers.forEach(container => {
            container.addEventListener('dragover', (e) => {
                e.preventDefault();
                container.classList.add('drag-over');
            });

            container.addEventListener('dragleave', (e) => {
                if (!container.contains(e.relatedTarget)) {
                    container.classList.remove('drag-over');
                }
            });

            container.addEventListener('drop', (e) => {
                e.preventDefault();
                container.classList.remove('drag-over');
                
                const activityId = e.dataTransfer.getData('text/plain');
                const targetDestinationId = container.dataset.destinationId;
                
                this.handleActivityDrop(activityId, targetDestinationId);
            });
        });
    }

    setupTimelineActivityInteractions() {
        // Edit activity buttons
        document.querySelectorAll('.edit-activity-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const activityId = btn.dataset.activityId;
                this.openEditModal(activityId);
            });
        });

        // Delete activity buttons
        document.querySelectorAll('.delete-activity-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const activityId = btn.dataset.activityId;
                this.deleteActivity(activityId);
            });
        });

        // Add activity buttons
        document.querySelectorAll('.add-activity-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const destinationId = btn.dataset.destinationId;
                this.openAddActivityModal(destinationId);
            });
        });

        // Double click to edit
        document.querySelectorAll('.activity-card').forEach(card => {
            card.addEventListener('dblclick', (e) => {
                const activityId = card.dataset.activityId;
                this.openEditModal(activityId);
            });
        });
    }

    setupModals() {
        // Edit modal
        const editModal = document.getElementById('editModal');
        const closeModal = document.getElementById('closeModal');
        const editForm = document.getElementById('editActivityForm');
        const deleteBtn = document.getElementById('deleteActivity');

        closeModal?.addEventListener('click', () => this.closeEditModal());
        editForm?.addEventListener('submit', (e) => this.handleEditSubmit(e));
        deleteBtn?.addEventListener('click', () => this.handleDeleteFromModal());

        // Add modal
        const addModal = document.getElementById('addActivityModal');
        const closeAddModal = document.getElementById('closeAddModal');
        const addForm = document.getElementById('addActivityForm');
        const cancelAdd = document.getElementById('cancelAdd');

        closeAddModal?.addEventListener('click', () => this.closeAddModal());
        cancelAdd?.addEventListener('click', () => this.closeAddModal());
        addForm?.addEventListener('submit', (e) => this.handleAddSubmit(e));

        // Close on outside click
        [editModal, addModal].forEach(modal => {
            modal?.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeEditModal();
                    this.closeAddModal();
                }
            });
        });
    }

    setupEventListeners() {
        // Calendar event handlers are already set in initializeCalendar
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeEditModal();
                this.closeAddModal();
            }
        });
    }

    // Event handlers
    handleEventDrop(info) {
        console.log('Event dropped:', info.event);
        this.showNotification('Event moved successfully', 'success');
        // Here you would save the changes to the backend
    }

    handleEventResize(info) {
        console.log('Event resized:', info.event);
        this.showNotification('Event duration updated', 'success');
        // Here you would save the changes to the backend
    }

    handleEventClick(info) {
        if (info.event.extendedProps.type === 'activity') {
            this.openEditModal(info.event.id);
        }
    }

    handleDateClick(info) {
        this.openAddActivityModal(null, info.dateStr);
    }

    handleActivityDrop(activityId, targetDestinationId) {
        console.log('Activity dropped:', activityId, 'to destination:', targetDestinationId);
        
        // Find the activity
        const activity = this.events.find(e => e.id === activityId);
        if (activity) {
            activity.extendedProps.destinationId = parseInt(targetDestinationId);
            this.showNotification('Activity moved successfully', 'success');
            
            // Refresh timeline view
            this.loadTimelineView();
        }
    }

    // Modal methods
    openEditModal(activityId) {
        const activity = this.events.find(e => e.id === activityId);
        if (!activity) return;

        this.currentEditingActivity = activity;
        
        // Populate form
        document.getElementById('editActivityName').value = activity.title.replace(/^[^\s]+\s/, ''); // Remove emoji
        document.getElementById('editStartTime').value = new Date(activity.start).toTimeString().slice(0, 5);
        document.getElementById('editEndTime').value = new Date(activity.end).toTimeString().slice(0, 5);
        document.getElementById('editActivityCost').value = activity.extendedProps.cost || 0;
        document.getElementById('editActivityNotes').value = activity.extendedProps.notes || '';
        
        document.getElementById('editModal').classList.add('active');
    }

    closeEditModal() {
        document.getElementById('editModal').classList.remove('active');
        this.currentEditingActivity = null;
    }

    openAddActivityModal(destinationId, date = null) {
        // Set default date if provided
        if (date) {
            document.getElementById('newActivityDate').value = date;
        }
        
        // Store destination ID for later use
        this.currentAddDestinationId = destinationId;
        
        document.getElementById('addActivityModal').classList.add('active');
    }

    closeAddModal() {
        document.getElementById('addActivityModal').classList.remove('active');
        document.getElementById('addActivityForm').reset();
        this.currentAddDestinationId = null;
    }

    handleEditSubmit(e) {
        e.preventDefault();
        
        if (!this.currentEditingActivity) return;
        
        // Get form data
        const name = document.getElementById('editActivityName').value;
        const startTime = document.getElementById('editStartTime').value;
        const endTime = document.getElementById('editEndTime').value;
        const cost = document.getElementById('editActivityCost').value;
        const notes = document.getElementById('editActivityNotes').value;
        
        // Update activity
        const activity = this.currentEditingActivity;
        const activityDate = new Date(activity.start).toISOString().split('T')[0];
        
        activity.title = `${this.getActivityIcon(activity.extendedProps.activityType)} ${name}`;
        activity.start = `${activityDate}T${startTime}:00`;
        activity.end = `${activityDate}T${endTime}:00`;
        activity.extendedProps.cost = parseInt(cost) || 0;
        activity.extendedProps.notes = notes;
        
        // Update calendar and timeline
        this.calendar.refetchEvents();
        if (!document.getElementById('timelineViewContainer').classList.contains('hidden')) {
            this.loadTimelineView();
        }
        
        this.closeEditModal();
        this.showNotification('Activity updated successfully', 'success');
    }

    handleAddSubmit(e) {
        e.preventDefault();
        
        // Get form data
        const name = document.getElementById('newActivityName').value;
        const date = document.getElementById('newActivityDate').value;
        const startTime = document.getElementById('newStartTime').value;
        const endTime = document.getElementById('newEndTime').value;
        const cost = document.getElementById('newActivityCost').value;
        const notes = document.getElementById('newActivityNotes').value;
        
        // Create new activity
        const newActivity = {
            id: `activity-new-${Date.now()}`,
            title: `🎯 ${name}`,
            start: `${date}T${startTime}:00`,
            end: `${date}T${endTime}:00`,
            backgroundColor: '#ef4444',
            borderColor: '#dc2626',
            classNames: ['activity-event'],
            extendedProps: {
                type: 'activity',
                activityType: 'activity',
                destinationId: this.currentAddDestinationId,
                cost: parseInt(cost) || 0,
                notes: notes
            }
        };
        
        // Add to events array
        this.events.push(newActivity);
        
        // Update calendar
        this.calendar.addEvent(newActivity);
        
        // Update timeline if visible
        if (!document.getElementById('timelineViewContainer').classList.contains('hidden')) {
            this.loadTimelineView();
        }
        
        this.closeAddModal();
        this.showNotification('Activity added successfully', 'success');
    }

    handleDeleteFromModal() {
        if (this.currentEditingActivity) {
            this.deleteActivity(this.currentEditingActivity.id);
            this.closeEditModal();
        }
    }

    deleteActivity(activityId) {
        if (confirm('Are you sure you want to delete this activity?')) {
            // Remove from events array
            this.events = this.events.filter(e => e.id !== activityId);
            
            // Remove from calendar
            const calendarEvent = this.calendar.getEventById(activityId);
            if (calendarEvent) {
                calendarEvent.remove();
            }
            
            // Update timeline if visible
            if (!document.getElementById('timelineViewContainer').classList.contains('hidden')) {
                this.loadTimelineView();
            }
            
            this.showNotification('Activity deleted successfully', 'success');
        }
    }

    // Utility methods
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg transform translate-x-full transition-transform duration-300 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Animate out and remove
        setTimeout(() => {
            notification.style.transform = 'translateX(full)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
}

// Make TripCalendar available globally
window.TripCalendar = TripCalendar;
