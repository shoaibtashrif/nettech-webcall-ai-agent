from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import os
import json
from datetime import datetime

router = APIRouter()

# Cromwell Cars API Configuration
CROMWELL_API_BASE = 'https://online.ontimechauffeurs.co.uk/api'
CABEE_API_BASE = 'https://capi.cabee-est.com/api'

# Pydantic models
class AddressValidationRequest(BaseModel):
    address_lines: Any  # Accept any type to handle AI mistakes
    postcode: Optional[str] = None
    building: Optional[str] = None

class PricingRequest(BaseModel):
    sourceAddress: str
    destinationAddress: str

class BookingRequest(BaseModel):
    operation: str
    companyId: Optional[str] = "99"
    jobNO: Optional[str] = None
    Phone: Optional[str] = None
    passengerName: Optional[str] = None
    passengerEmail: Optional[str] = None
    passengerPhone: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    date: Optional[str] = None
    vehicleTypeId: Optional[str] = None
    customerPrice: Optional[str] = None
    passengers: Optional[str] = None
    bags: Optional[str] = None
    note: Optional[str] = None

def get_jwt_token():
    """Get JWT token from environment"""
    token = os.getenv("CABEE_JWT_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="CABEE_JWT_TOKEN not configured")
    return token

def generate_call_id():
    """Generate a unique call ID for logging"""
    return f"call_{int(datetime.now().timestamp())}_{os.urandom(4).hex()}"

@router.post("/validateAddress")
async def validate_address(request: AddressValidationRequest):
    """Validate UK addresses using Cromwell Cars API with auto-retry on parameter errors"""
    
    call_id = generate_call_id()
    timestamp = datetime.now().isoformat()
    
    try:
        print(f"\n🔍 ===== ADDRESS VALIDATION TOOL CALLED =====")
        print(f"📅 Timestamp: {timestamp}")
        print(f"🆔 Call ID: {call_id}")
        print(f"📥 INCOMING REQUEST: {request.dict()}")
        
        # Parse address_lines if it's a string (auto-correct common AI mistakes)
        address_lines = request.address_lines
        if isinstance(address_lines, str):
            try:
                # Try to parse as JSON first
                address_lines = json.loads(address_lines)
                print(f"🔧 PARSED JSON STRING TO ARRAY: {request.address_lines} → {address_lines}")
            except json.JSONDecodeError:
                # If not JSON, treat as single address line
                address_lines = [address_lines]
                print(f"🔧 CONVERTED STRING TO ARRAY: {request.address_lines} → {address_lines}")
        
        # Ensure it's a proper list
        if not isinstance(address_lines, list):
            address_lines = [str(address_lines)]
            print(f"🔧 FORCED TO ARRAY: {address_lines}")
        
        request_payload = {
            "address_lines": address_lines,
            "postcode": request.postcode,
        }
        
        print(f"🌐 CALLING CROMWELL ADDRESS API:")
        print(f"   URL: {CROMWELL_API_BASE}/address/validate")
        print(f"   Payload: {json.dumps(request_payload, indent=2)}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CROMWELL_API_BASE}/address/validate",
                headers={"Content-Type": "application/json"},
                json=request_payload,
                timeout=30.0
            )
            
            print(f"📡 API Response Status: {response.status_code}")
            
            # Handle 422 validation errors by auto-correcting and retrying
            if response.status_code == 422:
                error_text = response.text
                print(f"⚠️ VALIDATION ERROR (422) - AUTO-CORRECTING: {error_text}")
                
                # Try alternative format - flatten address lines if they contain arrays
                if "list_type" in error_text and "address_lines" in error_text:
                    # Extract address components and flatten
                    flattened_lines = []
                    for line in address_lines:
                        if isinstance(line, list):
                            flattened_lines.extend([str(item) for item in line])
                        else:
                            flattened_lines.append(str(line))
                    
                    corrected_payload = {
                        "address_lines": flattened_lines,
                        "postcode": request.postcode,
                    }
                    
                    print(f"🔄 RETRYING WITH CORRECTED PAYLOAD: {json.dumps(corrected_payload, indent=2)}")
                    
                    # Retry with corrected format
                    retry_response = await client.post(
                        f"{CROMWELL_API_BASE}/address/validate",
                        headers={"Content-Type": "application/json"},
                        json=corrected_payload,
                        timeout=30.0
                    )
                    
                    if retry_response.is_success:
                        result = retry_response.json()
                        print(f"✅ AUTO-CORRECTION SUCCESSFUL")
                        print(f"📤 API RESPONSE DATA: {json.dumps(result, indent=2)}")
                        return result
                    else:
                        print(f"❌ RETRY ALSO FAILED: {retry_response.status_code}")
                        response = retry_response  # Use retry response for final error handling
            
            if not response.is_success:
                error_text = response.text
                print(f"❌ API Error: {response.status_code} - {error_text}")
                
                # Only show user-friendly errors for non-recoverable issues
                if response.status_code == 404:
                    return {
                        "success": False,
                        "error": "Address not found",
                        "candidates": []
                    }
                else:
                    # For other errors, return a generic message
                    return {
                        "success": False,
                        "error": "Unable to validate address at the moment",
                        "candidates": []
                    }
            
            result = response.json()
            print(f"📤 API RESPONSE DATA: {json.dumps(result, indent=2)}")
            print(f"✅ ADDRESS VALIDATION SUCCESS")
            print(f"🔍 Found {len(result.get('candidates', []))} address candidates")
            
            if result.get('candidates') and len(result['candidates']) > 0:
                print(f"📍 TOP ADDRESS CANDIDATE:")
                print(f"   Formatted: {result['candidates'][0].get('formatted')}")
                print(f"   Postcode: {result['candidates'][0].get('postcode')}")
            
            print(f"🔍 ===== ADDRESS VALIDATION COMPLETE =====\n")
            return result
            
    except httpx.RequestError as e:
        print(f"❌ ===== ADDRESS VALIDATION ERROR =====")
        print(f"🆔 Call ID: {call_id}")
        print(f"💥 REQUEST ERROR: {str(e)}")
        print(f"❌ ===== ADDRESS VALIDATION ERROR END =====\n")
        
        # Return user-friendly error instead of HTTP exception
        return {
            "success": False,
            "error": "Network error during address validation",
            "candidates": []
        }
    except Exception as e:
        print(f"❌ ===== ADDRESS VALIDATION ERROR =====")
        print(f"🆔 Call ID: {call_id}")
        print(f"💥 UNEXPECTED ERROR: {str(e)}")
        print(f"❌ ===== ADDRESS VALIDATION ERROR END =====\n")
        
        # Return user-friendly error instead of HTTP exception
        return {
            "success": False,
            "error": "Unable to validate address",
            "candidates": []
        }

@router.post("/checkPricing")
async def check_pricing(request: PricingRequest):
    """Check pricing using Make.com webhook"""
    
    call_id = generate_call_id()
    timestamp = datetime.now().isoformat()
    
    try:
        print(f"\n💰 ===== PRICING TOOL CALLED =====")
        print(f"📅 Timestamp: {timestamp}")
        print(f"🆔 Call ID: {call_id}")
        print(f"📥 INCOMING REQUEST: {request.dict()}")
        
        pricing_data = {
            "operation": "checkPricing",
            "companyId": "99",
            "sourceAddress": request.sourceAddress,
            "destinationAddress": request.destinationAddress
        }
        
        print(f"🌐 CALLING MAKE.COM WEBHOOK:")
        print(f"   URL: https://hook.eu2.make.com/7k8jjdhuqbuyywi3mkuwmm9rd6t1fpzi")
        print(f"   Payload: {json.dumps(pricing_data, indent=2)}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://hook.eu2.make.com/7k8jjdhuqbuyywi3mkuwmm9rd6t1fpzi",
                headers={"Content-Type": "application/json"},
                json=pricing_data,
                timeout=30.0
            )
            
            print(f"📡 Make.com Response Status: {response.status_code}")
            print(f"📋 Content-Type: {response.headers.get('content-type')}")
            
            if not response.is_success:
                print(f"❌ Make.com API Error: {response.status_code}")
                return {
                    "success": False,
                    "error": "Unable to get pricing at the moment",
                    "status": "api_error"
                }
            
            # Handle both JSON and text responses
            content_type = response.headers.get('content-type', '')
            
            if 'application/json' in content_type:
                result = response.json()
                print(f"📤 Make.com JSON Response: {json.dumps(result, indent=2)}")
            else:
                text_result = response.text
                print(f"📤 Make.com Text Response: {text_result}")
                
                if "Accepted" in text_result:
                    result = {
                        "success": True,
                        "message": "Pricing request accepted and processing",
                        "status": "accepted",
                        "webhook_response": text_result
                    }
                    print(f"✅ PRICING REQUEST ACCEPTED")
                else:
                    result = {
                        "success": False,
                        "error": "Unexpected response format",
                        "response": text_result
                    }
                    print(f"⚠️ UNEXPECTED RESPONSE FORMAT")
            
            print(f"💰 ===== PRICING TOOL COMPLETE =====\n")
            return result
            
    except httpx.RequestError as e:
        print(f"❌ ===== PRICING TOOL ERROR =====")
        print(f"🆔 Call ID: {call_id}")
        print(f"💥 REQUEST ERROR: {str(e)}")
        print(f"❌ ===== PRICING TOOL ERROR END =====\n")
        
        # Return user-friendly error instead of HTTP exception
        return {
            "success": False,
            "error": "Unable to get pricing at the moment",
            "status": "network_error"
        }
    except Exception as e:
        print(f"❌ ===== PRICING TOOL ERROR =====")
        print(f"🆔 Call ID: {call_id}")
        print(f"💥 UNEXPECTED ERROR: {str(e)}")
        print(f"❌ ===== PRICING TOOL ERROR END =====\n")
        
        # Return user-friendly error instead of HTTP exception
        return {
            "success": False,
            "error": "Unable to get pricing at the moment",
            "status": "system_error"
        }

@router.post("/bookCab")
async def book_cab(request: BookingRequest):
    """Handle all booking operations using Cabee APIs"""
    
    call_id = generate_call_id()
    timestamp = datetime.now().isoformat()
    jwt_token = get_jwt_token()
    
    try:
        print(f"\n🚖 ===== BOOKING TOOL CALLED =====")
        print(f"📅 Timestamp: {timestamp}")
        print(f"🆔 Call ID: {call_id}")
        print(f"📥 INCOMING REQUEST: {request.dict()}")
        print(f"🎯 OPERATION: {request.operation}")
        
        if request.operation == "cabBooking":
            return await handle_create_booking(request, jwt_token, call_id)
        elif request.operation == "getBooking":
            return await handle_get_booking(request, jwt_token, call_id)
        elif request.operation == "updateBooking":
            return await handle_update_booking(request, jwt_token, call_id)
        elif request.operation == "cancelBooking":
            return await handle_cancel_booking(request, jwt_token, call_id)
        elif request.operation == "getDriverLocation":
            return await handle_get_driver_location(request, jwt_token, call_id)
        else:
            return {
                "status": "error",
                "booking_status": "invalid_operation",
                "error": "Invalid operation requested",
                "data": None
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ===== BOOKING TOOL ERROR =====")
        print(f"🆔 Call ID: {call_id}")
        print(f"🎯 Failed Operation: {request.operation}")
        print(f"💥 UNEXPECTED ERROR: {str(e)}")
        print(f"❌ ===== BOOKING TOOL ERROR END =====\n")
        
        # Return user-friendly error instead of HTTP exception
        return {
            "status": "error",
            "booking_status": "system_error",
            "error": "System temporarily unavailable",
            "data": None
        }

async def handle_create_booking(request: BookingRequest, jwt_token: str, call_id: str):
    """Handle cab booking creation"""
    
    print(f"\n📝 === CREATE BOOKING OPERATION ===")
    
    # Vehicle type mapping
    vehicle_type_mapping = {
        'standard': 68,
        'estate': 69,
        'mpv': 70,
        'MPV': 70,
        'luxury': 71,
        'executive': 71
    }
    
    # Get numeric vehicle type ID
    numeric_vehicle_type_id = 68  # default to standard
    if request.vehicleTypeId:
        vehicle_type_lower = str(request.vehicleTypeId).lower()
        numeric_vehicle_type_id = vehicle_type_mapping.get(
            vehicle_type_lower, 
            vehicle_type_mapping.get(request.vehicleTypeId, 68)
        )
    
    # Use the user-provided phone number, prioritize passengerPhone over Phone
    user_phone = request.passengerPhone or request.Phone
    if not user_phone:
        print(f"⚠️ WARNING: No phone number provided, using fallback")
        user_phone = '03000000000'
    
    print(f"📞 Using phone number: {user_phone}")
    
    booking_data = {
        "id": 0,
        "jobNO": "string",
        "date": request.date or datetime.now().isoformat(),
        "passengerName": request.passengerName,
        "passengerPhone": user_phone,
        "passengerMobile": user_phone,
        "passengerEmail": request.passengerEmail,
        "passengers": int(request.passengers) if request.passengers else 1,
        "bags": int(request.bags) if request.bags else 0,
        "note": request.note or '',
        "companyId": 99,
        "driver_id": None,
        "paymentMethod_id": None,
        "driverPrice": float(request.customerPrice) if request.customerPrice else 0,
        "customerPrice": float(request.customerPrice) if request.customerPrice else 0,
        "duration": 0,
        "distance": 0,
        "jobSource": 3,
        "jobcase": 0,
        "vehicleTypeId": numeric_vehicle_type_id,
        "origin": request.origin,
        "destination": request.destination
    }
    
    print(f"🌐 CALLING CABEE CREATE BOOKING API:")
    print(f"   URL: {CABEE_API_BASE}/Job/CreateOnlineJob")
    print(f"   Vehicle Type Mapping: \"{request.vehicleTypeId}\" → {numeric_vehicle_type_id}")
    print(f"   Phone Number Used: {user_phone}")
    print(f"   Payload: {json.dumps(booking_data, indent=2)}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CABEE_API_BASE}/Job/CreateOnlineJob",
            headers={
                "accept": "text/plain",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {jwt_token}"
            },
            json=booking_data,
            timeout=30.0
        )
        
        print(f"📡 Cabee Response Status: {response.status_code}")
        
        if not response.is_success:
            error_text = response.text
            print(f"❌ CREATE BOOKING ERROR: {response.status_code} - {error_text}")
            
            # Return user-friendly error instead of HTTP exception
            return {
                "status": "error",
                "booking_status": "failed",
                "error": "Unable to create booking at the moment",
                "data": None
            }
        
        result = response.json()
        print(f"📤 CREATE BOOKING SUCCESS: {json.dumps(result, indent=2)}")
        print(f"✅ New Job Number: {result.get('jobNO')}")
        
        response_data = {
            "status": "success",
            "booking_status": "confirmed",
            "error": None,
            "data": {
                "jobNO": result.get("jobNO"),
                "bookingId": result.get("id"),
                "passengerName": result.get("passengerName"),
                "customerPrice": result.get("customerPrice"),
                "date": result.get("date"),
                "origin": result.get("origin"),
                "destination": result.get("destination"),
                "vehicleType": request.vehicleTypeId,
                "phoneNumber": user_phone
            }
        }
        
        print(f"📤 SENDING RESPONSE TO AI: {json.dumps(response_data, indent=2)}")
        return response_data

async def handle_get_booking(request: BookingRequest, jwt_token: str, call_id: str):
    """Handle getting booking details with job number cleaning"""
    
    print(f"📋 === GET BOOKING OPERATION ===")
    
    # Clean job number by removing dashes (A2-62 → A262)
    clean_job_no = None
    if request.jobNO:
        clean_job_no = request.jobNO.replace("-", "")
        if clean_job_no != request.jobNO:
            print(f"🔧 CLEANED JOB NUMBER: {request.jobNO} → {clean_job_no}")
        url = f"{CABEE_API_BASE}/Job/GetOnlineJobs?jobNO={clean_job_no}"
    elif request.Phone:
        url = f"{CABEE_API_BASE}/Job/GetOnlineJobs?phoneNumber={request.Phone}"
    else:
        return {
            "status": "error",
            "booking_status": "invalid_request",
            "error": "Either job number or phone number is required",
            "data": None
        }
    
    print(f"📤 GET BOOKING REQUEST: {url}")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={
                "accept": "text/plain",
                "Authorization": f"Bearer {jwt_token}"
            },
            timeout=30.0
        )
        
        print(f"📡 Get Response Status: {response.status_code}")
        
        if response.status_code == 404:
            return {
                "status": "error",
                "booking_status": "not_found",
                "error": "Booking not found",
                "data": None
            }
        
        if not response.is_success:
            error_text = response.text
            print(f"❌ GET BOOKING ERROR: {error_text}")
            
            # Return user-friendly error instead of HTTP exception
            return {
                "status": "error",
                "booking_status": "api_error",
                "error": "Unable to retrieve booking at the moment",
                "data": None
            }
        
        result = response.json()
        print(f"✅ GET BOOKING SUCCESS: {json.dumps(result, indent=2)}")
        
        return {
            "status": "success",
            "booking_status": "found",
            "error": None,
            "data": result
        }

async def handle_update_booking(request: BookingRequest, jwt_token: str, call_id: str):
    """Handle booking updates"""
    
    print(f"✏️ === UPDATE BOOKING OPERATION ===")
    
    update_data = {
        "id": request.jobNO,
        "companyId": 99,
        "passengerName": request.passengerName,
        "passengerPhone": request.Phone,
        "passengerEmail": request.passengerEmail,
        "passengers": int(request.passengers) if request.passengers else None,
        "date": request.date,
        "origin": request.origin,
        "destination": request.destination,
        "note": request.note
    }
    
    # Remove None values
    update_data = {k: v for k, v in update_data.items() if v is not None}
    
    print(f"📤 UPDATE REQUEST: {json.dumps(update_data, indent=2)}")
    
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{CABEE_API_BASE}/Job/UpdateJob",
            headers={
                "accept": "text/plain",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {jwt_token}"
            },
            json=update_data,
            timeout=30.0
        )
        
        print(f"📡 Update Response Status: {response.status_code}")
        
        if not response.is_success:
            error_text = response.text
            print(f"❌ UPDATE ERROR: {error_text}")
            raise HTTPException(
                status_code=500,
                detail=f"Update booking API error: {response.status_code} - {error_text}"
            )
        
        result = response.json()
        print(f"✅ UPDATE SUCCESS: {json.dumps(result, indent=2)}")
        
        return {
            "status": "success",
            "booking_status": "updated",
            "error": None,
            "data": result
        }

