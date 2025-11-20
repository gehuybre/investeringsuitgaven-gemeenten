document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

let map;
let chart;
let geojsonLayer;
let municipalitiesData = null; 
let averagesData = null;
let selectedRegions = new Set(['vlaanderen']); // Store selected values
let currentViewMode = 'auto'; // 'auto', 'bar', 'line', 'small-multiples'
let smallMultipleCharts = []; // Store small multiple chart instances
let cpiData = null; // CPI data for inflation adjustment
let inflationMode = 'nominal'; // 'nominal', 'adjusted', or 'both'

async function initApp() {
    map = L.map('map').setView([51.05, 4.4], 9);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(map);

    // Add Legend
    const legend = L.control({position: 'bottomright'});
    legend.onAdd = function (map) {
        const div = L.DomUtil.create('div', 'info legend');
        div.id = 'map-legend';
        div.style.backgroundColor = 'white';
        div.style.padding = '10px 12px';
        div.style.font = '14px/16px Arial, Helvetica, sans-serif';
        div.style.background = 'white';
        div.style.boxShadow = '0 0 15px rgba(0,0,0,0.2)';
        div.style.borderRadius = '5px';
        div.style.minWidth = '200px';
        
        // Initial legend content (will be updated after data loads)
        div.innerHTML = '<strong>Investeringen 2024</strong><br>' +
                        '<small>(€ per inwoner)</small><br>' +
                        '<div style="margin-top: 8px; font-size: 12px; color: #666;">Kleuren gebaseerd op percentielen van het maximum</div>' +
                        '<i style="background:#d73027; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7; margin-top: 4px;"></i> <span id="legend-top90">> 90% (hoog)</span><br>' +
                        '<i style="background:#f46d43; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7; margin-top: 4px;"></i> <span id="legend-70-90">70-90%</span><br>' +
                        '<i style="background:#fdae61; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7; margin-top: 4px;"></i> <span id="legend-50-70">50-70%</span><br>' +
                        '<i style="background:#abd9e9; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7; margin-top: 4px;"></i> <span id="legend-30-50">30-50%</span><br>' +
                        '<i style="background:#74add1; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7; margin-top: 4px;"></i> <span id="legend-10-30">10-30%</span><br>' +
                        '<i style="background:#4575b4; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7; margin-top: 4px;"></i> <span id="legend-low10">&lt; 10% (laag)</span>';
        return div;
    };
    legend.addTo(map);

    const ctx = document.getElementById('investmentChart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Array.from({length: 11}, (_, i) => 2014 + i),
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true, // Enable legend for multiple datasets
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': € ' + context.raw.toFixed(2);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Bedrag (€)' },
                    grid: { color: '#f0f0f0' }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });

    try {
        const [geoResponse, avgResponse, cpiResponse] = await Promise.all([
            fetch('municipalities.geojson'),
            fetch('averages.json'),
            fetch('cpi.json')
        ]);
        
        municipalitiesData = await geoResponse.json();
        averagesData = await avgResponse.json();
        cpiData = await cpiResponse.json();
        
        // Process CPI data into a simple year -> CPI mapping
        processCPIData();
        
        setupMap(municipalitiesData);
        setupControls(municipalitiesData, averagesData);
        setupViewToggle();
        setupInflationToggle();
        updateDashboard(); // Initial update

    } catch (error) {
        console.error('Error loading data:', error);
    }
}

// Store min/max values globally for legend
let mapMinValue = null;
let mapMaxValue = null;

function setupMap(data) {
    const values2024 = data.features
        .map(f => f.properties['2024'])
        .filter(v => v !== null && !isNaN(v));
    
    mapMaxValue = Math.max(...values2024);
    mapMinValue = Math.min(...values2024);

    geojsonLayer = L.geoJSON(data, {
        style: (feature) => style(feature, mapMinValue, mapMaxValue),
        onEachFeature: onEachFeature
    }).addTo(map);

    map.fitBounds(geojsonLayer.getBounds());
    
    // Update legend with actual values
    updateLegend();
}

