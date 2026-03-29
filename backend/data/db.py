"""
Database Layer — SQLite-backed singleton for billing data.
Loads synthetic data once, caches normalized DataFrames in memory.
"""

import os
import pandas as pd
from functools import lru_cache
from data.generator import load_or_generate
from data.normalizer import normalize, aggregate_daily, aggregate_by_provider_service, aggregate_by_team, get_summary_stats


class DataStore:
    _instance = None

    def __init__(self):
        raw = load_or_generate()
        self.full = normalize(raw)
        self.daily = aggregate_daily(self.full)
        self.by_provider_service = aggregate_by_provider_service(self.full)
        self.by_team = aggregate_by_team(self.full)
        self.summary = get_summary_stats(self.full)
        print(f"✅ DataStore initialized: {len(self.full):,} records, {len(self.daily):,} daily aggregates")

    @classmethod
    def get(cls) -> "DataStore":
        if cls._instance is None:
            cls._instance = DataStore()
        return cls._instance


def get_store() -> DataStore:
    return DataStore.get()
