#!/usr/bin/env python3
"""
Creëer ultra-efficiënte structuur met:
1. Hiërarchie definitie (1x per rekening code)
2. Gemeente index (gemeenten genummerd 0-293)
3. Data als sparse matrix: [rek_code, gemeente_id, waarde]

Dit elimineert ALLE repetitie van namen en metadata.
"""

import json
from pathlib import Path
from collections import defaultdict


def create_hierarchical_structure():
    """
    Structuur:
    {
      "metadata": {...},
      "hierarchy": {
        "REK2811": {
          "naam": "...",
          "niveau_8": "281 Belangen...",
          "niveau_7": "281 Belangen...",
          ...
        }
      },
      "gemeenten": ["Aalst", "Aarschot", ...],
      "data": [
        ["REK2811", 0, 0.04],  // rekening, gemeente_id, waarde
        ["REK2811", 1, 3.25],
        ...
      ]
    }
    """
    data_dir = Path(__file__).parent.parent / 'data'
    
    with open(data_dir / 'opgesplitst_normalized.json', 'r') as f:
        data = json.load(f)
    
    if not data:
        return
    
    # Bouw hiërarchie dictionary (1x per rekening)
    hierarchy = {}
    gemeente_set = set()
    
    for record in data:
        rek_code = record['alg_rekening_code']
        gemeente_set.add(record['gemeente'])
        
        if rek_code not in hierarchy:
            # Sla hiërarchie op voor deze rekening
            niveaus = {}
            for i in range(1, 9):
                key = f'niveau_{i}'
                if key in record and record[key]:
                    niveaus[f'niveau_{i}'] = record[key]
            
            hierarchy[rek_code] = {
                'naam': record['alg_rekening'],
                'categorie': record['categorie'],
                **niveaus,
                'niveau_diepte': record['niveau_diepte'],
                'path': record['path']
            }
    
    # Maak gemeente index (alfabetisch gesorteerd voor consistentie)
    gemeenten = sorted(list(gemeente_set))
    gemeente_to_id = {naam: idx for idx, naam in enumerate(gemeenten)}
    
    # Bouw compacte data array: [rek_code, gemeente_id, waarde]
    compact_data = []
    for record in data:
        rek_code = record['alg_rekening_code']
        gemeente_id = gemeente_to_id[record['gemeente']]
        waarde = record['waarde']
        compact_data.append([rek_code, gemeente_id, waarde])
    
    # Sorteer data voor efficiency (per rekening gegroepeerd)
    compact_data.sort(key=lambda x: (x[0], x[1]))
    
    output = {
        'metadata': {
            'boekjaar': data[0]['boekjaar'],
            'type_rapport': data[0]['type_rapport'],
            'versie': '1.0',
            'beschrijving': 'Hiërarchische structuur met gemeente index voor minimale repetitie',
            'record_count': len(compact_data),
            'rekening_count': len(hierarchy),
            'gemeente_count': len(gemeenten)
        },
        'hierarchy': hierarchy,
        'gemeenten': gemeenten,
        'data': compact_data
    }
    
    output_file = data_dir / 'opgesplitst_compact.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    original_size = (data_dir / 'opgesplitst_normalized.json').stat().st_size
    new_size = output_file.stat().st_size
    reduction = (1 - new_size / original_size) * 100
    
    print(f"✓ Compact format: {len(compact_data)} data points → {output_file.name}")
    print(f"  Size: {new_size/1024:.1f} KB (was {original_size/1024:.1f} KB)")
    print(f"  Reduction: {reduction:.1f}%")
    print(f"  Hiërarchie entries: {len(hierarchy)}")
    print(f"  Gemeenten: {len(gemeenten)}")


