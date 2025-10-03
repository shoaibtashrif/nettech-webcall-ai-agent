from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from routes.ultravox_routes import router as ultravox_router
from routes.cromwell_routes import router as cromwell_router

app = FastAPI(
    title="Cromwell Cars Web Dispatcher",
    description="Python web interface for Cromwell Cars AI Dispatcher",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(ultravox_router, prefix="/api")
app.include_router(cromwell_router, prefix="/cromwell")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main web interface"""
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "cromwell-web-dispatcher"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Starting Cromwell Cars Web Dispatcher on {host}:{port}")
    print(f"📱 Web interface: http://{host}:{port}")
    print(f"🔧 API docs: http://{host}:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )