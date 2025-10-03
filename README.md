# Cromwell Cars Web Dispatcher - Python Service

An independent Python web interface for Cromwell Cars AI Dispatcher, completely separate from the Twilio phone service but using the same agent prompt and tools for consistent customer experience.

## 🚀 Features

- **Independent Service**: Completely separate from Twilio service with its own configuration
- **Same Agent Experience**: Uses identical prompt and tools as phone service
- **Python FastAPI Backend**: Modern, fast, and reliable
- **Web Voice Interface**: Browser-based voice calling with Ultravox
- **Real-time Transcripts**: Live conversation display
- **Cromwell Cars Integration**: Direct API integration for bookings

## 🏗️ Architecture

```
python-cromwell-web-dispatcher/
├── config/
│   ├── __init__.py
│   └── agent_config.py          # Independent agent configuration
├── routes/
│   ├── __init__.py
│   ├── ultravox_routes.py       # Ultravox API integration
│   └── cromwell_routes.py       # Cromwell Cars API tools
├── static/
│   └── index.html               # Web interface
├── main.py                      # FastAPI application
├── run.py                       # Application runner
├── requirements.txt             # Python dependencies
├── .env                         # Environment configuration
└── README.md                    # This file
```

## 🛠️ Setup

### 1. Install Dependencies

```bash
cd python-cromwell-web-dispatcher
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env` and update with your credentials:

```bash
# Ultravox Configuration
ULTRAVOX_API_KEY=your_ultravox_api_key

# Cromwell Cars API Configuration  
CABEE_JWT_TOKEN=your_cabee_jwt_token

# Tools Base URL (should point to this Python service)
TOOLS_BASE_URL=http://localhost:8000

# Server Configuration
PORT=8000
HOST=0.0.0.0
```

### 3. Run the Service

```bash
# Using the runner script
python run.py

# Or directly with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 🌐 Usage

1. **Web Interface**: Open `http://localhost:8000` in your browser
2. **Start Call**: Click "Start Call" to begin voice conversation with Alex
3. **Talk to Alex**: Speak naturally to book taxis, check bookings, etc.
4. **End Call**: Click "End Call" when finished

## 🔧 API Endpoints

### Web Interface
- `GET /` - Main web interface
- `GET /health` - Health check

### Ultravox Integration
- `POST /api/ultravox` - Create new voice call
- `GET /api/config` - Get agent configuration

### Cromwell Cars Tools
- `POST /cromwell/validateAddress` - Validate UK addresses
- `POST /cromwell/checkPricing` - Get journey pricing
- `POST /cromwell/bookCab` - Handle all booking operations

## 🤖 Agent Configuration

The agent uses the same system prompt and tools as the Twilio service but with independent configuration:

- **Name**: Alex
- **Role**: Cromwell Cars Dispatcher
- **Voice**: Emma (custom voice)
- **Tools**: Address validation, pricing, booking management
- **Medium**: Web (instead of Twilio)

## 🔄 Booking Operations

The service supports all booking operations:

1. **Create Booking** (`cabBooking`)
2. **Get Booking** (`getBooking`)
3. **Update Booking** (`updateBooking`)
4. **Cancel Booking** (`cancelBooking`)
5. **Driver Location** (`getDriverLocation`)

## 🚖 Vehicle Types

- **Standard Car (68)**: Up to 4 passengers
- **Estate Car (69)**: Extra luggage space
- **MPV (70)**: Up to 6 passengers
- **Luxury Vehicle (71)**: Premium comfort

## 🔒 Security

- Environment-based configuration
- JWT token authentication for Cromwell APIs
- CORS enabled for web interface
- Request validation with Pydantic models

## 📊 Monitoring

- Comprehensive logging for all operations
- Health check endpoint
- Request/response tracking
- Error handling and reporting

## 🆚 Differences from Twilio Service

| Feature | Twilio Service | Python Web Service |
|---------|----------------|-------------------|
| **Language** | Node.js | Python |
| **Interface** | Phone calls | Web browser |
| **Configuration** | Shared config file | Independent config |
| **Medium** | Twilio | Web |
| **Dependencies** | Twilio SDK | FastAPI + Ultravox |
| **Agent Prompt** | ✅ Same | ✅ Same |
| **Tools** | ✅ Same | ✅ Same |

## 🚀 Deployment

### Local Development
```bash
python run.py
```

### Production
```bash
# With Gunicorn
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# With Docker (create Dockerfile as needed)
docker build -t cromwell-web-dispatcher .
docker run -p 8000:8000 cromwell-web-dispatcher
```

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ULTRAVOX_API_KEY` | Ultravox API key | ✅ |
| `CABEE_JWT_TOKEN` | Cromwell Cars API token | ✅ |
| `TOOLS_BASE_URL` | Base URL for tools | ✅ |
| `PORT` | Server port | ❌ (default: 8000) |
| `HOST` | Server host | ❌ (default: 0.0.0.0) |

## 🤝 Contributing

This service is designed to be completely independent from the Twilio service while maintaining the same customer experience through identical prompts and tools.

## 📄 License

MIT License - Independent service for Cromwell Cars