#!/usr/bin/env bash
set -e

ES=http://localhost:9200

echo "Waiting for Elasticsearch to be ready..."
until curl -s "${ES}" > /dev/null; do
  echo "Waiting for Elasticsearch..."
  sleep 2
done

echo "Creating index: analytics"
curl -X PUT "${ES}/analytics" -H 'Content-Type: application/json' -d @es-init/analytics_mapping.json

echo "Index 'analytics' created successfully!"