from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import duckdb
import os
import shutil
import time
import json
import logging
from typing import List, Optional
from pydantic import BaseModel

# Setup logging
logging.basicConfig(
    filename='backend_debug.log', 
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="Commodity Data API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DB_PATH = os.path.abspath("data/commodity_data.duckdb")
DB_VIEW_PATH = os.path.abspath("data/commodity_data_view.duckdb")
STATUS_FILE = "data/ingestion_status.json"

logging.info(f"DB_PATH: {DB_PATH}")
logging.info(f"DB_VIEW_PATH: {DB_VIEW_PATH}")

def get_db_connection():
    """
    Connects to the database. Prefer main DB read-only.
    """
    # 1. Try Main DB
    try:
        logging.debug("Attempting to connect to Main DB...")
        if not os.path.exists(DB_PATH):
            logging.error(f"Main DB file not found at {DB_PATH}")
            raise FileNotFoundError(f"Main DB file not found at {DB_PATH}")
            
        con = duckdb.connect(DB_PATH, read_only=True)
        logging.debug("Connected to Main DB successfully.")
        return con
    except Exception as e:
        logging.warning(f"Failed to connect to Main DB: {e}")
        # If main DB fails, try snapshot
        pass

    # 2. Snapshot Logic (Only if Main DB failed)
    try:
        # Check if we need to update snapshot
        should_update = False
        if not os.path.exists(DB_VIEW_PATH):
            should_update = True
        else:
            # Update if main is newer by > 5 mins
            try:
                main_mtime = os.path.getmtime(DB_PATH)
                view_mtime = os.path.getmtime(DB_VIEW_PATH)
                if (main_mtime - view_mtime) > 300:
                    should_update = True
            except:
                should_update = True

        if should_update:
            logging.info("Updating snapshot...")
            try:
                # This might take a while for 11GB!
                shutil.copy2(DB_PATH, DB_VIEW_PATH)
                logging.info("Snapshot updated.")
            except Exception as e:
                logging.error(f"Failed to update snapshot: {e}")
                # Proceeding to try reading old snapshot if exists

        logging.debug("Attempting to connect to Snapshot...")
        con = duckdb.connect(DB_VIEW_PATH, read_only=True)
        return con
    except Exception as e:
        logging.error(f"Critical: Failed to connect to both Main and Snapshot DB: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "Commodity Data API is running"}

@app.get("/status")
def get_ingestion_status():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"status": "unknown", "error": "Could not read status file"}
    return {"status": "not_started"}

# --- EIA Endpoints ---

@app.get("/eia/summary")
def get_eia_summary():
    try:
        logging.info("Calling get_eia_summary (v2)")
        con = get_db_connection()
        try:
            # Get counts and date ranges from eia_series
            stats = con.execute("""
                SELECT 
                    COUNT(*) as total_series,
                    MIN(start_date) as min_date,
                    MAX(end_date) as max_date,
                    COUNT(DISTINCT units) as distinct_units
                FROM eia_series
            """).fetchone()
            
            # Get counts from new bulk tables
            try:
                gen_count = con.execute("SELECT COUNT(*) FROM eia860_generators").fetchone()[0]
            except:
                gen_count = 0
                
            try:
                plant_count = con.execute("SELECT COUNT(*) FROM dim_plants").fetchone()[0]
            except:
                plant_count = 0
                
            try:
                gen_records = con.execute("SELECT COUNT(*) FROM eia923_generation_fuel").fetchone()[0]
            except:
                gen_records = 0
            
            # Get top units
            units = con.execute("""
                SELECT units, COUNT(*) as count 
                FROM eia_series 
                GROUP BY units 
                ORDER BY count DESC 
                LIMIT 10
            """).fetchall()
            
            return {
                "total_series": stats[0],
                "total_generators": gen_count,
                "total_plants": plant_count,
                "generation_records": gen_records,
                "date_range": {"start": stats[1], "end": stats[2]},
                "units": [{"name": u[0], "count": u[1]} for u in units]
            }
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /eia/summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/eia/search")
def search_eia_series(q: Optional[str] = None, category: Optional[str] = None, limit: int = 50, offset: int = 0):
    try:
        con = get_db_connection()
        try:
            # Simple case-insensitive search
            query = """
                SELECT series_id, name, units, frequency, start_date, end_date
                FROM eia_series
            """
            params = []
            conditions = []
            
            if q:
                conditions.append("(name ILIKE ? OR series_id ILIKE ?)")
                params.extend([f'%{q}%', f'%{q}%'])
            
            if category:
                cat = category.lower()
                if cat == 'electricity':
                    conditions.append("(name ILIKE 'Electricity%' OR name ILIKE 'Net generation%' OR name ILIKE 'Electric fuel consumption%' OR name ILIKE 'Coal shipment%' OR name ILIKE 'Renewable Energy%')")
                elif cat == 'natural-gas':
                    conditions.append("(name ILIKE 'Natural Gas%')")
                elif cat == 'petroleum':
                    conditions.append("(name ILIKE 'Liquid Fuels%' OR name ILIKE 'Refining Industry%' OR name ILIKE 'Crude Oil%' OR name ILIKE 'Petroleum%')")
                elif cat == 'transportation':
                    conditions.append("(name ILIKE 'Transportation%' OR name ILIKE 'Light-Duty Vehicle%' OR name ILIKE 'Freight%' OR name ILIKE 'Aircraft%' OR name ILIKE 'Air Travel%' OR name ILIKE 'New Light-Duty Vehicle%' OR name ILIKE 'New Vehicle Attributes%')")
                elif cat == 'environment':
                    conditions.append("(name ILIKE 'Carbon Dioxide%' OR name ILIKE 'Emissions%')")
                elif cat == 'economy':
                    conditions.append("(name ILIKE 'Macroeconomic%' OR name ILIKE 'Energy Expenditures%' OR name ILIKE 'Energy Prices%')")
                elif cat == 'consumption':
                    conditions.append("(name ILIKE 'Energy Use%' OR name ILIKE 'Residential%' OR name ILIKE 'Commercial%' OR name ILIKE 'Industrial%')")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY series_id LIMIT ? OFFSET ?"
            params.append(limit)
            params.append(offset)
            
            results = con.execute(query, params).fetchall()
            return [
                {
                    "series_id": r[0],
                    "name": r[1],
                    "unit": r[2],
                    "frequency": r[3],
                    "start_date": r[4],
                    "end_date": r[5]
                }
                for r in results
            ]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /eia/search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/eia/series/{series_id}")
def get_eia_series_data(series_id: str):
    try:
        con = get_db_connection()
        try:
            # Get metadata
            meta = con.execute("SELECT * FROM eia_series WHERE series_id = ?", [series_id]).fetchone()
            if not meta:
                raise HTTPException(status_code=404, detail="Series not found")
                
            # Get data points
            data = con.execute("""
                SELECT date, value 
                FROM eia_data 
                WHERE series_id = ? 
                ORDER BY date ASC
            """, [series_id]).fetchall()
            
            return {
                "metadata": {
                    "series_id": meta[0],
                    "name": meta[1],
                    "unit": meta[2],
                    "frequency": meta[3],
                    "description": meta[4] if len(meta) > 4 else ""
                },
                "data": [{"date": d[0], "value": d[1]} for d in data]
            }
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /eia/series: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- FERC Endpoints ---

@app.get("/ferc/respondents")
def get_ferc_respondents(limit: int = 100, offset: int = 0, year: Optional[str] = None, search: Optional[str] = None, sort: Optional[str] = None):
    try:
        con = get_db_connection()
        try:
            query = "SELECT * FROM ferc_respondents WHERE 1=1"
            params = []
            
            if year and year.lower() != 'all':
                query += " AND year = ?"
                params.append(int(year))
            
            if search:
                query += " AND (respondent_name ILIKE ? OR respondent_id ILIKE ?)"
                params.extend([f'%{search}%', f'%{search}%'])
            
            # sort=name: by name A-Z, then by year newest-first within each name
            # sort=year: by year newest-first, then by name A-Z
            # Use year as integer so 2021 > 2000 (not string sort)
            if sort == 'year':
                query += " ORDER BY year DESC NULLS LAST, respondent_name ASC NULLS LAST"
            else:
                query += " ORDER BY COALESCE(respondent_name,'') ASC, year DESC NULLS LAST"
                
            query += " LIMIT ? OFFSET ?"
            params.append(limit)
            params.append(offset)
            
            res = con.execute(query, params)
            cols = [desc[0] for desc in res.description]
            rows = res.fetchall()
            
            return [dict(zip(cols, row)) for row in rows]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /ferc/respondents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ferc/data/{respondent_id}")
def get_ferc_respondent_data(respondent_id: str, year: Optional[str] = None):
    try:
        con = get_db_connection()
        try:
            results = {}
            
            # Helper to fetch data with row literals
            def fetch_table(table_name, literal_table_name, columns):
                query = f"""
                    SELECT 
                        t.year, 
                        t.row_number, 
                        l.row_literal as description,
                        {', '.join(['t.' + c for c in columns])}
                    FROM {table_name} t
                    LEFT JOIN ferc_row_literals l 
                        ON t.row_number = l.row_number 
                        AND t.year = l.year
                        AND l.table_name = '{literal_table_name}'
                    WHERE t.respondent_id = ?
                """
                params = [respondent_id]
                if year and year.lower() != 'all':
                    query += " AND t.year = ?"
                    params.append(int(year))
                
                query += " ORDER BY t.year DESC, t.row_number ASC"
                
                res = con.execute(query, params)
                cols = [desc[0] for desc in res.description]
                return [dict(zip(cols, row)) for row in res.fetchall()]

            results['income_statement'] = fetch_table(
                'ferc_income_statement', 
                'F2_114_STMT_INCOME', 
                ['current_year_total', 'prev_year_total']
            )
            
            results['balance_sheet_assets'] = fetch_table(
                'ferc_balance_sheet_assets', 
                'F2_110_COMP_BAL_DEBIT', 
                ['current_year_end_balance', 'prev_year_end_balance']
            )

            results['balance_sheet_liabilities'] = fetch_table(
                'ferc_balance_sheet_liabilities', 
                'F2_112_COMP_BAL_CREDIT', 
                ['current_year_end_balance', 'prev_year_end_balance']
            )
            
            results['cash_flow'] = fetch_table(
                'ferc_cash_flow', 
                'F2_120_STMNT_CASH_FLOW', 
                ['current_year', 'prev_year']
            )
            
            return results
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /ferc/data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ferc/years")
def get_ferc_years():
    try:
        con = get_db_connection()
        try:
            years = con.execute("SELECT DISTINCT year FROM ferc_respondents ORDER BY year DESC").fetchall()
            return [y[0] for y in years]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /ferc/years: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ferc/form552")
def get_ferc_form552(limit: int = 100, offset: int = 0, search: Optional[str] = None):
    """Form 552 Natural Gas Transactions. Returns columns + rows; empty if table not populated."""
    try:
        con = get_db_connection()
        try:
            tables = con.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' AND table_name = 'ferc_form552_master'"
            ).fetchall()
            if not tables:
                return {"columns": [], "rows": []}
            cols = [r[0] for r in con.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'ferc_form552_master' ORDER BY ordinal_position"
            ).fetchall()]
            if not cols:
                return {"columns": [], "rows": []}
            # Build query; filter by search on string columns if provided
            query = "SELECT * FROM ferc_form552_master WHERE 1=1"
            params = []
            if search:
                query += " AND ("
                str_cols = [c for c in cols if c and c != "source_file"][:8]
                if str_cols:
                    query += " OR ".join([f"CAST({c} AS VARCHAR) ILIKE ?" for c in str_cols])
                    params.extend([f"%{search}%"] * len(str_cols))
                else:
                    query += "1=0"
                query += ")"
            query += " ORDER BY 1 DESC NULLS LAST LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            res = con.execute(query, params)
            cols = [desc[0] for desc in res.description]
            rows = [dict(zip(cols, row)) for row in res.fetchall()]
            return {"columns": cols, "rows": rows}
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /ferc/form552: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ferc1/respondents")
def get_ferc1_respondents(limit: int = 100, offset: int = 0, year: Optional[str] = None, search: Optional[str] = None):
    try:
        con = get_db_connection()
        try:
            query = "SELECT * FROM ferc1_respondents WHERE 1=1"
            params = []
            
            if year and year.lower() != 'all':
                query += " AND year = ?"
                params.append(int(year))
            
            if search:
                query += " AND (respondent_name ILIKE ? OR respondent_id ILIKE ?)"
                params.extend([f'%{search}%', f'%{search}%'])
            
            query += " ORDER BY respondent_name ASC, year DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            res = con.execute(query, params)
            cols = [desc[0] for desc in res.description]
            rows = res.fetchall()
            return [dict(zip(cols, row)) for row in rows]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /ferc1/respondents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ferc1/data/{respondent_id}")