function updateLegend() {
    if (mapMinValue === null || mapMaxValue === null) return;
    
    const legend = document.getElementById('map-legend');
    if (!legend) return;
    
    // Calculate threshold values
    const top90 = mapMaxValue * 0.9;
    const top70 = mapMaxValue * 0.7;
    const top50 = mapMaxValue * 0.5;
    const top30 = mapMaxValue * 0.3;
    const top10 = mapMaxValue * 0.1;
    
    // Update legend text with actual values
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

function setupControls(geoData, avgData) {
    // Setup tab navigation
    setupTabNavigation();
    
    // Populate Vlaanderen tab
    populateVlaanderenTab();
    
    // Populate Provincies tab
    if (avgData.Provincies) {
        populateProvinciesTab(avgData.Provincies);
    }
    
    // Populate Gemeenten tab
    populateGemeentenTab(geoData);
    
    // Setup search functionality
    setupSearchFunctionality();
    
    // Setup select all/deselect all buttons
    setupSelectAllButtons();
}

function setupTabNavigation() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');
            
            // Remove active class from all tabs and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            button.classList.add('active');
            document.getElementById(`tab-${targetTab}`).classList.add('active');
        });
    });
}

function populateVlaanderenTab() {
    const container = document.getElementById('checkbox-list-vlaanderen');
    container.innerHTML = '';
    
    const checkboxItem = document.createElement('div');
    checkboxItem.className = 'checkbox-item';
    
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = 'checkbox-vlaanderen';
    checkbox.value = 'vlaanderen';
    checkbox.checked = selectedRegions.has('vlaanderen');
    
    const label = document.createElement('label');
    label.setAttribute('for', 'checkbox-vlaanderen');
    label.textContent = 'Vlaanderen (gemiddelde)';
    
    checkboxItem.appendChild(checkbox);
    checkboxItem.appendChild(label);
    container.appendChild(checkboxItem);
    
    // Add event listener
    checkbox.addEventListener('change', (e) => {
        if (e.target.checked) {
            selectedRegions.add('vlaanderen');
        } else {
            selectedRegions.delete('vlaanderen');
        }
        updateDashboard();
    });
}

function populateProvinciesTab(provincesData) {
    const container = document.getElementById('checkbox-list-provincies');
    container.innerHTML = '';
    
    const provinces = Object.keys(provincesData).sort();
    
    provinces.forEach(provName => {
        const checkboxItem = document.createElement('div');
        checkboxItem.className = 'checkbox-item';
        checkboxItem.setAttribute('data-name', provName.toLowerCase());
        
        // Sanitize ID - replace spaces and special chars with hyphens
        const safeId = `checkbox-prov-${provName.replace(/[^a-zA-Z0-9]/g, '-')}`;
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = safeId;
        checkbox.value = `prov:${provName}`;
        checkbox.checked = selectedRegions.has(`prov:${provName}`);
        
        const label = document.createElement('label');
        label.setAttribute('for', safeId);
        label.textContent = provName;
        
        checkboxItem.appendChild(checkbox);
        checkboxItem.appendChild(label);
        container.appendChild(checkboxItem);
        
        // Add event listener
        checkbox.addEventListener('change', (e) => {
            const value = e.target.value;
            if (e.target.checked) {
                selectedRegions.add(value);
            } else {
                selectedRegions.delete(value);
            }
            updateDashboard();
        });
    });
}

function populateGemeentenTab(geoData) {
    const container = document.getElementById('checkbox-list-gemeenten');
    container.innerHTML = '';
    
    const municipalities = geoData.features
        .map(f => f.properties.municipality)
        .sort((a, b) => a.localeCompare(b));
    
    municipalities.forEach(munName => {
        const checkboxItem = document.createElement('div');
        checkboxItem.className = 'checkbox-item';
        checkboxItem.setAttribute('data-name', munName.toLowerCase());
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `checkbox-mun-${munName}`;
        checkbox.value = `mun:${munName}`;
        checkbox.checked = selectedRegions.has(`mun:${munName}`);
        
        const label = document.createElement('label');
        label.setAttribute('for', `checkbox-mun-${munName}`);
        label.textContent = munName;
        
        checkboxItem.appendChild(checkbox);
        checkboxItem.appendChild(label);
        container.appendChild(checkboxItem);
        
        // Add event listener
        checkbox.addEventListener('change', (e) => {
            const value = e.target.value;
            if (e.target.checked) {
                selectedRegions.add(value);
            } else {
                selectedRegions.delete(value);
            }
            updateDashboard();
        });
    });
}

