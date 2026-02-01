/**
 * MAP UTILITIES
 * Shared Leaflet map setup and error handling
 */

const MapUtils = {
    
    /**
     * Initialize base Leaflet map
     * @param {string} containerId - Map container element ID
     * @param {Array<number>} center - [lat, lng]
     * @param {number} zoom - Initial zoom level
     * @returns {L.Map}
     */
    createMap(containerId, center = [43.0, -75.0], zoom = 7) {
        const map = L.map(containerId).setView(center, zoom);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(map);
        
        return map;
    },
    
    /**
     * Show loading overlay on map
     * @param {string} containerId - Container to show loading in
     * @param {string} message - Loading message
     * @returns {HTMLElement} The loading overlay element
     */
    showLoading(containerId, message = 'Loading map data...') {
        const container = document.getElementById(containerId);
        
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.id = 'map-loading';
        overlay.innerHTML = `
            <div class="spinner"></div>
            <div class="loading-text">${message}</div>
        `;
        
        container.appendChild(overlay);
        return overlay;
    },
    
    /**
     * Hide loading overlay
     */
    hideLoading() {
        const overlay = document.getElementById('map-loading');
        if (overlay) {
            overlay.remove();
        }
    },
    
    /**
     * Fetch GeoJSON with error handling
     * @param {string} url - GeoJSON file path
     * @returns {Promise<Object>}
     */
    async fetchGeoJSON(url) {
        try {
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Failed to load ${url}: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('GeoJSON fetch error:', error);
            this.showMapError(error.message);
            throw error;
        }
    },
    
    /**
     * Show error message on map
     * @param {string} message - Error message
     */
    showMapError(message) {
        const mapContainer = document.getElementById('map');
        if (!mapContainer) return;
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.position = 'absolute';
        errorDiv.style.top = '50%';
        errorDiv.style.left = '50%';
        errorDiv.style.transform = 'translate(-50%, -50%)';
        errorDiv.style.zIndex = '1000';
        errorDiv.innerHTML = `
            <div class="error-title">Map Error</div>
            <p>${message}</p>
            <button class="btn btn-secondary" onclick="location.reload()">
                Retry
            </button>
        `;
        
        mapContainer.appendChild(errorDiv);
    },
    
    /**
     * County layer style configuration
     */
    countyStyle: {
        default: {
            color: '#2c5282',
            weight: 1,
            fillOpacity: 0.2,
            fillColor: '#edf2f7'
        },
        hover: {
            weight: 3,
            fillOpacity: 0.4,
            fillColor: '#cbd5e0'
        },
        selected: {
            color: '#48bb78',
            weight: 3,
            fillOpacity: 0.3,
            fillColor: '#c6f6d5'
        }
    },
    
    /**
     * Create custom marker icon for hospitals
     * @param {string} type - hospital type (e.g., 'general', 'specialty')
     * @returns {L.Icon}
     */
    createHospitalIcon(type = 'general') {
        const colors = {
            general: '#2c5282',
            specialty: '#48bb78',
            urgent: '#ed8936'
        };
        
        const color = colors[type] || colors.general;
        
        return L.divIcon({
            className: 'custom-hospital-marker',
            html: `
                <div style="
                    background: ${color};
                    width: 24px;
                    height: 24px;
                    border-radius: 50% 50% 50% 0;
                    transform: rotate(-45deg);
                    border: 2px solid white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                ">
                    <div style="
                        width: 8px;
                        height: 8px;
                        background: white;
                        border-radius: 50%;
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                    "></div>
                </div>
            `,
            iconSize: [24, 24],
            iconAnchor: [12, 24],
            popupAnchor: [0, -24]
        });
    },
    
    /**
     * Add county layer with interactions
     * @param {L.Map} map - Leaflet map instance
     * @param {Object} geoJsonData - County GeoJSON
     * @param {Function} onCountyClick - Click handler (receives feature)
     * @returns {L.GeoJSON}
     */
    addCountyLayer(map, geoJsonData, onCountyClick) {
        const layer = L.geoJSON(geoJsonData, {
            style: this.countyStyle.default,
            
            onEachFeature: (feature, layer) => {
                const countyName = feature.properties.name;
                
                // Permanent label
                layer.bindTooltip(countyName, {
                    permanent: true,
                    direction: 'center',
                    className: 'county-label'
                });
                
                // Click handler
                layer.on('click', () => {
                    if (onCountyClick) {
                        onCountyClick(feature, layer);
                    }
                });
                
                // Hover effects
                layer.on('mouseover', (e) => {
                    e.target.setStyle(this.countyStyle.hover);
                });
                
                layer.on('mouseout', (e) => {
                    if (!e.target.isSelected) {
                        e.target.setStyle(this.countyStyle.default);
                    }
                });
            }
        }).addTo(map);
        
        return layer;
    },
    
    /**
     * Add hospital markers with popups
     * @param {L.Map} map - Leaflet map instance
     * @param {Array<Object>} hospitals - Hospital features
     * @param {Function} onHospitalClick - Click handler
     * @returns {L.GeoJSON}
     */
    addHospitalMarkers(map, hospitals, onHospitalClick) {
        const layer = L.geoJSON(hospitals, {
            pointToLayer: (feature, latlng) => {
                const icon = this.createHospitalIcon();
                return L.marker(latlng, { icon });
            },
            
            onEachFeature: (feature, layer) => {
                const name = feature.properties['Facility Name'];
                const id = feature.properties['Facility ID'];
                
                // Popup content
                layer.bindPopup(`
                    <div style="font-weight: 600; margin-bottom: 8px;">
                        ${name}
                    </div>
                    <div style="font-size: 12px; color: #718096;">
                        ID: ${id}
                    </div>
                    <button 
                        class="btn btn-primary btn-full mt-md"
                        style="font-size: 14px; padding: 8px;"
                    >
                        Select Hospital
                    </button>
                `);
                
                // Click handler
                layer.on('click', () => {
                    if (onHospitalClick) {
                        onHospitalClick(feature);
                    }
                });
            }
        }).addTo(map);
        
        return layer;
    },
    
    /**
     * Filter GeoJSON features by property
     * @param {Object} geoJsonData - GeoJSON data
     * @param {string} property - Property name to filter by
     * @param {any} value - Value to match
     * @returns {Array<Object>}
     */
    filterFeatures(geoJsonData, property, value) {
        return geoJsonData.features.filter(
            feature => feature.properties[property] === value
        );
    },
    
    /**
     * Find single feature by property
     * @param {Object} geoJsonData - GeoJSON data
     * @param {string} property - Property name
     * @param {any} value - Value to match
     * @returns {Object|null}
     */
    findFeature(geoJsonData, property, value) {
        return geoJsonData.features.find(
            feature => feature.properties[property] === value
        ) || null;
    }
};

// Make globally available
window.MapUtils = MapUtils;