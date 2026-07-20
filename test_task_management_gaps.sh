#!/bin/bash

# Test script for LexFlow-MVP Task Management gaps
# Run locally after deploying to test new endpoints

BASE_URL="${1:-http://localhost:5000}"
echo "Testing against: $BASE_URL"
echo ""

# Test data
TASK_DATA='{"title": "Review contract", "caseid": 1, "priority": "high", "assigned_to": 2, "duration_minutes": 30}'
CASE_DATA='{"title": "New case", "contactid": 1, "priority": "high", "eventid": null}'

echo "=== 1. POST /api/tasks - Create task with priority, assigned_to, duration ==="
curl -s -X POST "$BASE_URL/api/tasks" \
  -H "Content-Type: application/json" \
  -d "$TASK_DATA" | jq . 2>/dev/null || echo "(Failed - need JWT token)"

echo ""
echo "=== 2. PATCH /api/tasks/:id/complete - Mark task complete with actual_duration ==="
curl -s -X PATCH "$BASE_URL/api/tasks/1/complete" \
  -H "Content-Type: application/json" \
  -d '{"actual_duration_minutes": 45}' | jq . 2>/dev/null || echo "(Failed - need JWT token)"

echo ""
echo "=== 3. GET /api/tasks/export.csv - Export tasks as CSV ==="
curl -s -X GET "$BASE_URL/api/tasks/export.csv" \
  -H "Content-Type: text/csv" | head -5 || echo "(Failed - need JWT token)"

echo ""
echo "=== 4. POST /api/tasks/import - Import tasks from CSV ==="
# Create a sample CSV
cat > /tmp/tasks_sample.csv << 'CSV'
caseid,title,priority,assigned_to,duration_minutes
1,Draft complaint,high,2,120
1,Review docs,medium,3,60
2,Deposition,urgent,2,180
CSV

curl -s -X POST "$BASE_URL/api/tasks/import" \
  -F "file=@/tmp/tasks_sample.csv" | jq . 2>/dev/null || echo "(Failed - need JWT token)"

echo ""
echo "=== 5. POST /api/cases with eventid support ==="
curl -s -X POST "$BASE_URL/api/cases" \
  -H "Content-Type: application/json" \
  -d "$CASE_DATA" | jq . 2>/dev/null || echo "(Failed - need JWT token)"

echo ""
echo "=== 6. Health check - Verify server is running ==="
curl -s "$BASE_URL/health" | jq . 2>/dev/null || echo "(Server not responding)"

echo ""
echo "✅ Test script complete. Check results above."