def get_ferc1_respondent_data(respondent_id: str, year: Optional[str] = None):
    try:
        con = get_db_connection()
        try:
            results = {}
            
            def fetch_table(table_name, columns):
                query = f"""
                    SELECT 
                        t.year, 
                        t.row_number, 
                        l.row_literal as description,
                        {', '.join(['t.' + c for c in columns])}
                    FROM {table_name} t
                    LEFT JOIN ferc1_row_literals l 
                        ON t.row_number = l.row_number 
                        AND t.year = l.year
                        AND l.table_name = '{table_name}'
                    WHERE t.respondent_id = ?
                """
                params = [respondent_id]
                if year and year.lower() != 'all':
                    query += " AND t.year = ?"
                    params.append(int(year))
                
                query += " ORDER BY t.year DESC, t.row_number ASC"
                
                res = con.execute(query, params)
                cols = [desc[0] for desc in res.description]
                return [dict(zip(cols, row)) for row in res.fetchall()]

            results['income_statement'] = fetch_table(
                'ferc1_income_statement', 
                ['current_year_amount', 'prev_year_amount']
            )
            
            results['balance_sheet_assets'] = fetch_table(
                'ferc1_balance_sheet_assets', 
                ['begin_year_balance', 'end_year_balance']
            )

            results['balance_sheet_liabilities'] = fetch_table(
                'ferc1_balance_sheet_liabilities', 
                ['begin_year_balance', 'end_year_balance']
            )
            
            results['cash_flow'] = fetch_table(
                'ferc1_cash_flow', 
                ['amount', 'prev_amount']
            )
            
            # Steam Plants
            plant_query = """
                SELECT * FROM ferc1_steam_plants 
                WHERE respondent_id = ?
            """
            params = [respondent_id]
            if year and year.lower() != 'all':
                plant_query += " AND year = ?"
                params.append(int(year))
            plant_query += " ORDER BY year DESC, plant_name ASC"
            
            res = con.execute(plant_query, params)
            cols = [desc[0] for desc in res.description]
            results['steam_plants'] = [dict(zip(cols, row)) for row in res.fetchall()]
            
            return results
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /ferc1/data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Market Monitor Endpoints ---

@app.get("/market/search")
def search_market_data(category: str, q: Optional[str] = None, limit: int = 50, offset: int = 0):
    try:
        con = get_db_connection()
        try:
            query = "SELECT series_id, name, units, frequency, start_date, end_date FROM eia_series WHERE "
            params = []
            
            if category == 'electricity':
                query += "dataset = 'ELEC' AND series_id NOT LIKE 'ELEC.PLANT%'"
            elif category == 'petroleum':
                query += "dataset = 'PET'"
            elif category == 'natural-gas':
                query += "dataset = 'NG'"
            elif category == 'coal':
                query += "dataset = 'COAL'"
            elif category == 'transportation':
                # Transportation data is often in PET or TOTAL, filtered by name
                # We'll search across all datasets but filter by keywords
                pass # Logic handled by conditions below
            else:
                raise HTTPException(status_code=400, detail="Invalid category")
                
            if q:
                query += " AND (name ILIKE ? OR series_id ILIKE ?)"
                params.extend([f'%{q}%', f'%{q}%'])
                
            query += " ORDER BY series_id LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            results = con.execute(query, params).fetchall()
            return [
                {
                    "series_id": r[0],
                    "name": r[1],
                    "unit": r[2],
                    "frequency": r[3],
                    "start_date": r[4],
                    "end_date": r[5]
                }
                for r in results
            ]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /market/search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/plants/search")
