#!/usr/bin/env python3
"""
Test script to demonstrate Universal Data Handler functionality.
"""

import requests
import json

BASE_URL = "http://localhost:8000"
CLIENT_ID = "client-techcorp-002"
USER_ID = "user-hr-manager-002"

def test_health():
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/health")
    print(f"Health Status: {response.json()}")
    print()

def test_tables():
    """Test available tables."""
    print("🔍 Testing available tables...")
    response = requests.get(f"{BASE_URL}/api/v1/tables", params={
        "client_id": CLIENT_ID,
        "user_id": USER_ID
    })
    data = response.json()
    print(f"Available Tables: {data['data']['total_tables']}")
    for table_name, table_info in data['data']['tables'].items():
        print(f"  - {table_name}: {table_info['columns']}")
    print()

def test_sql_query():
    """Test direct SQL query."""
    print("🔍 Testing SQL query...")
    sql = """
    SELECT department, 
           COUNT(*) as employee_count,
           AVG(salary) as avg_salary,
           MIN(salary) as min_salary,
           MAX(salary) as max_salary
    FROM structured_data.resource_9434a8d2_3760_432b_9e1e_ad23270e75d3 
    GROUP BY department 
    ORDER BY avg_salary DESC
    """
    
    response = requests.post(f"{BASE_URL}/api/v1/query/structured", json={
        "client_id": CLIENT_ID,
        "user_id": USER_ID,
        "sql_query": sql,
        "output_format": "json"
    })
    
    data = response.json()
    print("SQL Query Results:")
    for row in data['data']['results']:
        print(f"  {row['department']}: {row['employee_count']} employees, avg ${row['avg_salary']:,.0f}")
    print()

def test_smart_query():
    """Test smart query generation."""
    print("🔍 Testing smart query...")
    questions = [
        "Who are the highest paid employees?",
        "Which department has the most employees?",
        "Show me employees with performance scores above 4.0"
    ]
    
    for question in questions:
        response = requests.post(f"{BASE_URL}/api/v1/query/smart", params={
            "client_id": CLIENT_ID,
            "user_id": USER_ID,
            "question": question
        })
        
        data = response.json()
        if data['success']:
            print(f"Q: {question}")
            print(f"A: Found {data['data']['row_count']} results")
            if data['data']['results']:
                print(f"   Sample: {data['data']['results'][0]}")
        else:
            print(f"Q: {question}")
            print(f"A: Failed - {data.get('detail', 'Unknown error')}")
        print()

def test_natural_language():
    """Test natural language processing."""
    print("🔍 Testing natural language queries...")
    questions = [
        "Show me employee information",
        "What departments do we have?",
        "List all resources available"
    ]
    
    for question in questions:
        response = requests.post(f"{BASE_URL}/api/v1/query/natural", json={
            "client_id": CLIENT_ID,
            "user_id": USER_ID,
            "question": question,
            "output_format": "json"
        })
        
        data = response.json()
        print(f"Q: {question}")
        if data['success']:
            print(f"A: {data['data']['explanation']}")
            if data['data']['results']:
                print(f"   Results: {len(data['data']['results'])} items")
        else:
            print(f"A: Failed")
        print()

if __name__ == "__main__":
    print("🚀 Universal Data Handler Functionality Test")
    print("=" * 50)
    
    test_health()
    test_tables()
    test_sql_query()
    test_smart_query()
    test_natural_language()
    
    print("✅ Test completed!")