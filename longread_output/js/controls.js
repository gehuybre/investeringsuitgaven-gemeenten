// Controls and UI management module

export class ControlsManager {
    constructor(chartManager) {
        this.chartManager = chartManager;
        this.selectedRegions = new Set(['vlaanderen']);
    }

    // Setup all controls
    setupControls(geoData, avgData) {
        this.setupTabNavigation();
        this.populateVlaanderenTab();
        
        if (avgData.Provincies) {
            this.populateProvinciesTab(avgData.Provincies);
        }
        
        this.populateGemeentenTab(geoData);
        this.setupSearchFunctionality();
        this.setupSelectAllButtons();
    }

    // Setup tab navigation
    setupTabNavigation() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.getAttribute('data-tab');
                
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                button.classList.add('active');
                document.getElementById(`tab-${targetTab}`).classList.add('active');
            });
        });
    }

    // Populate Vlaanderen tab
    populateVlaanderenTab() {
        const container = document.getElementById('checkbox-list-vlaanderen');
        container.innerHTML = '';
        
        const checkboxItem = document.createElement('div');
        checkboxItem.className = 'checkbox-item';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = 'checkbox-vlaanderen';
        checkbox.value = 'vlaanderen';
        checkbox.checked = this.selectedRegions.has('vlaanderen');
        
        const label = document.createElement('label');
        label.setAttribute('for', 'checkbox-vlaanderen');
        label.textContent = 'Vlaanderen (gemiddelde)';
        
        checkboxItem.appendChild(checkbox);
        checkboxItem.appendChild(label);
        container.appendChild(checkboxItem);
        
        checkbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                this.selectedRegions.add('vlaanderen');
            } else {
                this.selectedRegions.delete('vlaanderen');
            }
            this.updateDashboard();
        });
    }

    // Populate Provincies tab
    populateProvinciesTab(provincesData) {
        const container = document.getElementById('checkbox-list-provincies');
        container.innerHTML = '';
        
        const provinces = Object.keys(provincesData).sort();
        
        provinces.forEach(provName => {
            const checkboxItem = document.createElement('div');
            checkboxItem.className = 'checkbox-item';
            checkboxItem.setAttribute('data-name', provName.toLowerCase());
            
            const safeId = `checkbox-prov-${provName.replace(/[^a-zA-Z0-9]/g, '-')}`;
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = safeId;
            checkbox.value = `prov:${provName}`;
            checkbox.checked = this.selectedRegions.has(`prov:${provName}`);
            
            const label = document.createElement('label');
            label.setAttribute('for', safeId);
            label.textContent = provName;
            
            checkboxItem.appendChild(checkbox);
            checkboxItem.appendChild(label);
            container.appendChild(checkboxItem);
            
            checkbox.addEventListener('change', (e) => {
                const value = e.target.value;
                if (e.target.checked) {
                    this.selectedRegions.add(value);
                } else {
                    this.selectedRegions.delete(value);
                }
                this.updateDashboard();
            });
        });
    }

    // Populate Gemeenten tab
    populateGemeentenTab(geoData) {
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
            checkbox.checked = this.selectedRegions.has(`mun:${munName}`);
            
            const label = document.createElement('label');
            label.setAttribute('for', `checkbox-mun-${munName}`);
            label.textContent = munName;
            
            checkboxItem.appendChild(checkbox);
            checkboxItem.appendChild(label);
            container.appendChild(checkboxItem);
            
            checkbox.addEventListener('change', (e) => {
                const value = e.target.value;
                if (e.target.checked) {
                    this.selectedRegions.add(value);
                } else {
                    this.selectedRegions.delete(value);
                }
                this.updateDashboard();
            });
        });
    }

    // Setup search functionality
    setupSearchFunctionality() {
        const searchProvincies = document.getElementById('search-provincies');
        searchProvincies.addEventListener('input', (e) => {
            this.filterCheckboxList('provincies', e.target.value);
        });
        
        const searchGemeenten = document.getElementById('search-gemeenten');
        searchGemeenten.addEventListener('input', (e) => {
            this.filterCheckboxList('gemeenten', e.target.value);
        });
    }

    // Filter checkbox list
    filterCheckboxList(tabName, searchTerm) {
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

    // Setup select all/deselect all buttons
    setupSelectAllButtons() {
        const selectAllButtons = document.querySelectorAll('.btn-select-all');
        const deselectAllButtons = document.querySelectorAll('.btn-deselect-all');
        
        selectAllButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.getAttribute('data-tab');
                this.selectAllInTab(tabName);
            });
        });
        
        deselectAllButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.getAttribute('data-tab');
                this.deselectAllInTab(tabName);
            });
        });
    }

    // Select all in tab
    selectAllInTab(tabName) {
        const container = document.getElementById(`checkbox-list-${tabName}`);
        const checkboxes = Array.from(container.querySelectorAll('input[type="checkbox"]:not(:checked)'))
            .filter(checkbox => !checkbox.closest('.checkbox-item').classList.contains('hidden'));
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
            this.selectedRegions.add(checkbox.value);
        });
        
        this.updateDashboard();
    }

    // Deselect all in tab
    deselectAllInTab(tabName) {
        const container = document.getElementById(`checkbox-list-${tabName}`);
        const checkboxes = Array.from(container.querySelectorAll('input[type="checkbox"]:checked'))
            .filter(checkbox => !checkbox.closest('.checkbox-item').classList.contains('hidden'));
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
            this.selectedRegions.delete(checkbox.value);
        });
        
        this.updateDashboard();
    }

    // Setup inflation toggle
    setupInflationToggle() {
        const nominalCheckbox = document.getElementById('toggle-nominal');
        const adjustedCheckbox = document.getElementById('toggle-adjusted');
        
        nominalCheckbox.addEventListener('change', () => {
            let showNominal = nominalCheckbox.checked;
            let showAdjusted = adjustedCheckbox.checked;
            
            if (!showNominal && !showAdjusted) {
                showAdjusted = true;
                adjustedCheckbox.checked = true;
            }
            
            this.chartManager.setDisplayOptions(showNominal, showAdjusted, this.chartManager.showStacked);
            this.updateDashboard();
        });
        
        adjustedCheckbox.addEventListener('change', () => {
            let showNominal = nominalCheckbox.checked;
            let showAdjusted = adjustedCheckbox.checked;
            
            if (!showNominal && !showAdjusted) {
                showNominal = true;
                nominalCheckbox.checked = true;
            }
            
            this.chartManager.setDisplayOptions(showNominal, showAdjusted, this.chartManager.showStacked);
            this.updateDashboard();
        });
    }

    // Setup stacked toggle
    setupStackedToggle() {
        const stackedCheckbox = document.getElementById('toggle-stacked');
        
        stackedCheckbox.addEventListener('change', () => {
            const showStacked = stackedCheckbox.checked;
            this.chartManager.setDisplayOptions(
                this.chartManager.showNominal,
                this.chartManager.showAdjusted,
                showStacked
            );
            this.updateDashboard();
        });
    }

    // Update dashboard
    updateDashboard() {
        this.chartManager.setSelectedRegions(this.selectedRegions);
        this.chartManager.updateDashboard();
    }

    // Toggle municipality selection (called from map clicks)
    toggleMunicipalitySelection(munName) {
        const value = `mun:${munName}`;
        const safeId = `checkbox-mun-${munName.replace(/[^a-zA-Z0-9]/g, '-')}`;
        const checkbox = document.getElementById(safeId);
        
        if (checkbox) {
            if (this.selectedRegions.has(value)) {
                this.selectedRegions.delete(value);
                checkbox.checked = false;
            } else {
                this.selectedRegions.add(value);
                checkbox.checked = true;
            }
            
            this.updateDashboard();
            
            // Switch to gemeenten tab
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

    getSelectedRegions() {
        return this.selectedRegions;
    }
}
