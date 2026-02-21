import time
import json
import os
import sys

STATUS_FILE = 'data/ingestion_status.json'

def main():
    print("\n=== EIA Ingestion Monitor (Passive Mode) ===")
    print(f"Reading status from: {STATUS_FILE}")
    print("This monitor does NOT connect to the database, so it won't cause locks.")
    print("Press Ctrl+C to stop.\n")

    last_update_time = 0
    
    try:
        while True:
            if os.path.exists(STATUS_FILE):
                try:
                    with open(STATUS_FILE, 'r') as f:
                        status = json.load(f)
                    
                    # Only print if updated
                    if status['last_updated'] != last_update_time:
                        print(f"[{time.strftime('%H:%M:%S')}] "
                              f"Dataset: {status['current_dataset']:<15} | "
                              f"Progress: {status['datasets_processed']}/{status['total_datasets']} | "
                              f"Series: {status['series_count']:10,} | "
                              f"Rows: {status['rows_count']:12,}")
                        
                        if status['status'] == 'completed':
                            print("\nIngestion Completed Successfully!")
                            break
                            
                        last_update_time = status['last_updated']
                except Exception as e:
                    # Ignore read errors (race conditions)
                    pass
            else:
                print(f"[{time.strftime('%H:%M:%S')}] Waiting for ingestion to start...", end='\r')
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

if __name__ == "__main__":
    main()
