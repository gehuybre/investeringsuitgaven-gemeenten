// Main application coordinator
import { MapManager } from './map.js';
import { ChartManager } from './chart.js';
import { ControlsManager } from './controls.js';
import { MunicipalityDetailManager } from './municipality-detail.js';
import { ProvincialManager } from './provincial.js';

class App {
    constructor() {
        this.mapManager = null;
        this.chartManager = null;
        this.controlsManager = null;
        this.detailManager = null;
        this.provincialManager = null;
        
        this.municipalitiesData = null;
        this.averagesData = null;
        this.cpiData = null;
        this.beleidsdomeinData = null;
    }

    async init() {
        try {
            console.log('Loading data...');
            await this.loadData();
            
            console.log('Initializing modules...');
            this.initializeModules();
            
            console.log('Setting up interactions...');
            this.setupInteractions();
            
            console.log('✓ Application initialized successfully');
        } catch (error) {
            console.error('Error initializing application:', error);
        }
    }

    async loadData() {
        const [geoResponse, avgResponse, cpiResponse, beleidsdomeinResponse] = await Promise.all([
            fetch('municipalities_enriched.geojson'),
            fetch('averages.json'),
            fetch('cpi.json'),
            fetch('beleidsdomein_totals.json')
        ]);
        
        if (!geoResponse.ok) throw new Error(`Failed to fetch municipalities_enriched.geojson: ${geoResponse.status}`);
        if (!avgResponse.ok) throw new Error(`Failed to fetch averages.json: ${avgResponse.status}`);
        if (!cpiResponse.ok) throw new Error(`Failed to fetch cpi.json: ${cpiResponse.status}`);
        if (!beleidsdomeinResponse.ok) throw new Error(`Failed to fetch beleidsdomein_totals.json: ${beleidsdomeinResponse.status}`);
        
        this.municipalitiesData = await geoResponse.json();
        this.averagesData = await avgResponse.json();
        this.cpiData = await cpiResponse.json();
        this.beleidsdomeinData = await beleidsdomeinResponse.json();
        
        // Process CPI data
        this.processCPIData();
    }

    processCPIData() {
        if (!this.cpiData || !this.cpiData.facts) return;
        
        const cpiMap = {};
        this.cpiData.facts.forEach(fact => {
            const year = parseInt(fact.Jaar);
            if (!cpiMap[year]) {
                cpiMap[year] = fact.Consumptieprijsindex;
            }
        });
        this.cpiData.map = cpiMap;
        this.cpiData.referenceYear = 2014;
        this.cpiData.referenceCPI = cpiMap[2014] || 100.34;
    }

    initializeModules() {
        // Initialize map
        this.mapManager = new MapManager();
        this.mapManager.initMap();
        this.mapManager.setupMap(this.municipalitiesData, (properties) => {
            this.handleFeatureClick(properties);
        });

        // Initialize chart
        this.chartManager = new ChartManager();
        this.chartManager.initChart();
        this.chartManager.setData(
            this.municipalitiesData,
            this.averagesData,
            this.beleidsdomeinData,
            this.cpiData
        );

        // Initialize controls
        this.controlsManager = new ControlsManager(this.chartManager);
        this.controlsManager.setupControls(this.municipalitiesData, this.averagesData);
        this.controlsManager.setupInflationToggle();
        this.controlsManager.setupStackedToggle();

        // Initialize detail manager
        this.detailManager = new MunicipalityDetailManager();

        // Initialize provincial manager (delayed to ensure page is fully loaded)
        setTimeout(() => {
            this.provincialManager = new ProvincialManager();
            this.provincialManager.init();
        }, 500);

        // Initial dashboard update
        this.controlsManager.updateDashboard();
    }

    setupInteractions() {
        // Map click handler is already setup through mapManager
        // Additional cross-module interactions can be added here
    }

    handleFeatureClick(properties) {
        // Show detail panel
        this.detailManager.show(properties);
        
        // Toggle municipality selection
        this.controlsManager.toggleMunicipalitySelection(properties.municipality);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    app.init();
});

export default App;