function setupSearchFunctionality() {
    // Vlaanderen tab - disabled but keep for consistency
    const searchVlaanderen = document.getElementById('search-vlaanderen');
    
    // Provincies tab
    const searchProvincies = document.getElementById('search-provincies');
    searchProvincies.addEventListener('input', (e) => {
        filterCheckboxList('provincies', e.target.value);
    });
    
    // Gemeenten tab
    const searchGemeenten = document.getElementById('search-gemeenten');
    searchGemeenten.addEventListener('input', (e) => {
        filterCheckboxList('gemeenten', e.target.value);
    });
}

function filterCheckboxList(tabName, searchTerm) {
    const container = document.getElementById(`checkbox-list-${tabName}`);
    const items = container.querySelectorAll('.checkbox-item');
    const term = searchTerm.toLowerCase().trim();
    
    items.forEach(item => {
        const name = item.getAttribute('data-name') || '';
        const label = item.querySelector('label').textContent.toLowerCase();
        
        if (term === '' || name.includes(term) || label.includes(term)) {
            item.classList.remove('hidden');
        } else {
            item.classList.add('hidden');
        }
    });
}

function setupSelectAllButtons() {
    const selectAllButtons = document.querySelectorAll('.btn-select-all');
    const deselectAllButtons = document.querySelectorAll('.btn-deselect-all');
    
    selectAllButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            selectAllInTab(tabName);
        });
    });
    
    deselectAllButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            deselectAllInTab(tabName);
        });
    });
}

function selectAllInTab(tabName) {
    const container = document.getElementById(`checkbox-list-${tabName}`);
    // Only select visible (not hidden) checkboxes
    const checkboxes = Array.from(container.querySelectorAll('input[type="checkbox"]:not(:checked)'))
        .filter(checkbox => !checkbox.closest('.checkbox-item').classList.contains('hidden'));
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
        selectedRegions.add(checkbox.value);
    });
    
    updateDashboard();
}

function deselectAllInTab(tabName) {
    const container = document.getElementById(`checkbox-list-${tabName}`);
    // Only deselect visible (not hidden) checkboxes
    const checkboxes = Array.from(container.querySelectorAll('input[type="checkbox"]:checked'))
        .filter(checkbox => !checkbox.closest('.checkbox-item').classList.contains('hidden'));
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
        selectedRegions.delete(checkbox.value);
    });
    
    updateDashboard();
}

function syncCheckboxStates() {
    // Sync Vlaanderen checkbox
    const vlaanderenCheckbox = document.getElementById('checkbox-vlaanderen');
    if (vlaanderenCheckbox) {
        vlaanderenCheckbox.checked = selectedRegions.has('vlaanderen');
    }
    
    // Sync Provincies checkboxes
    selectedRegions.forEach(value => {
        if (value.startsWith('prov:')) {
            const provName = value.split(':')[1];
            const checkbox = document.getElementById(`checkbox-prov-${provName}`);
            if (checkbox) {
                checkbox.checked = true;
            }
        }
    });
    
    // Sync Gemeenten checkboxes
    selectedRegions.forEach(value => {
        if (value.startsWith('mun:')) {
            const munName = value.split(':')[1];
            const safeId = `checkbox-mun-${munName.replace(/[^a-zA-Z0-9]/g, '-')}`;
            const checkbox = document.getElementById(safeId);
            if (checkbox) {
                checkbox.checked = true;
            }
        }
    });
    
    // Also uncheck items that are not in selectedRegions
    document.querySelectorAll('input[type="checkbox"][id^="checkbox-prov-"]').forEach(checkbox => {
        if (!selectedRegions.has(checkbox.value)) {
            checkbox.checked = false;
        }
    });
    
    document.querySelectorAll('input[type="checkbox"][id^="checkbox-mun-"]').forEach(checkbox => {
        if (!selectedRegions.has(checkbox.value)) {
            checkbox.checked = false;
        }
    });
}

