#!/usr/bin/env python3
"""
Cromwell Cars Web Dispatcher - Python Service
Independent web interface for Cromwell Cars AI Dispatcher
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main entry point"""
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print("🚖 ===== CROMWELL CARS WEB DISPATCHER =====")
    print(f"🐍 Python FastAPI Service")
    print(f"🌐 Independent from Twilio Service")
    print(f"🤖 Same Agent Prompt & Tools")
    print(f"📱 Web Interface: http://{host}:{port}")
    print(f"🔧 API Documentation: http://{host}:{port}/docs")
    print(f"❤️  Health Check: http://{host}:{port}/health")
    print("=" * 45)
    
    try:
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=True,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down Cromwell Cars Web Dispatcher...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()