async def handle_cancel_booking(request: BookingRequest, jwt_token: str, call_id: str):
    """Handle booking cancellation with job number cleaning"""
    
    print(f"❌ === CANCEL BOOKING OPERATION ===")
    
    # Clean job number by removing dashes (A2-62 → A262)
    clean_job_no = None
    if request.jobNO:
        clean_job_no = request.jobNO.replace("-", "")
        if clean_job_no != request.jobNO:
            print(f"� eCLEANED JOB NUMBER: {request.jobNO} → {clean_job_no}")
        url = f"{CABEE_API_BASE}/Job/CancelJob?jobNo={clean_job_no}&companyId=99"
        print(f"🔍 Cancelling by job number: {clean_job_no}")
    elif request.Phone:
        url = f"{CABEE_API_BASE}/Job/CancelJob?mobile={request.Phone}&companyId=99"
        print(f"🔍 Cancelling by phone: {request.Phone}")
    else:
        return {
            "status": "error",
            "booking_status": "invalid_request",
            "error": "Either job number or phone number is required to cancel booking",
            "data": None
        }
    
    print(f"📤 CANCEL REQUEST URL: {url}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers={
                "accept": "text/plain",
                "Authorization": f"Bearer {jwt_token}"
            },
            content="",
            timeout=30.0
        )
        
        print(f"📡 Cancel Response Status: {response.status_code}")
        
        if not response.is_success:
            error_text = response.text
            print(f"❌ CANCEL ERROR: {error_text}")
            
            # Return user-friendly error instead of HTTP exception
            return {
                "status": "error",
                "booking_status": "api_error",
                "error": "Unable to cancel booking at the moment",
                "data": None
            }
        
        cancel_result = response.text
        print(f"✅ CANCEL RESPONSE TEXT: {cancel_result}")
        
        # Determine if cancellation was successful
        if any(phrase in cancel_result.lower() for phrase in ["not found", "notfound", "error"]):
            booking_status = "not_found"
            status = "error"
            error = "Booking not found"
        else:
            booking_status = "cancelled"
            status = "success"
            error = None
        
        print(f"🎯 FINAL STATUS: {status}, BOOKING_STATUS: {booking_status}")
        
        return {
            "status": status,
            "booking_status": booking_status,
            "error": error,
            "data": {
                "jobNO": clean_job_no or request.jobNO,
                "result": cancel_result
            }
        }