def search_plants(q: Optional[str] = None, limit: int = 50, offset: int = 0):
    try:
        con = get_db_connection()
        try:
            query = "SELECT plant_id, plant_name, state, primary_fuel, technology FROM dim_plants WHERE 1=1"
            params = []
            
            if q:
                query += " AND (plant_name ILIKE ? OR CAST(plant_id AS VARCHAR) ILIKE ?)"
                params.extend([f'%{q}%', f'%{q}%'])
                
            query += " ORDER BY plant_name LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            results = con.execute(query, params).fetchall()
            return [
                {
                    "plant_id": r[0],
                    "name": r[1],
                    "state": r[2],
                    "primary_fuel": r[3],
                    "technology": r[4]
                }
                for r in results
            ]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /plants/search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/plants/{plant_id}")
def get_plant_details(plant_id: int):
    try:
        con = get_db_connection()
        try:
            # Basic info
            plant = con.execute("SELECT * FROM dim_plants WHERE plant_id = ?", [plant_id]).fetchone()
            if not plant:
                raise HTTPException(status_code=404, detail="Plant not found")
            
            cols = [d[0] for d in con.execute("DESCRIBE dim_plants").fetchall()]
            plant_data = dict(zip(cols, plant))
            
            # Generators
            gens = con.execute("""
                SELECT * FROM dim_generators 
                WHERE CAST(plant_id AS INTEGER) = ?
                ORDER BY generator_id
            """, [plant_id]).fetchall()
            gen_cols = [d[0] for d in con.execute("DESCRIBE dim_generators").fetchall()]
            plant_data['generators'] = [dict(zip(gen_cols, g)) for g in gens]
            
            # Generation History
            history = con.execute("""
                SELECT * FROM fact_plant_generation 
                WHERE plant_id = ?
                ORDER BY year
            """, [plant_id]).fetchall()
            hist_cols = [d[0] for d in con.execute("DESCRIBE fact_plant_generation").fetchall()]
            plant_data['generation_history'] = [dict(zip(hist_cols, h)) for h in history]
            
            return plant_data
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /plants/{plant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Pipeline Endpoints ---

@app.get("/pipelines/capacity")
def get_pipeline_capacity(limit: int = 100, offset: int = 0, year: Optional[int] = None, pipeline: Optional[str] = None):
    try:
        con = get_db_connection()
        try:
            query = """
                SELECT 
                    year,
                    pipeline,
                    state_from,
                    state_to,
                    capacity_mmcfd
                FROM fact_pipeline_capacity
                WHERE 1=1
            """
            params = []
            
            if year:
                query += " AND year = ?"
                params.append(year)
                
            if pipeline:
                query += " AND pipeline ILIKE ?"
                params.append(f'%{pipeline}%')
                
            query += " ORDER BY year DESC, capacity_mmcfd DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            res = con.execute(query, params)
            cols = [desc[0] for desc in res.description]
            rows = [dict(zip(cols, row)) for row in res.fetchall()]
            
            # Get total count for pagination
            count_query = "SELECT COUNT(*) FROM fact_pipeline_capacity WHERE 1=1"
            count_params = []
            if year:
                count_query += " AND year = ?"
                count_params.append(year)
            if pipeline:
                count_query += " AND pipeline ILIKE ?"
                count_params.append(f'%{pipeline}%')
                
            total = con.execute(count_query, count_params).fetchone()[0]
            
            return {"data": rows, "total": total}
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /pipelines/capacity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipelines/details/{pipeline_id}")
def get_pipeline_details(pipeline_id: str):
    try:
        con = get_db_connection()
        try:
            # Get pipeline name
            meta = con.execute("SELECT pipeline_name FROM dim_pipelines WHERE pipeline_id = ?", [pipeline_id]).fetchone()
            if not meta:
                raise HTTPException(status_code=404, detail="Pipeline not found")
            
            # Get current segments (most recent year)
            max_year = con.execute("SELECT MAX(year) FROM fact_pipeline_capacity").fetchone()[0]
            
            segments = con.execute("""
                SELECT state_from, state_to, capacity_mmcfd
                FROM fact_pipeline_capacity
                WHERE regexp_replace(lower(pipeline), '[^a-z0-9]', '', 'g') = ? AND year = ?
                ORDER BY capacity_mmcfd DESC
            """, [pipeline_id, max_year]).fetchall()
            
            # Get history (total capacity over time)
            history = con.execute("""
                SELECT year, SUM(capacity_mmcfd) as total_capacity
                FROM fact_pipeline_capacity
                WHERE regexp_replace(lower(pipeline), '[^a-z0-9]', '', 'g') = ?
                GROUP BY year
                ORDER BY year
            """, [pipeline_id]).fetchall()
            
            return {
                "id": pipeline_id,
                "name": meta[0],
                "current_year": max_year,
                "segments": [{"from": s[0], "to": s[1], "capacity": s[2]} for s in segments],
                "history": [{"year": h[0], "capacity": h[1]} for h in history]
            }
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /pipelines/details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipelines/state/{state_code}")
def get_pipeline_state_details(state_code: str, year: Optional[int] = None):
    try:
        con = get_db_connection()
        try:
            # Default to max year if not specified
            if not year:
                year = con.execute("SELECT MAX(year) FROM fact_pipeline_capacity").fetchone()[0]

            # Get Inflows (Coming INTO state_code)
            inflows = con.execute("""
                SELECT 
                    state_from,
                    pipeline,
                    capacity_mmcfd
                FROM fact_pipeline_capacity
                WHERE state_to = ? AND year = ?
                ORDER BY state_from, capacity_mmcfd DESC
            """, [state_code, year]).fetchall()

            # Get Outflows (Going OUT OF state_code)
            outflows = con.execute("""
                SELECT 
                    state_to,
                    pipeline,
                    capacity_mmcfd
                FROM fact_pipeline_capacity
                WHERE state_from = ? AND year = ?
                ORDER BY state_to, capacity_mmcfd DESC
            """, [state_code, year]).fetchall()

            # Process into structured data
            inflow_map = {}
            total_in = 0
            for r in inflows:
                partner = r[0]
                if partner not in inflow_map:
                    inflow_map[partner] = {"total": 0, "pipelines": []}
                inflow_map[partner]["total"] += r[2]
                inflow_map[partner]["pipelines"].append({"name": r[1], "capacity": r[2]})
                total_in += r[2]

            outflow_map = {}
            total_out = 0
            for r in outflows:
                partner = r[0]
                if partner not in outflow_map:
                    outflow_map[partner] = {"total": 0, "pipelines": []}
                outflow_map[partner]["total"] += r[2]
                outflow_map[partner]["pipelines"].append({"name": r[1], "capacity": r[2]})
                total_out += r[2]

            return {
                "state": state_code,
                "year": year,
                "total_inflow": total_in,
                "total_outflow": total_out,
                "inflows": [{"state": k, "capacity": v["total"], "pipelines": v["pipelines"]} for k, v in inflow_map.items()],
                "outflows": [{"state": k, "capacity": v["total"], "pipelines": v["pipelines"]} for k, v in outflow_map.items()]
            }
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /pipelines/state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipelines/state/{state_code}/intrastate")
def get_intrastate_pipelines(state_code: str):
    try:
        con = get_db_connection()
        try:
            # Get intrastate pipelines for this state
            # Note: The 'states' column in dim_intrastate_pipelines might contain multiple states (e.g. "TX, OK")
            # We use ILIKE with wildcards to match
            pipelines = con.execute("""
                SELECT 
                    pipeline,
                    parent_company,
                    type,
                    capacity_mmcfd,
                    miles,
                    region
                FROM dim_intrastate_pipelines
                WHERE states ILIKE ? OR states ILIKE ? OR states ILIKE ? OR states = ?
                ORDER BY capacity_mmcfd DESC NULLS LAST
            """, [f'{state_code},%', f'%, {state_code},%', f'%, {state_code}', state_code]).fetchall()
            
            return [
                {
                    "pipeline": r[0],
                    "parent_company": r[1],
                    "type": r[2],
                    "capacity_mmcfd": r[3],
                    "miles": r[4],
                    "region": r[5]
                }
                for r in pipelines
            ]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /pipelines/state/{state_code}/intrastate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipelines/state/{state_code}/intrastate/graph")
def get_intrastate_graph(state_code: str):
    try:
        con = get_db_connection()
        try:
            # Nodes: State (Center), Parent Companies, Pipelines
            nodes = []
            links = []
            node_ids = set()

            # 1. Central State Node
            state_node_id = f"STATE_{state_code}"
            nodes.append({
                "id": state_node_id,
                "name": state_code,
                "group": "state",
                "val": 30,
                "fx": 0,
                "fy": 0
            })
            node_ids.add(state_node_id)

            # 2. Get Intrastate Pipelines
            pipelines = con.execute("""
                SELECT 
                    pipeline,
                    parent_company,
                    capacity_mmcfd,
                    miles
                FROM dim_intrastate_pipelines
                WHERE states ILIKE ? OR states ILIKE ? OR states ILIKE ? OR states = ?
            """, [f'{state_code},%', f'%, {state_code},%', f'%, {state_code}', state_code]).fetchall()

            for p in pipelines:
                p_name = p[0]
                parent = p[1]
                capacity = p[2] or 0
                miles = p[3] or 0
                
                # Pipeline Node
                p_node_id = f"PIPE_{p_name}"
                if p_node_id not in node_ids:
                    nodes.append({
                        "id": p_node_id,
                        "name": p_name,
                        "group": "pipeline",
                        "val": 10 + (miles / 100) if miles else 10,
                        "capacity": capacity,
                        "miles": miles
                    })
                    node_ids.add(p_node_id)

                # Link Pipeline -> State
                links.append({
                    "source": p_node_id,
                    "target": state_node_id,
                    "type": "INTRASTATE",
                    "value": 2
                })

                # Parent Company Node (if exists)
                if parent:
                    parent_node_id = f"CORP_{parent}"
                    if parent_node_id not in node_ids:
                        nodes.append({
                            "id": parent_node_id,
                            "name": parent,
                            "group": "company",
                            "val": 20
                        })
                        node_ids.add(parent_node_id)
                    
                    # Link Parent -> Pipeline
                    links.append({
                        "source": parent_node_id,
                        "target": p_node_id,
                        "type": "OWNERSHIP",
                        "value": 1
                    })

            return {"nodes": nodes, "links": links}
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /pipelines/state/{state_code}/intrastate/graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipelines/state/{state_code}/intrastate")
def get_intrastate_pipelines(state_code: str):
    try:
        con = get_db_connection()
        try:
            # Get intrastate pipelines for this state
            # Note: The 'states' column in dim_intrastate_pipelines might contain multiple states (e.g. "TX, OK")
            # We use ILIKE with wildcards to match
            pipelines = con.execute("""
                SELECT 
                    pipeline,
                    parent_company,
                    type,
                    capacity_mmcfd,
                    miles,
                    region
                FROM dim_intrastate_pipelines
                WHERE states ILIKE ? OR states ILIKE ? OR states ILIKE ? OR states = ?
                ORDER BY capacity_mmcfd DESC NULLS LAST
            """, [f'{state_code},%', f'%, {state_code},%', f'%, {state_code}', state_code]).fetchall()
            
            return [
                {
                    "pipeline": r[0],
                    "parent_company": r[1],
                    "type": r[2],
                    "capacity_mmcfd": r[3],
                    "miles": r[4],
                    "region": r[5]
                }
                for r in pipelines
            ]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /pipelines/state/{state_code}/intrastate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipelines/state/{state_code}/intrastate/map")
def get_intrastate_map_data(state_code: str):
    try:
        con = get_db_connection()
        try:
            # Install spatial extension if needed (it should be loaded, but safe to ensure)
            con.execute("INSTALL spatial; LOAD spatial;")
            
            # Get pipeline geometries that intersect with the state
            # We don't have a state boundary table yet, so we'll rely on the 'states' column in dim_intrastate_pipelines
            # to filter the operators, then join with spatial_pipelines.
            # This is an approximation: "Show me all physical pipes owned by companies that operate in this state"
            
            # 1. Get operators in this state
            operators = con.execute("""
                SELECT DISTINCT parent_company, pipeline
                FROM dim_intrastate_pipelines
                WHERE states ILIKE ? OR states ILIKE ? OR states ILIKE ? OR states = ?
            """, [f'{state_code},%', f'%, {state_code},%', f'%, {state_code}', state_code]).fetchall()
            
            operator_names = [o[1] for o in operators if o[1]] # Use pipeline name as operator match
            
            if not operator_names:
                return {"type": "FeatureCollection", "features": []}
                
            # 2. Get geometry for these operators
            # We use ST_AsGeoJSON to return standard GeoJSON
            placeholders = ','.join(['?'] * len(operator_names))
            query = f"""
                SELECT ST_AsGeoJSON(geom) as geometry, operator, typepipe, status
                FROM spatial_pipelines
                WHERE operator IN ({placeholders})
            """
            
            features = con.execute(query, operator_names).fetchall()
            
            geojson_features = []
            for f in features:
                geom = json.loads(f[0])
                geojson_features.append({
                    "type": "Feature",
                    "geometry": geom,
                    "properties": {
                        "operator": f[1],
                        "type": f[2],
                        "status": f[3]
                    }
                })
                
            return {
                "type": "FeatureCollection",
                "features": geojson_features
            }
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /pipelines/state/{state_code}/intrastate/map: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/spatial/compressors")
def get_compressor_stations(state_code: Optional[str] = None):
    try:
        con = get_db_connection()
        try:
            con.execute("INSTALL spatial; LOAD spatial;")
            query = "SELECT ST_AsGeoJSON(geom), * EXCLUDE (geom) FROM spatial_compressors"
            params = []
            
            if state_code:
                # Assuming there's a state column. Let's check columns first or use spatial intersection if needed.
                # Inspecting columns from ingestion... usually 'state' or 'STATE'
                # For safety, we'll return all for now or filter in python if volume is low (1700 is low).
                # But let's try to be smart.
                pass

            # Since we don't know exact column names for state without checking, 
            # and 1700 points is small, we'll return all and let frontend filter if needed,
            # OR we can just return all for the map.
            
            res = con.execute(query).fetchall()
            
            features = []
            cols = [d[0] for d in con.execute("DESCRIBE spatial_compressors").fetchall() if d[0] != 'geom']
            
            for r in res:
                geom = json.loads(r[0])
                props = dict(zip(cols, r[1:]))
                features.append({
                    "type": "Feature",
                    "geometry": geom,
                    "properties": props
                })
                
            return {"type": "FeatureCollection", "features": features}
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /spatial/compressors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/spatial/storage")
def get_storage_fields(state_code: Optional[str] = None):
    try:
        con = get_db_connection()
        try:
            con.execute("INSTALL spatial; LOAD spatial;")
            query = "SELECT ST_AsGeoJSON(geom), * EXCLUDE (geom) FROM spatial_storage"
            
            res = con.execute(query).fetchall()
            
            features = []
            cols = [d[0] for d in con.execute("DESCRIBE spatial_storage").fetchall() if d[0] != 'geom']
            
            for r in res:
                geom = json.loads(r[0])
                props = dict(zip(cols, r[1:]))
                features.append({
                    "type": "Feature",
                    "geometry": geom,
                    "properties": props
                })
                
            return {"type": "FeatureCollection", "features": features}
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /spatial/storage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipelines/edge/{state_from}/{state_to}")
def get_pipeline_edge_details(state_from: str, state_to: str, year: Optional[int] = None):
    try:
        con = get_db_connection()
        try:
            # 1. Get total capacity for this edge
            query_total = """
                SELECT SUM(capacity_mmcfd) 
                FROM fact_pipeline_capacity 
                WHERE state_from = ? AND state_to = ?
            """
            params = [state_from, state_to]
            if year:
                query_total += " AND year = ?"
                params.append(year)
            else:
                # Default to max year if not specified
                max_year = con.execute("SELECT MAX(year) FROM fact_pipeline_capacity").fetchone()[0]
                query_total += " AND year = ?"
                params.append(max_year)
                
            total_capacity = con.execute(query_total, params).fetchone()[0] or 0
            
            # 2. Get individual pipelines on this edge
            query_pipelines = """
                SELECT 
                    pipeline,
                    regexp_replace(lower(pipeline), '[^a-z0-9]', '', 'g') as pipeline_id,
                    capacity_mmcfd
                FROM fact_pipeline_capacity
                WHERE state_from = ? AND state_to = ?
            """
            # Reuse params (they are the same)
            query_pipelines += " AND year = ?" # We know year is in params at index 2 (or added)
            
            # Re-build params for the second query to be safe
            p_params = [state_from, state_to]
            if year:
                p_params.append(year)
            else:
                max_year = con.execute("SELECT MAX(year) FROM fact_pipeline_capacity").fetchone()[0]
                p_params.append(max_year)
                
            query_pipelines += " ORDER BY capacity_mmcfd DESC"
            
            pipelines = con.execute(query_pipelines, p_params).fetchall()
            
            return {
                "state_from": state_from,
                "state_to": state_to,
                "total_capacity": total_capacity,
                "year": year or (p_params[-1] if not year else year),
                "pipelines": [
                    {
                        "name": p[0],
                        "id": p[1],
                        "capacity": p[2],
                        "share": (p[2] / total_capacity * 100) if total_capacity > 0 else 0
                    }
                    for p in pipelines
                ]
            }
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /pipelines/edge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipelines/graph")
def get_pipeline_graph(year: Optional[int] = None):
    try:
        con = get_db_connection()
        try:
            # Default to most recent year if not specified
            if not year:
                year = con.execute("SELECT MAX(year) FROM links_pipeline_capacity").fetchone()[0] or 2023

            # Nodes: States
            nodes = []
            links = []
            
            # Get states involved in pipelines
            states = con.execute("""
                SELECT DISTINCT state_code FROM dim_states
            """).fetchall()
            
            # --- Enrich Nodes with Production & Net Flow ---
            # 1. Total Production (Annual sum of monthly)
            # 2. Total Inflow (Sum of interstate receipts)
            # 3. Total Outflow (Sum of interstate deliveries)
            
            # Production
            prod_query = """
                SELECT state, SUM(value) as total_prod
                FROM fact_production_monthly
                WHERE EXTRACT(YEAR FROM date) = ?
                GROUP BY state
            """
            prod_data = dict(con.execute(prod_query, [year]).fetchall())
            
            # Flow (Inflow/Outflow)
            # Note: fact_interstate_flow_annual uses 'year' column
            flow_in_query = """
                SELECT to_state, SUM(value) as total_in
                FROM fact_interstate_flow_annual
                WHERE year = ?
                GROUP BY to_state
            """
            flow_in_data = dict(con.execute(flow_in_query, [year]).fetchall())
            
            flow_out_query = """
                SELECT from_state, SUM(value) as total_out
                FROM fact_interstate_flow_annual
                WHERE year = ?
                GROUP BY from_state
            """
            flow_out_data = dict(con.execute(flow_out_query, [year]).fetchall())
            
            for s in states:
                state_code = s[0]
                prod = prod_data.get(state_code, 0)
                inflow = flow_in_data.get(state_code, 0)
                outflow = flow_out_data.get(state_code, 0)
                
                net_flow = outflow - inflow # Positive = Net Exporter, Negative = Net Importer
                total_volume = prod + inflow # Total supply available
                
                nodes.append({
                    "id": state_code,
                    "name": state_code,
                    "group": "state",
                    "val": 10, # Base size, will be scaled in frontend
                    "metrics": {
                        "production": prod,
                        "inflow": inflow,
                        "outflow": outflow,
                        "net_flow": net_flow,
                        "total_volume": total_volume
                    }
                })
                
            # Edges: Pipeline capacity between states
            # Aggregated by state-to-state, BUT we also want the list of pipelines
            query = """
                SELECT 
                    state_from,
                    state_to,
                    SUM(capacity_mmcfd) as total_capacity,
                    COUNT(DISTINCT pipeline_id) as num_pipelines,
                    string_agg(DISTINCT pipeline_id, ',') as pipeline_ids
                FROM links_pipeline_capacity
                WHERE year = ?
                GROUP BY state_from, state_to
            """
            
            edges = con.execute(query, [year]).fetchall()
            
            # Get Flow for Edges to calculate utilization
            # Flow is annual MMcf. Capacity is daily MMcf/d.
            # Utilization = (Flow / 365) / Capacity
            edge_flow_query = """
                SELECT from_state, to_state, value
                FROM fact_interstate_flow_annual
                WHERE year = ?
            """
            edge_flows = {} # (from, to) -> value
            try:
                flows = con.execute(edge_flow_query, [year]).fetchall()
                for f in flows:
                    edge_flows[(f[0], f[1])] = f[2]
            except:
                pass # Flow data might be missing for some years
            
            for e in edges:
                s_from = e[0]
                s_to = e[1]
                capacity = e[2]
                
                annual_flow = edge_flows.get((s_from, s_to), 0)
                daily_flow_avg = annual_flow / 365.0 if annual_flow else 0
                utilization = (daily_flow_avg / capacity) if capacity > 0 else 0
                
                links.append({
                    "source": s_from,
                    "target": s_to,
                    "capacity": capacity,
                    "pipelines": e[3],
                    "pipeline_ids": e[4].split(',') if e[4] else [],
                    "flow_annual": annual_flow,
                    "utilization": utilization
                })
                
            return {"nodes": nodes, "links": links}
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /pipelines/graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipelines/{pipeline_id}/financials")
def get_pipeline_financials(pipeline_id: str, year: Optional[int] = None):
    try:
        con = get_db_connection()
        try:
            # 1. Resolve pipeline_id (from spatial layer operator name) to company_id
            # pipeline_id here is the raw operator string from the map (e.g. "El Paso Natural Gas Co")
            
            # First, try exact match on operator_name
            # We use ILIKE for case-insensitivity
            link_query = """
                SELECT company_id, match_score, operator_name
                FROM links_pipeline_operators 
                WHERE operator_name ILIKE ?
                ORDER BY match_score DESC
                LIMIT 1
            """
            link = con.execute(link_query, [pipeline_id]).fetchone()
            
            if not link:
                # If not found in links table, try direct lookup in dim_companies just in case
                direct_query = "SELECT company_id, company_name FROM dim_companies WHERE company_name ILIKE ?"
                direct = con.execute(direct_query, [pipeline_id]).fetchone()
                if direct:
                    company_id = direct[0]
                    operator_name = direct[1]
                else:
                    raise HTTPException(status_code=404, detail=f"Financial link not found for pipeline: {pipeline_id}")
            else:
                company_id = link[0]
                operator_name = link[2]
            
            # 2. Get Financial Data (FERC Form 2)
            # Find the FERC Respondent ID for this company_id
            # We join dim_companies to ferc_respondents on name
            
            resp_query = """
                SELECT 
                    r.respondent_id, 
                    r.respondent_name,
                    c.company_name
                FROM dim_companies c
                JOIN ferc_respondents r ON c.company_name = r.respondent_name
                WHERE c.company_id = ?
                ORDER BY r.year DESC
                LIMIT 1
            """
            
            # Note: company_id is a VARCHAR in links table, but might be INT in dim_companies depending on schema.
            # We cast to VARCHAR to be safe if needed, or rely on duckdb's auto-cast.
            # Based on previous steps, company_id in dim_companies is INT (e.g. 123), but links table stores as VARCHAR.
            # Let's try casting.
            
            try:
                # Try with string ID
                resp = con.execute(resp_query, [str(company_id)]).fetchone()
                if not resp:
                    # Try with int ID
                    resp = con.execute(resp_query, [int(company_id)]).fetchone()
            except Exception:
                # Fallback if casting fails (e.g. company_id is a UUID string)
                resp = con.execute(resp_query, [str(company_id)]).fetchone()
            
            if not resp:
                # If we have a company ID but no respondent, return basic info
                comp_name = con.execute("SELECT company_name FROM dim_companies WHERE CAST(company_id AS VARCHAR) = ?", [str(company_id)]).fetchone()
                return {
                    "company_name": comp_name[0] if comp_name else pipeline_id,
                    "data_available": False,
                    "message": "Company found but no FERC Form 2 filings linked."
                }
                
            respondent_id = resp[0]
            respondent_name = resp[1]
            
            # 3. Get Financial Metrics
            # Default to max year if not provided
            if not year:
                max_year_res = con.execute("SELECT MAX(year) FROM ferc_income_statement WHERE respondent_id = ?", [respondent_id]).fetchone()
                year = max_year_res[0] if max_year_res else None
                
            if not year:
                 return {
                    "company_name": respondent_name,
                    "data_available": False,
                    "message": "No income statement data found."
                }

            # Key Metrics:
            # Op Rev (Row 200/201), Op Exp (Row 202/215), Net Income (Row 7800/78)
            # Note: Row numbers change over time. We need a robust query.
            # Modern (2000+): 
            #   Operating Revenues: 200
            #   Operating Expenses: 201
            #   Net Income: 7800
            
            metrics_query = """
                SELECT 
                    year,
                    SUM(CASE WHEN row_number = 200 THEN current_year_total ELSE 0 END) as op_revenues,
                    SUM(CASE WHEN row_number = 201 THEN current_year_total ELSE 0 END) as op_expenses,
                    SUM(CASE WHEN row_number = 7800 THEN current_year_total ELSE 0 END) as net_income
                FROM ferc_income_statement
                WHERE respondent_id = ? AND year = ?
                GROUP BY year
            """
            
            fin_data = con.execute(metrics_query, [respondent_id, year]).fetchone()
            
            if not fin_data:
                 return {
                    "company_name": respondent_name,
                    "respondent_id": respondent_id,
                    "year": year,
                    "data_available": False
                }

            return {
                "company_name": respondent_name,
                "respondent_id": respondent_id,
                "year": fin_data[0],
                "operating_revenues": fin_data[1],
                "operating_expenses": fin_data[2],
                "net_income": fin_data[3],
                "data_available": True
            }
            
        finally:
            con.close()
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Error in /pipelines/{pipeline_id}/financials: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipelines/financial-links")
def get_pipeline_financial_links():
    try:
        con = get_db_connection()
        try:
            # Return a map of operator_name -> company_id
            # This allows the frontend to know which pipelines have financial data
            links = con.execute("SELECT operator_name, company_id, match_score FROM links_pipeline_operators").fetchall()
            return {l[0]: {"company_id": l[1], "score": l[2]} for l in links}
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /pipelines/financial-links: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipelines/top")
def get_top_pipelines(year: Optional[int] = None, limit: int = 10):
    try:
        con = get_db_connection()
        try:
            query = """
                SELECT 
                    pipeline,
                    SUM(capacity_mmcfd) as total_capacity
                FROM fact_pipeline_capacity
                WHERE 1=1
            """
            params = []
            if year:
                query += " AND year = ?"
                params.append(year)
            else:
                max_year = con.execute("SELECT MAX(year) FROM fact_pipeline_capacity").fetchone()[0]
                query += " AND year = ?"
                params.append(max_year)
                
            query += " GROUP BY pipeline ORDER BY total_capacity DESC LIMIT ?"
            params.append(limit)
            
            res = con.execute(query, params).fetchall()
            return [{"name": r[0], "value": r[1]} for r in res]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /pipelines/top: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- AEO Endpoints ---

@app.get("/aeo/years")
def get_aeo_years():
    try:
        con = get_db_connection()
        try:
            years = con.execute("SELECT DISTINCT dataset FROM eia_series WHERE dataset LIKE 'AEO%' ORDER BY 1 DESC").fetchall()
            return [y[0] for y in years]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /aeo/years: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/aeo/scenarios/{dataset}")
def get_aeo_scenarios(dataset: str):
    try:
        con = get_db_connection()
        try:
            # Scenario is the 3rd part of the ID: AEO.<Year>.<Scenario>...
            scenarios = con.execute("""
                SELECT DISTINCT split_part(series_id, '.', 3) 
                FROM eia_series 
                WHERE dataset = ? 
                ORDER BY 1
            """, [dataset]).fetchall()
            return [s[0] for s in scenarios]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /aeo/scenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/aeo/search")
def search_aeo(dataset: str, scenario: Optional[str] = None, metric: Optional[str] = None, q: Optional[str] = None, limit: int = 50, offset: int = 0):
    try:
        con = get_db_connection()
        try:
            query = "SELECT series_id, name, units, frequency, start_date, end_date FROM eia_series WHERE dataset = ?"
            params = [dataset]
            
            if scenario and scenario != 'all':
                query += " AND split_part(series_id, '.', 3) = ?"
                params.append(scenario)
                
            if metric and metric != 'all':
                # Metric mapping based on 4th part prefix
                if metric == 'capacity':
                    query += " AND split_part(series_id, '.', 4) LIKE 'CAP_%'"
                elif metric == 'generation':
                    query += " AND split_part(series_id, '.', 4) LIKE 'GEN_%'"
                elif metric == 'emissions':
                    query += " AND split_part(series_id, '.', 4) LIKE 'EMI_%'"
                elif metric == 'price':
                    query += " AND split_part(series_id, '.', 4) LIKE 'PRCE_%'"
                elif metric == 'consumption':
                    query += " AND split_part(series_id, '.', 4) LIKE 'CNSM_%'"
            
            if q:
                query += " AND (name ILIKE ? OR series_id ILIKE ?)"
                params.extend([f'%{q}%', f'%{q}%'])
                
            query += " ORDER BY series_id LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            results = con.execute(query, params).fetchall()
            return [
                {
                    "series_id": r[0],
                    "name": r[1],
                    "unit": r[2],
                    "frequency": r[3],
                    "start_date": r[4],
                    "end_date": r[5]
                }
                for r in results
            ]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /aeo/search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Graph Endpoints ---

@app.get("/reference/us_states")
def get_us_states_geojson():
    try:
        file_path = os.path.abspath("data/reference/us_states.geojson")
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="US States GeoJSON not found")
            
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error in /reference/us_states: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph/snapshot")
def get_graph_snapshot(limit: int = 2000, year: Optional[int] = None):
    try:
        con = get_db_connection()
        try:
            nodes = []
            links = []
            node_ids = set()
            
            # 1. Get ALL Companies (up to limit)
            # We want to see the corporate structure, so we prioritize companies.
            companies = con.execute("SELECT company_id, company_name FROM dim_companies LIMIT ?", [limit]).fetchall()
            for c in companies:
                cid = f"C_{c[0]}"
                nodes.append({
                    "id": cid,
                    "name": c[1],
                    "group": "company",
                    "val": 20
                })
                node_ids.add(cid)
                
            # 2. Get Corporate Links (Affiliates)
            # These are Company <-> Company
            corp_links = con.execute("SELECT source_id, target_id, relation_type FROM links_corporate").fetchall()
            for l in corp_links:
                sid = f"C_{l[0]}"
                tid = f"C_{l[1]}"
                
                if sid in node_ids and tid in node_ids:
                    links.append({
                        "source": sid,
                        "target": tid,
                        "type": l[2] # AFFILIATE_552
                    })

            # 3. Get Plants (connected to these companies)
            # We only fetch plants that have an owner in our current node list
            # to avoid floating plants and keep the graph clean.
            
            plant_query = """
                SELECT DISTINCT p.plant_id, p.plant_name 
                FROM dim_plants p
                JOIN links_ownership lo ON p.plant_id = lo.plant_id
                WHERE 1=1
            """
            params = []
            
            if year:
                plant_query += " AND p.start_year <= ? AND p.end_year >= ?"
                params.extend([year, year])
            
            # We can't easily filter by "owner in node_ids" in SQL without a huge IN clause.
            # So we fetch a reasonable number of plants and filter in Python.
            plant_query += " LIMIT ?"
            params.append(limit) # Fetch up to limit plants
            
            plants = con.execute(plant_query, params).fetchall()
            
            for p in plants:
                pid = f"P_{p[0]}"
                nodes.append({
                    "id": pid,
                    "name": p[1],
                    "group": "plant",
                    "val": 10
                })
                node_ids.add(pid)
                
            # 4. Get Ownership Links (Company <-> Plant)
            own_links = con.execute("SELECT company_id, plant_id, match_type FROM links_ownership").fetchall()
            
            for l in own_links:
                cid = f"C_{l[0]}"
                pid = f"P_{l[1]}"
                
                if cid in node_ids and pid in node_ids:
                    links.append({
                        "source": cid,
                        "target": pid,
                        "type": l[2] # EXACT or FUZZY
                    })
                
            return {"nodes": nodes, "links": links}
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /graph/snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Production & Flow Endpoints ---

