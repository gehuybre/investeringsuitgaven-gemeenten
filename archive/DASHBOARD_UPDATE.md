# Dashboard Integratie - Update 25 november 2025

## Wat is toegevoegd?

De longread heeft nu een volledig geïntegreerd **detail dashboard** dat gedetailleerde investeringsinformatie toont wanneer je op een gemeente klikt op de kaart.

## Nieuwe Functionaliteit

### 1. Detail Panel per Gemeente

Wanneer je op een gemeente klikt op de kaart, verschijnt er een detail panel met:

- **Basisinformatie**: Gemeentenaam en provincie
- **Statistieken**:
  - Totaal investeringen 2024 (per inwoner)
  - Som van gedetailleerde rekeningen
  - Aantal rekeningen in de jaarrekening
  - Verschil tussen totaal en details
- **Top 10 Investeringscategorieën**: Een tabel met de grootste uitgavenposten
- **Waarschuwing**: Als er een significant verschil is tussen het totaal en de som van details

### 2. Data Bron

Het dashboard gebruikt nu `municipalities_enriched.geojson` in plaats van het originele bestand. Dit verrijkte bestand bevat:

- Alle originele data (investeringen 2014-2024)
- **Nieuw**: `detail_2024` veld met:
  - `totaal_details`: Som van alle gedetailleerde bedragen
  - `aantal_rekeningen`: Aantal rekeningen voor deze gemeente
  - `verschil_met_totaal`: Verschil tussen details en totaal
  - `top_rekeningen`: Top 10 grootste rekeningen

### 3. Interactie

1. **Klik op een gemeente** op de kaart
2. Het **detail panel opent** automatisch onder de kaart
3. **Scroll automatisch** naar het panel voor makkelijke weergave
4. De gemeente wordt ook **toegevoegd aan de dashboard selectie**
5. Klik op de **× knop** om het detail panel te sluiten

## Technische Details

### Aangepaste Bestanden

1. **`longread_output/index.html`**
   - Nieuwe CSS voor detail panel styling
   - Nieuwe HTML sectie voor het detail panel
   - Responsief design voor verschillende schermgroottes

2. **`longread_output/js/app.js`**
   - Update: Laadt nu `municipalities_enriched.geojson`
   - Nieuwe functie: `showMunicipalityDetail(properties)` - toont detail panel
   - Nieuwe functie: `hideMunicipalityDetail()` - verbergt detail panel
   - Update: Click handler op kaart roept nu detail functie aan

### Styling Features

- **Modern design**: Schone, professionele uitstraling
- **Color coding**: Blauwe accenten voor consistentie
- **Responsive layout**: Werkt op verschillende schermgroottes
- **Toegankelijkheid**: Duidelijke labels en ARIA attributen
- **Hover effects**: Visuele feedback bij interactie

### Data Validatie

Het detail panel toont automatisch een waarschuwing wanneer:
- Het verschil tussen totaal en details > 1% is
- Dit helpt gebruikers te begrijpen dat er mogelijk rekeningen ontbreken

## Gebruik

### Lokaal Testen

```bash
cd longread_output
python3 -m http.server 8000
```

Open browser op `http://localhost:8000`

### GitHub Pages

De pagina werkt ook op GitHub Pages. Zorg dat `municipalities_enriched.geojson` is gecommit.

## Voorbeeldweergave

### Statistieken Box
```
┌─────────────────────────┐
│ Totaal 2024             │
│ € 386.04                │
│ per inwoner             │
└─────────────────────────┘
```

### Rekeningen Tabel
```
Code        | Rekening              | Categorie       | Bedrag
REK221-7    | Gebouwen - activa in  | 221 Terreinen   | € 168.73
            | aanbouw               |                 |
```

## Volgende Stappen

Mogelijke uitbreidingen:
1. **Export functie**: Download detail data als CSV
2. **Vergelijking**: Vergelijk meerdere gemeenten naast elkaar
3. **Filters**: Filter rekeningen op categorie
4. **Grafieken**: Visualiseer verdeling van uitgaven
5. **Trends**: Toon historische trends per categorie

## Browser Compatibiliteit

- Chrome/Edge: ✅ Volledig ondersteund
- Firefox: ✅ Volledig ondersteund
- Safari: ✅ Volledig ondersteund
- Mobile browsers: ✅ Responsive design

## Troubleshooting

### Detail panel verschijnt niet
- Controleer of `municipalities_enriched.geojson` bestaat
- Check browser console voor fouten
- Verifieer dat JavaScript niet geblokkeerd is

### Data laadt niet
- Controleer of alle bestanden in de juiste map staan
- Verifieer dat de webserver draait
- Check netwerk tab in developer tools

## Credits

- Data: Agentschap Binnenlands Bestuur
- Verwerking: Embuild Vlaanderen
- Visualisatie: Custom dashboard 2025
