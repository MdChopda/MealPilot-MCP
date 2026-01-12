
import sys
import logging
from typing import Any, Dict, List, Optional, Union
import json
import requests
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP


# Logging (stderr only)

logger = logging.getLogger("meals_mcp")
handler = logging.StreamHandler(stream=sys.stderr)  # <-- stderr
handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Let `mcp dev` know what to install in the ephemeral env (optional)
dependencies = ["requests", "pydantic"]


# Constants
API_BASE = "https://www.themealdb.com/api/json/v1/1"
TIMEOUT = 15  # seconds
MAX_LIMIT = 25

# App
app = FastMCP("meals")


# Schemas (for return types)
class MealCard(BaseModel):
    id: str
    name: str
    area: Optional[str] = None
    category: Optional[str] = None
    thumb: Optional[str] = None

class IngredientMeasure(BaseModel):
    name: str
    measure: Optional[str] = None

class MealDetails(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    area: Optional[str] = None
    instructions: Optional[str] = None
    image: Optional[str] = None
    source: Optional[str] = None
    youtube: Optional[str] = None
    ingredients: List[IngredientMeasure] = Field(default_factory=list)

# HTTP helper

def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{API_BASE}{path}"
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.error(f"Network error calling {url}: {e}")
        raise RuntimeError(f"Network error calling TheMealDB: {e}") from e
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from {url}: {e}")
        raise RuntimeError(f"Invalid JSON from TheMealDB: {e}") from e


def _coerce_limit(limit: int, default_val: int) -> int:
    try:
        n = int(limit)
    except Exception:
        n = default_val
    return max(1, min(MAX_LIMIT, n))

# Shaping helpers

def _shape_search_meal(m: Dict[str, Any]) -> MealCard:
    return MealCard(
        id=str(m.get("idMeal", "")),
        name=m.get("strMeal", ""),
        area=m.get("strArea"),
        category=m.get("strCategory"),
        thumb=m.get("strMealThumb"),
    )


def _shape_filter_card(m: Dict[str, Any]) -> MealCard:
    return MealCard(
        id=str(m.get("idMeal", "")),
        name=m.get("strMeal", ""),
        area=None,
        category=None,
        thumb=m.get("strMealThumb"),
    )


def _shape_meal_details(m: Dict[str, Any]) -> MealDetails:
    ingredients: List[IngredientMeasure] = []
    for i in range(1, 21):
        name = (m.get(f"strIngredient{i}") or "").strip()
        measure = (m.get(f"strMeasure{i}") or "").strip()
        if name:
            ingredients.append(IngredientMeasure(name=name, measure=measure or None))

    return MealDetails(
        id=str(m.get("idMeal", "")),
        name=m.get("strMeal", ""),
        category=m.get("strCategory"),
        area=m.get("strArea"),
        instructions=m.get("strInstructions"),
        image=m.get("strMealThumb"),
        source=m.get("strSource"),
        youtube=m.get("strYoutube"),
        ingredients=ingredients,
    )


# Tools

@app.tool()
def search_meals_by_name(
    query: str = Field(..., description="Search text for meal names (e.g., 'Arrabiata')."),
    limit: int = Field(5, ge=1, le=MAX_LIMIT, description="Max results to return (1–25)."),
) -> List[MealCard]:
    """
    Search for meals by name. Returns a list of meals with brief summaries.
    """
    s_query = query.strip()
    s_limit = _coerce_limit(limit, 5)

    if not s_query:
        return []

    data = _get("/search.php", params={"s": s_query})
    meals = data.get("meals")

    if not meals:
        logger.info(f"search_meals_by_name: no matches for query '{s_query}'")
        return []

    shaped = [_shape_search_meal(m) for m in meals]
    return shaped[:s_limit]


@app.tool()
def meals_by_ingredient(
    ingredient: str = Field(..., description="Main ingredient to filter by (e.g., 'chicken')."),
    limit: int = Field(12, ge=1, le=MAX_LIMIT, description="Max results to return (1–25)."),
) -> List[MealCard]:
    """
    Find meals that use a specific main ingredient.
    """
    s_ingredient = ingredient.strip()
    s_limit = _coerce_limit(limit, 12)

    if not s_ingredient:
        return []

    data = _get("/filter.php", params={"i": s_ingredient})
    meals = data.get("meals")

    if not meals:
        logger.info(f"meals_by_ingredient: no matches for ingredient '{s_ingredient}'")
        return []

    shaped = [_shape_filter_card(m) for m in meals]
    return shaped[:s_limit]


@app.tool()
def meal_details(
    id: Union[str, int] = Field(..., description="Meal ID for lookup (e.g., 52772).")
) -> MealDetails:
    """
    Fetch the full details for a single meal by its ID.
    """
    meal_id = str(id).strip()
    if not meal_id:
        raise ValueError("Missing meal id")

    data = _get("/lookup.php", params={"i": meal_id})
    meals = data.get("meals")

    if not meals:
        logger.info(f"meal_details: no matches for id '{meal_id}'")
        raise ValueError(f"No meal found for id {meal_id}")

    return _shape_meal_details(meals[0])


@app.tool()
def random_meal() -> MealDetails:
    """
    Fetch a single random meal with full details.
    """
    data = _get("/random.php")
    meals = data.get("meals")

    if not meals:
        logger.error("random_meal: API returned no meal data")
        raise RuntimeError("Random meal endpoint returned no data")

    return _shape_meal_details(meals[0])

# entrypoint

if __name__ == "__main__":

    app.run()