@app.get("/production/history")
def get_production_history(state_code: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None):
    try:
        con = get_db_connection()
        try:
            query = """
                SELECT date, state, value, unit
                FROM fact_production_monthly
                WHERE 1=1
            """
            params = []
            
            if state_code:
                query += " AND state = ?"
                params.append(state_code)
                
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
                
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
                
            query += " ORDER BY date ASC"
            
            res = con.execute(query, params).fetchall()
            return [
                {
                    "date": r[0],
                    "state": r[1],
                    "value": r[2],
                    "unit": r[3]
                }
                for r in res
            ]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /production/history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/flow/interstate")
def get_interstate_flow(year: Optional[int] = None, state_code: Optional[str] = None):
    try:
        con = get_db_connection()
        try:
            query = """
                SELECT year, from_state, to_state, value, unit
                FROM fact_interstate_flow_annual
                WHERE 1=1
            """
            params = []
            
            if year:
                query += " AND year = ?"
                params.append(year)
                
            if state_code:
                query += " AND (from_state = ? OR to_state = ?)"
                params.extend([state_code, state_code])
                
            query += " ORDER BY year DESC, value DESC"
            
            res = con.execute(query, params).fetchall()
            return [
                {
                    "year": r[0],
                    "from_state": r[1],
                    "to_state": r[2],
                    "value": r[3],
                    "unit": r[4]
                }
                for r in res
            ]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /flow/interstate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Financials / Transactions Endpoints ---

