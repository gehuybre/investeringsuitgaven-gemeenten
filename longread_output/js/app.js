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
        div.style.backgroundColor = 'white';
        div.style.padding = '6px 8px';
        div.style.font = '14px/16px Arial, Helvetica, sans-serif';
        div.style.background = 'white';
        div.style.boxShadow = '0 0 15px rgba(0,0,0,0.2)';
        div.style.borderRadius = '5px';
        
        // Gradient definition
        div.innerHTML = '<strong>Investeringen 2024</strong><br>' +
                        '<small>(€ per inwoner)</small><br>' +
                        '<i style="background:#08306b; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7;"></i> > 90%<br>' +
                        '<i style="background:#08519c; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7;"></i> 70-90%<br>' +
                        '<i style="background:#2171b5; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7;"></i> 50-70%<br>' +
                        '<i style="background:#4292c6; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7;"></i> 30-50%<br>' +
                        '<i style="background:#9ecae1; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7;"></i> 10-30%<br>' +
                        '<i style="background:#deebf7; width: 18px; height: 18px; float: left; margin-right: 8px; opacity: 0.7;"></i> < 10%';
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
        const [geoResponse, avgResponse] = await Promise.all([
            fetch('municipalities.geojson'),
            fetch('averages.json')
        ]);
        
        municipalitiesData = await geoResponse.json();
        averagesData = await avgResponse.json();
        
        setupMap(municipalitiesData);
        setupControls(municipalitiesData, averagesData);
        setupViewToggle();
        updateDashboard(); // Initial update

    } catch (error) {
        console.error('Error loading data:', error);
    }
}

function setupMap(data) {
    const values2024 = data.features
        .map(f => f.properties['2024'])
        .filter(v => v !== null && !isNaN(v));
    
    const maxVal = Math.max(...values2024);
    const minVal = Math.min(...values2024);

    geojsonLayer = L.geoJSON(data, {
        style: (feature) => style(feature, minVal, maxVal),
        onEachFeature: onEachFeature
    }).addTo(map);

    map.fitBounds(geojsonLayer.getBounds());
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

    // Track indices for provinces and municipalities separately for color assignment
    let provinceIndex = 0;
    let municipalityIndex = 0;

    // 1. Vlaanderen
    if (selectedRegions.has('vlaanderen')) {
        datasets.push(createDataset(
            'Vlaanderen (gemiddelde)', 
            years.map(y => averagesData.Vlaanderen[y]),
            getColorForRegion('vlaanderen', 0, ''),
            viewMode,
            datasetIndex++
        ));
    }

    // 2. Provinces
    selectedRegions.forEach(val => {
        if (val.startsWith('prov:')) {
            const provName = val.split(':')[1];
            datasets.push(createDataset(
                provName,
                years.map(y => averagesData.Provincies[provName][y]),
                getColorForRegion('province', provinceIndex++, provName),
                viewMode,
                datasetIndex++
            ));
        }
    });

    // 3. Municipalities
    selectedRegions.forEach(val => {
        if (val.startsWith('mun:')) {
            const munName = val.split(':')[1];
            const feature = municipalitiesData.features.find(f => f.properties.municipality === munName);
            if (feature) {
                datasets.push(createDataset(
                    munName,
                    years.map(y => feature.properties[String(y)]),
                    getColorForRegion('municipality', municipalityIndex++, munName),
                    viewMode,
                    datasetIndex++
                ));
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
    
    // Collect all selected regions
    if (selectedRegions.has('vlaanderen')) {
        regions.push({
            name: 'Vlaanderen (gemiddelde)',
            data: years.map(y => averagesData.Vlaanderen[y]),
            color: getColorForRegion('vlaanderen', 0, ''),
            index: 0
        });
    }
    
    selectedRegions.forEach(val => {
        if (val.startsWith('prov:')) {
            const provName = val.split(':')[1];
            regions.push({
                name: provName,
                data: years.map(y => averagesData.Provincies[provName][y]),
                color: getColorForRegion('province', provinceIndex++, provName),
                index: regions.length
            });
        }
    });
    
    selectedRegions.forEach(val => {
        if (val.startsWith('mun:')) {
            const munName = val.split(':')[1];
            const feature = municipalitiesData.features.find(f => f.properties.municipality === munName);
            if (feature) {
                regions.push({
                    name: munName,
                    data: years.map(y => feature.properties[String(y)]),
                    color: getColorForRegion('municipality', municipalityIndex++, munName),
                    index: regions.length
                });
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
                datasets: [{
                    label: region.name,
                    data: region.data,
                    backgroundColor: region.color + 'CC',
                    borderColor: region.color,
                    borderWidth: 2,
                    borderRadius: 4,
                    borderDash: lineStyle.borderDash
                }]
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

// Styling
function getColor(d, min, max) {
    const t = (d - min) / (max - min);
    return d > max * 0.9 ? '#08306b' :
           d > max * 0.7 ? '#08519c' :
           d > max * 0.5 ? '#2171b5' :
           d > max * 0.3 ? '#4292c6' :
           d > max * 0.1 ? '#9ecae1' :
                           '#deebf7';
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
