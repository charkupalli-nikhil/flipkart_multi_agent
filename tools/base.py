"""
Flipkart Sales Intelligence System - Base Tool Infrastructure
Provides data loading, caching, tool registry, and execution tracing.
"""

import os
import time
import functools
import pandas as pd
from typing import Callable, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

_DATA_CACHE = None

def get_data_path() -> str:
    path = os.getenv("DATA_PATH", "data/cleaned_flipkart.csv")
    if not os.path.exists(path):
        # Check parent or default
        if os.path.exists("data/cleaned_flipkart.csv"):
            return "data/cleaned_flipkart.csv"
        elif os.path.exists("data/flipkart_sales_enriched.csv"):
            from data.prepare_data import clean_and_profile_data
            clean_and_profile_data()
            return "data/cleaned_flipkart.csv"
    return path

def load_sales_data(reload: bool = False) -> pd.DataFrame:
    global _DATA_CACHE
    if _DATA_CACHE is None or reload:
        filepath = get_data_path()
        df = pd.read_csv(filepath)
        if "Order Date" in df.columns:
            df["Order Date"] = pd.to_datetime(df["Order Date"])
        _DATA_CACHE = df
    return _DATA_CACHE.copy()

TOOL_REGISTRY: Dict[str, Callable] = {}

def register_tool(name: str = None, description: str = ""):
    """Decorator to register a tool function in the global registry."""
    def decorator(func: Callable):
        tool_name = name or func.__name__
        func.__tool_name__ = tool_name
        func.__tool_description__ = description or (func.__doc__ or "").strip()
        TOOL_REGISTRY[tool_name] = func
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

def execute_tool_with_trace(tool_func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """Executes a registered tool, capturing execution timing, parameters, and results."""
    tool_name = getattr(tool_func, "__tool_name__", tool_func.__name__)
    start_time = time.time()
    try:
        result = tool_func(*args, **kwargs)
        elapsed = round(time.time() - start_time, 4)
        return {
            "tool": tool_name,
            "status": "success",
            "parameters": {"args": args, "kwargs": kwargs},
            "result": result,
            "execution_time_sec": elapsed,
            "error": None
        }
    except Exception as e:
        elapsed = round(time.time() - start_time, 4)
        return {
            "tool": tool_name,
            "status": "error",
            "parameters": {"args": args, "kwargs": kwargs},
            "result": None,
            "execution_time_sec": elapsed,
            "error": str(e)
        }
