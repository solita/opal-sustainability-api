from fastapi import FastAPI, Body
from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Any
import math
import hashlib

app = FastAPI(
    title="Compass Sustainability & Waste API",
    description="Mock sustainability KPI API for Opal demo by Víctor Manuel Ontiveros",
    version="1.0.0",
)

# ----- models ----- #

Period = Literal["current", "previous", "last_month", "last_quarter"]


class SiteInfo(BaseModel):
    site_id: str
    name: str
    region: str
    segment: str  # workplace / school / healthcare / senior / logistics


MOCK_SITES: List[SiteInfo] = [
    SiteInfo(site_id="helsinki-hq", name="Helsinki Headquarters", region="Uusimaa", segment="workplace"),
    SiteInfo(site_id="espoo-campus", name="Espoo Campus Restaurant", region="Uusimaa", segment="school"),
    SiteInfo(site_id="vantaa-logistics", name="Vantaa Logistics Canteen", region="Uusimaa", segment="workplace"),
    SiteInfo(site_id="tampere-tech", name="Tampere Tech Park Kitchen", region="Pirkanmaa", segment="workplace"),
    SiteInfo(site_id="turku-hospital", name="Turku Hospital Cafeteria", region="Varsinais-Suomi", segment="healthcare"),
]

def _extract_parameters(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    enables support for both:
      - direct payload: {"site_id": "...", "period": "..."}
      - opal payload: {"parameters": {"site_id": "...", "period": "..."}}
    """
    if isinstance(body, dict) and "parameters" in body and isinstance(body["parameters"], dict):
        return body["parameters"]
    return body

class GetKpisRequest(BaseModel):
    site_id: str = Field(..., description="Identifier for the site/location")
    period: Period = Field(
        "current",
        description="Time range for KPIs (mocked: current, previous, last_month, last_quarter)",
    )


class SiteKpis(BaseModel):
    site_id: str
    period: Period
    meals_served: int
    food_waste_kg: float
    food_waste_per_meal_g: float
    co2_per_meal_kg: float
    vegetarian_share_percent: float
    total_co2_kg: float


class CompareKpisRequest(BaseModel):
    site_id: str
    current_period: Period = "current"
    previous_period: Period = "previous"


class DeltaKpis(BaseModel):
    site_id: str
    current_period: Period
    previous_period: Period

    # absolute values
    current: SiteKpis
    previous: SiteKpis

    # deltas
    delta_food_waste_per_meal_g: float
    delta_co2_per_meal_kg: float
    delta_vegetarian_share_percent: float

    # simple flags
    waste_trend: Literal["up", "down", "flat"]
    co2_trend: Literal["up", "down", "flat"]
    vegetarian_trend: Literal["up", "down", "flat"]

# ----- opal tool registry ----- #
@app.get("/opal-tool-registry")
async def opal_tool_registry() -> Dict[str, Any]:
    """
    discovery endpoint for Optimizely opal
    returns tool manifest in opal's expected format
    don't worry about this for now
    """
    return {
        "functions": [
            {
                "name": "list_sites",
                "description": (
                    "List all available Compass food service sites that can be used "
                    "in sustainability KPI analysis. Use this when the user wants "
                    "to browse or select a site."
                ),
                "parameters": [],  # no input parameters
                "endpoint": "/sites",          # relative path
                "http_method": "GET",
                "auth_requirements": []        # no auth for the demo
            },
            {
                "name": "get_site_kpis",
                "description": (
                    "Fetch sustainability KPIs (meals served, food waste, CO₂, "
                    "vegetarian share) for a given site and period. "
                    "Use this when the user wants the KPI numbers themselves."
                ),
                "parameters": [
                    {
                        "name": "site_id",
                        "type": "string",
                        "description": "ID of the site (e.g. 'helsinki-hq').",
                        "required": True
                    },
                    {
                        "name": "period",
                        "type": "string",
                        "description": (
                            "Time period to analyze: 'current', 'previous', "
                            "'last_month', or 'last_quarter'."
                        ),
                        "required": True
                    }
                ],
                "endpoint": "/get-kpis",       # relative path
                "http_method": "POST",
                "auth_requirements": []
            },
            {
                "name": "compare_site_kpis",
                "description": (
                    "Compare sustainability KPIs between two periods for a single site "
                    "and return deltas and trends. Use this when the user asks if "
                    "waste/CO₂/vegetarian share is getting better or worse."
                ),
                "parameters": [
                    {
                        "name": "site_id",
                        "type": "string",
                        "description": "ID of the site (e.g. 'helsinki-hq').",
                        "required": True
                    },
                    {
                        "name": "current_period",
                        "type": "string",
                        "description": "Current period (e.g. 'current').",
                        "required": True
                    },
                    {
                        "name": "previous_period",
                        "type": "string",
                        "description": "Previous period (e.g. 'previous').",
                        "required": True
                    }
                ],
                "endpoint": "/compare-kpis",
                "http_method": "POST",
                "auth_requirements": []
            }
        ]
    }


# ----- utility: deterministic mock generator ----- #

def _seed_from_site_and_period(site_id: str, period: str) -> int:
    key = f"{site_id}:{period}"
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def _pseudo_random(seed: int, min_val: float, max_val: float) -> float:
    x = math.sin(seed) * 10000
    frac = x - math.floor(x)
    return min_val + (max_val - min_val) * frac


def generate_mock_kpis(site_id: str, period: Period) -> SiteKpis:
    seed = _seed_from_site_and_period(site_id, period)

    meals_served = int(_pseudo_random(seed, 500.0, 5000.0))
    food_waste_kg = round(_pseudo_random(seed + 1, 50.0, 600.0), 1)

    if meals_served > 0:
        food_waste_per_meal_g = round((food_waste_kg * 1000) / meals_served, 1)
    else:
        food_waste_per_meal_g = 0.0

    co2_per_meal_kg = round(_pseudo_random(seed + 2, 0.3, 2.5), 2)
    vegetarian_share_percent = round(_pseudo_random(seed + 3, 10.0, 70.0), 1)
    total_co2_kg = round(co2_per_meal_kg * meals_served, 1)

    return SiteKpis(
        site_id=site_id,
        period=period,
        meals_served=meals_served,
        food_waste_kg=food_waste_kg,
        food_waste_per_meal_g=food_waste_per_meal_g,
        co2_per_meal_kg=co2_per_meal_kg,
        vegetarian_share_percent=vegetarian_share_percent,
        total_co2_kg=total_co2_kg,
    )


# ----- routes ----- #

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/sites", response_model=List[SiteInfo])
def list_sites():
    """
    returns sone mocked compass site locations
    for expanding the demo to multi-site workflows
    or showing how opal could look up available locations
    """
    return MOCK_SITES


@app.post("/get-kpis", response_model=SiteKpis)
def get_kpis(body: Dict[str, Any] = Body(...)):
    params = _extract_parameters(body)
    payload = GetKpisRequest(**params)  # validate

    return generate_mock_kpis(payload.site_id, payload.period)


@app.post("/compare-kpis", response_model=DeltaKpis)
def compare_kpis(body: Dict[str, Any] = Body(...)):
    params = _extract_parameters(body)
    payload = CompareKpisRequest(**params)  # Pydantic validation

    current = generate_mock_kpis(payload.site_id, payload.current_period)
    previous = generate_mock_kpis(payload.site_id, payload.previous_period)

    def trend(delta: float, threshold: float = 0.1) -> str:
        if delta > threshold:
            return "up"
        elif delta < -threshold:
            return "down"
        else:
            return "flat"

    delta_waste = round(current.food_waste_per_meal_g - previous.food_waste_per_meal_g, 1)
    delta_co2 = round(current.co2_per_meal_kg - previous.co2_per_meal_kg, 2)
    delta_veg = round(current.vegetarian_share_percent - previous.vegetarian_share_percent, 1)

    return DeltaKpis(
        site_id=payload.site_id,
        current_period=payload.current_period,
        previous_period=payload.previous_period,
        current=current,
        previous=previous,
        delta_food_waste_per_meal_g=delta_waste,
        delta_co2_per_meal_kg=delta_co2,
        delta_vegetarian_share_percent=delta_veg,
        waste_trend=trend(delta_waste, threshold=5.0),
        co2_trend=trend(delta_co2, threshold=0.05),
        vegetarian_trend=trend(delta_veg, threshold=2.0),
    )