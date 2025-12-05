// Provincial visualization module

export class ProvincialManager {
    constructor() {
        this.provincialChart = null;
        this.provincialData = null;
        this.provincialDetailedData = null;
        this.provincialRekeningenData = null;
        this.cpiData = null;
        this.showNominal = true;
        this.showAdjusted = false;
        this.showStacked = false;
        this.smallMultipleCharts = [];
        this.colorPalette = {
            provinces: ['#029453', '#0066cc', '#ff9900', '#cc0066', '#9933cc'],
            domains: [
                '#029453', '#0066cc', '#ff9900', '#cc0066', '#9933cc',
                '#00cc99', '#ff6600', '#3399ff', '#cc3399', '#99cc00',
                '#ff3366', '#6699cc', '#cc9900', '#9966cc', '#66cc66'
            ]
        };
    }

    // Initialize provincial visualization
    async init() {
        try {
            const [totalsResponse, detailedResponse, rekeningenResponse, cpiResponse] = await Promise.all([
                fetch('provincie_totals.json'),
                fetch('provincie_detailed.json'),
                fetch('provincie_rekeningen_detailed.json'),
                fetch('cpi.json')
            ]);
            
            this.provincialData = await totalsResponse.json();
            this.provincialDetailedData = await detailedResponse.json();
            this.provincialRekeningenData = await rekeningenResponse.json();
            this.cpiData = await cpiResponse.json();
            
            // Process CPI data
            this.processCPIData();
            
            this.initChart();
            this.renderTable();
            this.setupControls();
            
            console.log('✓ Provincial visualization initialized');
        } catch (error) {
            console.error('Error initializing provincial visualization:', error);
        }
    }

    // Process CPI data into usable format
    processCPIData() {
        this.cpiIndex = {};
        if (this.cpiData && this.cpiData.facts) {
            this.cpiData.facts.forEach(fact => {
                const year = parseInt(fact.Jaar);
                if (!this.cpiIndex[year]) {
                    this.cpiIndex[year] = fact.Consumptieprijsindex;
                }
            });
        }
        // Use 2014 as base year
        this.baseYearCPI = this.cpiIndex[2014] || 100;
    }

    // Calculate period-averaged CPI for adjustment
    getPeriodCPI(periodLabel) {
        const [startYear, endYear] = periodLabel.split('-').map(y => parseInt(y));
        let sum = 0;
        let count = 0;
        for (let year = startYear; year <= endYear; year++) {
            if (this.cpiIndex[year]) {
                sum += this.cpiIndex[year];
                count++;
            }
        }
        return count > 0 ? sum / count : this.baseYearCPI;
    }

    // Adjust value for inflation to 2014 prices
    adjustForInflation(value, periodLabel) {
        if (!value || value === 0) return 0;
        const periodCPI = this.getPeriodCPI(periodLabel);
        return value * (this.baseYearCPI / periodCPI);
    }

