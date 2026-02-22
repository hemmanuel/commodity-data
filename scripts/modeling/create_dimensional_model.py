import duckdb
import os
from datetime import date

DB_PATH = "data/commodity_data.duckdb"

def create_dimensional_model():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    con = duckdb.connect(DB_PATH)
    print("Creating dimensional schema...")
    
    # 1. DIM_TIME (The "True Timeline")
    # Range: 1990 to 2055 (to cover history and AEO forecasts)
    print("Creating dim_time...")
    con.execute("DROP TABLE IF EXISTS dim_time")
    con.execute("""
        CREATE TABLE dim_time (
            date_key INTEGER PRIMARY KEY, -- YYYYMMDD
            full_date DATE,
            year INTEGER,
            quarter INTEGER,
            month INTEGER,
            month_name VARCHAR,
            week_of_year INTEGER,
            day_of_year INTEGER,
            day_of_month INTEGER,
            day_name VARCHAR,
            is_weekend BOOLEAN,
            season VARCHAR -- Winter, Spring, Summer, Fall
        )
    """)
    
    # Generate dates using DuckDB's generate_series
    start_date = '1990-01-01'
    end_date = '2055-12-31'
    
    con.execute(f"""
        INSERT INTO dim_time
        SELECT 
            CAST(strftime(d, '%Y%m%d') AS INTEGER) as date_key,
            d as full_date,
            EXTRACT(year FROM d) as year,
            EXTRACT(quarter FROM d) as quarter,
            EXTRACT(month FROM d) as month,
            strftime(d, '%B') as month_name,
            EXTRACT(week FROM d) as week_of_year,
            EXTRACT(doy FROM d) as day_of_year,
            EXTRACT(day FROM d) as day_of_month,
            strftime(d, '%A') as day_name,
            CASE WHEN EXTRACT(dow FROM d) IN (0, 6) THEN TRUE ELSE FALSE END as is_weekend,
            CASE 
                WHEN EXTRACT(month FROM d) IN (12, 1, 2) THEN 'Winter'
                WHEN EXTRACT(month FROM d) IN (3, 4, 5) THEN 'Spring'
                WHEN EXTRACT(month FROM d) IN (6, 7, 8) THEN 'Summer'
                ELSE 'Fall' 
            END as season
        FROM (
            SELECT unnest(generate_series(DATE '{start_date}', DATE '{end_date}', INTERVAL 1 DAY)) as d
        )
    """)
    print("dim_time populated.")

    # 2. DIM_PLANTS (Extracted from EIA Series)
    print("Creating dim_plants...")
    con.execute("DROP TABLE IF EXISTS dim_plants")
    con.execute("""
        CREATE TABLE dim_plants (
            plant_id INTEGER PRIMARY KEY,
            plant_name VARCHAR,
            extracted_from_source VARCHAR,
            start_year INTEGER,
            end_year INTEGER
        )
    """)
    
    # Extract distinct Plant ID and Name from EIA Series
    # Pattern: "... : Plant Name (ID) : ..."
    # Also capture the min start_date and max end_date to establish lifespan
    con.execute("""
        INSERT INTO dim_plants
        WITH extracted AS (
            SELECT 
                regexp_extract(name, '\(([0-9]+)\)', 1) as pid_str,
                regexp_extract(name, '(.*) \([0-9]+\)', 1) as pname_raw,
                source,
                start_date,
                end_date
            FROM eia_series
            WHERE series_id LIKE 'ELEC.PLANT%'
            AND regexp_matches(name, '\([0-9]+\)')
        )
        SELECT DISTINCT ON (pid)
            CAST(pid_str AS INTEGER) as pid,
            TRIM(split_part(pname_raw, ':', 2)) as clean_name,
            'EIA',
            MIN(CAST(LEFT(start_date, 4) AS INTEGER)) OVER (PARTITION BY pid_str) as start_year,
            MAX(CAST(LEFT(end_date, 4) AS INTEGER)) OVER (PARTITION BY pid_str) as end_year
        FROM extracted
        WHERE pid_str != '' AND pid_str IS NOT NULL
        ORDER BY pid, clean_name
    """)
    
    count = con.execute('SELECT COUNT(*) FROM dim_plants').fetchone()[0]
    print(f"dim_plants populated with {count} plants.")

    # 3. DIM_COMPANIES (From FERC)
    print("Creating dim_companies...")
    con.execute("DROP TABLE IF EXISTS dim_companies")
    con.execute("""
        CREATE TABLE dim_companies (
            company_id VARCHAR PRIMARY KEY, -- FERC ID
            company_name VARCHAR,
            source VARCHAR
        )
    """)
    
    # Check if ferc_respondents exists
    tables = con.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'ferc_respondents'").fetchall()
    if tables:
        con.execute("""
            INSERT INTO dim_companies
            SELECT DISTINCT ON (respondent_id)
                CAST(respondent_id AS VARCHAR),
                respondent_name,
                'FERC'
            FROM ferc_respondents
            ORDER BY respondent_id
        """)
        count = con.execute('SELECT COUNT(*) FROM dim_companies').fetchone()[0]
        print(f"dim_companies populated with {count} companies.")
    else:
        print("ferc_respondents table not found, skipping dim_companies population.")

    con.close()
    print("Dimensional model created successfully.")

if __name__ == "__main__":
    create_dimensional_model()
