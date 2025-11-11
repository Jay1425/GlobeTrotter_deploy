/**
 * Fast Search, Sort, and Loading Utilities for GlobeTrotter
 * Optimized algorithms for client-side performance
 */

class FastSearch {
    constructor() {
        this.searchCache = new Map();
        this.debounceTimeout = null;
        this.currentController = null;
        
        // Initialize fast search components
        this.initializeSearchComponents();
    }
    
    initializeSearchComponents() {
        // Setup debounced search inputs
        document.querySelectorAll('[data-fast-search]').forEach(input => {
            input.addEventListener('input', (e) => {
                this.debouncedSearch(e.target.value, e.target.dataset.fastSearch);
            });
        });
        
        // Setup sort controls
        document.querySelectorAll('[data-fast-sort]').forEach(control => {
            control.addEventListener('click', (e) => {
                e.preventDefault();
                const sortBy = control.dataset.fastSort;
                const reverse = control.dataset.reverse === 'true';
                this.fastSort(sortBy, reverse);
            });
        });
    }
    
    // Debounced search with caching
    debouncedSearch(query, searchType, delay = 300) {
        clearTimeout(this.debounceTimeout);
        
        this.debounceTimeout = setTimeout(() => {
            this.performSearch(query, searchType);
        }, delay);
    }
    
    // Fast search implementation
    async performSearch(query, searchType = 'trips') {
        const cacheKey = `${searchType}:${query}`;
        
        // Check cache first
        if (this.searchCache.has(cacheKey)) {
            const cachedResult = this.searchCache.get(cacheKey);
            this.displaySearchResults(cachedResult, searchType);
            return;
        }
        
        // Cancel previous request
        if (this.currentController) {
            this.currentController.abort();
        }
        
        this.currentController = new AbortController();
        
        try {
            this.showSearchLoading(searchType);
            
            const endpoint = searchType === 'trips' ? '/api/search/trips' : '/api/search/recommendations';
            const params = new URLSearchParams({
                q: query,
                limit: '50', // Load more for better UX
                sort: searchType === 'trips' ? 'created_at' : 'rating',
                order: 'desc'
            });
            
            const response = await fetch(`${endpoint}?${params}`, {
                signal: this.currentController.signal,
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) throw new Error('Search failed');
            
            const data = await response.json();
            
            if (data.ok) {
                // Cache results for fast future access
                this.searchCache.set(cacheKey, data);
                this.displaySearchResults(data, searchType);
            } else {
                throw new Error(data.error || 'Search failed');
            }
            
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Search error:', error);
                this.showSearchError(searchType, error.message);
            }
        } finally {
            this.hideSearchLoading(searchType);
        }
    }
    
    // Fast client-side filtering for loaded data
    clientSideFilter(items, query, fields = ['title', 'name']) {
        if (!query || query.length < 2) return items;
        
        const searchTerms = query.toLowerCase().split(' ').filter(term => term.length > 0);
        
        return items.filter(item => {
            return searchTerms.every(term => {
                return fields.some(field => {
                    const value = this.getNestedValue(item, field);
                    return value && value.toLowerCase().includes(term);
                });
            });
        }).sort((a, b) => {
            // Sort by relevance (exact matches first)
            const aTitle = this.getNestedValue(a, fields[0]) || '';
            const bTitle = this.getNestedValue(b, fields[0]) || '';
            
            const aExact = aTitle.toLowerCase().includes(query.toLowerCase());
            const bExact = bTitle.toLowerCase().includes(query.toLowerCase());
            
            if (aExact && !bExact) return -1;
            if (!aExact && bExact) return 1;
            return 0;
        });
    }
    
    // Fast sort implementation
    async fastSort(sortBy, reverse = false) {
        const container = document.querySelector('[data-sort-container]');
        if (!container) return;
        
        const items = Array.from(container.children);
        const itemData = items.map(item => ({
            element: item,
            id: item.dataset.id,
            value: this.getSortValue(item, sortBy)
        }));
        
        // Use optimized quicksort
        const sorted = this.quickSort(itemData, reverse);
        
        // Animate the reordering
        this.animateSort(container, sorted);
    }
    
    // Optimized quicksort implementation
    quickSort(arr, reverse = false) {
        if (arr.length <= 1) return arr;
        
        const pivot = arr[Math.floor(arr.length / 2)];
        const less = [];
        const equal = [];
        const greater = [];
        
        for (const item of arr) {
            const comparison = this.compareValues(item.value, pivot.value);
            if (comparison < 0) {
                less.push(item);
            } else if (comparison > 0) {
                greater.push(item);
            } else {
                equal.push(item);
            }
        }
        
        const result = [
            ...this.quickSort(less, reverse),
            ...equal,
            ...this.quickSort(greater, reverse)
        ];
        
        return reverse ? result.reverse() : result;
    }
    
