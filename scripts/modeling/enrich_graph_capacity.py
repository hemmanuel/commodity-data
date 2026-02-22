import duckdb

db_path = 'data/commodity_data.duckdb'
con = duckdb.connect(db_path)

print("Enriching graph with pipeline capacity data...")

try:
    # Drop tables to ensure clean slate (dev mode)
    con.execute("DROP TABLE IF EXISTS links_pipeline_capacity")
    con.execute("DROP TABLE IF EXISTS links_plant_location")
    con.execute("DROP TABLE IF EXISTS dim_states")
    con.execute("DROP TABLE IF EXISTS dim_pipelines")

    # 1. Create dim_pipelines
    print("Creating dim_pipelines...")
    con.execute("CREATE TABLE IF NOT EXISTS dim_pipelines (pipeline_id VARCHAR PRIMARY KEY, pipeline_name VARCHAR)")
    
    # Insert unique pipelines
    con.execute("""
        INSERT INTO dim_pipelines (pipeline_id, pipeline_name)
        SELECT DISTINCT 
            regexp_replace(lower(pipeline), '[^a-z0-9]', '', 'g') as pid,
            pipeline
        FROM fact_pipeline_capacity
        WHERE pipeline IS NOT NULL
        ON CONFLICT DO NOTHING
    """)
    
    # 2. Create dim_states (if not exists)
    print("Creating dim_states...")
    con.execute("CREATE TABLE IF NOT EXISTS dim_states (state_code VARCHAR PRIMARY KEY)")
    
    # Insert unique states from fact_pipeline_capacity (both from and to)
    con.execute("""
        INSERT INTO dim_states (state_code)
        SELECT DISTINCT state_from FROM fact_pipeline_capacity WHERE state_from IS NOT NULL
        UNION
        SELECT DISTINCT state_to FROM fact_pipeline_capacity WHERE state_to IS NOT NULL
        UNION
        SELECT DISTINCT state FROM dim_plants WHERE state IS NOT NULL
        ON CONFLICT DO NOTHING
    """)

    # 3. Create links_pipeline_capacity (edges)
    # This represents the capacity between states via a specific pipeline
    print("Creating links_pipeline_capacity...")
    con.execute("""
        CREATE TABLE IF NOT EXISTS links_pipeline_capacity (
            pipeline_id VARCHAR,
            state_from VARCHAR,
            state_to VARCHAR,
            capacity_mmcfd DOUBLE,
            year INTEGER,
            FOREIGN KEY (pipeline_id) REFERENCES dim_pipelines(pipeline_id),
            FOREIGN KEY (state_from) REFERENCES dim_states(state_code),
            FOREIGN KEY (state_to) REFERENCES dim_states(state_code)
        )
    """)
    
    # Clear existing data to avoid duplicates if re-run
    con.execute("DELETE FROM links_pipeline_capacity")

    # Insert capacity links
    con.execute("""
        INSERT INTO links_pipeline_capacity (pipeline_id, state_from, state_to, capacity_mmcfd, year)
        SELECT 
            regexp_replace(lower(pipeline), '[^a-z0-9]', '', 'g') as pid,
            state_from,
            state_to,
            SUM(capacity_mmcfd) as capacity,
            year
        FROM fact_pipeline_capacity
        WHERE pipeline IS NOT NULL AND state_from IS NOT NULL AND state_to IS NOT NULL
        GROUP BY 1, 2, 3, 5
    """)
    
    # 4. Create links_plant_location (edges)
    # This links plants to their state
    print("Creating links_plant_location...")
    con.execute("""
        CREATE TABLE IF NOT EXISTS links_plant_location (
            plant_id INTEGER,
            state_code VARCHAR,
            FOREIGN KEY (state_code) REFERENCES dim_states(state_code)
        )
    """)
    
    # Clear existing data
    con.execute("DELETE FROM links_plant_location")
    
    # Insert plant location links
    con.execute("""
        INSERT INTO links_plant_location (plant_id, state_code)
        SELECT plant_id, state
        FROM dim_plants
        WHERE state IS NOT NULL
    """)

    print("Graph enrichment complete.")
    
    # Verify counts
    pipelines = con.execute("SELECT COUNT(*) FROM dim_pipelines").fetchone()[0]
    states = con.execute("SELECT COUNT(*) FROM dim_states").fetchone()[0]
    links = con.execute("SELECT COUNT(*) FROM links_pipeline_capacity").fetchone()[0]
    plant_links = con.execute("SELECT COUNT(*) FROM links_plant_location").fetchone()[0]
    
    print(f"Pipelines: {pipelines}")
    print(f"States: {states}")
    print(f"Capacity Links: {links}")
    print(f"Plant Location Links: {plant_links}")

except Exception as e:
    print(f"Error: {e}")
finally:
    con.close()