@app.get("/financials/gas/prices/history")
def get_gas_prices_history(location: Optional[str] = None):
    try:
        con = get_db_connection()
        try:
            query = """
                SELECT date, location, value, unit
                FROM fact_gas_prices_monthly
                WHERE 1=1
            """
            params = []
            if location:
                query += " AND location = ?"
                params.append(location)
            
            query += " ORDER BY date ASC"
            
            res = con.execute(query, params).fetchall()
            return [
                {
                    "date": r[0],
                    "location": r[1],
                    "value": r[2],
                    "unit": r[3]
                }
                for r in res
            ]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /financials/gas/prices/history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/financials/gas/prices/basis")
def get_gas_basis_map(year: int = 2023, month: int = 1):
    try:
        con = get_db_connection()
        try:
            # Get Henry Hub price for this month
            hh_query = """
                SELECT value 
                FROM fact_gas_prices_monthly 
                WHERE location = 'Henry Hub' 
                AND EXTRACT(YEAR FROM date) = ? 
                AND EXTRACT(MONTH FROM date) = ?
            """
            hh_price = con.execute(hh_query, [year, month]).fetchone()
            hh_val = hh_price[0] if hh_price else 0
            
            # Get Citygate prices
            cg_query = """
                SELECT location, value
                FROM fact_gas_prices_monthly
                WHERE type = 'Citygate'
                AND EXTRACT(YEAR FROM date) = ?
                AND EXTRACT(MONTH FROM date) = ?
            """
            cg_prices = con.execute(cg_query, [year, month]).fetchall()
            
            return {
                "henry_hub": hh_val,
                "states": [
                    {
                        "state": r[0],
                        "price": r[1],
                        "basis": r[1] - hh_val if hh_val else 0
                    }
                    for r in cg_prices
                ]
            }
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /financials/gas/prices/basis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/financials/gas/top-traders")
def get_gas_top_traders(year: Optional[int] = None, limit: int = 10):
    try:
        con = get_db_connection()
        try:
            # Default to latest year
            if not year:
                year = con.execute("SELECT MAX(CAST(Year_of_Report_End AS INTEGER)) FROM ferc_form552_master").fetchone()[0]
            
            query = """
                SELECT 
                    Respondent,
                    CAST(Volume_TBtu_Sales AS DOUBLE) as sales,
                    CAST(Volume_TBtu_Purchase AS DOUBLE) as purchases,
                    (CAST(Volume_TBtu_Sales AS DOUBLE) + CAST(Volume_TBtu_Purchase AS DOUBLE)) as total_volume
                FROM ferc_form552_master
                WHERE CAST(Year_of_Report_End AS INTEGER) = ?
                ORDER BY total_volume DESC
                LIMIT ?
            """
            
            res = con.execute(query, [year, limit]).fetchall()
            
            return {
                "year": year,
                "traders": [
                    {
                        "name": r[0],
                        "sales": r[1],
                        "purchases": r[2],
                        "total": r[3]
                    }
                    for r in res
                ]
            }
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /financials/gas/top-traders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/financials/gas/market-summary")
def get_gas_market_summary():
    try:
        con = get_db_connection()
        try:
            # Aggregate volume by year
            query = """
                SELECT 
                    CAST(Year_of_Report_End AS INTEGER) as year,
                    SUM(CAST(Volume_TBtu_Sales AS DOUBLE)) as total_sales,
                    SUM(CAST(Volume_TBtu_Purchase AS DOUBLE)) as total_purchases,
                    COUNT(*) as respondent_count
                FROM ferc_form552_master
                GROUP BY year
                ORDER BY year
            """
            
            res = con.execute(query).fetchall()
            
            return [
                {
                    "year": r[0],
                    "total_sales": r[1],
                    "total_purchases": r[2],
                    "respondent_count": r[3]
                }
                for r in res
            ]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /financials/gas/market-summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/financials/pipelines/rankings")
