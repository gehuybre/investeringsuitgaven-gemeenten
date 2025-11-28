# Data Structuur Vergelijking

## 📊 File Size Overview

| Format | Size | Reductie | Gebruik |
|--------|------|----------|---------|
| **Parquet** ⭐⭐⭐ | **45 KB** | **99.2%** | Analytics, Python/pandas |
| **Tree JSON** ⭐⭐ | **320 KB** | **94.6%** | Hiërarchische UI, drill-down |
| **Compact JSON** ⭐⭐ | **362 KB** | **93.9%** | Efficiënte lookup, aggregatie |
| **Grouped JSON** ⭐ | **318 KB** | **94.7%** | Per-rekening toegang |
| Original CSV | 221 KB | - | PowerBI export |
| Normalized CSV | 4.3 MB | 25.9% | Excel, spreadsheets |
| Normalized JSON | 5.8 MB | 0% | Origineel (verbose) |

---

## 🏗️ Structuur Details

### 1. **Compact JSON** (362 KB) - Aanbevolen voor HTML
```json
{
  "hierarchy": {
    "REK2811": {
      "naam": "REK2811 Belangen...",
      "niveau_1": "I Investeringsverrichtingen",
      "niveau_2": "I.1 Investeringsuitgaven",
      ...
    }
  },
  "gemeenten": ["District Antwerpen", "Gemeente Aalst", ...],
  "data": [
    ["REK2811", 0, 0.04],  // [rekening_code, gemeente_id, waarde]
    ["REK2811", 1, 3.25],
    ...
  ]
}
```

**Voordelen:**
- ✅ Hiërarchie 1x gedefinieerd (93 rekeningen)
- ✅ Gemeenten 1x gedefinieerd (294 gemeenten)  
- ✅ Data als compacte array: `[code, id, waarde]`
- ✅ Makkelijk aggregeren in HTML/JS
- ✅ 94% kleiner dan origineel

**HTML Aggregatie:**
```javascript
// Totaal per gemeente
function getTotaalPerGemeente(gemeenteId) {
  return data.data
    .filter(([rek, gem, val]) => gem === gemeenteId)
    .reduce((sum, [rek, gem, val]) => sum + val, 0);
}

// Totaal per niveau
function getTotaalPerNiveau(niveauKey) {
  const totals = new Map();
  data.data.forEach(([rek, gem, val]) => {
    const niveauNaam = data.hierarchy[rek][niveauKey];
    totals.set(niveauNaam, (totals.get(niveauNaam) || 0) + val);
  });
  return totals;
}
```

---

### 2. **Tree JSON** (320 KB) - Voor drill-down UI
```json
{
  "tree": {
    "I_Investeringsverrichtingen": {
      "naam": "I Investeringsverrichtingen",
      "children": {
        "I1_Investeringsuitgaven": {
          "naam": "I.1 Investeringsuitgaven",
          "children": {...}
        }
      }
    }
  },
  "rekeningen": {
    "REK2811": {
      "naam": "...",
      "tree_path": ["I_Invest...", "I1_Invest...", ...]
    }
  },
  "gemeenten": [...],
  "data": [["REK2811", 0, 0.04], ...]
}
```

**Voordelen:**
- ✅ Echte boom structuur met parent-child
- ✅ Ideaal voor treeview componenten
- ✅ Navigatie door niveaus
- ✅ 95% kleiner

**HTML Gebruik:**
```javascript
// Recursief door boom navigeren
function renderTree(node, level = 0) {
  return `
    <div class="level-${level}">
      <span>${node.naam}</span>
      ${Object.entries(node.children)
        .map(([key, child]) => renderTree(child, level + 1))
        .join('')}
    </div>
  `;
}
```

---

### 3. **Parquet** (45 KB) - Voor data science
- Kolomgeoriënteerd + gecomprimeerd
- 99% kleiner!
- Direct in pandas laden
- Ideaal voor Python analytics

```python
import pandas as pd
df = pd.read_parquet('opgesplitst_normalized.parquet')

# Groepeer per gemeente
df.groupby('gemeente')['waarde'].sum()

# Filter op categorie
df[df['categorie'].str.contains('financiële')]
```

---

## 🎯 Welke kiezen voor HTML dashboard?

### **Compact JSON** voor dynamische aggregatie
```html
<script>
// Laad 1x
const data = await fetch('opgesplitst_compact.json').then(r => r.json());

// Snelle queries
- Zoek gemeente: O(n) door data.data
- Lookup hiërarchie: O(1) via data.hierarchy[code]
- Lookup gemeente naam: O(1) via data.gemeenten[id]

// Totalen berekenen
function getTotalen() {
  const gemeenteTotalen = new Array(data.gemeenten.length).fill(0);
  data.data.forEach(([rek, gem, val]) => {
    gemeenteTotalen[gem] += val;
  });
  return gemeenteTotalen;
}
</script>
```

### **Tree JSON** voor drill-down interface
```html
<!-- Perfect voor: -->
<div class="hierarchy-browser">
  <ul>
    <li>I Investeringsverrichtingen
      <ul>
        <li>I.1 Investeringsuitgaven
          <ul>
            <li>I.1.A Financiële activa
              ...
```

---

## 📝 Conclusie

**Voor jouw HTML longread:**
1. Gebruik **Compact JSON** als primary data source
2. Pre-compute totalen als apart bestand (zie hieronder)
3. Lazy-load detail data on-demand

**Optioneel: Pre-computed totals** (nog compacter)
```json
{
  "gemeente_totalen": [19.11, 9.35, ...],  // per gemeente_id
  "niveau1_totalen": {"I Invest...": 12345.67},
  "niveau2_totalen": {...},
  ...
}
```

Dit voorkomt runtime berekeningen voor overview visualisaties!