// Color palette with high contrast between consecutive colors
// Colors are ordered to maximize contrast between adjacent selections
const colorPalette = {
    vlaanderen: '#e63946', // Red
    provinces: [
        '#2a9d8f', // Teal
        '#d62828', // Red
        '#003049', // Dark blue
        '#f77f00', // Orange
        '#06a77d', // Green
        '#6c5ce7'  // Purple
    ],
    municipalities: [
        '#0055cc', // Blue
        '#ff6b6b', // Coral red
        '#00b894', // Mint green
        '#6c5ce7', // Purple
        '#f9ca24', // Yellow
        '#d63031', // Dark red
        '#4ecdc4', // Turquoise
        '#e17055', // Orange
        '#0984e3', // Bright blue
        '#fd79a8', // Pink
        '#00cec9', // Cyan
        '#fdcb6e', // Peach
        '#2d3436', // Charcoal
        '#55efc4', // Aqua
        '#e84393', // Magenta
        '#74b9ff', // Light blue
        '#a29bfe', // Light purple
        '#ffeaa7', // Light yellow
        '#636e72', // Dark gray
        '#00b894'  // Green
    ]
};

// Line and border styles for differentiation
const lineStyles = [
    { borderDash: [] },           // Solid
    { borderDash: [5, 5] },        // Dashed
    { borderDash: [2, 2] },        // Dotted
    { borderDash: [10, 5, 2, 5] }, // Dash-dot
    { borderDash: [5, 10] },       // Long dash
    { borderDash: [2, 8, 2, 8] }  // Dot-dash
];

function getColorForRegion(type, index, name) {
    if (type === 'vlaanderen') {
        return colorPalette.vlaanderen;
    } else if (type === 'province') {
        // Use index directly for sequential selection to maximize contrast
        return colorPalette.provinces[index % colorPalette.provinces.length];
    } else if (type === 'municipality') {
        // For municipalities, use index for sequential selection to maximize contrast
        // This ensures consecutive selections have very different colors
        return colorPalette.municipalities[index % colorPalette.municipalities.length];
    }
    return '#0055cc'; // Default
}

function getLineStyle(index) {
    return lineStyles[index % lineStyles.length];
}

function processCPIData() {
    if (!cpiData || !cpiData.facts) return;
    
    // Create a simple year -> CPI mapping (using unique years only)
    const cpiMap = {};
    cpiData.facts.forEach(fact => {
        const year = parseInt(fact.Jaar);
        if (!cpiMap[year]) {
            cpiMap[year] = fact.Consumptieprijsindex;
        }
    });
    cpiData.map = cpiMap;
    
    // Set 2014 as reference year for inflation adjustment
    cpiData.referenceYear = 2014;
    cpiData.referenceCPI = cpiMap[2014] || 100.34;
}

function setupViewToggle() {
    const toggleBtn = document.getElementById('view-toggle-btn');
    const toggleText = document.getElementById('view-toggle-text');
    
    toggleBtn.addEventListener('click', () => {
        // Cycle through view modes
        if (currentViewMode === 'auto') {
            currentViewMode = 'bar';
            toggleText.textContent = 'Staafdiagram';
        } else if (currentViewMode === 'bar') {
            currentViewMode = 'line';
            toggleText.textContent = 'Lijndiagram';
        } else if (currentViewMode === 'line') {
            currentViewMode = 'small-multiples';
            toggleText.textContent = 'Small multiples';
        } else {
            currentViewMode = 'auto';
            toggleText.textContent = 'Automatisch';
        }
        updateDashboard();
    });
}

function setupInflationToggle() {
    const inflationSelect = document.getElementById('inflation-mode');
    
    inflationSelect.addEventListener('change', (e) => {
        inflationMode = e.target.value;
        updateDashboard();
    });
}

function adjustForInflation(value, year) {
    if (!cpiData || !cpiData.map) return value;
    
    const yearCPI = cpiData.map[year];
    if (!yearCPI) return value;
    
    // Adjust to 2014 prices: value * (2014 CPI / year CPI)
    return value * (cpiData.referenceCPI / yearCPI);
}

