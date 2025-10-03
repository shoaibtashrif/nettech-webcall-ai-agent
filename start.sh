#!/bin/bash

# Cromwell Cars Web Dispatcher - Python Service Startup Script

echo "🚖 ===== CROMWELL CARS WEB DISPATCHER ====="
echo "🐍 Starting Python FastAPI Service"
echo "🌐 Independent Web Interface"
echo "🤖 Same Agent Prompt & Tools as Twilio"
echo "=" * 45

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please create one based on .env.example"
    echo "📋 Required variables:"
    echo "   - ULTRAVOX_API_KEY"
    echo "   - CABEE_JWT_TOKEN"
    echo "   - TOOLS_BASE_URL"
    exit 1
fi

# Start the service
echo "🚀 Starting Cromwell Cars Web Dispatcher..."
echo "📱 Web Interface will be available at: http://localhost:8000"
echo "🔧 API Documentation at: http://localhost:8000/docs"
echo ""

python run.py