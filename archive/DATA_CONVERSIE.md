# Data Conversie

## Structuur

```
scripts/prepare_data.py  → Converteer opgesplitst.csv naar opgesplitst_grouped.json
data/opgesplitst.csv     → Input: PowerBI export
data/opgesplitst_grouped.json → Output: Geoptimaliseerde structuur
```

## Gebruik

```bash
python3 scripts/prepare_data.py
```

## Output formaat

`opgesplitst_grouped.json` bevat:

```json
{
  "boekjaar": 2024,
  "type_rapport": "Jaarrekening",
  "rekeningen": {
    "REK2811": {
      "alg_rekening": "REK2811 Belangen in...",
      "categorie": "281 Belangen...",
      "niveaus": {
        "niveau_1": "I Investeringsverrichtingen",
        "niveau_2": "I.1 Investeringsuitgaven",
        ...
      },
      "niveau_diepte": 8,
      "path": "I Investeringsverrichtingen > ...",
      "gemeenten": {
        "Gemeente en OCMW Aalst": 0.04,
        "Gemeente en OCMW Aarschot": 3.25,
        ...
      }
    }
  },
  "metadata": {
    "rekening_count": 93,
    "gemeente_count": 294
  }
}
```

### Voordelen

- ✅ Hiërarchie metadata 1x per rekening (93x)
- ✅ Gemeenten als key-value (geen repetitie)
- ✅ Compacte file size: 318 KB (was 5.8 MB normalized)
- ✅ 94.7% reductie
- ✅ Makkelijk te gebruiken in HTML/JavaScript

## Archive

Oude experimenten en alternatieve structuren zijn verplaatst naar `archive/`:
- Verschillende JSON formaten (compact, tree, table, normalized)
- Parquet export
- CSV exports
- Eerdere conversie scripts
