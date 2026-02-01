/**
 * STATE MANAGER
 * Handles all navigation state via URL parameters
 * Replaces localStorage for better UX (bookmarkable, shareable URLs)
 */

const StateManager = {
    
    /**
     * Get URL parameters as object
     * @returns {Object} Key-value pairs from URL
     */
    getParams() {
        const params = new URLSearchParams(window.location.search);
        const result = {};
        
        for (const [key, value] of params) {
            result[key] = value;
        }
        
        return result;
    },
    
    /**
     * Get single parameter from URL
     * @param {string} key - Parameter name
     * @param {string} defaultValue - Fallback if not found
     * @returns {string|null}
     */
    getParam(key, defaultValue = null) {
        const params = new URLSearchParams(window.location.search);
        return params.get(key) || defaultValue;
    },
    
    /**
     * Navigate to new page with state
     * @param {string} page - Target HTML page
     * @param {Object} params - State to pass via URL
     */
    navigate(page, params = {}) {
        const url = new URL(page, window.location.origin);
        
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                url.searchParams.set(key, params[key]);
            }
        });
        
        window.location.href = url.toString();
    },
    
    /**
     * Update current URL without page reload
     * @param {Object} params - Parameters to add/update
     */
    updateURL(params) {
        const url = new URL(window.location);
        
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                url.searchParams.set(key, params[key]);
            }
        });
        
        window.history.pushState({}, '', url);
    },
    
    /**
     * Validate required parameters exist
     * @param {Array<string>} required - Required parameter names
     * @param {string} redirectTo - Page to redirect if missing
     * @returns {boolean} True if valid, false if redirected
     */
    validateRequired(required, redirectTo = 'index.html') {
        const missing = required.filter(key => !this.getParam(key));
        
        if (missing.length > 0) {
            console.warn(`Missing required parameters: ${missing.join(', ')}`);
            this.showError(
                `Invalid navigation. Missing: ${missing.join(', ')}`,
                redirectTo
            );
            return false;
        }
        
        return true;
    },
    
    /**
     * Show error and redirect after delay
     * @param {string} message - Error message
     * @param {string} redirectTo - Page to redirect to
     */
    showError(message, redirectTo) {
        const container = document.body;
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <div class="error-title">Navigation Error</div>
            <p>${message}</p>
            <p class="text-small">Redirecting to ${redirectTo} in 3 seconds...</p>
        `;
        
        container.insertBefore(errorDiv, container.firstChild);
        
        setTimeout(() => {
            window.location.href = redirectTo;
        }, 3000);
    },
    
    /**
     * Build breadcrumb data from current state
     * @returns {Array<Object>} Breadcrumb items
     */
    getBreadcrumbs() {
        const crumbs = [
            { label: 'Counties', page: 'index.html', active: false }
        ];
        
        const countyName = this.getParam('county_name');
        const hospitalName = this.getParam('hospital_name');
        
        if (countyName) {
            crumbs.push({
                label: `${countyName} County`,
                page: `county_map.html?county_id=${this.getParam('county_id')}&county_name=${countyName}`,
                active: !hospitalName
            });
        }
        
        if (hospitalName) {
            crumbs.push({
                label: hospitalName,
                page: `prediction_form.html?${window.location.search.slice(1)}`,
                active: true
            });
        }
        
        return crumbs;
    },
    
    /**
     * Render breadcrumb navigation
     * @param {string} containerId - ID of breadcrumb container
     */
    renderBreadcrumbs(containerId = 'breadcrumb') {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const crumbs = this.getBreadcrumbs();
        
        container.innerHTML = crumbs.map((crumb, index) => {
            const isLast = index === crumbs.length - 1;
            const classes = crumb.active ? 'breadcrumb-item active' : 'breadcrumb-item';
            
            const html = crumb.active 
                ? `<span class="${classes}">${crumb.label}</span>`
                : `<a href="${crumb.page}" class="${classes}">${crumb.label}</a>`;
            
            return html + (isLast ? '' : '<span class="breadcrumb-separator">›</span>');
        }).join(' ');
    },
    
    /**
     * Get current page name without extension
     * @returns {string}
     */
    getCurrentPage() {
        const path = window.location.pathname;
        return path.substring(path.lastIndexOf('/') + 1).replace('.html', '');
    },
    
    // In stateManager.js, update cachePredictionData:

    /**
     * Save prediction form data AND API results for results page
     * @param {Object} data - Can be { input: {}, result: {} } or just input data
     */
    cachePredictionData(data) {
        try {
            // Support both old format (just data) and new format (input + result)
            const cachePayload = data.input ? data : { input: data, result: null };
            
            sessionStorage.setItem('prediction_cache', JSON.stringify({
                data: cachePayload,
                timestamp: Date.now()
            }));
        } catch (e) {
            console.warn('Could not cache prediction data:', e);
        }
    },

    /**
     * Retrieve cached prediction data
     * @returns {Object|null} { input: {}, result: {} }
     */
    getCachedPrediction() {
        try {
            const cached = sessionStorage.getItem('prediction_cache');
            if (!cached) return null;
            
            const { data, timestamp } = JSON.parse(cached);
            
            // Expire after 1 hour
            if (Date.now() - timestamp > 3600000) {
                sessionStorage.removeItem('prediction_cache');
                return null;
            }
            
            return data;
        } catch (e) {
            console.warn('Could not retrieve cached prediction:', e);
            return null;
        }
    }
};

// Make globally available
window.StateManager = StateManager;