async def handle_get_driver_location(request: BookingRequest, jwt_token: str, call_id: str):
    """Handle getting driver location with job number cleaning"""
    
    print(f"📍 === GET DRIVER LOCATION OPERATION ===")
    
    if not request.jobNO:
        return {
            "status": "error",
            "booking_status": "invalid_request",
            "error": "Job number is required to get driver location",
            "data": None
        }
    
    # Clean job number by removing dashes (A2-62 → A262)
    clean_job_no = request.jobNO.replace("-", "")
    if clean_job_no != request.jobNO:
        print(f"🔧 CLEANED JOB NUMBER: {request.jobNO} → {clean_job_no}")
    
    print(f"📤 LOCATION REQUEST: Job {clean_job_no}")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CABEE_API_BASE}/Job/GetDriverCurrentLocationForJob/{clean_job_no}",
            headers={
                "accept": "text/plain",
                "Authorization": f"Bearer {jwt_token}"
            },
            timeout=30.0
        )
        
        print(f"📡 Location Response Status: {response.status_code}")
        
        if response.status_code == 404:
            return {
                "status": "error",
                "booking_status": "driver_not_found",
                "error": "Driver location not available or not assigned yet",
                "data": None
            }
        
        if not response.is_success:
            error_text = response.text
            print(f"❌ LOCATION ERROR: {error_text}")
            
            # Return user-friendly error instead of HTTP exception
            return {
                "status": "error",
                "booking_status": "api_error",
                "error": "Unable to get driver location at the moment",
                "data": None
            }
        
        result = response.json()
        print(f"✅ LOCATION SUCCESS: {json.dumps(result, indent=2)}")
        
        return {
            "status": "success",
            "booking_status": "driver_located",
            "error": None,
            "data": {
                "jobNO": clean_job_no,
                "location": result
            }
        }