function updateDashboard() {
    const count = selectedRegions.size;
    const viewMode = determineViewMode(count);
    
    // Update toggle button text for auto mode
    if (currentViewMode === 'auto') {
        const toggleText = document.getElementById('view-toggle-text');
        if (count <= 3) {
            toggleText.textContent = 'Automatisch (Staaf)';
        } else if (count <= 7) {
            toggleText.textContent = 'Automatisch (Lijn)';
        } else {
            toggleText.textContent = 'Automatisch (Multiples)';
        }
    }
    
    // Show/hide containers based on view mode
    const chartWrapper = document.getElementById('chart-wrapper');
    const smallMultiplesContainer = document.getElementById('small-multiples-container');
    
    if (viewMode === 'small-multiples') {
        chartWrapper.style.display = 'none';
        smallMultiplesContainer.style.display = 'grid';
        renderSmallMultiples();
    } else {
        chartWrapper.style.display = 'block';
        smallMultiplesContainer.style.display = 'none';
        renderMainChart(viewMode);
    }
    
    // Update Title
    document.getElementById('selected-label').textContent = count > 0 
        ? `${count} regio('s) geselecteerd` 
        : 'Selecteer een regio';
    
    // Update subtitle based on inflation adjustment
    const subtitleText = document.getElementById('subtitle-text');
    if (subtitleText) {
        if (inflationMode === 'adjusted') {
            subtitleText.textContent = 'Investeringsuitgaven per inwoner (€, gecorrigeerd naar 2014 prijzen)';
        } else if (inflationMode === 'both') {
            subtitleText.textContent = 'Investeringsuitgaven per inwoner (€, nominaal en gecorrigeerd naar 2014)';
        } else {
            subtitleText.textContent = 'Investeringsuitgaven per inwoner (€)';
        }
    }
    
    // Sync checkbox states
    syncCheckboxStates();
}

function determineViewMode(count) {
    if (currentViewMode !== 'auto') {
        return currentViewMode;
    }
    
    // Auto mode: determine based on count
    if (count <= 3) {
        return 'bar';
    } else if (count <= 7) {
        return 'line';
    } else {
        return 'small-multiples';
    }
}

function renderMainChart(viewMode) {
    const datasets = [];
    const years = Array.from({length: 11}, (_, i) => 2014 + i);

    // Track indices for color and style assignment
    let datasetIndex = 0;

    // Helper to create dataset with alternating colors and styles
    const createDataset = (label, data, color, type, index) => {
        const lineStyle = getLineStyle(index);
        const base = {
            label: label,
            data: data,
            borderColor: color,
            backgroundColor: color,
            borderWidth: 2,
            ...lineStyle
        };
        
        if (type === 'bar') {
            // For bars, use different border styles and opacity
            return {
                ...base,
                borderRadius: 4,
                barPercentage: 0.8,
                categoryPercentage: 0.9,
                backgroundColor: color + (index % 2 === 0 ? 'CC' : '99'), // Alternating opacity
                borderDash: lineStyle.borderDash,
                borderWidth: index % 3 === 0 ? 2 : (index % 3 === 1 ? 1.5 : 2.5) // Varying border width
            };
        } else if (type === 'line') {
            return {
                ...base,
                fill: false,
                tension: 0.1,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: color,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                borderDash: lineStyle.borderDash,
                borderWidth: index % 3 === 0 ? 2 : (index % 3 === 1 ? 1.5 : 2.5) // Varying line width
            };
        }
        return base;
    };

    // Helper function to add datasets for a region
    const addRegionDatasets = (name, nominalData, color, datasetIndex) => {
        if (inflationMode === 'nominal' || inflationMode === 'both') {
            const ds = createDataset(
                inflationMode === 'both' ? `${name} (nominaal)` : name,
                nominalData,
                color,
                viewMode,
                datasetIndex
            );
            datasets.push(ds);
            datasetIndex++;
        }
        
        if (inflationMode === 'adjusted' || inflationMode === 'both') {
            const adjustedData = nominalData.map((val, idx) => adjustForInflation(val, years[idx]));
            const ds = createDataset(
                inflationMode === 'both' ? `${name} (2014 €)` : name,
                adjustedData,
                color,
                viewMode,
                datasetIndex
            );
            
            // Make adjusted data visually distinct when showing both
            if (inflationMode === 'both') {
                if (viewMode === 'line') {
                    ds.borderDash = [5, 5]; // Dashed line for adjusted
                    ds.borderWidth = 2;
                } else if (viewMode === 'bar') {
                    ds.backgroundColor = color + '99'; // More transparent
                    ds.borderWidth = 2;
                    ds.borderColor = color;
                }
            }
            
            datasets.push(ds);
            datasetIndex++;
        }
        
        return datasetIndex;
    };

    // Track indices for provinces and municipalities separately for color assignment
    let provinceIndex = 0;
    let municipalityIndex = 0;

    // 1. Vlaanderen
    if (selectedRegions.has('vlaanderen')) {
        const nominalData = years.map(y => averagesData.Vlaanderen[y]);
        datasetIndex = addRegionDatasets(
            'Vlaanderen (gemiddelde)',
            nominalData,
            getColorForRegion('vlaanderen', 0, ''),
            datasetIndex
        );
    }

    // 2. Provinces
    selectedRegions.forEach(val => {
        if (val.startsWith('prov:')) {
            const provName = val.split(':')[1];
            const nominalData = years.map(y => averagesData.Provincies[provName][y]);
            datasetIndex = addRegionDatasets(
                provName,
                nominalData,
                getColorForRegion('province', provinceIndex++, provName),
                datasetIndex
            );
        }
    });

    // 3. Municipalities
    selectedRegions.forEach(val => {
        if (val.startsWith('mun:')) {
            const munName = val.split(':')[1];
            const feature = municipalitiesData.features.find(f => f.properties.municipality === munName);
            if (feature) {
                const nominalData = years.map(y => feature.properties[String(y)]);
                datasetIndex = addRegionDatasets(
                    munName,
                    nominalData,
                    getColorForRegion('municipality', municipalityIndex++, munName),
                    datasetIndex
                );
            }
        }
    });

    // Update chart type
    chart.config.type = viewMode;
    
    // Update chart options based on type
    if (viewMode === 'bar') {
        chart.options.scales.x.stacked = false;
        chart.options.scales.y.stacked = false;
    } else if (viewMode === 'line') {
        chart.options.scales.x.stacked = false;
        chart.options.scales.y.stacked = false;
    }

    chart.data.datasets = datasets;
    chart.update();
}

