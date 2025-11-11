/**
 * Trip Actions Handler
 * Manages trip deletion, sharing, and UI interactions
 */

class TripActions {
    constructor() {
        this.tripId = document.getElementById('itinerary-root')?.dataset.tripId;
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Share button
        document.querySelector('[onclick*="shareItinerary"]')?.addEventListener('click', () => {
            this.shareItinerary();
        });

        // Delete trip button
        document.querySelector('[onclick*="confirmDeleteTrip"]')?.addEventListener('click', () => {
            this.showDeleteConfirmation();
        });

        // Modal cancel button
        document.getElementById('cancelDelete')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.closeDeleteModal();
        });

        // Modal confirm button
        document.getElementById('confirmDelete')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleDeleteTrip();
        });

        // Modal overlay click
        document.getElementById('deleteModal')?.addEventListener('click', (e) => {
            if (e.target.id === 'deleteModal') {
                this.closeDeleteModal();
            }
        });
    }

    showDeleteConfirmation() {
        const modal = document.getElementById('deleteModal');
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    closeDeleteModal() {
        const modal = document.getElementById('deleteModal');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    async handleDeleteTrip() {
        if (!this.tripId) {
            showNotification('Trip ID not found. Cannot delete trip.', 'error');
            return;
        }

        const confirmBtn = document.getElementById('confirmDelete');
        const deleteText = confirmBtn.querySelector('.delete-btn-text');
        const deleteLoading = confirmBtn.querySelector('.delete-btn-loading');

        if (!deleteText || !deleteLoading) return;

        // Show loading state
        deleteText.classList.add('hidden');
        deleteLoading.classList.remove('hidden');
        confirmBtn.disabled = true;

        try {
            const response = await fetch(`/api/trips/${this.tripId}/delete`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });

            const result = await response.json();

            if (response.ok) {
                showNotification('Trip deleted successfully!', 'success');
                this.closeDeleteModal();

                // Redirect to dashboard
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1500);
            } else {
                throw new Error(result.message || 'Failed to delete trip');
            }
        } catch (error) {
            console.error('Error deleting trip:', error);
            showNotification('Failed to delete trip. Please try again.', 'error');

            // Reset button state
            deleteText.classList.remove('hidden');
            deleteLoading.classList.add('hidden');
            confirmBtn.disabled = false;
        }
    }

    async shareItinerary() {
        const tripData = {
            title: document.querySelector('h1')?.textContent || 'My Trip Itinerary',
            description: 'Check out my amazing trip itinerary!',
            url: window.location.href
        };

        if (navigator.share) {
            try {
                await navigator.share({
                    title: tripData.title,
                    text: tripData.description,
                    url: tripData.url
                });
                showNotification('Itinerary shared successfully!', 'success');
            } catch (error) {
                if (error.name !== 'AbortError') {
                    this.fallbackShare(tripData.url);
                }
            }
        } else {
            this.fallbackShare(tripData.url);
        }
    }

    fallbackShare(url) {
        navigator.clipboard.writeText(url).then(() => {
            showNotification('Itinerary link copied to clipboard!', 'success');
        }).catch(() => {
            showNotification('Failed to copy link. Please try again.', 'error');
        });
    }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    window.tripActions = new TripActions();
});
