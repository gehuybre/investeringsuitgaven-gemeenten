#!/usr/bin/env python3
"""
Hoofd build script voor het genereren van alle output bestanden.

Dit script:
1. Verwerkt de CSV input bestanden
2. Genereert de verrijkte GeoJSON met alle data
3. Genereert de beleidsdomein totals
4. Produceert alle bestanden die nodig zijn voor de longread

Gebruik:
    python build.py

Output:
    - longread_output/municipalities_enriched.geojson
    - longread_output/beleidsdomein_totals.json
"""

import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.loaders import (
    load_geojson, 
    save_geojson, 
    save_json,
    load_detail_csv, 
    load_beleidsdomein_csv
)
from modules.processors import (
    enrich_with_detail_data, 
    enrich_with_beleidsdomein_data
)
from modules.beleidsdomein_totals import generate_beleidsdomein_totals
from modules.provincie_processors import (
    load_provincie_data,
    aggregate_provincie_totals,
    create_detailed_provincie_data,
    calculate_provincie_statistics
)


def main():
    """Main build pipeline."""
    
    print("=" * 80)
    print("BUILD PIPELINE: Investeringsuitgaven Gemeenten")
    print("=" * 80)
    print()
    
    # Define paths
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / 'data'
    output_dir = base_dir / 'longread_output'
    
    # Input files
    geojson_input = output_dir / 'municipalities.geojson'
    detail_csv = data_dir / 'detail-alle-2024.csv'
    beleidsdomein_csv = data_dir / 'investeringsuitgave per beleidsdomein 2024.csv'
    beleidsdomein_all_years_csv = data_dir / 'investeringsuitgave per beleidsdomein.csv'
    
    # Output files
    geojson_output = output_dir / 'municipalities_enriched.geojson'
    beleidsdomein_totals_output = output_dir / 'beleidsdomein_totals.json'
    
    # Step 1: Load base GeoJSON
    print("📂 Stap 1: Laden van base GeoJSON...")
    geojson_data = load_geojson(geojson_input)
    print(f"   ✓ {len(geojson_data['features'])} gemeenten geladen")
    print()
    
    # Step 2: Load and process detail CSV
    print("📂 Stap 2: Verwerken van detail CSV (rekeningen)...")
    detail_data = load_detail_csv(detail_csv)
    print(f"   ✓ {len(detail_data)} gemeenten met detail data")
    print()
    
    # Step 3: Load and process beleidsdomein CSV
    print("📂 Stap 3: Verwerken van beleidsdomein CSV...")
    beleidsdomein_data = load_beleidsdomein_csv(beleidsdomein_csv)
    print(f"   ✓ {len(beleidsdomein_data)} gemeenten met beleidsdomein data")
    print()
    
    # Step 4: Enrich GeoJSON with detail data
    print("🔗 Stap 4: Verrijken GeoJSON met detail data...")
    geojson_data, detail_matches = enrich_with_detail_data(geojson_data, detail_data)
    print(f"   ✓ {detail_matches} gemeenten gekoppeld met detail data")
    print()
    
    # Step 5: Enrich GeoJSON with beleidsdomein data
    print("🔗 Stap 5: Verrijken GeoJSON met beleidsdomein data...")
    geojson_data, beleidsdomein_matches = enrich_with_beleidsdomein_data(geojson_data, beleidsdomein_data)
    print(f"   ✓ {beleidsdomein_matches} gemeenten gekoppeld met beleidsdomein data")
    print()
    
    # Step 6: Save enriched GeoJSON
    print("💾 Stap 6: Opslaan verrijkte GeoJSON...")
    save_geojson(geojson_data, geojson_output)
    print(f"   ✓ Opgeslagen: {geojson_output}")
    print()
    
    # Step 7: Generate beleidsdomein totals
    print("📊 Stap 7: Genereren beleidsdomein totals (alle jaren)...")
    beleidsdomein_totals = generate_beleidsdomein_totals(beleidsdomein_all_years_csv)
    print(f"   ✓ {len(beleidsdomein_totals)} beleidsdomeinen verwerkt")
    years = sorted(set(year for subdomeinen in beleidsdomein_totals.values() for year in subdomeinen.keys()))
    print(f"   ✓ Jaren: {min(years)} - {max(years)}")
    print()
    
    # Step 8: Save beleidsdomein totals
    print("💾 Stap 8: Opslaan beleidsdomein totals...")
    save_json(beleidsdomein_totals, beleidsdomein_totals_output)
    print(f"   ✓ Opgeslagen: {beleidsdomein_totals_output}")
    print()
    
    # Step 9: Load and process provinciale data
    print("📂 Stap 9: Laden provinciale investeringsdata...")
    provincie_csv = data_dir / 'provinciebesturen' / 'provincie_investeringen_per_beleidsveld_cleaned.csv'
    
    if provincie_csv.exists():
        provincie_df = load_provincie_data(provincie_csv)
        print(f"   ✓ {len(provincie_df)} rijen provinciale data geladen")
        print()
        
        # Step 10: Aggregate provincie totals
        print("📊 Stap 10: Aggregeren provinciale totalen...")
        provincie_totals = aggregate_provincie_totals(provincie_df)
        print(f"   ✓ {len(provincie_totals)} provincies verwerkt")
        print()
        
        # Step 11: Create detailed provincie data
        print("📊 Stap 11: Genereren gedetailleerde provinciale data...")
        provincie_detailed = create_detailed_provincie_data(provincie_df)
        print(f"   ✓ Gedetailleerde data gegenereerd")
        print()
        
        # Step 12: Calculate statistics
        print("📊 Stap 12: Berekenen provinciale statistieken...")
        provincie_stats = calculate_provincie_statistics(provincie_totals)
        print(f"   ✓ Statistieken berekend voor {len(provincie_stats)} meerjarenplannen")
        print()
        
        # Step 13: Save provincie outputs
        print("💾 Stap 13: Opslaan provinciale data...")
        provincie_totals_output = output_dir / 'provincie_totals.json'
        provincie_detailed_output = output_dir / 'provincie_detailed.json'
        provincie_stats_output = output_dir / 'provincie_stats.json'
        
        save_json(provincie_totals, provincie_totals_output)
        save_json(provincie_detailed, provincie_detailed_output)
        save_json(provincie_stats, provincie_stats_output)
        
        print(f"   ✓ Opgeslagen: {provincie_totals_output.name}")
        print(f"   ✓ Opgeslagen: {provincie_detailed_output.name}")
        print(f"   ✓ Opgeslagen: {provincie_stats_output.name}")
        print()
    else:
        print(f"   ⚠ Provinciale data niet gevonden: {provincie_csv}")
        print(f"   → Run eerst: python scripts/clean_provincie_data.py")
        print()
    
    # Summary
    print("=" * 80)
    print("✅ BUILD VOLTOOID")
    print("=" * 80)
    print()
    print("Output bestanden (gemeenten):")
    print(f"  • {geojson_output.relative_to(base_dir)}")
    print(f"  • {beleidsdomein_totals_output.relative_to(base_dir)}")
    print()
    
    if provincie_csv.exists():
        print("Output bestanden (provincies):")
        print(f"  • {(output_dir / 'provincie_totals.json').relative_to(base_dir)}")
        print(f"  • {(output_dir / 'provincie_detailed.json').relative_to(base_dir)}")
        print(f"  • {(output_dir / 'provincie_stats.json').relative_to(base_dir)}")
        print()
    
    print("Bestaande bestanden (niet gewijzigd):")
    print(f"  • {(output_dir / 'municipalities.geojson').relative_to(base_dir)}")
    print(f"  • {(output_dir / 'averages.json').relative_to(base_dir)}")
    print(f"  • {(output_dir / 'cpi.json').relative_to(base_dir)}")
    print()


if __name__ == '__main__':
    main()
