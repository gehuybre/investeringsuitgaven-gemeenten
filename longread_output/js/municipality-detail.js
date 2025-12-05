// Municipality detail panel management

export class MunicipalityDetailManager {
    constructor() {
        this.currentDetailView = 'beleidsveld';
        this.currentMunicipalityProperties = null;
        this.setupEventListeners();
    }

    // Setup event listeners
    setupEventListeners() {
        const closeBtn = document.getElementById('detail-close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hide());
        }
        
        const toggleUitgavenpost = document.getElementById('toggle-uitgavenpost');
        const toggleBeleidsveld = document.getElementById('toggle-beleidsveld');
        
        if (toggleUitgavenpost) {
            toggleUitgavenpost.addEventListener('click', () => {
                this.currentDetailView = 'uitgavenpost';
                toggleUitgavenpost.classList.add('active');
                toggleBeleidsveld.classList.remove('active');
                
                if (this.currentMunicipalityProperties) {
                    this.renderDetailTable(this.currentMunicipalityProperties, this.currentDetailView);
                }
            });
        }
        
        if (toggleBeleidsveld) {
            toggleBeleidsveld.addEventListener('click', () => {
                this.currentDetailView = 'beleidsveld';
                toggleBeleidsveld.classList.add('active');
                toggleUitgavenpost.classList.remove('active');
                
                if (this.currentMunicipalityProperties) {
                    this.renderDetailTable(this.currentMunicipalityProperties, this.currentDetailView);
                }
            });
        }
    }

