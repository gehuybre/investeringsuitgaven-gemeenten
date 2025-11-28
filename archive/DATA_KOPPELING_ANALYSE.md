# Data Koppeling: Opgesplitste Details vs Totalen

## Overzicht

Deze analyse koppelt de gedetailleerde investeringsuitgaven per rekening (`data/opgesplitst_grouped.json`) aan de totale waarden in het GeoJSON bestand (`longread_output/municipalities.geojson`).

## Bevindingen

### Structuur van de Bestanden

#### opgesplitst_grouped.json
- **Boekjaar**: 2024
- **Type rapport**: Jaarrekening
- **Aantal gemeenten**: 294
- **Aantal rekeningen**: 4,672 totaal (~16 per gemeente gemiddeld)
- **Structuur**: Rekeningen gegroepeerd per code, met bedragen per gemeente

#### municipalities.geojson
- **Aantal gemeenten**: 285
- **Bevat**: Jaarlijkse totalen 2014-2024 per gemeente
- **Format**: GeoJSON met geometrie en properties

### Systematische Verschillen

**Belangrijke Bevinding**: Er bestaat een systematisch verschil tussen de som van de details in `opgesplitst_grouped.json` en het totaal "2024" in `municipalities.geojson`.

- **Alle 285 gemeenten**: Details som is LAGER dan GeoJSON totaal
- **Gemiddeld verschil**: €20-30 per gemeente
- **Range**: €0.02 tot €65.49

#### Voorbeelden van Verschillen

| Gemeente | Details Som | GeoJSON 2024 | Verschil |
|----------|-------------|--------------|----------|
| Steenokkerzeel | €469.00 | €534.49 | -€65.49 |
| Vleteren | €444.40 | €509.21 | -€64.81 |
| Pajottegem | €443.39 | €507.89 | -€64.50 |
| Zuienkerke | €625.51 | €625.53 | -€0.02 |

### Mogelijke Verklaringen

Het systematische verschil suggereert dat:

1. **Bepaalde rekeningen ontbreken** in het opgesplitste bestand
2. **Verschillende rapportagemomenten**: De bestanden kunnen op verschillende tijdstippen zijn gegenereerd
3. **Correcties/Aanpassingen**: Er kunnen correcties zijn toegepast in het totale bestand die niet in de details zitten
4. **Afronding**: Hoewel dit het grotere verschil niet verklaart

## Aangemaakte Bestanden

### 1. municipalities_enriched.geojson
Een verrijkte versie van het originele GeoJSON bestand met:
- Alle originele data
- **Nieuw veld**: `detail_2024` met:
  - `totaal_details`: Som van alle detail bedragen
  - `aantal_rekeningen`: Aantal rekeningen voor deze gemeente
  - `verschil_met_totaal`: Verschil tussen details en totaal
  - `top_rekeningen`: Top 10 grootste rekeningen voor deze gemeente

**Voorbeeld structuur**:
```json
{
  "properties": {
    "municipality": "Aalst",
    "2024": 386.04,
    "detail_2024": {
      "totaal_details": 359.35,
      "aantal_rekeningen": 24,
      "verschil_met_totaal": -26.69,
      "top_rekeningen": [
        {
          "code": "REK221-7",
          "naam": "Gebouwen - gemeenschapsgoederen - activa in aanbouw",
          "bedrag": 168.73,
          "categorie": "221 Terreinen - gemeenschapsgoederen"
        },
        ...
      ]
    }
  }
}
```

### 2. municipality_details_2024.json
Een volledig overzicht van alle details per gemeente:
- Alle rekeningen per gemeente (niet alleen top 10)
- Volledige metadata (niveaus, categorieën, etc.)
- Totaal per gemeente

### 3. verification_report.json
Gedetailleerd verificatierapport met:
- Alle gemeenten
- Vergelijking tussen detail som en totaal
- Status: MATCH, MISMATCH, of MISSING_IN_GEOJSON

## Aanbevelingen

### Voor Data Analyse
1. **Gebruik het originele 2024 totaal** uit `municipalities.geojson` als de "officiële" waarde
2. **Gebruik de details** voor uitsplitsing en inzicht in de samenstelling
3. **Houd rekening met het verschil** bij interpretatie

### Voor Verdere Verificatie
1. Controleer met de databron waarom er systematische verschillen zijn
2. Identificeer welke rekeningen ontbreken in het opgesplitste bestand
3. Overweeg een volledige export van alle rekeningen voor 2024

## Gebruik in Dashboard

De verrijkte data kan nu gebruikt worden om:
1. **Drill-down functionaliteit** te bieden: Klik op een gemeente → zie top uitgaven
2. **Categorieën te visualiseren**: Verdeling over infrastructuur, gebouwen, etc.
3. **Vergelijkingen te maken**: Welke gemeenten investeren relatief veel in rioleringen, wegen, etc.

## Scripts

- `scripts/verify_totals.py`: Verificatie script om verschillen te controleren
- `scripts/link_detail_data.py`: Koppeling script om data te verrijken

## Datum

Analyse uitgevoerd: 25 november 2025