function renderSmallMultiples() {
    // Destroy existing small multiple charts
    smallMultipleCharts.forEach(ch => ch.destroy());
    smallMultipleCharts = [];
    
    const container = document.getElementById('small-multiples-container');
    container.innerHTML = '';
    
    const years = Array.from({length: 11}, (_, i) => 2014 + i);
    const regions = [];
    
    // Track indices for color assignment
    let provinceIndex = 0;
    let municipalityIndex = 0;
    
    // Helper to create region data (with nominal and/or adjusted)
    const createRegionData = (name, nominalData, color, index) => {
        const datasets = [];
        
        if (inflationMode === 'nominal' || inflationMode === 'both') {
            datasets.push({
                label: inflationMode === 'both' ? 'Nominaal' : name,
                data: nominalData,
                backgroundColor: color,
                borderColor: color,
                borderWidth: 2,
                fill: false
            });
        }
        
        if (inflationMode === 'adjusted' || inflationMode === 'both') {
            const adjustedData = nominalData.map((val, idx) => adjustForInflation(val, years[idx]));
            datasets.push({
                label: inflationMode === 'both' ? '2014 €' : name,
                data: adjustedData,
                backgroundColor: color + '99',
                borderColor: color,
                borderWidth: 2,
                borderDash: inflationMode === 'both' ? [5, 5] : [],
                fill: false
            });
        }
        
        return { name, datasets, color, index };
    };
    
    // Collect all selected regions
    if (selectedRegions.has('vlaanderen')) {
        const nominalData = years.map(y => averagesData.Vlaanderen[y]);
        regions.push(createRegionData(
            'Vlaanderen (gemiddelde)',
            nominalData,
            getColorForRegion('vlaanderen', 0, ''),
            0
        ));
    }
    
    selectedRegions.forEach(val => {
        if (val.startsWith('prov:')) {
            const provName = val.split(':')[1];
            const nominalData = years.map(y => averagesData.Provincies[provName][y]);
            regions.push(createRegionData(
                provName,
                nominalData,
                getColorForRegion('province', provinceIndex++, provName),
                regions.length
            ));
        }
    });
    
    selectedRegions.forEach(val => {
        if (val.startsWith('mun:')) {
            const munName = val.split(':')[1];
            const feature = municipalitiesData.features.find(f => f.properties.municipality === munName);
            if (feature) {
                const nominalData = years.map(y => feature.properties[String(y)]);
                regions.push(createRegionData(
                    munName,
                    nominalData,
                    getColorForRegion('municipality', municipalityIndex++, munName),
                    regions.length
                ));
            }
        }
    });
    
    // Create a chart for each region
    regions.forEach((region, idx) => {
        const chartDiv = document.createElement('div');
        chartDiv.className = 'small-multiple-chart';
        
        const title = document.createElement('h4');
        title.textContent = region.name;
        chartDiv.appendChild(title);
        
        const canvas = document.createElement('canvas');
        chartDiv.appendChild(canvas);
        container.appendChild(chartDiv);
        
        const lineStyle = getLineStyle(region.index);
        const ctx = canvas.getContext('2d');
        const smallChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: years,
                datasets: region.datasets.map(ds => ({
                    ...ds,
                    borderRadius: 4
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return '€ ' + context.raw.toFixed(2);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            font: {
                                size: 10
                            }
                        }
                    },
                    x: {
                        ticks: {
                            font: {
                                size: 10
                            }
                        }
                    }
                }
            }
        });
        
        smallMultipleCharts.push(smallChart);
    });
}