    // Animated sorting for smooth UX
    animateSort(container, sortedItems) {
        // Get current positions
        const positions = new Map();
        sortedItems.forEach((item, index) => {
            const rect = item.element.getBoundingClientRect();
            positions.set(item.element, { 
                top: rect.top, 
                left: rect.left,
                targetIndex: index
            });
        });
        
        // Reorder DOM
        sortedItems.forEach(item => {
            container.appendChild(item.element);
        });
        
        // Animate to new positions
        sortedItems.forEach(item => {
            const element = item.element;
            const oldPos = positions.get(element);
            const newRect = element.getBoundingClientRect();
            
            const deltaX = oldPos.left - newRect.left;
            const deltaY = oldPos.top - newRect.top;
            
            if (deltaX || deltaY) {
                element.style.transform = `translate(${deltaX}px, ${deltaY}px)`;
                element.style.transition = 'none';
                
                requestAnimationFrame(() => {
                    element.style.transition = 'transform 0.3s ease';
                    element.style.transform = '';
                });
            }
        });
    }
    
    // Display search results with virtual scrolling for large datasets
    displaySearchResults(data, searchType) {
        const container = document.querySelector(`[data-results="${searchType}"]`);
        if (!container) return;
        
        const items = searchType === 'trips' ? data.trips : data.recommendations;
        
        // Clear existing results
        container.innerHTML = '';
        
        // Create virtual scrolling container if needed
        if (items.length > 50) {
            this.createVirtualScrollContainer(container, items, searchType);
        } else {
            this.createSimpleResults(container, items, searchType);
        }
        
        // Update result count
        const countElement = document.querySelector(`[data-count="${searchType}"]`);
        if (countElement) {
            countElement.textContent = items.length;
        }
    }
    
    // Virtual scrolling for performance with large datasets
    createVirtualScrollContainer(container, items, searchType) {
        const itemHeight = 100; // Estimated height per item
        const containerHeight = 600; // Visible container height
        const visibleItems = Math.ceil(containerHeight / itemHeight);
        const bufferItems = 5;
        
        let scrollTop = 0;
        let startIndex = 0;
        let endIndex = Math.min(visibleItems + bufferItems, items.length);
        
        const scrollContainer = document.createElement('div');
        scrollContainer.style.height = `${containerHeight}px`;
        scrollContainer.style.overflowY = 'auto';
        scrollContainer.style.position = 'relative';
        
        const totalHeight = items.length * itemHeight;
        const spacer = document.createElement('div');
        spacer.style.height = `${totalHeight}px`;
        spacer.style.position = 'relative';
        
        const viewport = document.createElement('div');
        viewport.style.position = 'absolute';
        viewport.style.top = '0';
        viewport.style.width = '100%';
        
        const renderItems = () => {
            viewport.innerHTML = '';
            viewport.style.transform = `translateY(${startIndex * itemHeight}px)`;
            
            for (let i = startIndex; i < endIndex; i++) {
                if (items[i]) {
                    const itemElement = this.createResultItem(items[i], searchType);
                    viewport.appendChild(itemElement);
                }
            }
        };
        
        scrollContainer.addEventListener('scroll', () => {
            scrollTop = scrollContainer.scrollTop;
            const newStartIndex = Math.floor(scrollTop / itemHeight);
            const newEndIndex = Math.min(newStartIndex + visibleItems + bufferItems, items.length);
            
            if (newStartIndex !== startIndex || newEndIndex !== endIndex) {
                startIndex = newStartIndex;
                endIndex = newEndIndex;
                renderItems();
            }
        });
        
        spacer.appendChild(viewport);
        scrollContainer.appendChild(spacer);
        container.appendChild(scrollContainer);
        
        renderItems();
    }
    
    // Simple results for smaller datasets
    createSimpleResults(container, items, searchType) {
        const fragment = document.createDocumentFragment();
        
        items.forEach(item => {
            const itemElement = this.createResultItem(item, searchType);
            fragment.appendChild(itemElement);
        });
        
        container.appendChild(fragment);
    }
    