def create_tree_structure():
    """
    Alternatieve structuur: echte boom met parent-child relaties.
    
    {
      "tree": {
        "niveau_1_key": {
          "naam": "I Investeringsverrichtingen",
          "children": {
            "niveau_2_key": {
              "naam": "I.1 Investeringsuitgaven",
              "children": {...}
            }
          }
        }
      },
      "rekeningen": {
        "REK2811": {
          "naam": "...",
          "tree_path": ["niveau_1_key", "niveau_2_key", ...]
        }
      },
      "gemeenten": [...],
      "data": [[rek_code, gemeente_id, waarde], ...]
    }
    """
    data_dir = Path(__file__).parent.parent / 'data'
    
    with open(data_dir / 'opgesplitst_normalized.json', 'r') as f:
        data = json.load(f)
    
    if not data:
        return
    
    # Bouw boom structuur
    tree = {}
    rekeningen = {}
    gemeente_set = set()
    
    def get_or_create_node(parent, niveau_naam):
        """Helper: vind of creëer node in boom."""
        # Maak een key (slug) van de naam
        key = niveau_naam.replace(' ', '_').replace('.', '').replace(',', '')[:50]
        
        if key not in parent:
            parent[key] = {
                'naam': niveau_naam,
                'children': {}
            }
        return parent[key], key
    
    for record in data:
        gemeente_set.add(record['gemeente'])
        rek_code = record['alg_rekening_code']
        
        # Navigeer/bouw boom voor dit record
        current_node = tree
        tree_path = []
        
        for i in range(1, 9):
            niveau_key = f'niveau_{i}'
            if niveau_key in record and record[niveau_key]:
                niveau_naam = record[niveau_key]
                node, node_key = get_or_create_node(current_node, niveau_naam)
                tree_path.append(node_key)
                current_node = node['children']
        
        # Sla rekening info op (1x)
        if rek_code not in rekeningen:
            rekeningen[rek_code] = {
                'naam': record['alg_rekening'],
                'tree_path': tree_path
            }
    
    # Gemeente index
    gemeenten = sorted(list(gemeente_set))
    gemeente_to_id = {naam: idx for idx, naam in enumerate(gemeenten)}
    
    # Compacte data
    compact_data = []
    for record in data:
        rek_code = record['alg_rekening_code']
        gemeente_id = gemeente_to_id[record['gemeente']]
        waarde = record['waarde']
        compact_data.append([rek_code, gemeente_id, waarde])
    
    compact_data.sort(key=lambda x: (x[0], x[1]))
    
    output = {
        'metadata': {
            'boekjaar': data[0]['boekjaar'],
            'type_rapport': data[0]['type_rapport'],
            'versie': '1.0',
            'beschrijving': 'Boom structuur met parent-child relaties en gemeente index',
            'record_count': len(compact_data),
            'rekening_count': len(rekeningen),
            'gemeente_count': len(gemeenten)
        },
        'tree': tree,
        'rekeningen': rekeningen,
        'gemeenten': gemeenten,
        'data': compact_data
    }
    
    output_file = data_dir / 'opgesplitst_tree.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    original_size = (data_dir / 'opgesplitst_normalized.json').stat().st_size
    new_size = output_file.stat().st_size
    reduction = (1 - new_size / original_size) * 100
    
    print(f"✓ Tree format: {len(compact_data)} data points → {output_file.name}")
    print(f"  Size: {new_size/1024:.1f} KB (was {original_size/1024:.1f} KB)")
    print(f"  Reduction: {reduction:.1f}%")
    print(f"  Rekeningen: {len(rekeningen)}")


def create_usage_example():
    """Genereer voorbeeld code voor het gebruiken van de compacte structuur."""
    example = '''
# Voorbeeld: Hoe de compacte structuur gebruiken in JavaScript/HTML

// 1. Laad de data
const data = await fetch('opgesplitst_compact.json').then(r => r.json());

// 2. Lookup functies
function getGemeenteNaam(id) {
  return data.gemeenten[id];
}

function getRekeningInfo(code) {
  return data.hierarchy[code];
}

// 3. Vind alle waarden voor een gemeente
function getGemeenteData(gemeenteNaam) {
  const gemeenteId = data.gemeenten.indexOf(gemeenteNaam);
  return data.data
    .filter(([rek, gem_id, val]) => gem_id === gemeenteId)
    .map(([rek, gem_id, val]) => ({
      rekening: getRekeningInfo(rek),
      waarde: val
    }));
}

// 4. Vind alle gemeenten voor een rekening
function getRekeningData(rekeningCode) {
  return data.data
    .filter(([rek, gem_id, val]) => rek === rekeningCode)
    .map(([rek, gem_id, val]) => ({
      gemeente: getGemeenteNaam(gem_id),
      waarde: val
    }));
}

// 5. Aggregeer per niveau
function aggregateByNiveau(niveau_key) {
  const aggregated = new Map();
  
  data.data.forEach(([rek, gem_id, val]) => {
    const hierarchy = getRekeningInfo(rek);
    const niveau_naam = hierarchy[niveau_key];
    
    if (!aggregated.has(niveau_naam)) {
      aggregated.set(niveau_naam, 0);
    }
    aggregated.set(niveau_naam, aggregated.get(niveau_naam) + val);
  });
  
  return Object.fromEntries(aggregated);
}

// Gebruik:
console.log('Gemeente Aalst:', getGemeenteData('Gemeente en OCMW Aalst'));
console.log('Rekening REK2811:', getRekeningData('REK2811'));
console.log('Totalen per niveau 2:', aggregateByNiveau('niveau_2'));
'''
    
    data_dir = Path(__file__).parent.parent / 'data'
    with open(data_dir / 'usage_example.js', 'w') as f:
        f.write(example)
    
    print(f"✓ Usage example: usage_example.js")


if __name__ == '__main__':
    print("=" * 60)
    print("Ultra-Compacte Structuren (geen repetitie)")
    print("=" * 60)
    print()
    
    create_hierarchical_structure()
    print()
    
    create_tree_structure()
    print()
    
    create_usage_example()
    print()
    
    print("=" * 60)
    print("✓ Compacte structuren gegenereerd!")
    print("=" * 60)
