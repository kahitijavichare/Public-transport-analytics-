"""
Automated Test Suite for Public Transport Analytics
Tests data ingestion, flexible column detection, preprocessing, KPIs, and edge cases.
"""

import os
import pandas as pd
import numpy as np
from app import load_data, detect_columns, preprocess_data, calculate_kpis, generate_insights

def run_tests():
    print("==================================================")
    print("RUNNING AUTOMATED TEST SUITE")
    print("==================================================")

    # 1. Test Sample Data Loading
    print("[TEST 1] Loading sample dataset...")
    df_sample = load_data()
    assert df_sample is not None, "Failed to load sample dataset"
    assert len(df_sample) > 0, "Sample dataset is empty"
    print(f" -> PASSED: Loaded {len(df_sample)} rows, {len(df_sample.columns)} columns.")

    # 2. Test Column Detection
    print("[TEST 2] Testing dynamic column detection on sample data...")
    col_map = detect_columns(df_sample)
    print(f" -> Detected mappings: {col_map}")
    assert col_map["date"] == "date", f"Expected 'date', got {col_map['date']}"
    assert col_map["passenger_count"] == "passenger_count", f"Expected 'passenger_count', got {col_map['passenger_count']}"
    assert col_map["route"] == "route_name", f"Expected 'route_name', got {col_map['route']}"
    print(" -> PASSED: Key columns detected accurately.")

    # 3. Test Preprocessing Pipeline
    print("[TEST 3] Running preprocessing pipeline...")
    cleaned_df, audit = preprocess_data(df_sample, col_map)
    assert len(cleaned_df) > 0, "Cleaned df is empty"
    assert "_hour" in cleaned_df.columns, "_hour helper column missing"
    assert "_extracted_date" in cleaned_df.columns, "_extracted_date missing"
    print(f" -> PASSED: Cleaned {audit['final_rows']} rows, duplicates removed: {audit['duplicates_removed']}.")

    # 4. Test KPI Calculations
    print("[TEST 4] Calculating KPIs...")
    kpis = calculate_kpis(cleaned_df, col_map)
    print(f" -> KPIs computed: {kpis}")
    assert kpis["total_passengers"] > 0, "Total passengers should be > 0"
    assert kpis["total_trips"] == len(cleaned_df), "Trips count mismatch"
    assert kpis["total_revenue"] > 0, "Total revenue should be > 0"
    assert kpis["avg_delay"] is not None, "Average delay should be computed"
    print(" -> PASSED: All KPIs correctly computed from dataset.")

    # 5. Test Automated Insights
    print("[TEST 5] Generating automated insights...")
    insights = generate_insights(cleaned_df, col_map)
    assert len(insights) >= 4, f"Expected at least 4 insights, got {len(insights)}"
    for ins in insights:
        # Safely print without crashing on Windows cp1252
        print("    * " + ins.encode('ascii', errors='replace').decode('ascii'))
    print(" -> PASSED: Automated data-backed insights generated.")

    # 6. Test Edge Case: Missing Revenue Column (formula fallback)
    print("[TEST 6] Edge Case: Dataset with missing revenue column...")
    df_no_rev = df_sample.drop(columns=["revenue"])
    col_map_no_rev = detect_columns(df_no_rev)
    cleaned_no_rev, _ = preprocess_data(df_no_rev, col_map_no_rev)
    kpis_no_rev = calculate_kpis(cleaned_no_rev, col_map_no_rev)
    assert kpis_no_rev["total_revenue"] > 0, "Revenue fallback formula failed"
    print(f" -> PASSED: Estimated revenue computed using (Passengers * Fare) = Rs. {kpis_no_rev['total_revenue']:,.2f}")

    # 7. Test Edge Case: Missing Delay Column
    print("[TEST 7] Edge Case: Dataset with missing delay column...")
    df_no_delay = df_sample.drop(columns=["delay_minutes"])
    col_map_no_delay = detect_columns(df_no_delay)
    cleaned_no_delay, _ = preprocess_data(df_no_delay, col_map_no_delay)
    kpis_no_delay = calculate_kpis(cleaned_no_delay, col_map_no_delay)
    assert kpis_no_delay["avg_delay"] is None, "Delay should be None when absent"
    print(" -> PASSED: Gracefully handled absent delay column without crashing.")

    # 8. Test Edge Case: Empty Dataset
    print("[TEST 8] Edge Case: Empty dataset...")
    df_empty = pd.DataFrame(columns=["date", "passenger_count", "route_name"])
    col_map_empty = detect_columns(df_empty)
    cleaned_empty, _ = preprocess_data(df_empty, col_map_empty)
    kpis_empty = calculate_kpis(cleaned_empty, col_map_empty)
    assert kpis_empty["total_trips"] == 0
    assert kpis_empty["total_passengers"] == 0
    insights_empty = generate_insights(cleaned_empty, col_map_empty)
    assert len(insights_empty) > 0
    print(" -> PASSED: Empty dataset handled gracefully.")

    # 9. Test Ingesting cleaned_transport_survey.xlsx if present
    survey_file = r"C:\Users\Kunal Pol\cleaned_transport_survey.xlsx"
    if os.path.exists(survey_file):
        print("[TEST 9] Testing with external file: cleaned_transport_survey.xlsx...")
        df_survey = pd.read_excel(survey_file)
        col_map_survey = detect_columns(df_survey)
        cleaned_survey, audit_survey = preprocess_data(df_survey, col_map_survey)
        kpis_survey = calculate_kpis(cleaned_survey, col_map_survey)
        insights_survey = generate_insights(cleaned_survey, col_map_survey)
        print(f" -> PASSED: External survey processed without error ({audit_survey['final_rows']} rows).")

    print("==================================================")
    print("ALL TESTS PASSED SUCCESSFULLY! 100% HEALTHY.")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
