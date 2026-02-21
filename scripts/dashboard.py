import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import os
import shutil
import time

# Page Config
st.set_page_config(page_title="Commodity Data Explorer", layout="wide")

# Database Configuration
DB_PATH = 'data/commodity_data.duckdb'
DB_COPY_PATH = 'data/commodity_data_view.duckdb'

@st.cache_resource
def get_connection():
    """
    Connects to the database. 
    If the main DB is locked, it tries to copy it to a temp file and read that.
    """
    try:
        # Try connecting to the main DB in read-only mode
        con = duckdb.connect(DB_PATH, read_only=True)
        # Test a simple query to ensure we actually have access
        con.execute("SELECT 1")
        return con
    except Exception as e:
        st.warning(f"Main database is locked (likely ingestion running). Using a snapshot copy instead.")
        
        # Check if we need to refresh the copy (e.g., older than 5 minutes)
        should_copy = True
        if os.path.exists(DB_COPY_PATH):
            mtime = os.path.getmtime(DB_COPY_PATH)
            if time.time() - mtime < 300: # 5 minutes
                should_copy = False
        
        if should_copy:
            try:
                shutil.copy2(DB_PATH, DB_COPY_PATH)
            except Exception as copy_error:
                st.error(f"Could not copy database: {copy_error}")
                st.stop()
        
        return duckdb.connect(DB_COPY_PATH, read_only=True)

try:
    con = get_connection()
except Exception as e:
    st.error(f"Could not connect to database: {e}")
    st.stop()

# Sidebar - Dataset Selection
st.sidebar.title("Data Explorer")

# Get list of datasets
try:
    datasets_df = con.execute("SELECT DISTINCT dataset FROM eia_series ORDER BY dataset").fetchdf()
    datasets = datasets_df['dataset'].tolist()
except:
    datasets = []

if not datasets:
    st.warning("No datasets found in the database. Please run the ingestion script.")
    st.stop()

selected_dataset = st.sidebar.selectbox("Select Dataset", datasets)

# Main Content
st.title(f"Dataset: {selected_dataset}")

# Search/Filter Series
search_term = st.text_input("Search Series (Name or ID)", "")

query = f"""
    SELECT series_id, name, units, frequency, start_date, end_date 
    FROM eia_series 
    WHERE dataset = '{selected_dataset}'
"""

if search_term:
    query += f" AND (name ILIKE '%{search_term}%' OR series_id ILIKE '%{search_term}%')"

query += " LIMIT 1000"

series_df = con.execute(query).fetchdf()

st.dataframe(series_df, use_container_width=True, selection_mode="single-row", on_select="rerun")

# Series Detail View
series_ids = series_df['series_id'].tolist()

if series_ids:
    st.markdown("### Series Analysis")
    selected_series_id = st.selectbox("Select Series to Visualize", series_ids)
    
    if selected_series_id:
        # Get Metadata
        meta = con.execute(f"SELECT * FROM eia_series WHERE series_id = '{selected_series_id}'").fetchdf().iloc[0]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Name:** {meta['name']}")
            st.markdown(f"**Units:** {meta['units']}")
        with col2:
            st.markdown(f"**Frequency:** {meta['frequency']}")
            st.markdown(f"**Source:** {meta['source']}")
        with col3:
            st.markdown(f"**Start:** {meta['start_date']}")
            st.markdown(f"**End:** {meta['end_date']}")
            
        st.markdown(f"**Description:** {meta['description']}")

        # Get Data
        data_df = con.execute(f"""
            SELECT date, value 
            FROM eia_data 
            WHERE series_id = '{selected_series_id}' 
            ORDER BY date
        """).fetchdf()
        
        if not data_df.empty:
            # Plot
            fig = px.line(data_df, x='date', y='value', title=f"{meta['name']} ({meta['units']})")
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("View Raw Data"):
                st.dataframe(data_df)
        else:
            st.info("No time series data available for this series.")

else:
    st.info("No series found matching your criteria.")