def get_pipeline_rankings(year: Optional[int] = None, limit: int = 10):
    try:
        con = get_db_connection()
        try:
            # Default to max year in income statement
            if not year:
                year = con.execute("SELECT MAX(year) FROM ferc_income_statement").fetchone()[0]
            
            # Row 200 = Gas Operating Revenues
            # Row 7800 = Net Income (Most recent years use 7800, older might use 7200/7400. We'll try 7800 first)
            
            query = """
                SELECT 
                    r.respondent_name,
                    MAX(CASE WHEN i.row_number = 200 THEN i.current_year_total ELSE 0 END) as operating_revenues,
                    MAX(CASE WHEN i.row_number = 7800 THEN i.current_year_total ELSE 0 END) as net_income
                FROM ferc_income_statement i
                JOIN ferc_respondents r ON i.respondent_id = r.respondent_id AND i.year = r.year
                WHERE i.year = ? AND i.row_number IN (200, 7800)
                GROUP BY r.respondent_name
                ORDER BY operating_revenues DESC
                LIMIT ?
            """
            
            res = con.execute(query, [year, limit]).fetchall()
            
            return {
                "year": year,
                "rankings": [
                    {
                        "name": r[0],
                        "operating_revenues": r[1],
                        "net_income": r[2]
                    }
                    for r in res
                ]
            }
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /financials/pipelines/rankings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Petroleum / COT / Rig Count Endpoints ---

