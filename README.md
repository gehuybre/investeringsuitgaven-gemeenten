# Investeringsuitgaven Gemeenten

Visualisatie van de gemeentelijke investeringsuitgaven in Vlaanderen (2014-2024).

**Bron:** Agentschap Binnenlands Bestuur, verwerking Embuild Vlaanderen

## 📁 Project Structuur

```
├── data/                           # Input data (CSV, GeoJSON)
│   ├── detail-alle-2024.csv       # Detail rekeningen per gemeente (2024)
│   ├── investeringsuitgave per beleidsdomein 2024.csv
│   ├── investeringsuitgave per beleidsdomein.csv  # Alle jaren
│   ├── cpi.json                   # Consumenten Prijs Index
│   ├── code-rekeningen.csv        # Mapping rekening codes
│   └── gisco/                     # Geografische data
│
├── scripts/                        # Data processing pipeline
│   ├── build.py                   # 🚀 HOOFD BUILD SCRIPT
│   ├── prepare_data.py            # Legacy conversie script
│   └── modules/                   # Herbruikbare modules
│       ├── loaders.py             # Data loaders (CSV, JSON, GeoJSON)
│       ├── processors.py          # GeoJSON enrichment processors
│       ├── beleidsdomein_totals.py # Aggregatie per beleidsdomein
│       └── utils.py               # Utility functies
│
├── longread_output/               # 🌐 Output voor website
│   ├── index.html                 # Hoofd pagina
│   ├── municipalities_enriched.geojson  # ✨ Gegenereerd door build.py
│   ├── beleidsdomein_totals.json        # ✨ Gegenereerd door build.py
│   ├── municipalities.geojson     # Base GeoJSON (alle jaren)
│   ├── averages.json              # Gemiddelden per provincie/regio
│   ├── cpi.json                   # Inflatie correctie data
│   ├── css/                       # Stylesheets
│   └── js/                        # JavaScript applicatie
│
└── archive/                       # Oude scripts en intermediate files
    ├── scripts/                   # Oude/vervangen scripts
    └── data/                      # Intermediate data bestanden
```

## 🚀 Build Pipeline

### Vereisten

```bash
python -m venv venv
source venv/bin/activate  # of: venv\Scripts\activate op Windows
pip install pandas
```

### Output Genereren

Het volledige build proces wordt uitgevoerd door één script:

```bash
python scripts/build.py
```

Dit script:
1. ✅ Laadt de base GeoJSON met gemeenten en historische data
2. ✅ Verwerkt detail CSV (rekeningen per gemeente)
3. ✅ Verwerkt beleidsdomein CSV
4. ✅ Verrijkt GeoJSON met beide datasets
5. ✅ Genereert beleidsdomein totals voor alle jaren
6. ✅ Slaat output op in `longread_output/`

**Output:**
- `municipalities_enriched.geojson` - GeoJSON met detail + beleidsdomein data
- `beleidsdomein_totals.json` - Totalen per beleidsdomein (2014-2024)

### Modulaire Architectuur

De nieuwe structuur is volledig modulair:

**`modules/loaders.py`**
- `load_geojson()` / `save_geojson()` - GeoJSON I/O
- `load_detail_csv()` - Parse detail rekeningen CSV
- `load_beleidsdomein_csv()` - Parse beleidsdomein CSV

**`modules/processors.py`**
- `enrich_with_detail_data()` - Voeg rekening details toe
- `enrich_with_beleidsdomein_data()` - Voeg beleidsdomein data toe

**`modules/beleidsdomein_totals.py`**
- `generate_beleidsdomein_totals()` - Aggregeer over alle gemeenten

**`modules/utils.py`**
- `normalize_municipality_name()` - Gemeentenaam normalisatie
- `parse_value()` - CSV waarde parsing

## 🌐 Lokale Ontwikkeling

Start een lokale webserver:

```bash
cd longread_output
python -m http.server 8000
```

Open http://localhost:8000 in je browser.

## 📤 GitHub Pages Deployment

1. Push naar GitHub:
   ```bash
   git push origin main
   ```

2. Ga naar **Settings → Pages** in je repository

3. Selecteer:
   - **Source:** Deploy from a branch
   - **Branch:** `main`
   - **Folder:** `/longread_output`

4. Klik **Save**

De website is dan beschikbaar op: `https://USERNAME.github.io/REPO-NAME/`

## 🗂️ Data Flow

```
Input CSV bestanden
       ↓
   build.py  ← Gebruikt modules voor herbruikbare logica
       ↓
  Output JSON/GeoJSON
       ↓
   index.html (Leaflet + Chart.js)
```

### Benodigde Input Bestanden

| Bestand | Beschrijving |
|---------|--------------|
| `municipalities.geojson` | Base GeoJSON met geometrie en jaren 2014-2024 |
| `detail-alle-2024.csv` | Rekeningen per gemeente (2024) |
| `investeringsuitgave per beleidsdomein 2024.csv` | Beleidsdomeinen (2024) |
| `investeringsuitgave per beleidsdomein.csv` | Beleidsdomeinen (alle jaren) |
| `averages.json` | Regionale gemiddelden |
| `cpi.json` | Inflatie correctie |

## 📚 Archief

Oude scripts en intermediate bestanden zijn verplaatst naar `archive/`:
- Experimentele conversie scripts
- Verificatie en analyse scripts  
- Intermediate data formats
- Oude documentatie

Deze bestanden zijn niet nodig voor de huidige build pipeline maar worden bewaard voor referentie.

