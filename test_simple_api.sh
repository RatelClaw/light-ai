#!/bin/bash
# Test script for Simple Analysis API

echo "🧪 Testing Simple Analysis API"
echo "================================"
echo ""

# Test 1: Health check
echo "1️⃣  Testing health endpoint..."
curl -s http://127.0.0.1:5000/health | python -m json.tool
echo ""
echo ""

# Test 2: Upload data
echo "2️⃣  Uploading test data..."
UPLOAD_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8000/api/v1/upload/json" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "123e4567-e89b-12d3-a456-426614174007",
    "json_data": {
      "student_profile": {
        "name": "Test Student",
        "program": "Computer Science",
        "gpa": 3.8,
        "interests": ["AI", "Machine Learning", "Data Science"]
      }
    },
    "resource_name": "test_student_data",
    "flatten": false
  }')

echo "$UPLOAD_RESPONSE" | python -m json.tool
echo ""
echo ""

# Test 3: Run analysis
echo "3️⃣  Running analysis..."
curl -s -X POST "http://127.0.0.1:5000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "123e4567-e89b-12d3-a456-426614174007",
    "query": "Extract persona characteristics and provide insights about this student"
  }' | python -m json.tool

echo ""
echo ""
echo "✅ Test complete!"
