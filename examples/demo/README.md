# TinyGrid Demo Application

A lightweight demo webapp showcasing the TinyGrid SDK's features for accessing ERCOT grid data.

## Features

This demo application demonstrates:

- **Dashboard**: Real-time grid status, fuel mix visualization, and renewable generation gauges
- **Prices**: Settlement point prices (SPP) and locational marginal prices (LMP) with filtering
- **Forecasts**: System load and wind/solar generation forecasts
- **Historical**: Access to archived ERCOT data (>90 days old)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │Dashboard │  │  Prices  │  │Forecasts │  │Historical│    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │             │             │            │
│       └─────────────┴──────┬──────┴─────────────┘            │
│                            │                                  │
│                     TanStack Query                            │
└────────────────────────────┼────────────────────────────────┘
                             │ HTTP/JSON
┌────────────────────────────┼────────────────────────────────┐
│                    FastAPI Backend                           │
│                            │                                  │
│  ┌─────────────────────────┴─────────────────────────────┐  │
│  │                    TinyGrid SDK                        │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │  │
│  │  │  ERCOT     │  │  Dashboard │  │  ERCOTArchive  │  │  │
│  │  │  Client    │  │  Methods   │  │  (Historical)  │  │  │
│  │  └────────────┘  └────────────┘  └────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

**Option 1: Docker (Recommended)**
- Docker and Docker Compose

**Option 2: Local Development**
- Python 3.10+
- Node.js 18+
- TinyGrid SDK installed in your Python environment

## Quick Start with Docker

The easiest way to run the demo is with Docker:

### 1. Configure Environment

Create a `.env` file in the `examples/demo` directory:

```bash
cd examples/demo
cp .env.example .env
# Edit .env with your ERCOT credentials
```

### 2. Build and Run

```bash
docker compose up --build
```

This will:
- Build the backend (FastAPI + TinyGrid SDK)
- Build the frontend (React + Vite)
- Start both services

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Docker Commands

```bash
# Start in background
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Rebuild after code changes
docker compose up --build
```

## Local Development Setup

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt

# Make sure tinygrid is installed
pip install -e ../..
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 3. Start the Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API will be available at http://localhost:8000

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 4. Start the Frontend

In a new terminal:

```bash
cd frontend
npm run dev
```

The app will be available at http://localhost:5173

## API Endpoints

### Dashboard (No Auth Required)

These endpoints use ERCOT's public dashboard JSON and don't require authentication:

| Endpoint | Description |
|----------|-------------|
| `GET /api/status` | Current grid operating status |
| `GET /api/fuel-mix` | Generation by fuel type |
| `GET /api/renewable` | Wind and solar generation |
| `GET /api/supply-demand` | Supply vs demand data |

### Prices

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /api/spp` | Settlement point prices | `start`, `end`, `market`, `location_type`, `locations` |
| `GET /api/lmp` | Locational marginal prices | `start`, `end`, `market`, `location_type` |
| `GET /api/daily-prices` | Daily price summary | - |

### Forecasts

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /api/load` | System load data | `start`, `end`, `by` |
| `GET /api/wind-forecast` | Wind generation forecast | `start`, `end`, `resolution`, `by_region` |
| `GET /api/solar-forecast` | Solar generation forecast | `start`, `end`, `resolution`, `by_region` |

### Historical

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /api/historical/endpoints` | List available endpoints | - |
| `GET /api/historical` | Fetch archived data | `endpoint`, `start`, `end` |

## TinyGrid Features Demonstrated

| SDK Feature | Demo Component |
|-------------|----------------|
| `ercot.get_status()` | Grid status card on Dashboard |
| `ercot.get_fuel_mix()` | Fuel mix pie chart |
| `ercot.get_renewable_generation()` | Renewable gauges |
| `ercot.get_supply_demand()` | Supply/demand timeline |
| `ercot.get_spp()` | SPP table on Prices page |
| `ercot.get_lmp()` | LMP data on Prices page |
| `ercot.get_load()` | Load chart on Forecasts |
| `ercot.get_wind_forecast()` | Wind forecast chart |
| `ercot.get_solar_forecast()` | Solar forecast chart |
| `ERCOTArchive.fetch_historical()` | Historical data page |
| Rate limiting | Built into all API calls |
| Error handling | Error cards with retry |

## Configuration

### Authenticated Endpoints

Some endpoints (like SPP, LMP, and historical data) work best with ERCOT API authentication. To enable:

1. Register at https://apiexplorer.ercot.com to get a subscription key
2. Set up authentication in the backend:

```python
from tinygrid import ERCOT, ERCOTAuth, ERCOTAuthConfig

auth = ERCOTAuth(ERCOTAuthConfig(
    username="your-email@example.com",
    password="your-password",
    subscription_key="your-subscription-key",
))

ercot = ERCOT(auth=auth)
```

### Environment Variables

You can configure the backend using environment variables:

```bash
ERCOT_USERNAME=your-email@example.com
ERCOT_PASSWORD=your-password
ERCOT_SUBSCRIPTION_KEY=your-key
```

## Development

### Backend

```bash
cd backend
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm run dev     # Start dev server
npm run build   # Build for production
npm run preview # Preview production build
```

## Tech Stack

**Backend:**
- FastAPI
- TinyGrid SDK
- Pydantic

**Frontend:**
- React 18
- TypeScript
- Vite
- TanStack Query
- Recharts
- Tailwind CSS
- Lucide Icons

## License

This demo is part of the TinyGrid project. See the main repository for license information.
