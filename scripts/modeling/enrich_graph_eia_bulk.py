import duckdb

DB_PATH = 'data/commodity_data.duckdb'

def enrich_graph():
    con = duckdb.connect(DB_PATH)
    print("Enriching Graph with EIA Bulk Data...")

    # 1. Ensure all plants are in dim_plants
    print("Updating dim_plants...")
    
    # Add state column if not exists
    try:
        con.execute("ALTER TABLE dim_plants ADD COLUMN state VARCHAR")
    except:
        pass

    con.execute("""
        INSERT INTO dim_plants (plant_id, plant_name, state, extracted_from_source, start_year, end_year)
        SELECT 
            CAST(plant_code AS INTEGER) as pid,
            arg_max(plant_name, report_year) as pname,
            arg_max(state, report_year) as pstate,
            'EIA_860' as src,
            MIN(report_year) as syear,
            MAX(report_year) as eyear
        FROM eia860_generators
        WHERE TRY_CAST(plant_code AS INTEGER) IS NOT NULL
          AND CAST(plant_code AS INTEGER) NOT IN (SELECT plant_id FROM dim_plants)
        GROUP BY CAST(plant_code AS INTEGER)
    """)
    
    # 2. Create dim_generators
    print("Creating dim_generators...")
    con.execute("DROP TABLE IF EXISTS dim_generators")
    con.execute("""
        CREATE TABLE dim_generators AS
        SELECT 
            plant_code || '-' || generator_id as generator_uid,
            plant_code as plant_id,
            generator_id,
            arg_max(technology, report_year) as technology,
            arg_max(prime_mover, report_year) as prime_mover,
            arg_max(nameplate_capacity_mw, report_year) as capacity_mw,
            arg_max(energy_source_1, report_year) as primary_fuel,
            arg_max(status, report_year) as status,
            MIN(operating_year) as operating_year,
            MAX(planned_retirement_year) as retirement_year
        FROM eia860_generators
        GROUP BY plant_code, generator_id
    """)
    
    # 3. Create fact_plant_generation (Annual)
    print("Creating fact_plant_generation...")
    con.execute("DROP TABLE IF EXISTS fact_plant_generation")
    con.execute("""
        CREATE TABLE fact_plant_generation AS
        SELECT
            CAST(plant_id AS INTEGER) as plant_id,
            report_year as year,
            SUM(net_generation_mwh) as net_generation_mwh,
            SUM(elec_fuel_consumption_mmbtu) as fuel_consumption_mmbtu
        FROM eia923_generation_fuel
        WHERE plant_id IS NOT NULL 
          AND TRY_CAST(plant_id AS INTEGER) IS NOT NULL
        GROUP BY plant_id, report_year
    """)

    # 4. Enrich dim_companies from EIA-860 Utilities
    print("Enriching dim_companies from EIA-860...")
    # EIA-860 has utility_id and utility_name.
    # We'll treat them as companies.
    # Check if they exist (fuzzy match or ID match if we had a common ID system, but we don't really).
    # For now, we'll add them with a specific source prefix if they don't exist.
    # Actually, let's just add them as 'EIA_UTIL_{id}' to avoid collisions, 
    # and we can rely on entity resolution later to merge.
    
    con.execute("""
        INSERT INTO dim_companies (company_id, company_name, source)
        SELECT 
            'EIA_UTIL_' || utility_id,
            arg_max(utility_name, report_year),
            'EIA_860'
        FROM eia860_generators
        WHERE 'EIA_UTIL_' || utility_id NOT IN (SELECT company_id FROM dim_companies)
          AND utility_id IS NOT NULL
        GROUP BY utility_id
    """)
    
    # 5. Link Plants to Utilities (Ownership)
    # EIA-860 implies ownership by utility_id.
    print("Creating Ownership Links (EIA-860)...")
    # We'll assume the utility listed in 860 owns the plant.
    # This is a simplification (there's a separate Owner file in 860), but good for now.
    
    con.execute("""
        INSERT INTO links_ownership (link_id, company_id, plant_id, match_type, confidence)
        SELECT 
            nextval('seq_link_id'),
            'EIA_UTIL_' || utility_id,
            CAST(plant_code AS INTEGER),
            'EIA_860_REPORTED',
            'HIGH'
        FROM (
            SELECT DISTINCT utility_id, plant_code 
            FROM eia860_generators
            WHERE utility_id IS NOT NULL AND plant_code IS NOT NULL
        ) t
        WHERE NOT EXISTS (
            SELECT 1 FROM links_ownership lo 
            WHERE lo.company_id = 'EIA_UTIL_' || t.utility_id 
              AND lo.plant_id = CAST(t.plant_code AS INTEGER)
        )
    """)

    print("Graph enrichment complete.")
    con.close()

if __name__ == "__main__":
    enrich_graph()
