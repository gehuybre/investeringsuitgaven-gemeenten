// Map management module
import { getColorScale } from './utils.js';

export class MapManager {
    constructor() {
        this.map = null;
        this.geojsonLayer = null;
        this.mapMinValue = null;
        this.mapMaxValue = null;
    }

    // Initialize the map
    initMap() {
        this.map = L.map('map').setView([51.05, 4.4], 9);

        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(this.map);

        this.addLegend();
        
        return this.map;
    }

    // Add legend control
    addLegend() {
        const legend = L.control({position: 'bottomright'});
        legend.onAdd = (map) => {
            const div = L.DomUtil.create('div', 'info legend');
            div.id = 'map-legend';
            div.style.backgroundColor = 'white';
            div.style.padding = '10px 12px';
            div.style.font = '14px/16px Arial, Helvetica, sans-serif';
            div.style.background = 'white';
            div.style.boxShadow = '0 0 15px rgba(0,0,0,0.2)';
            div.style.borderRadius = '5px';
            div.style.minWidth = '200px';
            
            div.innerHTML = '<strong>Investeringen 2024</strong><br>' +
                            '<small>(€ per inwoner)</small><br>' +
                            '<div style="margin-top: 8px; font-size: 12px; color: #666;">Kleuren gebaseerd op percentielen van het maximum</div>' +
                            '<i style="background:#d73027; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7; margin-top: 4px;"></i> <span id="legend-top90">> 90% (hoog)</span><br>' +
                            '<i style="background:#f46d43; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7; margin-top: 4px;"></i> <span id="legend-70-90">70-90%</span><br>' +
                            '<i style="background:#fdae61; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7; margin-top: 4px;"></i> <span id="legend-50-70">50-70%</span><br>' +
                            '<i style="background:#abd9e9; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7; margin-top: 4px;"></i> <span id="legend-30-50">30-50%</span><br>' +
                            '<i style="background:#74add1; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7; margin-top: 4px;"></i> <span id="legend-10-30">10-30%</span><br>' +
                            '<i style="background:#4575b4; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7; margin-top: 4px;"></i> <span id="legend-low10">&lt; 10% (laag)</span><br>' +
                            '<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #ddd;"></div>' +
                            '<i style="background:#999999; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.5; margin-top: 4px; border: 2px dashed #666;"></i> <span style="font-size: 12px;">Onbetrouwbare data</span>';
            return div;
        };
        legend.addTo(this.map);
    }

    // Setup map with geojson data
    setupMap(data, onFeatureClick) {
        const values2024 = data.features
            .map(f => f.properties['2024'])
            .filter(v => v !== null && !isNaN(v));
        
        this.mapMaxValue = Math.max(...values2024);
        this.mapMinValue = Math.min(...values2024);

        this.geojsonLayer = L.geoJSON(data, {
            style: (feature) => this.getFeatureStyle(feature),
            onEachFeature: (feature, layer) => this.onEachFeature(feature, layer, onFeatureClick)
        }).addTo(this.map);

        this.map.fitBounds(this.geojsonLayer.getBounds());
        this.updateLegend();
    }

    // Get style for a feature
    getFeatureStyle(feature) {
        const val = feature.properties['2024'];
        const municipalityName = feature.properties.municipality;
        
        // Special styling for Kaprijke due to unreliable data
        if (municipalityName === 'Kaprijke') {
            return {
                fillColor: '#999999',
                weight: 2,
                opacity: 1,
                color: '#666666',
                dashArray: '5, 5',
                fillOpacity: 0.5
            };
        }
        
        return {
            fillColor: getColorScale(val, this.mapMinValue, this.mapMaxValue),
            weight: 1,
            opacity: 1,
            color: 'white',
            dashArray: '3',
            fillOpacity: 0.7
        };
    }

    // Setup feature interactions
    onEachFeature(feature, layer, onFeatureClick) {
        layer.on({
            mouseover: (e) => {
                const layer = e.target;
                layer.setStyle({ weight: 3, color: '#666', dashArray: '', fillOpacity: 0.9 });
                layer.bringToFront();
            },
            mouseout: (e) => {
                this.geojsonLayer.resetStyle(e.target);
            },
            click: (e) => {
                if (onFeatureClick) {
                    onFeatureClick(feature.properties);
                }
            }
        });
        
        const name = feature.properties.municipality;
        const val2024 = feature.properties['2024'];
        layer.bindTooltip(`<strong>${name}</strong><br>2024: €${val2024 ? val2024.toFixed(2) : '-'}`);
    }

    // Update legend with actual values
    updateLegend() {
        if (this.mapMinValue === null || this.mapMaxValue === null) return;
        
        const legend = document.getElementById('map-legend');
        if (!legend) return;
        
        const top90 = this.mapMaxValue * 0.9;
        const top70 = this.mapMaxValue * 0.7;
        const top50 = this.mapMaxValue * 0.5;
        const top30 = this.mapMaxValue * 0.3;
        const top10 = this.mapMaxValue * 0.1;
        
        const legendTop90 = document.getElementById('legend-top90');
        const legend70_90 = document.getElementById('legend-70-90');
        const legend50_70 = document.getElementById('legend-50-70');
        const legend30_50 = document.getElementById('legend-30-50');
        const legend10_30 = document.getElementById('legend-10-30');
        const legendLow10 = document.getElementById('legend-low10');
        
        if (legendTop90) legendTop90.innerHTML = `> 90% (≥ €${top90.toFixed(0)})`;
        if (legend70_90) legend70_90.innerHTML = `70-90% (€${top70.toFixed(0)}-${top90.toFixed(0)})`;
        if (legend50_70) legend50_70.innerHTML = `50-70% (€${top50.toFixed(0)}-${top70.toFixed(0)})`;
        if (legend30_50) legend30_50.innerHTML = `30-50% (€${top30.toFixed(0)}-${top50.toFixed(0)})`;
        if (legend10_30) legend10_30.innerHTML = `10-30% (€${top10.toFixed(0)}-${top30.toFixed(0)})`;
        if (legendLow10) legendLow10.innerHTML = `< 10% (< €${top10.toFixed(0)})`;
    }

    getMap() {
        return this.map;
    }
}
