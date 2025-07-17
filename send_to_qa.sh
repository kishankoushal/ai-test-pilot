#!/bin/bash

# Path to your log file
LOG_FILE="pytest_output.log"

# Check if log file exists
if [ -f "$LOG_FILE" ]; then
  echo "Test log file found at $LOG_FILE"
  # Extract the last 200 lines to keep the most relevant error information
  LOG_CONTENT=$(tail -n 200 "$LOG_FILE")
else
  # If log file doesn't exist, provide an informative message
  echo "Warning: Test log file not found at $LOG_FILE"
  LOG_CONTENT="Test logs not found. Please run the tests first."
  exit 1
fi

# Properly escape the log content for JSON
LOG_CONTENT_ESCAPED=$(echo "$LOG_CONTENT" | jq -Rs .)

# Send to your webhook endpoint
echo "Sending logs to QA Assistant webhook..."


# curl -X POST http://44.247.131.46:30080/webhook/ \
#   -H "Content-Type: application/json" \
#   -d "$(jq -n --arg log "$LOG_CONTENT" --arg job_name "API-Inspector-local-test" --arg commit_sha "local-test" \
#     '{log: $log, job_name: $job_name, commit_sha: $commit_sha}')"


curl -X POST https://9517-2409-40c2-301d-d786-9dab-e442-c408-23aa.ngrok-free.app/webhook/ \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg log "$LOG_CONTENT" --arg job_name "API-Inspector-local-test" --arg commit_sha "local-test" \
    '{log: $log, job_name: $job_name, commit_sha: $commit_sha}')"