    // Show municipality detail panel
    show(properties) {
        this.currentMunicipalityProperties = properties;
        
        const detailPanel = document.getElementById('municipality-detail');
        const detailName = document.getElementById('detail-municipality-name');
        const detailProvince = document.getElementById('detail-municipality-province');
        const detailTotal2024 = document.getElementById('detail-total-2024');
        const detailSumBeleidsdomein = document.getElementById('detail-sum-beleidsdomein');
        const detailDifferenceBeleidsdomein = document.getElementById('detail-difference-beleidsdomein');
        const detailSumRekeningen = document.getElementById('detail-sum-rekeningen');
        const detailDifferenceRekeningen = document.getElementById('detail-difference-rekeningen');
        
        // Fill basic info
        detailName.textContent = properties.municipality;
        
        // Add warning badge for Kaprijke
        if (properties.municipality === 'Kaprijke') {
            detailName.innerHTML = properties.municipality + ' <span style="background: #999; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.7em; margin-left: 8px;">⚠ Data onbetrouwbaar</span>';
        }
        
        detailProvince.textContent = properties.province || 'Provincie onbekend';
        
        const total2024 = properties['2024'];
        detailTotal2024.textContent = total2024 ? `€ ${total2024.toFixed(2)}` : '€ -';
        
        // Fill beleidsdomein sum
        if (properties.beleidsdomein_2024 && properties.beleidsdomein_2024.totaal_beleidsdomein !== null) {
            const totaalBeleidsdomein = properties.beleidsdomein_2024.totaal_beleidsdomein;
            detailSumBeleidsdomein.textContent = `€ ${totaalBeleidsdomein.toFixed(2)}`;
            const diffBeleidsdomein = properties.beleidsdomein_2024.verschil_met_totaal;
            detailDifferenceBeleidsdomein.textContent = `verschil: € ${diffBeleidsdomein.toFixed(2)}`;
        } else {
            detailSumBeleidsdomein.textContent = '€ -';
            detailDifferenceBeleidsdomein.textContent = 'geen data';
        }
        
        // Fill rekeningen sum
        if (properties.detail_2024 && properties.detail_2024.totaal_details !== null) {
            const totaalRekeningen = properties.detail_2024.totaal_details;
            detailSumRekeningen.textContent = `€ ${totaalRekeningen.toFixed(2)}`;
            const diffRekeningen = properties.detail_2024.verschil_met_totaal;
            detailDifferenceRekeningen.textContent = `verschil: € ${diffRekeningen.toFixed(2)}`;
        } else {
            detailSumRekeningen.textContent = '€ -';
            detailDifferenceRekeningen.textContent = 'geen data';
        }
        
        // Render the table
        this.renderDetailTable(properties, this.currentDetailView);
        
        // Show panel and scroll to it
        detailPanel.classList.add('active');
        detailPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // Hide detail panel
    hide() {
        const detailPanel = document.getElementById('municipality-detail');
        detailPanel.classList.remove('active');
    }

    // Render detail table
    renderDetailTable(properties, viewType) {
        const detailWarning = document.getElementById('detail-warning');
        const detailTableBody = document.getElementById('detail-rekeningen-tbody');
        const detailTableTitle = document.getElementById('detail-table-title');
        const detailTableHeaderCol = document.getElementById('detail-table-header-col');
        
        const total2024 = properties['2024'];
        
        if (viewType === 'uitgavenpost') {
            this.renderUitgavenpostView(properties, total2024, detailTableTitle, detailTableHeaderCol, detailTableBody, detailWarning);
        } else if (viewType === 'beleidsveld') {
            this.renderBeleidsveldView(properties, total2024, detailTableTitle, detailTableHeaderCol, detailTableBody, detailWarning);
        }
    }

    // Render uitgavenpost view
    renderUitgavenpostView(properties, total2024, detailTableTitle, detailTableHeaderCol, detailTableBody, detailWarning) {
        detailTableTitle.textContent = 'Top 10 per uitgavenpost';
        detailTableHeaderCol.textContent = 'Rekening';
        
        if (properties.detail_2024 && properties.detail_2024.totaal_details !== null) {
            const detail2024 = properties.detail_2024;
            
            const diffRekeningen = detail2024.verschil_met_totaal;
            const diffRekeningenPercent = Math.abs(diffRekeningen / total2024 * 100);
            
            let showWarning = diffRekeningenPercent > 1;
            
            if (properties.beleidsdomein_2024 && properties.beleidsdomein_2024.totaal_beleidsdomein !== null) {
                const diffBeleidsdomein = properties.beleidsdomein_2024.verschil_met_totaal;
                const diffBeleidsdoeinPercent = Math.abs(diffBeleidsdomein / total2024 * 100);
                if (diffBeleidsdoeinPercent > 1) showWarning = true;
            }
            
            const detailWarningText = document.getElementById('detail-warning-text');
            if (properties.municipality === 'Kaprijke') {
                detailWarningText.innerHTML = '<strong>Data onbetrouwbaar:</strong> Het verschil tussen de verschillende totalen is extreem groot (> 80%). De getoonde investeringsgegevens voor deze gemeente zijn niet betrouwbaar en mogen niet gebruikt worden voor analyses.';
                detailWarning.style.display = 'flex';
            } else {
                detailWarningText.textContent = 'Er is een verschil tussen de som van de details en het totaal. Dit kan duiden op ontbrekende rekeningen in de gedetailleerde data.';
                detailWarning.style.display = showWarning ? 'flex' : 'none';
            }
            
            detailTableBody.innerHTML = '';
            if (detail2024.top_rekeningen && detail2024.top_rekeningen.length > 0) {
                detail2024.top_rekeningen.forEach(rek => {
                    const row = document.createElement('tr');
                    let displayName = rek.naam;
                    if (displayName.startsWith(rek.code)) {
                        displayName = displayName.substring(rek.code.length).trim();
                        if (displayName.startsWith('-')) {
                            displayName = displayName.substring(1).trim();
                        }
                    }
                    row.innerHTML = `
                        <td class="code-col">${rek.code}</td>
                        <td>${displayName}</td>
                        <td class="bedrag-col">€ ${rek.bedrag.toFixed(2)}</td>
                    `;
                    detailTableBody.appendChild(row);
                });
            } else {
                const row = document.createElement('tr');
                row.innerHTML = '<td colspan="3" class="text-center text-muted">Geen gedetailleerde rekeningen beschikbaar</td>';
                detailTableBody.appendChild(row);
            }
        } else {
            detailWarning.style.display = 'none';
            detailTableBody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Geen gedetailleerde data beschikbaar voor deze gemeente</td></tr>';
        }
    }

    // Render beleidsveld view
    renderBeleidsveldView(properties, total2024, detailTableTitle, detailTableHeaderCol, detailTableBody, detailWarning) {
        detailTableTitle.textContent = 'Top 10 per beleidsveld';
        detailTableHeaderCol.textContent = 'Beleidsveld';
        
        if (properties.beleidsdomein_2024 && properties.beleidsdomein_2024.totaal_beleidsdomein !== null) {
            const beleidsdomein2024 = properties.beleidsdomein_2024;
            
            const diffBeleidsdomein = beleidsdomein2024.verschil_met_totaal;
            const diffBeleidsdoeinPercent = Math.abs(diffBeleidsdomein / total2024 * 100);
            
            let showWarning = diffBeleidsdoeinPercent > 1;
            
            if (properties.detail_2024 && properties.detail_2024.totaal_details !== null) {
                const diffRekeningen = properties.detail_2024.verschil_met_totaal;
                const diffRekeningenPercent = Math.abs(diffRekeningen / total2024 * 100);
                if (diffRekeningenPercent > 1) showWarning = true;
            }
            
            const detailWarningText = document.getElementById('detail-warning-text');
            if (properties.municipality === 'Kaprijke') {
                detailWarningText.innerHTML = '<strong>Data onbetrouwbaar:</strong> Het verschil tussen de verschillende totalen is extreem groot (> 80%). De getoonde investeringsgegevens voor deze gemeente zijn niet betrouwbaar en mogen niet gebruikt worden voor analyses.';
                detailWarning.style.display = 'flex';
            } else {
                detailWarningText.textContent = 'Er is een verschil tussen de som van de details en het totaal. Dit kan duiden op ontbrekende rekeningen in de gedetailleerde data.';
                detailWarning.style.display = showWarning ? 'flex' : 'none';
            }
            
            detailTableBody.innerHTML = '';
            if (beleidsdomein2024.top_beleidsvelden && beleidsdomein2024.top_beleidsvelden.length > 0) {
                beleidsdomein2024.top_beleidsvelden.forEach(beleid => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td class="code-col">${beleid.code}</td>
                        <td>${beleid.naam}</td>
                        <td class="bedrag-col">€ ${beleid.bedrag.toFixed(2)}</td>
                    `;
                    detailTableBody.appendChild(row);
                });
            } else {
                const row = document.createElement('tr');
                row.innerHTML = '<td colspan="3" class="text-center text-muted">Geen beleidsdomein data beschikbaar</td>';
                detailTableBody.appendChild(row);
            }
        } else {
            detailWarning.style.display = 'none';
            detailTableBody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Geen beleidsdomein data beschikbaar voor deze gemeente</td></tr>';
        }
    }
}
