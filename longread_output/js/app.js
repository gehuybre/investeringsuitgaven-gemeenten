document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

let map;
let chart;
let geojsonLayer;
let municipalitiesData = null; 
let averagesData = null;
let selectedRegions = new Set(['vlaanderen']); // Store selected values

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
    const select = document.getElementById('region-select');
    
    // Enable multiple selection
    select.multiple = true;
    select.style.height = '300px'; // Make it taller to see options

    // Populate Provinces
    if (avgData.Provincies) {
        Object.keys(avgData.Provincies).sort().forEach(prov => {
            const option = document.createElement('option');
            option.value = `prov:${prov}`;
            option.textContent = prov;
            document.getElementById('optgroup-provinces').appendChild(option);
        });
    }

    // Populate Municipalities
    const municipalities = geoData.features
        .map(f => f.properties.municipality)
        .sort((a, b) => a.localeCompare(b));

    municipalities.forEach(name => {
        const option = document.createElement('option');
        option.value = `mun:${name}`;
        option.textContent = name;
        document.getElementById('optgroup-municipalities').appendChild(option);
    });

    // Event Listener
    select.addEventListener('change', (e) => {
        // Update selectedRegions set from select options
        selectedRegions.clear();
        Array.from(select.selectedOptions).forEach(opt => {
            selectedRegions.add(opt.value);
        });
        updateDashboard();
    });
}

function updateDashboard() {
    const datasets = [];
    const years = Array.from({length: 11}, (_, i) => 2014 + i);

    // Helper to create dataset
    const createDataset = (label, data, color) => ({
        label: label,
        data: data,
        backgroundColor: color,
        borderColor: color,
        borderWidth: 1,
        borderRadius: 4,
        barPercentage: 0.8,
        categoryPercentage: 0.9
    });

    // 1. Vlaanderen (Always show if selected or default? Logic says user selects)
    // Check 'vlaanderen'
    if (selectedRegions.has('vlaanderen')) {
        datasets.push(createDataset(
            'Vlaanderen (gemiddelde)', 
            years.map(y => averagesData.Vlaanderen[y]),
            '#e63946'
        ));
    }

    // 2. Provinces
    selectedRegions.forEach(val => {
        if (val.startsWith('prov:')) {
            const provName = val.split(':')[1];
            datasets.push(createDataset(
                provName,
                years.map(y => averagesData.Provincies[provName][y]),
                '#2a9d8f' // Use a color palette ideally
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
                    '#0055cc'
                ));
            }
        }
    });

    // Update Title
    const count = selectedRegions.size;
    document.getElementById('selected-label').textContent = count > 0 
        ? `${count} regio('s) geselecteerd` 
        : 'Selecteer een regio';

    chart.data.datasets = datasets;
    chart.update();
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
            
            // Toggle selection logic
            const select = document.getElementById('region-select');
            const option = Array.from(select.options).find(opt => opt.value === value);
            
            if (option) {
                // If ctrl key pressed, or just add to selection? 
                // Requirement: "sta multiple selectie toe". 
                // Standard behavior on map click is usually "add to selection" or "replace".
                // Let's implement: Add to selection (toggle)
                
                if (selectedRegions.has(value)) {
                    selectedRegions.delete(value);
                    option.selected = false;
                } else {
                    selectedRegions.add(value);
                    option.selected = true;
                }
                
                updateDashboard();
                // REMOVED scrollIntoView to prevent jumping
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
