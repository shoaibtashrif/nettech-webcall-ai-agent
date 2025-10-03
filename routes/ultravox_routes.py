from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import httpx
import os
from datetime import datetime
from dotenv import load_dotenv
from config.agent_config import ULTRAVOX_WEB_CALL_CONFIG

# Ensure environment variables are loaded
load_dotenv()

router = APIRouter()

# Pydantic models
class CallConfig(BaseModel):
    systemPrompt: str
    model: Optional[str] = "fixie-ai/ultravox"
    languageHint: Optional[str] = "en"
    selectedTools: Optional[List[Dict[str, Any]]] = []
    voice: Optional[str] = None
    temperature: Optional[float] = 0.3
    maxDuration: Optional[str] = None
    timeExceededMessage: Optional[str] = None

class UltravoxCallResponse(BaseModel):
    callId: str
    created: datetime
    ended: Optional[datetime] = None
    model: str
    systemPrompt: str
    temperature: float
    joinUrl: str

@router.post("/ultravox", response_model=UltravoxCallResponse)
async def create_ultravox_call(call_config: CallConfig):
    """Create a new Ultravox call with web-specific configuration"""
    
    ultravox_api_key = os.getenv("ULTRAVOX_API_KEY")
    print(f"🔑 API Key loaded: {ultravox_api_key[:10] if ultravox_api_key else 'None'}...")
    
    if not ultravox_api_key:
        raise HTTPException(status_code=500, detail="ULTRAVOX_API_KEY not configured")
    
    # Use the web-specific configuration
    config_data = ULTRAVOX_WEB_CALL_CONFIG.copy()
    
    # Override with any provided config
    if call_config.model:
        config_data["model"] = call_config.model
    if call_config.voice:
        config_data["voice"] = call_config.voice
    if call_config.temperature is not None:
        config_data["temperature"] = call_config.temperature
    if call_config.maxDuration:
        config_data["maxDuration"] = call_config.maxDuration
    if call_config.timeExceededMessage:
        config_data["timeExceededMessage"] = call_config.timeExceededMessage
    
    # Log the configuration being sent
    print(f"🤖 Creating Ultravox call with config:")
    print(f"   Model: {config_data.get('model')}")
    print(f"   Voice: {config_data.get('voice')}")
    print(f"   Temperature: {config_data.get('temperature')}")
    print(f"   Tools count: {len(config_data.get('selectedTools', []))}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.ultravox.ai/api/calls",
                headers={
                    "X-API-Key": ultravox_api_key,
                    "Content-Type": "application/json"
                },
                json=config_data,
                timeout=30.0
            )
            
            print(f"📡 Ultravox API Response Status: {response.status_code}")
            
            if response.status_code not in [200, 201]:
                error_text = response.text
                print(f"❌ Ultravox API Error: {response.status_code}")
                print(f"❌ Error Response: {error_text}")
                
                error_detail = f"Ultravox API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_detail += f" - {error_data}"
                except:
                    error_detail += f" - {error_text}"
                raise HTTPException(status_code=response.status_code, detail=error_detail)
            
            result = response.json()
            print(f"✅ Ultravox call created successfully: {result.get('callId')}")
            
            return UltravoxCallResponse(
                callId=result["callId"],
                created=datetime.fromisoformat(result["created"].replace("Z", "+00:00")),
                ended=datetime.fromisoformat(result["ended"].replace("Z", "+00:00")) if result.get("ended") else None,
                model=result["model"],
                systemPrompt=result["systemPrompt"],
                temperature=result["temperature"],
                joinUrl=result["joinUrl"]
            )
            
    except httpx.RequestError as e:
        print(f"❌ HTTP Request Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/config")
async def get_web_config():
    """Get the web-specific agent configuration"""
    return {
        "title": "Cromwell Cars Web Dispatcher",
        "overview": "Independent web interface for Cromwell Cars AI Dispatcher. This service has its own agent configuration separate from the Twilio phone service.",
        "callConfig": {
            "systemPrompt": ULTRAVOX_WEB_CALL_CONFIG["systemPrompt"],
            "model": ULTRAVOX_WEB_CALL_CONFIG["model"],
            "languageHint": "en",
            "selectedTools": ULTRAVOX_WEB_CALL_CONFIG["selectedTools"],
            "voice": ULTRAVOX_WEB_CALL_CONFIG["voice"],
            "temperature": ULTRAVOX_WEB_CALL_CONFIG["temperature"]
        }
    }