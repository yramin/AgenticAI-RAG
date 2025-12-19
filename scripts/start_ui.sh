#!/bin/bash
# Script to start the Streamlit UI

cd "$(dirname "$0")/.."

echo "Starting Agentic RAG Streamlit UI..."
echo "UI will be available at http://localhost:8501"
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run ui/streamlit_app.py

