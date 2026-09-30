"""
Unit tests for LangGraph Multi-Agent Orchestrator and Query Router.
"""

import pytest
from agents.orchestrator import process_query, route_query, check_out_of_scope

def test_route_query_classification():
    """Test 1: Intent router correctly identifies single and multi-agent flows."""
    # Sales
    assert route_query("What are the top 5 products by total sales?") == ["sales"]
    
    # Profit
    assert route_query("Show me profit margins across discount bands") == ["profit"]
    
    # Advisor
    assert route_query("Forecast revenue for the next 3 months") == ["advisor"]
    
    # Multi-Agent Chain
    combined = route_query("Which region is least profitable and what should we do about it?")
    assert combined == ["profit", "advisor"]

def test_multi_agent_sequential_execution():
    """Test 2: Combined profit + advisor query triggers both agents and synthesizes output."""
    state = process_query("Which region is least profitable and what should we do about it?")
    
    assert not state["is_out_of_scope"]
    assert "profit_optimization" in state["agent_results"]
    assert "business_advisor" in state["agent_results"]
    assert len(state["final_answer"]) > 50
    assert any(w in state["final_answer"] for w in ["Executive", "Summary", "Briefing", "Profit", "West", "Region"])

def test_out_of_scope_query_refusal():
    """Test 3: Query requesting review text is gracefully refused with boundary explanation."""
    state = process_query("Show me customer review text and sentiment for mobile phones")
    
    assert state["is_out_of_scope"] is True
    assert state["refusal_reason"] is not None
    assert "Query Outside Dataset Scope" in state["final_answer"]
    assert "no customer review text" in state["final_answer"]

def test_out_of_scope_customer_id_refusal():
    """Test 4: Query requesting customer IDs/names is rejected."""
    state = process_query("What is the name and phone number of the customer for order OD10001?")
    
    assert state["is_out_of_scope"] is True
    assert "Query Outside Dataset Scope" in state["final_answer"]

def test_trace_capture_and_kpis():
    """Test 5: Execution state captures complete timing and tool execution metadata."""
    state = process_query("Show me the total sales and revenue breakdown by category")
    
    assert len(state["tool_traces"]) > 0
    first_trace = state["tool_traces"][0]
    assert "agent" in first_trace
    assert "tool" in first_trace
    assert "execution_time_sec" in first_trace
    assert first_trace["status"] == "success"
