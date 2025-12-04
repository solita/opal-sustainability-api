# Compass Sustainability & Waste API

Víctor Manuel Ontiveros

A lightweight **FastAPI** service that generates deterministic mock sustainability KPIs for demo purposes.  
Designed for use with **Opal AI** tools and workflows (agents + tools + workflows).

---

## 🚀 Deploy with Docker

Build the image:

    docker build -t sustainability-api .

Run the container:

    docker run -p 8000:8000 sustainability-api

API will be available at:

    http://localhost:8000

OpenAPI docs:

    http://localhost:8000/docs

---

## 📡 Endpoints

### GET /health

Health probe.

**Example response:**

    { "status": "ok" }

---

### GET /sites

Returns a static list of mock Compass sites.

**Example response:**

    [
      {
        "site_id": "helsinki-hq",
        "name": "Helsinki Headquarters",
        "region": "Uusimaa",
        "segment": "workplace"
      },
      {
        "site_id": "espoo-campus",
        "name": "Espoo Campus Restaurant",
        "region": "Uusimaa",
        "segment": "school"
      }
    ]

Used for multi-site demos or potential Opal agent discovery.

---

### POST /get-kpis

Returns sustainability KPIs for a site and period.

**Request body:**

    {
      "site_id": "helsinki-hq",
      "period": "current"
    }

**Example response:**

    {
      "site_id": "helsinki-hq",
      "period": "current",
      "meals_served": 3250,
      "food_waste_kg": 210.5,
      "food_waste_per_meal_g": 64.8,
      "co2_per_meal_kg": 1.35,
      "vegetarian_share_percent": 32.4,
      "total_co2_kg": 4387.5
    }

Used by Opal’s **GetSiteKpis** tool.

---

### POST /compare-kpis

Compares KPIs between two periods and returns deltas and trend flags.

**Request body:**

    {
      "site_id": "helsinki-hq",
      "current_period": "current",
      "previous_period": "previous"
    }

**Example response:**

    {
      "site_id": "helsinki-hq",
      "current_period": "current",
      "previous_period": "previous",
      "current": { ... },
      "previous": { ... },
      "delta_food_waste_per_meal_g": -11.1,
      "delta_co2_per_meal_kg": -0.07,
      "delta_vegetarian_share_percent": 4.3,
      "waste_trend": "down",
      "co2_trend": "down",
      "vegetarian_trend": "up"
    }

Used by Opal’s **CompareSiteKpis** tool.

### 📘 Opal Tools Registry (`/opal-tools-registry`)

This API includes a special endpoint that allows **Opal** to automatically discover and register tools for use in AI workflows.  
Because the current Opal interface does not support adding individual tools manually, this endpoint provides a **tool registry manifest** that Opal can read and import.

The registry is exposed at: `GET /opal-tools-registry`

This endpoint returns a JSON document containing a `functions` array. Each entry describes a tool’s:

- **name**  
- **description**  
- **input parameters** (JSON Schema format)  
- **HTTP method and URL** (via the `x-opal-http` field)

Opal uses this information to automatically create tools such as:

- `ListSites` – fetch available Compass locations  
- `GetSiteKpis` – retrieve sustainability KPIs  
- `CompareSiteKpis` – compare KPIs across time periods  

These tools become available to Opal **agents** inside workflows, enabling them to call this API as part of their reasoning and execution steps.

This endpoint is specifically intended for Opal integration and is not required for general API use.

//TODO: document Opal Tool Registry further

---

## 📐 Architecture Diagram

Export your architecture diagram (API ↔ Render ↔ Opal tools/agents) as `architecture.png` and place it in the repo root, then reference it here:

    ![Architecture Diagram](architecture.png)

---

## 🧠 Technical Notes

- KPI generation is **deterministic** based on `site_id` + `period` (hash-based), giving stable outputs.
- Ideal for testing multi-step Opal workflows (analysis → recommendations → stakeholder communication).
- Simulates real sustainability metrics without requiring a live Compass data source.

---

## 🔧 Stack

- Python / FastAPI
- Uvicorn
- Docker
- Deployed on Render (Web Service, Docker runtime)

## 🔮 Future Opal Demo Usage

This API is designed to be reusable for future Opal demos beyond sustainability reporting.  
Because the data model is predictable and endpoints are cleanly structured, it can support:

- Multi-site workflows (regional comparisons, dashboards)  
- Additional agent roles (forecasts, anomaly detection, benchmarking)  
- Expanded KPI sets (energy, water, labor, menu-level emissions)  
- Instruction-framework experimentation (CLEAR, CRISPE, TRACE)  
- Demonstrations of Opal tools integrating with real HTTP APIs  

The API can easily grow as new demo scenarios appear, making it a flexible foundation for showcasing end-to-end automated workflows in Opal.