// Map Interaction
function onEachFeature(feature, layer) {
    layer.on({
        mouseover: (e) => {
            const layer = e.target;
            layer.setStyle({ weight: 3, color: '#666', dashArray: '', fillOpacity: 0.9 });
            layer.bringToFront();
        },
        mouseout: (e) => {
            geojsonLayer.resetStyle(e.target);
        },
        click: (e) => {
            const name = feature.properties.municipality;
            const value = `mun:${name}`;
            
            // Toggle selection logic - update checkbox state
            // Sanitize ID to match the one used in populateGemeentenTab
            const safeId = `checkbox-mun-${name.replace(/[^a-zA-Z0-9]/g, '-')}`;
            const checkbox = document.getElementById(safeId);
            
            if (checkbox) {
                // Toggle selection
                if (selectedRegions.has(value)) {
                    selectedRegions.delete(value);
                    checkbox.checked = false;
                } else {
                    selectedRegions.add(value);
                    checkbox.checked = true;
                }
                
                updateDashboard();
                
                // Switch to gemeenten tab if not already active
                const gemeentenTab = document.querySelector('.tab-button[data-tab="gemeenten"]');
                const gemeentenContent = document.getElementById('tab-gemeenten');
                if (gemeentenTab && !gemeentenTab.classList.contains('active')) {
                    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
                    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
                    gemeentenTab.classList.add('active');
                    gemeentenContent.classList.add('active');
                }
            }
        }
    });
    
    const name = feature.properties.municipality;
    const val2024 = feature.properties['2024'];
    layer.bindTooltip(`<strong>${name}</strong><br>2024: €${val2024 ? val2024.toFixed(2) : '-'}`);
}

// Styling - Intuitive color scale: warm colors (red/orange) = high, cool colors (green/blue) = low
// This makes it immediately clear which municipalities have high vs low investment
function getColor(d, min, max) {
    const t = (d - min) / (max - min);
    
    // Intuitive gradient: Red/Orange (high) → Yellow → Light Green → Green → Blue (low)
    // Warm colors = high investment, cool colors = low investment
    if (t >= 0.9) return '#d73027';      // Top 10% - Bright red (high) - clearly highest
    if (t >= 0.7) return '#f46d43';      // 70-90% - Orange-red - high
    if (t >= 0.5) return '#fdae61';      // 50-70% - Orange-yellow - medium-high
    if (t >= 0.3) return '#abd9e9';      // 30-50% - Light blue - medium-low
    if (t >= 0.1) return '#74add1';      // 10-30% - Blue - low
    return '#4575b4';                    // Bottom 10% - Dark blue (low) - clearly lowest
}

function style(feature, min, max) {
    const val = feature.properties['2024'];
    return {
        fillColor: getColor(val, min, max),
        weight: 1,
        opacity: 1,
        color: 'white',
        dashArray: '3',
        fillOpacity: 0.7
    };
}
