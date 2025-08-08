#!/bin/bash
set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: $0 <path-to-config.ini>"
    echo "    example: $0 ./config.ini"
    exit 1
fi

CONFIG_FILE=$1

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found: $CONFIG_FILE"
    echo "Sad face :("
    exit 1
fi

# These should be defined if supabase integration is enabled
SUPABASE_USER_PASSWORD=$(grep -oP 'SUPABASE_USER_PASSWORD = \K.*' "$CONFIG_FILE")
SUPABASE_API_KEY=$(grep -oP 'SUPABASE_API_KEY = \K.*' "$CONFIG_FILE")
SUPABASE_URL=$(grep -oP 'SUPABASE_URL = \K.*' "$CONFIG_FILE")
SUPABASE_USER_EMAIL=$(grep -oP 'SUPABASE_USER_EMAIL = \K.*' "$CONFIG_FILE")
echo "SUPABASE variables loaded"

# This is needed for the barcode api to accept requests
# /barcode/<api_key>/<task_barcode_id>
BARCODE_API_KEY=$(grep -oP 'BARCODE_API_KEY = \K.*' "$CONFIG_FILE" || true)

if [ -z "$BARCODE_API_KEY" ]; then
    echo "Error: BARCODE_API_KEY not found in $CONFIG_FILE"
    exit 1
fi

echo "Config loaded maybe:"
echo "    SUPABASE_EMAIL: $SUPABASE_USER_EMAIL"
echo "    SUPABASE_URL: $SUPABASE_URL"
echo "Requests will be made to: http://localhost:3000/barcode/<BARCODE_API_KEY>/<task_barcode_id>"

echo "Starting container..."

RANDOM_TAG=$(date +%s)

docker build -t ts_api:${RANDOM_TAG} .

docker run -d --rm --name ts_api_${RANDOM_TAG} -p 3000:3000 \
    -e SUPABASE_USER_PASSWORD=${SUPABASE_USER_PASSWORD} \
    -e SUPABASE_API_KEY=${SUPABASE_API_KEY} \
    -e SUPABASE_URL=${SUPABASE_URL} \
    -e SUPABASE_USER_EMAIL=${SUPABASE_USER_EMAIL} \
    -e BARCODE_API_KEY=${BARCODE_API_KEY} \
    ts_api:${RANDOM_TAG}

echo "Container started with tag: ts_api_${RANDOM_TAG}"
echo "To stop the container, run: docker stop ts_api_${RANDOM_TAG}"