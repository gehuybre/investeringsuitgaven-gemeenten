# Architectuur Documentatie

## Overzicht

Dit project gebruikt een modulaire pipeline architectuur waarbij herbruikbare Python modules data verwerken van CSV naar verrijkte GeoJSON bestanden voor een interactieve webvisualisatie.

## Build Pipeline

### Single Entry Point

```bash
python scripts/build.py
```

Dit script orchestreert het volledige build proces in 8 stappen:

```
Step 1: Load base GeoJSON              → municipalities.geojson
Step 2: Parse detail CSV               → detail_data dict
Step 3: Parse beleidsdomein CSV        → beleidsdomein_data dict
Step 4: Enrich with detail data        → geojson + detail_2024
Step 5: Enrich with beleidsdomein      → geojson + beleidsdomein_2024
Step 6: Save enriched GeoJSON          → municipalities_enriched.geojson
Step 7: Generate beleidsdomein totals  → beleidsdomein_totals dict
Step 8: Save beleidsdomein totals      → beleidsdomein_totals.json
```

## Module Beschrijving

### `modules/utils.py`

Utility functies gedeeld over alle modules:

- **`normalize_municipality_name(name: str) -> str`**
  - Verwijdert "Gemeente en OCMW " prefix
  - Converteert naar lowercase voor consistent matching
  - Gebruikt in alle data linking operaties

- **`parse_value(value: str) -> float | None`**
  - Converteert CSV strings naar floats
  - Handelt komma als decimaal scheidingsteken
  - Retourneert None voor lege of invalide waarden

### `modules/loaders.py`

Data I/O operaties:

- **`load_geojson(filepath) -> dict`**
  - Laadt GeoJSON bestanden
  - Valideert JSON structuur

- **`save_geojson(data, filepath) -> None`**
  - Slaat GeoJSON op met pretty printing
  - Gebruikt UTF-8 encoding

- **`load_detail_csv(csv_path) -> dict`**
  - Parse CSV met gemeenten als rijen, rekeningen als kolommen
  - Retourneert: `{gemeente: {rekeningen: [...], totaal: float}}`
  - Skipt nul-waarden voor compacte output

- **`load_beleidsdomein_csv(csv_path) -> dict`**
  - Parse CSV met beleidsdomein data
  - Retourneert: `{gemeente: {beleidsvelden: [...], totaal: float}}`
  - Extraheert code en naam uit kolom headers

### `modules/processors.py`

GeoJSON enrichment functies:

- **`enrich_with_detail_data(geojson, detail_data) -> (dict, int)`**
  - Voegt `detail_2024` property toe aan elk feature
  - Includeert top 10 rekeningen per gemeente
  - Berekent verschil met totaal bedrag
  - Retourneert aantal successful matches

- **`enrich_with_beleidsdomein_data(geojson, beleidsdomein_data) -> (dict, int)`**
  - Voegt `beleidsdomein_2024` property toe aan elk feature
  - Includeert top beleidsvelden per gemeente
  - Berekent verschil met totaal bedrag
  - Retourneert aantal successful matches

### `modules/beleidsdomein_totals.py`

Aggregatie over alle gemeenten:

- **`generate_beleidsdomein_totals(csv_path) -> dict`**
  - Parse multi-header CSV (4 header rijen)
  - Aggregeert investeringen per beleidsdomein per jaar
  - Retourneert: `{subdomein: {year: total}}`
  - Gebruikt pandas voor efficiënte CSV verwerking

## Data Structuren

### Input: detail-alle-2024.csv

```csv
Gemeente;REK221-7 ...;REK222-1 ...;...
Gemeente en OCMW Aalst;168.73;12.45;...
Gemeente en OCMW Aarschot;25.30;5.67;...
```

### Input: investeringsuitgave per beleidsdomein 2024.csv

```csv
Grondgebied;Bestuur;02 Zich verplaatsen...;061 Gebiedsontwikkeling...
Gemeente en OCMW Aalst;OCMW + Gemeente;45.23;89.12
```

### Output: municipalities_enriched.geojson

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "municipality": "Aalst",
        "2024": 386.04,
        "detail_2024": {
          "totaal_details": 359.35,
          "aantal_rekeningen": 24,
          "verschil_met_totaal": -26.69,
          "top_rekeningen": [...]
        },
        "beleidsdomein_2024": {
          "totaal_beleidsdomein": 380.12,
          "aantal_beleidsvelden": 12,
          "verschil_met_totaal": -5.92,
          "top_beleidsvelden": [...]
        }
      },
      "geometry": {...}
    }
  ]
}
```

### Output: beleidsdomein_totals.json

```json
{
  "02 Zich verplaatsen en mobiliteit": {
    "2014": 5101.04,
    "2015": 4523.12,
    ...
    "2024": 6789.45
  },
  "061 Gebiedsontwikkeling": {
    ...
  }
}
```

## Frontend Integratie

De longread website (`index.html`) laadt 4 JSON bestanden:

1. **municipalities_enriched.geojson** - Hoofddata met geometrie
2. **averages.json** - Gemiddelden voor vergelijking
3. **cpi.json** - Inflatie correctie data
4. **beleidsdomein_totals.json** - Aggregaties voor charts

### JavaScript Applicatie (app.js)

```javascript
// Parallel laden van data
const [geoResponse, avgResponse, cpiResponse, beleidsdomeinResponse] = 
    await Promise.all([...]);

// Leaflet map met choropleth
setupMap(municipalitiesData);

// Chart.js visualisatie
setupChart(selectedMunicipalities);
```

## Error Handling

### Gemeente Name Matching

- **Probleem:** Verschillende schrijfwijzen van gemeentenamen
- **Oplossing:** `normalize_municipality_name()` zorgt voor consistentie
- **Resultaat:** 285/285 gemeenten succesvol gematched (100%)

### Data Verschillen

- **Observatie:** Detail soms != totaal (€0.02 - €65 verschil)
- **Aanpak:** Beide waarden worden opgeslagen voor transparantie
- **Property:** `verschil_met_totaal` toont het verschil

## Performance

### File Sizes

| Bestand | Grootte | Compressie |
|---------|---------|------------|
| municipalities_enriched.geojson | ~8 MB | - |
| beleidsdomein_totals.json | ~15 KB | - |
| averages.json | ~5 KB | - |

### Build Time

- Volledige build: ~3-5 seconden
- CSV parsing: <1 seconde
- GeoJSON enrichment: <1 seconde
- Totals aggregation: ~2 seconden (pandas)

## Extensibility

### Nieuwe Data Toevoegen

1. Voeg parser toe aan `modules/loaders.py`
2. Voeg enrichment toe aan `modules/processors.py`
3. Update `scripts/build.py` met nieuwe stap

### Nieuwe Visualisatie

1. Genereer JSON in gewenst formaat
2. Voeg toe aan `longread_output/`
3. Update `app.js` om data te laden

## Testing

### Validatie

```bash
# Run build
python scripts/build.py

# Start webserver
cd longread_output && python -m http.server 8000

# Open http://localhost:8000
# Controleer:
# - Map laadt correct
# - Charts tonen data
# - Geen console errors
```

### Data Integriteit

- 100% gemeente matching success rate
- Geen NULL waarden in verrijkte properties
- Totalen komen overeen (binnen marge)
