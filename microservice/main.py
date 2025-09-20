import os
from fastapi import FastAPI, Query, Body, HTTPException
from pydantic import BaseModel
import asyncio
from dotenv import load_dotenv
import httpx
import json

load_dotenv()

app = FastAPI()

OPENAI_KEY = os.getenv("OPENAI_KEY")
FIRECRAWL_KEY = os.getenv("FIRECRAWL_KEY")
APIFY_API_KEY = os.getenv("APIFY_API_KEY")
GH_PAT = os.getenv("GH_PAT")

CORAL_SERVER_HOST = os.getenv("CORAL_SERVER_HOST", "http://localhost:5555")
THIS_HOST = os.getenv("THIS_HOST", "http://localhost:8000")

customTools = {
    "search-result": {
        "transport": {
            "type": "http",
            "url": THIS_HOST + "/mcp/search-result"
        },
        "toolSchema": {
          "name": "send-research-result",
          "description": "Send a single result of your research. You can call this multiple times as you find more info.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "result": {
                "type": "string",
                "description": "The text of the result, as markdown"
              }
            },
            "required": ["result"]
          }
        }
    }
}
# we use the same agent graph, so lets keep it here
agentGraphRequest = {
    "agents": [
        {},
        {
            "id": {"name": "company-research", "version": "0.0.1"},
            "name": "company-research",
            "coralPlugins": [],
            "provider": {"type": "local", "runtime": "executable"},
            "blocking": True,
            "options": {
                "MODEL_API_KEY": {"type": "string", "value": OPENAI_KEY}
            },
            "customToolAccess": [],
        },
        {
            "id": {"name": "linkedin", "version": "0.0.1"},
            "name": "firecrawl",
            "coralPlugins": [],
            "provider": {"type": "local", "runtime": "executable"},
            "blocking": True,
            "options": {
                "MODEL_API_KEY": {"type": "string", "value": OPENAI_KEY},
                "FIRECRAWL_API_KEY": {"type": "string", "value": FIRECRAWL_KEY},
                "APIFY_API_KEY": {"type": "string", "value": APIFY_API_KEY}
            },
            "customToolAccess": [],
        },
        {
            "id": {"name": "github", "version": "0.0.1"},
            "name": "github",
            "coralPlugins": [],
            "provider": {"type": "local", "runtime": "executable"},
            "blocking": True,
            "options": {
                "MODEL_API_KEY": {"type": "string", "value": OPENAI_KEY},	
                "GITHUB_PERSONAL_ACCESS_TOKEN": {"type": "string", "value": GH_PAT},
            },
            "customToolAccess": [],
        },
        {
            "id": {"name": "company-research", "version": "0.0.1"},
            "name": "company-research",
            "coralPlugins": [],
            "provider": {"type": "local", "runtime": "executable"},
            "blocking": True,
            "options": {
                "MODEL_API_KEY": {"type": "string", "value": OPENAI_KEY},
                "APIFY_API_KEY": {"type": "string", "value": APIFY_API_KEY}
            },
            "customToolAccess": [],
        },
        {
            "id": {"name": "person-research", "version": "0.0.1"},
            "name": "person-research",
            "coralPlugins": [],
            "provider": {"type": "local", "runtime": "executable"},
            "blocking": True,
            "options": {
                "MODEL_API_KEY": {"type": "string", "value": OPENAI_KEY},
                "APIFY_API_KEY": {"type": "string", "value": APIFY_API_KEY}
            },
            "customToolAccess": [],
        },
        {
            "id": {"name": "role-requirements-builder", "version": "0.0.1"},
            "name": "person-research",
            "coralPlugins": [],
            "provider": {"type": "local", "runtime": "executable"},
            "blocking": True,
            "options": {
                "MODEL_API_KEY": {"type": "string", "value": OPENAI_KEY},
                "APIFY_API_KEY": {"type": "string", "value": APIFY_API_KEY}
            },
            "customToolAccess": [],
        },
    ],
    "groups": [["interface",
                "firecrawl",
                "linkedin",
                "person-research",
                "company-research",
                "role-requirements-builder"]],
    "customTools": customTools
}

def create_app_graph_request(query: str):
    interface_agent = {
        "id": {"name": "interface", "version": "0.0.1"},
        "name": "interface",
        "coralPlugins": [],
        "provider": {"type": "local", "runtime": "executable"},
        "blocking": True,
        "options": {
            "MODEL_API_KEY": {"type": "string", "value": OPENAI_KEY},
            "USER_REQUEST": {"type": "string", "value": query}
        },
        "customToolAccess": ["search-result"],
    }
    final_req = agentGraphRequest
    final_req["agents"][0] = interface_agent
    print("FINAL_REQ")
    print(json.dumps(final_req, indent=4))
    return final_req


pending_researches: dict[str, asyncio.Future] = {}

@app.post("/research")
async def search(q: str = Query(..., description="Research linkedin")):
    future_id = "FROM_SESSION"


    payload = {
        "privacyKey": "priv",
        "applicationId": "app",
        "sessionId": "",
        "agentGraphRequest": create_app_graph_request(q),
    }
    print("PAYLOAD")
    print(json.dumps(payload, indent=4))
    # 3️⃣ POST request to coral server (to create our session)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(CORAL_SERVER_HOST + "/api/v1/sessions", json=payload)
            data = response.json()
            future_id = data.get("sessionId")
        except httpx.RequestError as e:
            print(f"Error sending POST to http://todo/: {e}")

    loop = asyncio.get_event_loop()
    future = loop.create_future()
    pending_researches[future_id] = future

    try:
        # Wait for someone to resolve it via /mcp
        result = await future
    finally:
        # Clean up whether it was resolved or cancelled
        pending_researches.pop(future_id, None)
    
    return {"result": result}


class ResearchResult(BaseModel):
    result: str 

@app.post("/mcp/research-result/{sessionId}/{agentId}")
async def mcp_research_result(sessionId: str, agentId: str, body: ResearchResult):
    print("Got result from agent: ", body.result)
    # Lookup pending search by sessionId
    future = pending_researches.get(sessionId)
    if not future:
        raise HTTPException(status_code=404, detail="No pending request for this session")

    if not future.done():
        future.set_result(body.result)
    return "Success"
