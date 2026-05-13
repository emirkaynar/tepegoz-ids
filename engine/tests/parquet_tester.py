import pandas as pd
import os
import sys
import time
from typing import List

# Add engine directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.contracts import FlowRecord
from core.rules import RuleEngine

def run_parquet_test(parquet_dir: str, rules_path: str):
    print(f"--- Parquet Dataset Evaluator Starting ---")
    rule_engine = RuleEngine(config_path=rules_path)
    
    files = [f for f in os.listdir(parquet_dir) if f.endswith('.parquet')]
    if not files:
        print(f"No parquet files found in {parquet_dir}")
        return

    for filename in files:
        file_path = os.path.join(parquet_dir, filename)
        print(f"\nProcessing: {filename}")
        
        try:
            df = pd.read_parquet(file_path)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            continue

        print(f"Rows: {len(df)}")
        
        total_alerts = 0
        alert_counts = {}

        # Column mapping based on CIC-IDS-2017 CSV/Parquet conventions
        # Note: 'no-metadata' files usually lack IPs/Ports, using dummy values.
        for _, row in df.iterrows():
            # Build mock FlowRecord from tabular data
            flow = FlowRecord(
                flow_key="MOCKED_FLOW",
                start_time=time.time(),
                last_seen=time.time(),
                src_ip="0.0.0.0",
                dst_ip="0.0.0.0",
                src_port=0,
                dst_port=0,
                protocol=str(row.get('Protocol', '6')),
                packet_count=int(row.get('Total Fwd Packets', 0) + row.get('Total Backward Packets', 0)),
                byte_count=int(row.get('Fwd Packets Length Total', 0) + row.get('Bwd Packets Length Total', 0)),
                duration=float(row.get('Flow Duration', 0)) / 1000000.0, # CIC uses microseconds
                packets_per_second=float(row.get('Flow Packets/s', 0)),
                bytes_per_second=float(row.get('Flow Bytes/s', 0)),
                is_finalized=True,
                syn_count=int(row.get('SYN Flag Count', 0)),
                unique_dst_ports=set() # Metadata stripped in these files
            )
            
            alerts = rule_engine.evaluate(flow)
            if alerts:
                total_alerts += len(alerts)
                for a in alerts:
                    alert_counts[a.rule_name] = alert_counts.get(a.rule_name, 0) + 1

        print(f"Evaluation Complete for {filename}")
        print(f"Total Alerts Triggered: {total_alerts}")
        for rule, count in alert_counts.items():
            print(f" - {rule}: {count}")

if __name__ == "__main__":
    p_dir = "data/parquet"
    r_path = "config/rules.yaml"
    run_parquet_test(p_dir, r_path)