@app.get("/financials/petroleum/prices")
def get_petroleum_prices(metric: str = "WTI Spot Price", start_date: Optional[str] = None):
    try:
        con = get_db_connection()
        try:
            query = """
                SELECT date, value, unit
                FROM fact_petroleum_metrics
                WHERE metric = ?
            """
            params = [metric]
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            
            query += " ORDER BY date ASC"
            
            res = con.execute(query, params).fetchall()
            return [{"date": r[0], "value": r[1], "unit": r[2]} for r in res]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /financials/petroleum/prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/financials/petroleum/stocks")
def get_petroleum_stocks(metric: str = "Crude Stocks Total", start_date: Optional[str] = None):
    try:
        con = get_db_connection()
        try:
            query = """
                SELECT date, value, unit
                FROM fact_petroleum_metrics
                WHERE metric = ?
            """
            params = [metric]
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            
            query += " ORDER BY date ASC"
            
            res = con.execute(query, params).fetchall()
            return [{"date": r[0], "value": r[1], "unit": r[2]} for r in res]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /financials/petroleum/stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/financials/petroleum/refining")
def get_refining_utilization(start_date: Optional[str] = None):
    try:
        con = get_db_connection()
        try:
            query = """
                SELECT date, value, unit
                FROM fact_petroleum_metrics
                WHERE metric = 'Refinery Utilization'
            """
            params = []
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            
            query += " ORDER BY date ASC"
            
            res = con.execute(query, params).fetchall()
            return [{"date": r[0], "value": r[1], "unit": r[2]} for r in res]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /financials/petroleum/refining: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/financials/petroleum/futures")
