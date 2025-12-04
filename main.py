from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional, Literal, List
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
def opal_tool_registry():
    return {
        "version": "1.0",
        "functions": [
            {
                "name": "ListSites",
                "description": "Return all available Compass sites.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                # Opal-specific HTTP wiring
                "x-opal-http": {
                    "method": "GET",
                    "url": "https://opal-sustainability-api.onrender.com/sites"
                }
            },
            {
                "name": "GetSiteKpis",
                "description": "Return sustainability KPIs for the given site and period.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "site_id": {
                            "type": "string",
                            "description": "ID of the site (e.g. helsinki-hq)."
                        },
                        "period": {
                            "type": "string",
                            "description": "Time period (current, previous, last_month, last_quarter)."
                        }
                    },
                    "required": ["site_id", "period"]
                },
                "x-opal-http": {
                    "method": "POST",
                    "url": "https://opal-sustainability-api.onrender.com/get-kpis"
                }
            },
            {
                "name": "CompareSiteKpis",
                "description": "Compare sustainability KPIs between two periods for a site.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "site_id": {
                            "type": "string",
                            "description": "ID of the site (e.g. helsinki-hq)."
                        },
                        "current_period": {
                            "type": "string",
                            "description": "Current period (e.g. current)."
                        },
                        "previous_period": {
                            "type": "string",
                            "description": "Previous period (e.g. previous)."
                        }
                    },
                    "required": ["site_id", "current_period", "previous_period"]
                },
                "x-opal-http": {
                    "method": "POST",
                    "url": "https://opal-sustainability-api.onrender.com/compare-kpis"
                }
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
def get_kpis(payload: GetKpisRequest):
    """
    returns mocked sustainability KPIs for a given site and period,
    opal's GetSiteKpis tool will call this
    """
    return generate_mock_kpis(payload.site_id, payload.period)


@app.post("/compare-kpis", response_model=DeltaKpis)
def compare_kpis(payload: CompareKpisRequest):
    """
    compares KPIs between two periods for a given site,
    opal's CompareSiteKpis tool will call this endpoint
    """
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