    // Initialize provincial chart
    initChart() {
        const ctx = document.getElementById('province-chart');
        if (!ctx) return;
        
        this.provincialChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
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
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Investeringen (€ per inwoner)' },
                        ticks: {
                            callback: (value) => '€' + value.toFixed(0)
                        }
                    },
                    x: {
                        title: { display: true, text: 'Meerjarenplan' }
                    }
                }
            }
        });
        
        this.updateChart();
    }

    // Update chart based on current selections
    updateChart() {
        if (!this.provincialChart) return;
        
        const periods = ['2014-2019', '2020-2025', '2026-2031'];
        const provinces = Object.keys(this.provincialData).sort();
        
        // Update label and subtitle
        this.updateChartLabel();
        this.updateSubtitle();
        
        // Always show small multiples (one chart per province)
        document.getElementById('province-chart-wrapper').style.display = 'none';
        document.getElementById('province-legend-container').style.display = 'block';
        document.getElementById('province-small-multiples-container').style.display = 'grid';
        
        if (this.showStacked) {
            this.renderCommonLegendStacked();
            this.renderStackedSmallMultiples(provinces, periods);
        } else {
            this.renderCommonLegend();
            this.renderComparisonSmallMultiples(provinces, periods);
        }
    }

    // Update chart label
    updateChartLabel() {
        const label = document.getElementById('province-selected-label');
        if (!label) return;
        label.textContent = 'Alle provincies';
    }

    // Update subtitle based on current settings
    updateSubtitle() {
        const subtitleText = document.getElementById('province-subtitle-text');
        if (!subtitleText) return;
        
        if (this.showStacked) {
            if (this.showNominal && this.showAdjusted) {
                subtitleText.textContent = 'Geplande investeringen per beleidsdomein per provincie (nominaal & reëel 2014)';
            } else if (this.showAdjusted) {
                subtitleText.textContent = 'Geplande investeringen per beleidsdomein per provincie (reëel, 2014 prijzen)';
            } else {
                subtitleText.textContent = 'Geplande investeringen per beleidsdomein per provincie (nominaal)';
            }
        } else if (this.showNominal && this.showAdjusted) {
            subtitleText.textContent = 'Geplande investeringsuitgaven per inwoner per provincie (€) - beide weergaven';
        } else if (this.showAdjusted) {
            subtitleText.textContent = 'Geplande investeringsuitgaven per inwoner per provincie (€, reëel 2014 prijzen)';
        } else {
            subtitleText.textContent = 'Geplande investeringsuitgaven per inwoner per provincie (€, nominaal)';
        }
    }

    // Render common legend for comparison view
    renderCommonLegend() {
        const container = document.getElementById('province-legend-container');
        if (!container) return;

        const showBoth = this.showNominal && this.showAdjusted;
        let html = '<div class="common-legend">';

        if (!showBoth) {
            // If only one type is shown, show province colors
            const provinces = Object.keys(this.provincialData).sort();
            provinces.forEach((province, index) => {
                const color = this.colorPalette.provinces[index % this.colorPalette.provinces.length];
                html += `
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: ${color};"></div>
                        <span class="legend-label">${province}</span>
                    </div>
                `;
            });
        } else {
            // Show both nominal and real
            html += `
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #029453;"></div>
                    <span class="legend-label">Nominaal</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #029453AA;"></div>
                    <span class="legend-label">Reëel (2014 prijzen)</span>
                </div>
            `;
        }

        html += '</div>';
        container.innerHTML = html;
    }

    // Render common legend for stacked view
    renderCommonLegendStacked() {
        const container = document.getElementById('province-legend-container');
        if (!container) return;

        const showBoth = this.showNominal && this.showAdjusted;
        let html = '<div class="common-legend">';

        if (showBoth) {
            html += `
                <div class="legend-item">
                    <span class="legend-label" style="font-weight: 600;">Legenda:</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #029453;"></div>
                    <span class="legend-label">Volle kleur = Nominaal</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #029453AA;"></div>
                    <span class="legend-label">Lichtere tint = Reëel (2014)</span>
                </div>
            `;
        } else {
            html += `
                <div class="legend-item">
                    <span class="legend-label">Top ${showBoth ? '8' : '8'} beleidsdomeinen per provincie</span>
                </div>
            `;
        }

        html += '</div>';
        container.innerHTML = html;
    }

    // Render comparison small multiples (one chart per province)
    renderComparisonSmallMultiples(provinces, periods) {
        const container = document.getElementById('province-small-multiples-container');
        if (!container) return;

        // Destroy existing charts
        this.smallMultipleCharts.forEach(chart => chart.destroy());
        this.smallMultipleCharts = [];

        // Clear container
        container.innerHTML = '';

        const showBoth = this.showNominal && this.showAdjusted;

        // Create a chart for each province
        provinces.forEach((province, index) => {
            const wrapper = document.createElement('div');
            wrapper.className = 'small-multiple-chart';

            const title = document.createElement('h4');
            title.textContent = province;
            wrapper.appendChild(title);

            const canvas = document.createElement('canvas');
            canvas.id = `province-comp-small-${index}`;
            wrapper.appendChild(canvas);

            container.appendChild(wrapper);

            const color = this.colorPalette.provinces[index % this.colorPalette.provinces.length];
            const datasets = [];

            if (this.showNominal) {
                datasets.push({
                    label: showBoth ? 'Nominaal' : province,
                    data: periods.map(period => this.provincialData[province][period] || 0),
                    backgroundColor: color,
                    borderColor: color,
                    borderWidth: 1,
                    isNominal: true
                });
            }

            if (this.showAdjusted) {
                datasets.push({
                    label: showBoth ? 'Reëel (2014)' : province,
                    data: periods.map(period => {
                        const value = this.provincialData[province][period] || 0;
                        return this.adjustForInflation(value, period);
                    }),
                    backgroundColor: color + 'AA',
                    borderColor: color,
                    borderWidth: 1,
                    isAdjusted: true
                });
            }

            const ctx = canvas.getContext('2d');
            const chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: periods,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    const suffix = context.dataset.isAdjusted ? ' (2014 €)' : context.dataset.isNominal ? ' (nominaal)' : '';
                                    return context.dataset.label + suffix + ': €' + context.raw.toFixed(2);
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { font: { size: 9 } }
                        },
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: (value) => '€' + value.toFixed(0),
                                font: { size: 9 }
                            },
                            title: {
                                display: true,
                                text: '€ per inw.',
                                font: { size: 10 }
                            }
                        }
                    }
                }
            });

            this.smallMultipleCharts.push(chart);
        });
    }



    // Render stacked small multiples
    renderStackedSmallMultiples(provinces, periods) {
        const container = document.getElementById('province-small-multiples-container');
        if (!container) return;

        // Destroy existing charts
        this.smallMultipleCharts.forEach(chart => chart.destroy());
        this.smallMultipleCharts = [];

        // Clear container
        container.innerHTML = '';

        // Create a small multiple for each province
        provinces.forEach((province, provIndex) => {
            if (!this.provincialDetailedData[province]) return;

            const wrapper = document.createElement('div');
            wrapper.className = 'small-multiple-chart';

            const title = document.createElement('h4');
            title.textContent = province;
            wrapper.appendChild(title);

            const canvas = document.createElement('canvas');
            canvas.id = `province-stacked-small-${provIndex}`;
            wrapper.appendChild(canvas);

            container.appendChild(wrapper);

            // Collect domain data
            const domainAverages = {};
            periods.forEach(period => {
                const periodData = this.provincialDetailedData[province][period];
                if (periodData && periodData.per_beleidsdomein) {
                    Object.entries(periodData.per_beleidsdomein).forEach(([domain, value]) => {
                        if (!domainAverages[domain]) {
                            domainAverages[domain] = { sum: 0, count: 0 };
                        }
                        domainAverages[domain].sum += value;
                        domainAverages[domain].count++;
                    });
                }
            });

            // Get top 8 domains for small multiples
            const topDomains = Object.entries(domainAverages)
                .map(([domain, data]) => ({ domain, avg: data.sum / data.count }))
                .sort((a, b) => b.avg - a.avg)
                .slice(0, 8)
                .map(item => item.domain);

            const datasets = [];
            const showBoth = this.showNominal && this.showAdjusted;

            topDomains.forEach((domain, idx) => {
                const color = this.colorPalette.domains[idx % this.colorPalette.domains.length];
                const shortLabel = domain.length > 20 ? domain.substring(0, 17) + '...' : domain;

                if (this.showNominal) {
                    const nominalData = periods.map(period => {
                        const periodData = this.provincialDetailedData[province][period];
                        return periodData?.per_beleidsdomein?.[domain] || 0;
                    });

                    datasets.push({
                        label: shortLabel,
                        data: nominalData,
                        backgroundColor: color,
                        borderWidth: 1,
                        stack: showBoth ? 'nominal' : 'combined'
                    });
                }

                if (this.showAdjusted) {
                    const adjustedData = periods.map(period => {
                        const periodData = this.provincialDetailedData[province][period];
                        const value = periodData?.per_beleidsdomein?.[domain] || 0;
                        return this.adjustForInflation(value, period);
                    });

                    datasets.push({
                        label: shortLabel,
                        data: adjustedData,
                        backgroundColor: color + 'AA',
                        borderWidth: 1,
                        stack: showBoth ? 'adjusted' : 'combined'
                    });
                }
            });

            const ctx = canvas.getContext('2d');
            const chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: periods,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    return context.dataset.label + ': €' + context.raw.toFixed(2);
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            stacked: true,
                            ticks: { font: { size: 9 } }
                        },
                        y: {
                            stacked: true,
                            beginAtZero: true,
                            ticks: {
                                callback: (value) => '€' + value.toFixed(0),
                                font: { size: 9 }
                            },
                            title: {
                                display: true,
                                text: '€ per inw.',
                                font: { size: 10 }
                            }
                        }
                    }
                }
            });

            this.smallMultipleCharts.push(chart);
        });
    }

    // Render provincial table
    renderTable() {
        const tbody = document.getElementById('province-table-body');
        if (!tbody || !this.provincialData) return;
        
        const provinces = Object.keys(this.provincialData);
        const rows = [];
        
        let sum2014 = 0, sum2020 = 0, sum2026 = 0;
        let count2014 = 0, count2020 = 0, count2026 = 0;
        let sumEvol1 = 0, sumEvol2 = 0;
        let countEvol1 = 0, countEvol2 = 0;
        
        provinces.forEach(province => {
            const data = this.provincialData[province];
            const val2014 = data['2014-2019'];
            const val2020 = data['2020-2025'];
            const val2026 = data['2026-2031'];
            
            // Calculate evolution between 2014-2019 and 2020-2025
            let evolution1 = '-';
            if (val2014 > 0 && val2020 > 0) {
                const change = ((val2020 - val2014) / val2014) * 100;
                const sign = change >= 0 ? '+' : '';
                evolution1 = sign + change.toFixed(1) + '%';
                sumEvol1 += change;
                countEvol1++;
            }
            
            // Calculate evolution between 2020-2025 and 2026-2031
            let evolution2 = '-';
            if (val2020 > 0 && val2026 > 0) {
                const change = ((val2026 - val2020) / val2020) * 100;
                const sign = change >= 0 ? '+' : '';
                evolution2 = sign + change.toFixed(1) + '%';
                sumEvol2 += change;
                countEvol2++;
            }
            
            if (val2014 > 0) { sum2014 += val2014; count2014++; }
            if (val2020 > 0) { sum2020 += val2020; count2020++; }
            if (val2026 > 0) { sum2026 += val2026; count2026++; }
            
            const row = `
                <tr>
                    <td><strong>${province}</strong></td>
                    <td class="text-right">${val2014 > 0 ? '€' + val2014.toFixed(2) : '-'}</td>
                    <td class="text-right evolution-col">${evolution1}</td>
                    <td class="text-right">${val2020 > 0 ? '€' + val2020.toFixed(2) : '-'}</td>
                    <td class="text-right evolution-col">${evolution2}</td>
                    <td class="text-right">${val2026 > 0 ? '€' + val2026.toFixed(2) : '-'}</td>
                </tr>
            `;
            rows.push(row);
        });
        
        tbody.innerHTML = rows.join('');
        
        // Update averages
        const avg2014 = count2014 > 0 ? (sum2014 / count2014).toFixed(2) : '-';
        const avg2020 = count2020 > 0 ? (sum2020 / count2020).toFixed(2) : '-';
        const avg2026 = count2026 > 0 ? (sum2026 / count2026).toFixed(2) : '-';
        const avgEvol1 = countEvol1 > 0 ? (sumEvol1 / countEvol1).toFixed(1) : '-';
        const avgEvol2 = countEvol2 > 0 ? (sumEvol2 / countEvol2).toFixed(1) : '-';
        
        document.getElementById('avg-2014-2019').textContent = avg2014 !== '-' ? '€' + avg2014 : avg2014;
        document.getElementById('avg-evolution-1').textContent = avgEvol1 !== '-' ? (avgEvol1 >= 0 ? '+' : '') + avgEvol1 + '%' : avgEvol1;
        document.getElementById('avg-2020-2025').textContent = avg2020 !== '-' ? '€' + avg2020 : avg2020;
        document.getElementById('avg-evolution-2').textContent = avgEvol2 !== '-' ? (avgEvol2 >= 0 ? '+' : '') + avgEvol2 + '%' : avgEvol2;
        document.getElementById('avg-2026-2031').textContent = avg2026 !== '-' ? '€' + avg2026 : avg2026;
    }

    // Setup controls
    setupControls() {
        // Price toggle controls
        const nominalToggle = document.getElementById('province-toggle-nominal');
        const adjustedToggle = document.getElementById('province-toggle-adjusted');
        const stackedToggle = document.getElementById('province-toggle-stacked');
        
        if (nominalToggle) {
            nominalToggle.addEventListener('change', () => {
                this.showNominal = nominalToggle.checked;
                // Ensure at least one is selected
                if (!this.showNominal && !this.showAdjusted) {
                    adjustedToggle.checked = true;
                    this.showAdjusted = true;
                }
                this.updateChart();
            });
        }
        
        if (adjustedToggle) {
            adjustedToggle.addEventListener('change', () => {
                this.showAdjusted = adjustedToggle.checked;
                // Ensure at least one is selected
                if (!this.showNominal && !this.showAdjusted) {
                    nominalToggle.checked = true;
                    this.showNominal = true;
                }
                this.updateChart();
            });
        }

        if (stackedToggle) {
            stackedToggle.addEventListener('change', () => {
                this.showStacked = stackedToggle.checked;
                this.updateChart();
            });
        }
        
        this.setupTableToggles();
        this.setupProvinceSelectors();
    }

    // Setup table toggles
    setupTableToggles() {
        const toggleTotaal = document.getElementById('province-toggle-totaal');
        const toggleBeleidsveld = document.getElementById('province-toggle-beleidsveld');
        const toggleRekening = document.getElementById('province-toggle-rekening');
        
        const viewTotaal = document.getElementById('province-table-totaal');
        const viewBeleidsveld = document.getElementById('province-table-beleidsveld');
        const viewRekening = document.getElementById('province-table-rekening');
        
        if (!toggleTotaal || !toggleBeleidsveld || !toggleRekening) return;
        
        toggleTotaal.addEventListener('click', () => {
            this.showView('totaal', toggleTotaal, toggleBeleidsveld, toggleRekening, viewTotaal, viewBeleidsveld, viewRekening);
        });
        
        toggleBeleidsveld.addEventListener('click', () => {
            this.showView('beleidsveld', toggleTotaal, toggleBeleidsveld, toggleRekening, viewTotaal, viewBeleidsveld, viewRekening);
        });
        
        toggleRekening.addEventListener('click', () => {
            this.showView('rekening', toggleTotaal, toggleBeleidsveld, toggleRekening, viewTotaal, viewBeleidsveld, viewRekening);
        });
    }

    // Show specific view
    showView(viewType, toggleTotaal, toggleBeleidsveld, toggleRekening, viewTotaal, viewBeleidsveld, viewRekening) {
        toggleTotaal.classList.remove('active');
        toggleBeleidsveld.classList.remove('active');
        toggleRekening.classList.remove('active');
        
        viewTotaal.style.display = 'none';
        viewBeleidsveld.style.display = 'none';
        viewRekening.style.display = 'none';
        
        if (viewType === 'totaal') {
            toggleTotaal.classList.add('active');
            viewTotaal.style.display = 'block';
        } else if (viewType === 'beleidsveld') {
            toggleBeleidsveld.classList.add('active');
            viewBeleidsveld.style.display = 'block';
        } else if (viewType === 'rekening') {
            toggleRekening.classList.add('active');
            viewRekening.style.display = 'block';
        }
    }

    // Setup province selectors
    setupProvinceSelectors() {
        const beleidsveldButtons = document.getElementById('province-beleidsveld-buttons');
        const rekeningButtons = document.getElementById('province-rekening-buttons');
        
        if (!beleidsveldButtons || !rekeningButtons) return;
        
        const provinces = Object.keys(this.provincialDetailedData).sort();
        
        // Create buttons for beleidsveld view
        provinces.forEach((prov, index) => {
            const btn = document.createElement('button');
            btn.className = 'detail-toggle-btn' + (index === 0 ? ' active' : '');
            btn.textContent = prov;
            btn.dataset.province = prov;
            btn.addEventListener('click', (e) => {
                // Remove active class from all buttons
                beleidsveldButtons.querySelectorAll('.detail-toggle-btn').forEach(b => b.classList.remove('active'));
                // Add active class to clicked button
                e.target.classList.add('active');
                this.renderBeleidsveldView(prov);
            });
            beleidsveldButtons.appendChild(btn);
        });
        
        // Create buttons for rekening view
        provinces.forEach((prov, index) => {
            const btn = document.createElement('button');
            btn.className = 'detail-toggle-btn' + (index === 0 ? ' active' : '');
            btn.textContent = prov;
            btn.dataset.province = prov;
            btn.addEventListener('click', (e) => {
                // Remove active class from all buttons
                rekeningButtons.querySelectorAll('.detail-toggle-btn').forEach(b => b.classList.remove('active'));
                // Add active class to clicked button
                e.target.classList.add('active');
                this.renderRekeningView(prov);
            });
            rekeningButtons.appendChild(btn);
        });
        
        // Show first province by default
        if (provinces.length > 0) {
            this.renderBeleidsveldView(provinces[0]);
            this.renderRekeningView(provinces[0]);
        }
    }

    // Render beleidsveld view
    renderBeleidsveldView(selectedProvince) {
        const container = document.getElementById('province-beleidsveld-container');
        if (!container || !this.provincialDetailedData) return;
        
        if (!selectedProvince) {
            container.innerHTML = '<p class="text-muted">Selecteer een provincie om de details te bekijken.</p>';
            return;
        }
        
        const provinceData = this.provincialDetailedData[selectedProvince];
        if (!provinceData) {
            container.innerHTML = '<p class="text-muted">Geen data beschikbaar voor deze provincie.</p>';
            return;
        }
        
        // Build table HTML
        let html = '<div class="table-responsive"><table class="rekeningen-table"><thead><tr>';
        html += '<th>Beleidsdomein</th>';
        html += '<th class="text-right">2014-2019</th>';
        html += '<th class="text-right">2020-2025</th>';
        html += '<th class="text-right">2026-2031</th>';
        html += '</tr></thead><tbody>';
        
        // Collect all unique beleidsdomein names with their max value across all periods
        const beleidsveldData = {};
        Object.entries(provinceData).forEach(([period, data]) => {
            if (data.per_beleidsdomein) {
                Object.entries(data.per_beleidsdomein).forEach(([bd, value]) => {
                    if (!beleidsveldData[bd]) {
                        beleidsveldData[bd] = { maxValue: 0, values: {} };
                    }
                    beleidsveldData[bd].values[period] = value;
                    beleidsveldData[bd].maxValue = Math.max(beleidsveldData[bd].maxValue, value || 0);
                });
            }
        });
        
        // Sort by max value descending
        const sortedBeleidsvelden = Object.entries(beleidsveldData)
            .sort((a, b) => b[1].maxValue - a[1].maxValue);
        
        // Take top 15 and aggregate the rest
        const top15 = sortedBeleidsvelden.slice(0, 15);
        const rest = sortedBeleidsvelden.slice(15);
        
        // Create rows for top 15
        top15.forEach(([beleidsveld, data]) => {
            html += '<tr>';
            html += `<td>${beleidsveld}</td>`;
            
            ['2014-2019', '2020-2025', '2026-2031'].forEach(period => {
                const value = data.values[period];
                html += `<td class="text-right">${value ? '€' + value.toFixed(2) : '-'}</td>`;
            });
            
            html += '</tr>';
        });
        
        // Add "Overige" row if there are more than 15 items
        if (rest.length > 0) {
            html += '<tr class="text-muted">';
            html += `<td><em>Overige (${rest.length} items)</em></td>`;
            
            ['2014-2019', '2020-2025', '2026-2031'].forEach(period => {
                const sum = rest.reduce((acc, [_, data]) => acc + (data.values[period] || 0), 0);
                html += `<td class="text-right"><em>${sum > 0 ? '€' + sum.toFixed(2) : '-'}</em></td>`;
            });
            
            html += '</tr>';
        }
        
        // Add totals row
        html += '<tr class="font-semibold"><td><strong>Totaal</strong></td>';
        ['2014-2019', '2020-2025', '2026-2031'].forEach(period => {
            const total = provinceData[period]?.totaal;
            html += `<td class="text-right"><strong>${total ? '€' + total.toFixed(2) : '-'}</strong></td>`;
        });
        html += '</tr>';
        
        html += '</tbody></table></div>';
        html += '<p class="mt-sm text-muted"><small>Bedragen in euro per inwoner voor de hele periode van het meerjarenplan. Getoond worden de top 15 posten, gesorteerd op hoogste waarde.</small></p>';
        
        container.innerHTML = html;
    }

    // Render rekening view
    renderRekeningView(selectedProvince) {
        const container = document.getElementById('province-rekening-container');
        if (!container || !this.provincialRekeningenData) return;
        
        if (!selectedProvince) {
            container.innerHTML = '<p class="text-muted">Selecteer een provincie om de details te bekijken.</p>';
            return;
        }
        
        const provinceData = this.provincialRekeningenData[selectedProvince];
        if (!provinceData) {
            container.innerHTML = '<p class="text-muted">Geen data beschikbaar voor deze provincie.</p>';
            return;
        }
        
        // Build table HTML
        let html = '<div class="table-responsive"><table class="rekeningen-table"><thead><tr>';
        html += '<th>Rekening</th>';
        html += '<th class="text-right">2014-2019</th>';
        html += '<th class="text-right">2020-2025</th>';
        html += '<th class="text-right">2026-2031</th>';
        html += '</tr></thead><tbody>';
        
        // Collect all unique rekeningen with their max value across all periods
        const rekeningData = {};
        Object.entries(provinceData).forEach(([period, data]) => {
            if (data.per_rekening) {
                Object.entries(data.per_rekening).forEach(([rek, value]) => {
                    if (!rekeningData[rek]) {
                        rekeningData[rek] = { maxValue: 0, values: {} };
                    }
                    rekeningData[rek].values[period] = value;
                    rekeningData[rek].maxValue = Math.max(rekeningData[rek].maxValue, value || 0);
                });
            }
        });
        
        // Sort by max value descending
        const sortedRekeningen = Object.entries(rekeningData)
            .sort((a, b) => b[1].maxValue - a[1].maxValue);
        
        // Take top 15 and aggregate the rest
        const top15 = sortedRekeningen.slice(0, 15);
        const rest = sortedRekeningen.slice(15);
        
        // Create rows for top 15
        top15.forEach(([rekening, data]) => {
            html += '<tr>';
            html += `<td>${rekening}</td>`;
            
            ['2014-2019', '2020-2025', '2026-2031'].forEach(period => {
                const value = data.values[period];
                html += `<td class="text-right">${value ? '€' + value.toFixed(2) : '-'}</td>`;
            });
            
            html += '</tr>';
        });
        
        // Add "Overige" row if there are more than 15 items
        if (rest.length > 0) {
            html += '<tr class="text-muted">';
            html += `<td><em>Overige (${rest.length} items)</em></td>`;
            
            ['2014-2019', '2020-2025', '2026-2031'].forEach(period => {
                const sum = rest.reduce((acc, [_, data]) => acc + (data.values[period] || 0), 0);
                html += `<td class="text-right"><em>${sum > 0 ? '€' + sum.toFixed(2) : '-'}</em></td>`;
            });
            
            html += '</tr>';
        }
        
        // Add totals row
        html += '<tr class="font-semibold"><td><strong>Totaal</strong></td>';
        ['2014-2019', '2020-2025', '2026-2031'].forEach(period => {
            const total = provinceData[period]?.totaal;
            html += `<td class="text-right"><strong>${total ? '€' + total.toFixed(2) : '-'}</strong></td>`;
        });
        html += '</tr>';
        
        html += '</tbody></table></div>';
        html += '<p class="mt-sm text-muted"><small>Bedragen in euro per inwoner voor de hele periode van het meerjarenplan. Getoond worden de top 15 posten, gesorteerd op hoogste waarde.</small></p>';
        
        container.innerHTML = html;
    }
}