    // Create individual result item
    createResultItem(item, searchType) {
        const element = document.createElement('div');
        element.className = 'search-result-item animate-fadeInUp';
        element.dataset.id = item.id;
        
        if (searchType === 'trips') {
            element.innerHTML = `
                <div class="trip-result p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer" 
                     onclick="window.location.href='/itinerary/${item.id}'">
                    <h3 class="font-semibold text-lg">${item.title}</h3>
                    <p class="text-gray-600">${item.status.charAt(0).toUpperCase() + item.status.slice(1)}</p>
                    <p class="text-sm text-gray-500">
                        ${item.start_date ? new Date(item.start_date).toLocaleDateString() : 'Date TBA'}
                    </p>
                    ${item.destinations.length > 0 ? `
                        <p class="text-sm text-blue-600">${item.destinations.map(d => d.name).join(', ')}</p>
                    ` : ''}
                </div>
            `;
        } else {
            element.innerHTML = `
                <div class="recommendation-result p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer"
                     onclick="window.location.href='/explore'">
                    <div class="flex items-center space-x-4">
                        ${item.image_url ? `<img src="${item.image_url}" alt="${item.title}" class="w-16 h-16 rounded object-cover">` : ''}
                        <div>
                            <h3 class="font-semibold text-lg">${item.title}</h3>
                            <p class="text-gray-600">${item.city || ''} ${item.country || ''}</p>
                            <div class="flex items-center space-x-2">
                                <span class="text-yellow-500">★</span>
                                <span class="text-sm">${item.rating || 0}/5</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        return element;
    }
    
    // Utility functions
    getNestedValue(obj, path) {
        return path.split('.').reduce((o, p) => o && o[p], obj);
    }
    
    getSortValue(element, sortBy) {
        const value = element.dataset[sortBy] || element.querySelector(`[data-${sortBy}]`)?.textContent;
        
        // Try to parse as number or date
        if (!isNaN(value)) return parseFloat(value);
        if (Date.parse(value)) return new Date(value);
        return value?.toLowerCase() || '';
    }
    
    compareValues(a, b) {
        if (a === b) return 0;
        if (a == null) return 1;
        if (b == null) return -1;
        
        if (typeof a === 'number' && typeof b === 'number') {
            return a - b;
        }
        
        if (a instanceof Date && b instanceof Date) {
            return a.getTime() - b.getTime();
        }
        
        return String(a).localeCompare(String(b));
    }
    
    showSearchLoading(searchType) {
        const loader = document.querySelector(`[data-loading="${searchType}"]`);
        if (loader) loader.classList.remove('hidden');
    }
    
    hideSearchLoading(searchType) {
        const loader = document.querySelector(`[data-loading="${searchType}"]`);
        if (loader) loader.classList.add('hidden');
    }
    
    showSearchError(searchType, message) {
        const errorElement = document.querySelector(`[data-error="${searchType}"]`);
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.remove('hidden');
        }
    }
    
    // Clear cache when needed
    clearCache() {
        this.searchCache.clear();
    }
}

// Fast loading utilities
class FastLoader {
    constructor() {
        this.loadingStates = new Map();
        this.preloadQueue = [];
        this.intersectionObserver = null;
        
        this.initializeLazyLoading();
    }
    
    // Lazy loading with Intersection Observer
    initializeLazyLoading() {
        if ('IntersectionObserver' in window) {
            this.intersectionObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadElement(entry.target);
                        this.intersectionObserver.unobserve(entry.target);
                    }
                });
            }, {
                rootMargin: '50px'
            });
            
            // Observe all lazy load elements
            document.querySelectorAll('[data-lazy-load]').forEach(el => {
                this.intersectionObserver.observe(el);
            });
        }
    }
    
    async loadElement(element) {
        const loadType = element.dataset.lazyLoad;
        const url = element.dataset.url;
        
        if (!url) return;
        
        try {
            this.setLoadingState(element, true);
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (loadType === 'trips') {
                this.renderTrips(element, data.trips || []);
            } else if (loadType === 'recommendations') {
                this.renderRecommendations(element, data.recommendations || []);
            }
            
        } catch (error) {
            console.error('Lazy load error:', error);
            element.innerHTML = '<p class="text-red-500">Failed to load content</p>';
        } finally {
            this.setLoadingState(element, false);
        }
    }
    
    setLoadingState(element, isLoading) {
        if (isLoading) {
            element.innerHTML = '<div class="animate-pulse bg-gray-200 h-32 rounded"></div>';
        }
        this.loadingStates.set(element, isLoading);
    }
    
    renderTrips(container, trips) {
        const html = trips.map(trip => `
            <div class="trip-card p-4 bg-white rounded-lg shadow">
                <h3 class="font-semibold">${trip.title}</h3>
                <p class="text-gray-600">${trip.status}</p>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
    
    renderRecommendations(container, recommendations) {
        const html = recommendations.map(rec => `
            <div class="rec-card p-4 bg-white rounded-lg shadow">
                <h3 class="font-semibold">${rec.title}</h3>
                <p class="text-gray-600">${rec.city || ''} ${rec.country || ''}</p>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
}

// Initialize fast utilities
document.addEventListener('DOMContentLoaded', () => {
    window.fastSearch = new FastSearch();
    window.fastLoader = new FastLoader();
    
    console.log('🚀 Fast Search & Loading utilities initialized');
});
