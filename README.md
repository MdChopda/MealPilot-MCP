# MealPilot (MCP) — Python LLM Tool Server for Recipe Discovery

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](#license)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)]()
[![MCP](https://img.shields.io/badge/Model%20Context%20Protocol-Server-orange)]()

Turn a public recipe API (TheMealDB) into **typed tools for LLMs** via the **Model Context Protocol (MCP)**.  
Supports search by name, filter by ingredient, fetch meal details, and a random meal endpoint — all with **Pydantic** validation, **timeouts**, **result limits**, and **structured logging**.

> Demo (optional): add a GIF or video here — `docs/demo.gif`

---

## ✨ Features
- **MCP server** exposing **4 agent tools** for reliable LLM function-calling
- **Contract-first** data models using **Pydantic** / JSON Schema
- **Resilient I/O**: timeouts, result caps, structured stderr logging
- **Minimal deps**: `requests`, `pydantic`
- Works with **`mcp dev`** for quick local bring-up

---

## 🚀 Quickstart

```bash
# 1) Clone or download
git clone https://github.com/vrushabh05/mealpilot-mcp.git
cd mealpilot-mcp

# 2) (Optional) Create a virtualenv
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate

# 3) Install dependencies
pip install -r requirements.txt

# 4) Run the server
python meals_server.py

# 5) Dev with MCP (if installed)
mcp dev
```

> If you don't have MCP CLI: https://github.com/modelcontextprotocol

---

## 🧰 Tools Exposed (MCP)
- `search_by_name(query: str)` → list of **MealCard**
- `filter_by_ingredient(ingredient: str)` → list of **MealCard**
- `meal_details(id: str)` → **MealDetails**
- `random_meal()` → **MealDetails**

<details>
<summary><b>Data Models (Pydantic)</b></summary>

```python
class IngredientMeasure(BaseModel):
    ingredient: str
    measure: str

class MealCard(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    area: Optional[str] = None
    thumbnail: Optional[str] = None

class MealDetails(MealCard):
    instructions: Optional[str] = None
    tags: List[str] = []
    youtube: Optional[str] = None
    source: Optional[str] = None
    ingredients: List[IngredientMeasure] = []
```
</details>

<details>
<summary><b>Server Settings</b></summary>

- `TIMEOUT = 15` seconds
- `MAX_LIMIT = 25` results per tool by default
- Structured logging to `stderr` (JSON or key-value style)
</details>

---

## 📦 Project Structure (suggested)
```
.
├── meals_server.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
└── docs/
    └── demo.gif   # (optional)
```

---

## 🧪 Example Usage (pseudo)
```json
{
  "tool": "search_by_name",
  "params": {"query": "pasta"},
  "timeout": 15000
}
```
Returns a list of `MealCard` objects with id, name, category, area, thumbnail.

---

## 🔧 Development Notes
- Fail fast on network errors; wrap API calls with `requests` + `timeout`
- Validate and coerce third‑party API payloads into Pydantic models
- Cap list sizes (`MAX_LIMIT`) to keep calls predictable for LLM agents

---

## 📄 License
Released under the **MIT License**. See [LICENSE](#license).

## 🙌 Acknowledgements
- TheMealDB — Public recipe API
- Model Context Protocol — Agent tool standard
