#!/bin/bash
# Script to start the API server

cd "$(dirname "$0")/.."

echo "Starting Agentic RAG API server..."
echo "API will be available at http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

