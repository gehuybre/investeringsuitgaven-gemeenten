// Chart management module
import { getColorForRegion, getLineStyle, colorPalette } from './utils.js';

export class ChartManager {
    constructor() {
        this.chart = null;
        this.smallMultipleCharts = [];
        this.municipalitiesData = null;
        this.averagesData = null;
        this.beleidsdomeinData = null;
        this.cpiData = null;
        this.selectedRegions = new Set(['vlaanderen']);
        this.showNominal = true;
        this.showAdjusted = false;
        this.showStacked = false;
    }

    // Initialize main chart
    initChart() {
        const ctx = document.getElementById('investmentChart').getContext('2d');
        this.chart = new Chart(ctx, {
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
                        display: true,
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
        
        return this.chart;
    }

    // Set data references
    setData(municipalitiesData, averagesData, beleidsdomeinData, cpiData) {
        this.municipalitiesData = municipalitiesData;
        this.averagesData = averagesData;
        this.beleidsdomeinData = beleidsdomeinData;
        this.cpiData = cpiData;
    }

    // Set selected regions
    setSelectedRegions(regions) {
        this.selectedRegions = regions;
    }

    // Set display options
    setDisplayOptions(showNominal, showAdjusted, showStacked) {
        this.showNominal = showNominal;
        this.showAdjusted = showAdjusted;
        this.showStacked = showStacked;
    }

    // Adjust value for inflation
    adjustForInflation(value, year) {
        if (!this.cpiData || !this.cpiData.map) return value;
        
        const yearCPI = this.cpiData.map[year];
        if (!yearCPI) return value;
        
        return value * (this.cpiData.referenceCPI / yearCPI);
    }

    // Update dashboard based on current selections
    updateDashboard() {
        const count = this.selectedRegions.size;
        
        const chartWrapper = document.getElementById('chart-wrapper');
        const smallMultiplesContainer = document.getElementById('small-multiples-container');
        
        if (this.showStacked && count === 1) {
            chartWrapper.style.display = 'block';
            smallMultiplesContainer.style.display = 'none';
            this.renderStackedChart();
        } else if (this.showStacked && count > 1) {
            chartWrapper.style.display = 'none';
            smallMultiplesContainer.style.display = 'grid';
            this.renderStackedSmallMultiples();
        } else {
            chartWrapper.style.display = 'none';
            smallMultiplesContainer.style.display = 'grid';
            this.renderSmallMultiples();
        }
        
        document.getElementById('selected-label').textContent = count > 0 
            ? `${count} regio('s) geselecteerd` 
            : 'Selecteer een regio';
        
        this.updateSubtitle();
    }

    // Update subtitle based on current settings
    updateSubtitle() {
        const subtitleText = document.getElementById('subtitle-text');
        if (!subtitleText) return;

        const count = this.selectedRegions.size;
        
        if (this.showStacked && count === 1) {
            if (this.showNominal && this.showAdjusted) {
                subtitleText.textContent = 'Totale investeringen per beleidsdomein (nominaal & reëel 2014)';
            } else if (this.showAdjusted) {
                subtitleText.textContent = 'Totale investeringen per beleidsdomein (reëel, 2014 prijzen)';
            } else {
                subtitleText.textContent = 'Totale investeringen per beleidsdomein (nominaal)';
            }
        } else if (this.showStacked && count > 1) {
            if (this.showNominal && this.showAdjusted) {
                subtitleText.textContent = 'Investeringen per beleidsdomein per gemeente (nominaal & reëel 2014)';
            } else if (this.showAdjusted) {
                subtitleText.textContent = 'Investeringen per beleidsdomein per gemeente (reëel, 2014 prijzen)';
            } else {
                subtitleText.textContent = 'Investeringen per beleidsdomein per gemeente (nominaal)';
            }
        } else if (this.showNominal && this.showAdjusted) {
            subtitleText.textContent = 'Investeringsuitgaven per inwoner (€) - beide weergaven getoond';
        } else if (this.showAdjusted) {
            subtitleText.textContent = 'Investeringsuitgaven per inwoner (€, reëel 2014 prijzen)';
        } else {
            subtitleText.textContent = 'Investeringsuitgaven per inwoner (€, nominaal)';
        }
    }

    // Render stacked chart for single region
    renderStackedChart() {
        const datasets = [];
        const years = Array.from({length: 11}, (_, i) => 2014 + i);

        const domainAverages = {};
        for (const [subdomein, yearData] of Object.entries(this.beleidsdomeinData)) {
            const values = Object.values(yearData);
            const avg = values.reduce((sum, val) => sum + val, 0) / values.length;
            domainAverages[subdomein] = avg;
        }
        
        const topDomains = Object.entries(domainAverages)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10)
            .map(([domain]) => domain);
        
        const showBoth = this.showNominal && this.showAdjusted;
        
        topDomains.forEach((subdomein, idx) => {
            const nominalData = years.map(year => {
                return this.beleidsdomeinData[subdomein][year] || 0;
            });
            
            const shortLabel = subdomein.length > 30 ? subdomein.substring(0, 27) + '...' : subdomein;
            const baseColor = colorPalette.domains[idx % colorPalette.domains.length];
            
            if (this.showNominal) {
                datasets.push({
                    label: shortLabel,
                    data: nominalData,
                    backgroundColor: baseColor,
                    borderColor: baseColor,
                    borderWidth: 1,
                    stack: showBoth ? 'nominal' : 'combined',
                    legendLabel: shortLabel,
                    isNominal: true
                });
            }
            
            if (this.showAdjusted) {
                const adjustedData = nominalData.map((val, yearIdx) => 
                    this.adjustForInflation(val, years[yearIdx])
                );
                
                datasets.push({
                    label: shortLabel,
                    data: adjustedData,
                    backgroundColor: baseColor + 'AA',
                    borderColor: baseColor,
                    borderWidth: 1,
                    borderDash: showBoth ? [3, 3] : [],
                    stack: showBoth ? 'adjusted' : 'combined',
                    legendLabel: shortLabel,
                    isAdjusted: true
                });
            }
        });
        
        this.chart.config.type = 'bar';
        this.chart.options.scales.x.stacked = true;
        this.chart.options.scales.y.stacked = true;
        this.chart.options.scales.y.title.text = 'Totaal bedrag (€ x 1000)';
        this.chart.options.plugins.legend.display = true;
        this.chart.options.plugins.legend.labels = {
            generateLabels: (chart) => {
                const datasets = chart.data.datasets;
                const labels = [];
                const seen = new Set();
                
                for (let i = 0; i < datasets.length; i++) {
                    const dataset = datasets[i];
                    const labelText = dataset.legendLabel || dataset.label;
                    
                    if (seen.has(labelText)) continue;
                    seen.add(labelText);
                    
                    labels.push({
                        text: labelText,
                        fillStyle: dataset.backgroundColor,
                        strokeStyle: dataset.borderColor,
                        lineWidth: dataset.borderWidth,
                        hidden: false,
                        index: i,
                        datasetIndex: i
                    });
                }
                
                if (showBoth && labels.length > 0) {
                    labels.push({
                        text: '(volle kleur = nominaal, lichtere tint = reëel)',
                        fillStyle: 'rgba(0,0,0,0)',
                        strokeStyle: 'rgba(0,0,0,0)',
                        fontColor: '#666',
                        lineWidth: 0,
                        index: -1
                    });
                }
                
                return labels;
            }
        };
        this.chart.options.plugins.tooltip.mode = 'index';
        this.chart.options.plugins.tooltip.callbacks = {
            label: (context) => {
                const suffix = context.dataset.isAdjusted ? ' (2014 €)' : context.dataset.isNominal ? ' (nominaal)' : '';
                return context.dataset.label + suffix + ': €' + (context.raw / 1000).toFixed(1) + 'k';
            },
            footer: (items) => {
                const total = items.reduce((sum, item) => sum + item.raw, 0);
                return 'Totaal: €' + (total / 1000).toFixed(1) + 'k';
            }
        };
        
        this.chart.data.datasets = datasets;
        this.chart.update();
    }

    // Render small multiples (one chart per region)
    renderSmallMultiples() {
        this.smallMultipleCharts.forEach(ch => ch.destroy());
        this.smallMultipleCharts = [];
        
        const container = document.getElementById('small-multiples-container');
        container.innerHTML = '';
        
        const years = Array.from({length: 11}, (_, i) => 2014 + i);
        const regions = [];
        
        let provinceIndex = 0;
        let municipalityIndex = 0;
        
        const createRegionData = (name, nominalData, color, index) => {
            const datasets = [];
            const showBoth = this.showNominal && this.showAdjusted;
            
            if (this.showNominal) {
                datasets.push({
                    label: showBoth ? 'Nominaal' : name,
                    data: nominalData,
                    backgroundColor: color,
                    borderColor: color,
                    borderWidth: 2,
                    fill: false
                });
            }
            
            if (this.showAdjusted) {
                const adjustedData = nominalData.map((val, idx) => this.adjustForInflation(val, years[idx]));
                datasets.push({
                    label: showBoth ? '2014 €' : name,
                    data: adjustedData,
                    backgroundColor: color + '99',
                    borderColor: color,
                    borderWidth: 2,
                    borderDash: showBoth ? [5, 5] : [],
                    fill: false
                });
            }
            
            return { name, datasets, color, index };
        };
        
        if (this.selectedRegions.has('vlaanderen')) {
            const nominalData = years.map(y => this.averagesData.Vlaanderen[y]);
            regions.push(createRegionData(
                'Vlaanderen (gemiddelde)',
                nominalData,
                getColorForRegion('vlaanderen', 0, ''),
                0
            ));
        }
        
        this.selectedRegions.forEach(val => {
            if (val.startsWith('prov:')) {
                const provName = val.split(':')[1];
                const nominalData = years.map(y => this.averagesData.Provincies[provName][y]);
                regions.push(createRegionData(
                    provName,
                    nominalData,
                    getColorForRegion('province', provinceIndex++, provName),
                    regions.length
                ));
            }
        });
        
        this.selectedRegions.forEach(val => {
            if (val.startsWith('mun:')) {
                const munName = val.split(':')[1];
                const feature = this.municipalitiesData.features.find(f => f.properties.municipality === munName);
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
        
        regions.forEach((region) => {
            const chartDiv = document.createElement('div');
            chartDiv.className = 'small-multiple-chart';
            
            const title = document.createElement('h4');
            title.textContent = region.name;
            chartDiv.appendChild(title);
            
            const canvas = document.createElement('canvas');
            chartDiv.appendChild(canvas);
            container.appendChild(chartDiv);
            
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
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (context) => '€ ' + context.raw.toFixed(2)
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { font: { size: 10 } }
                        },
                        x: {
                            ticks: { font: { size: 10 } }
                        }
                    }
                }
            });
            
            this.smallMultipleCharts.push(smallChart);
        });
    }

    // Render stacked small multiples for multiple regions
    renderStackedSmallMultiples() {
        this.smallMultipleCharts.forEach(ch => ch.destroy());
        this.smallMultipleCharts = [];
        
        const container = document.getElementById('small-multiples-container');
        container.innerHTML = '';
        
        const years = Array.from({length: 11}, (_, i) => 2014 + i);
        
        const domainAverages = {};
        for (const [subdomein, yearData] of Object.entries(this.beleidsdomeinData)) {
            const values = Object.values(yearData);
            const avg = values.reduce((sum, val) => sum + val, 0) / values.length;
            domainAverages[subdomein] = avg;
        }
        
        const topDomains = Object.entries(domainAverages)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10)
            .map(([domain]) => domain);
        
        const showBoth = this.showNominal && this.showAdjusted;
        
        this.selectedRegions.forEach(val => {
            if (val.startsWith('mun:')) {
                const munName = val.split(':')[1];
                const feature = this.municipalitiesData.features.find(f => f.properties.municipality === munName);
                if (!feature || !feature.properties.beleidsdomein_2024) return;
                
                const datasets = [];
                
                topDomains.forEach((subdomein, idx) => {
                    const baseColor = colorPalette.domains[idx % colorPalette.domains.length];
                    const shortLabel = subdomein.length > 30 ? subdomein.substring(0, 27) + '...' : subdomein;
                    
                    const yearData = this.beleidsdomeinData[subdomein];
                    if (!yearData) return;
                    
                    const nominalData = years.map(year => yearData[String(year)] || 0);
                    
                    if (this.showNominal) {
                        datasets.push({
                            label: shortLabel,
                            data: nominalData,
                            backgroundColor: baseColor,
                            borderColor: baseColor,
                            borderWidth: 1,
                            stack: showBoth ? 'nominal' : 'combined',
                            legendLabel: shortLabel,
                            isNominal: true
                        });
                    }
                    
                    if (this.showAdjusted) {
                        const adjustedData = nominalData.map((val, yearIdx) => 
                            this.adjustForInflation(val, years[yearIdx])
                        );
                        
                        datasets.push({
                            label: shortLabel,
                            data: adjustedData,
                            backgroundColor: baseColor + 'AA',
                            borderColor: baseColor,
                            borderWidth: 1,
                            borderDash: showBoth ? [3, 3] : [],
                            stack: showBoth ? 'adjusted' : 'combined',
                            legendLabel: shortLabel,
                            isAdjusted: true
                        });
                    }
                });
                
                const chartDiv = document.createElement('div');
                chartDiv.className = 'small-multiple-chart';
                
                const title = document.createElement('h4');
                title.textContent = munName;
                chartDiv.appendChild(title);
                
                const canvas = document.createElement('canvas');
                chartDiv.appendChild(canvas);
                container.appendChild(chartDiv);
                
                const ctx = canvas.getContext('2d');
                const smallChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: years,
                        datasets: datasets
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: (context) => {
                                        const label = context.dataset.label || '';
                                        return label + ': €' + context.raw.toFixed(0);
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                stacked: true,
                                ticks: { font: { size: 10 } }
                            },
                            y: {
                                stacked: true,
                                beginAtZero: true,
                                ticks: {
                                    font: { size: 10 },
                                    callback: (value) => {
                                        if (value >= 1000000) return '€' + (value / 1000000).toFixed(1) + 'M';
                                        if (value >= 1000) return '€' + (value / 1000).toFixed(0) + 'K';
                                        return '€' + value;
                                    }
                                }
                            }
                        }
                    }
                });
                
                this.smallMultipleCharts.push(smallChart);
            }
        });
    }
}
