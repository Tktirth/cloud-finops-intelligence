"""
Database Layer — SQLite-backed singleton for billing data.
Loads synthetic data once, caches normalized DataFrames in memory.
"""

import os
import pandas as pd
from functools import lru_cache
from data.generator import load_or_generate
from data.normalizer import normalize, aggregate_daily, aggregate_by_provider_service, aggregate_by_team, get_summary_stats


import os
import pandas as pd
import gc
from data.generator import load_or_generate
from data.normalizer import normalize, aggregate_daily, aggregate_by_provider_service, aggregate_by_team, get_summary_stats


class DataStore:
    _instance = None

    def __init__(self):
        print("🚀 Initializing DataStore with memory optimization...")
        raw = load_or_generate()
        self.full = normalize(raw)
        
        # Aggressive memory cleanup: drop raw from local scope immediately
        del raw
        gc.collect()

        # Drop columns not needed for aggregation/UI to keep memory low
        cols_to_keep = [
            'date', 'provider', 'service', 'resource_key', 'category', 
            'team', 'cost_usd', 'pricing_model', 'is_anomaly', 
            'anomaly_id', 'environment'
        ]
        self.full = self.full[cols_to_keep]
        gc.collect()

        self.daily = aggregate_daily(self.full)
        self.by_provider_service = aggregate_by_provider_service(self.full)
        self.by_team = aggregate_by_team(self.full)
        self.summary = get_summary_stats(self.full)
        
        print(f"✅ DataStore initialized: {len(self.full):,} records. Stability optimized.")

    @classmethod
    def get(cls) -> "DataStore":
        if cls._instance is None:
            cls._instance = DataStore()
        return cls._instance


def get_store() -> DataStore:
    return DataStore.get()
