# Milestone 3.5: Parquet Dataset Evaluation

## Status
Completed

## What Changed
- **Dependencies:** Added `pandas`, `fastparquet`, and `pyarrow` to `engine/requirements-dev.txt`.
- **Parquet Tester:** Implemented `engine/tests/parquet_tester.py` to stream tabular CIC-IDS-2017 data directly into the `RuleEngine`.
- **Discovery:** Inspected Parquet columns and mapped them to the `FlowRecord` contract.
- **Evaluation:** Successfully processed all 8 dataset files in `data/parquet/`.

## Validation
- The `parquet_tester.py` script processed over 2.5 million flows in seconds.
- **Findings:** The "Volumetric Flood" rule triggered frequently across all datasets (including Benign), indicating that the default 1000 PPS threshold is likely too low for this specific high-speed dataset environment.

## Memory / Decisions Updated
- **Tabular Testing:** Confirmed that Parquet-based testing is exponentially faster than PCAP replay for logic and threshold validation.