def get_futures_curve(date: Optional[str] = None):
    try:
        con = get_db_connection()
        try:
            # Get the curve for a specific date (or latest available)
            if not date:
                date = con.execute("SELECT MAX(date) FROM fact_petroleum_metrics WHERE metric LIKE 'WTI Futures Contract%'").fetchone()[0]
            
            query = """
                SELECT metric, value
                FROM fact_petroleum_metrics
                WHERE metric LIKE 'WTI Futures Contract%' AND date = ?
                ORDER BY metric
            """
            res = con.execute(query, [date]).fetchall()
            
            # Map metric name to contract number (1, 2, 3, 4)
            curve = []
            for r in res:
                contract_num = int(r[0].split(' ')[-1])
                curve.append({"contract": contract_num, "price": r[1]})
                
            return {"date": date, "curve": curve}
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /financials/petroleum/futures: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/financials/cot")
def get_cot_positioning(market: str = "CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE", start_date: Optional[str] = None):
    try:
        con = get_db_connection()
        try:
            # If market is generic "WTI", map it
            if market == "WTI":
                market = "CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE"
                
            query = """
                SELECT 
                    report_date,
                    open_interest,
                    prod_merc_long,
                    prod_merc_short,
                    managed_money_long,
                    managed_money_short,
                    (managed_money_long - managed_money_short) as managed_money_net
                FROM fact_cot_positions
                WHERE market_name = ?
            """
            params = [market]
            if start_date:
                query += " AND report_date >= ?"
                params.append(start_date)
                
            query += " ORDER BY report_date ASC"
            
            res = con.execute(query, params).fetchall()
            return [
                {
                    "date": r[0],
                    "open_interest": r[1],
                    "commercial_long": r[2],
                    "commercial_short": r[3],
                    "managed_money_long": r[4],
                    "managed_money_short": r[5],
                    "managed_money_net": r[6]
                }
                for r in res
            ]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /financials/cot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/financials/rig-count")
def get_rig_counts(basin: Optional[str] = None, start_date: Optional[str] = None):
    try:
        con = get_db_connection()
        try:
            query = """
                SELECT report_date, basin, total_rigs, oil_rigs, gas_rigs
                FROM fact_baker_hughes_rig_count
                WHERE 1=1
            """
            params = []
            if basin:
                query += " AND basin = ?"
                params.append(basin)
            else:
                # If no basin specified, maybe aggregate? Or return 'Total US RigCount' if it exists
                # The dataset has 'Total US RigCount' as a basin entry in historical, but what about recent?
                # In recent data, we pivoted. 'Total US RigCount' might not be a basin name.
                # Let's check if 'Total US RigCount' exists in the table.
                check = con.execute("SELECT 1 FROM fact_baker_hughes_rig_count WHERE basin = 'Total US RigCount' LIMIT 1").fetchone()
                if check:
                    query += " AND basin = 'Total US RigCount'"
                else:
                    # Aggregate
                    query = """
                        SELECT report_date, 'Total US' as basin, SUM(total_rigs), SUM(oil_rigs), SUM(gas_rigs)
                        FROM fact_baker_hughes_rig_count
                        WHERE 1=1
                    """
                    # We need to group by date
            
            if start_date:
                query += " AND report_date >= ?"
                params.append(start_date)
                
            if "GROUP BY" in query:
                query += " GROUP BY report_date"
                
            query += " ORDER BY report_date ASC"
            
            res = con.execute(query, params).fetchall()
            return [
                {
                    "date": r[0],
                    "basin": r[1],
                    "total": r[2],
                    "oil": r[3],
                    "gas": r[4]
                }
                for r in res
            ]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /financials/rig-count: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Transmission Endpoints ---

@app.get("/spatial/transmission-lines")
def get_transmission_lines(min_voltage: Optional[float] = None, max_voltage: Optional[float] = None, limit: int = 5000):
    try:
        con = get_db_connection()
        try:
            con.execute("INSTALL spatial; LOAD spatial;")
            
            query = """
                SELECT ST_AsGeoJSON(geom), VOLTAGE, VOLT_CLASS, OWNER, STATUS, TYPE, SUB_1, SUB_2
                FROM spatial_transmission_lines
                WHERE 1=1
            """
            params = []
            
            if min_voltage:
                query += " AND VOLTAGE >= ?"
                params.append(min_voltage)
                
            if max_voltage:
                query += " AND VOLTAGE <= ?"
                params.append(max_voltage)
                
            # Limit to avoid browser crash
            query += " LIMIT ?"
            params.append(limit)
            
            res = con.execute(query, params).fetchall()
            
            features = []
            for r in res:
                geom = json.loads(r[0])
                features.append({
                    "type": "Feature",
                    "geometry": geom,
                    "properties": {
                        "voltage": r[1],
                        "class": r[2],
                        "owner": r[3],
                        "status": r[4],
                        "type": r[5],
                        "sub_1": r[6],
                        "sub_2": r[7]
                    }
                })
                
            return {"type": "FeatureCollection", "features": features}
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /spatial/transmission-lines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/spatial/substations")
def get_substations(min_voltage: Optional[float] = None, state_code: Optional[str] = None):
    try:
        con = get_db_connection()
        try:
            con.execute("INSTALL spatial; LOAD spatial;")
            
            query = """
                SELECT ST_AsGeoJSON(geom), NAME, MAX_INFER, MIN_INFER, LINES, STATUS, TYPE
                FROM spatial_substations
                WHERE 1=1
            """
            params = []
            
            # Note: MAX_INFER/MIN_INFER are strings like "69", "138", etc. or "NOT AVAILABLE"
            # We might need to cast or handle them carefully if filtering.
            # For now, let's just return them and filter in frontend or add basic filtering if easy.
            
            if state_code:
                query += " AND STATE = ?"
                params.append(state_code)
                
            # Limit to avoid browser crash if no filter
            if not state_code and not min_voltage:
                query += " LIMIT 5000"
            
            res = con.execute(query, params).fetchall()
            
            features = []
            for r in res:
                geom = json.loads(r[0])
                features.append({
                    "type": "Feature",
                    "geometry": geom,
                    "properties": {
                        "name": r[1],
                        "max_voltage": r[2],
                        "min_voltage": r[3],
                        "lines": r[4],
                        "status": r[5],
                        "type": r[6]
                    }
                })
                
            return {"type": "FeatureCollection", "features": features}
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /spatial/substations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- ERCOT Endpoints ---

@app.get("/financials/ercot/lmp")
def get_ercot_lmp(settlement_point: Optional[str] = None, start_date: Optional[str] = None, limit: int = 1000):
    try:
        con = get_db_connection()
        try:
            query = """
                SELECT interval_start, settlement_point, settlement_point_type, price
                FROM fact_ercot_rtm_spp
                WHERE 1=1
            """
            params = []
            
            if settlement_point:
                query += " AND settlement_point = ?"
                params.append(settlement_point)
                
            if start_date:
                query += " AND interval_start >= ?"
                params.append(start_date)
            
            query += " ORDER BY interval_start DESC LIMIT ?"
            params.append(limit)
            
            res = con.execute(query, params).fetchall()
            return [
                {
                    "timestamp": r[0],
                    "settlement_point": r[1],
                    "type": r[2],
                    "price": r[3]
                }
                for r in res
            ]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /financials/ercot/lmp: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/financials/ercot/points")
def get_ercot_points():
    try:
        con = get_db_connection()
        try:
            points = con.execute("SELECT DISTINCT settlement_point, settlement_point_type FROM fact_ercot_rtm_spp ORDER BY settlement_point").fetchall()
            return [{"name": p[0], "type": p[1]} for p in points]
        finally:
            con.close()
    except Exception as e:
        logging.error(f"Error in /financials/ercot/points: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
