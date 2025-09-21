import os
import tempfile
import uuid
from fastapi import FastAPI, Query, Body, HTTPException, File, UploadFile, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from dotenv import load_dotenv
import httpx
import json
from typing import Optional, Dict, List

load_dotenv()

app = FastAPI(title="Candidate Research API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
            "id": {"name": "firecrawl", "version": "0.0.1"},
            "name": "firecrawl",
            "coralPlugins": [],
            "provider": {"type": "local", "runtime": "executable"},
            "blocking": True,
            "options": {
                "MODEL_API_KEY": {"type": "string", "value": OPENAI_KEY},
                "FIRECRAWL_API_KEY": {"type": "string", "value": FIRECRAWL_KEY}
            },
            "customToolAccess": [],
        },
        {
            "id": {"name": "linkedin", "version": "0.0.1"},
            "name": "linkedin",
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
            "name": "role-requirements-builder",
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
            "id": {"name": "match-evaluation", "version": "0.0.1"},
            "name": "match-evaluation",
            "coralPlugins": [],
            "provider": {"type": "local", "runtime": "executable"},
            "blocking": True,
            "options": {
                "MODEL_API_KEY": {"type": "string", "value": OPENAI_KEY}
            },
            "customToolAccess": [],
        },
    ],
    "groups": [["interface",
                "firecrawl",
                "linkedin",
                "github",
                "person-research",
                "company-research",
                "role-requirements-builder",
                "match-evaluation"]],
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
            "MODEL_API_KEY": {"type": "string", "value": OPENAI_KEY}
        },
        "customToolAccess": ["search-result"],
    }
    final_req = agentGraphRequest
    final_req["agents"][0] = interface_agent
    print("FINAL_REQ")
    print(json.dumps(final_req, indent=4))
    return final_req


pending_researches: dict[str, asyncio.Future] = {}
websocket_connections: Dict[str, List[WebSocket]] = {}

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


# Data models
class ResearchResult(BaseModel):
    result: str

class ResearchRequest(BaseModel):
    linkedin_url: str
    cv_content: Optional[str] = None
    job_description: Optional[str] = None

class ResearchResponse(BaseModel):
    research_id: str
    status: str
    message: str

class FileUploadResponse(BaseModel):
    filename: str
    size: int
    content_type: str
    content: str


# Utility functions
async def read_file_content(file: UploadFile) -> str:
    """Extract text content from uploaded files"""
    try:
        content = await file.read()

        if file.content_type == "text/plain":
            return content.decode('utf-8')
        elif file.content_type == "application/pdf":
            # For now, return a placeholder - in production, use PyPDF2 or similar
            return f"[PDF content from {file.filename} - content extraction would be implemented here]"
        elif file.content_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            # For now, return a placeholder - in production, use python-docx or similar
            return f"[DOC/DOCX content from {file.filename} - content extraction would be implemented here]"
        else:
            return f"[Unsupported file type: {file.content_type}]"
    except Exception as e:
        return f"[Error reading file: {str(e)}]"

def create_research_query(linkedin_url: str, cv_content: str, job_description: str) -> str:
    """Create a research query that includes all the input data for the agent pipeline"""
    query = f"""
Please conduct a comprehensive candidate evaluation with the following information:

LINKEDIN PROFILE: {linkedin_url}

CV CONTENT:
{cv_content}

JOB DESCRIPTION:
{job_description}

Please analyze this candidate's fit for the role by:
1. Extracting candidate information from LinkedIn and CV
2. Researching the target company and role requirements
3. Building detailed role requirements from the job description
4. Conducting final match evaluation with scoring

Provide a detailed match evaluation with scores, justification, and recommendations.
"""
    return query


# New file upload endpoints
@app.post("/api/upload/cv", response_model=FileUploadResponse)
async def upload_cv(file: UploadFile = File(...)):
    """Upload and process CV file"""
    # Validate file type
    allowed_types = ["text/plain", "application/pdf", "application/msword",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]

    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Validate file size (10MB limit)
    file_size = 0
    content = await file.read()
    file_size = len(content)

    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")

    # Reset file position and extract content
    await file.seek(0)
    extracted_content = await read_file_content(file)

    return FileUploadResponse(
        filename=file.filename,
        size=file_size,
        content_type=file.content_type,
        content=extracted_content
    )

@app.post("/api/upload/job-description", response_model=FileUploadResponse)
async def upload_job_description(file: UploadFile = File(...)):
    """Upload and process job description file"""
    # Validate file type
    allowed_types = ["text/plain", "application/pdf", "application/msword",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]

    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Validate file size (5MB limit)
    file_size = 0
    content = await file.read()
    file_size = len(content)

    if file_size > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB")

    # Reset file position and extract content
    await file.seek(0)
    extracted_content = await read_file_content(file)

    return FileUploadResponse(
        filename=file.filename,
        size=file_size,
        content_type=file.content_type,
        content=extracted_content
    )

@app.post("/api/research", response_model=ResearchResponse)
async def submit_research(
    linkedin_url: str = Form(...),
    cv_file: UploadFile = File(...),
    job_description: Optional[str] = Form(None),
    job_description_file: Optional[UploadFile] = File(None)
):
    """Submit a complete research request with file uploads"""

    # Validate LinkedIn URL
    if not linkedin_url or "linkedin.com" not in linkedin_url:
        raise HTTPException(status_code=400, detail="Valid LinkedIn URL is required")

    # Process CV file
    try:
        cv_content = await read_file_content(cv_file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing CV file: {str(e)}")

    # Process job description (either text or file)
    jd_content = ""
    if job_description_file:
        try:
            jd_content = await read_file_content(job_description_file)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing job description file: {str(e)}")
    elif job_description:
        jd_content = job_description
    else:
        raise HTTPException(status_code=400, detail="Job description is required (either text or file)")

    # Validate job description length
    if len(jd_content.strip()) < 100:
        raise HTTPException(status_code=400, detail="Job description must be at least 100 characters")

    # Create research query
    research_query = create_research_query(linkedin_url, cv_content, jd_content)

    # Generate unique research ID
    research_id = str(uuid.uuid4())

    # Create Coral server request
    payload = {
        "privacyKey": "priv",
        "applicationId": "app",
        "sessionId": research_id,
        "agentGraphRequest": create_app_graph_request(research_query),
    }

    # Submit to Coral server
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(CORAL_SERVER_HOST + "/api/v1/sessions", json=payload)
            data = response.json()
            session_id = data.get("sessionId", research_id)

        # Set up future for this research
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        pending_researches[session_id] = future

        return ResearchResponse(
            research_id=session_id,
            status="initiated",
            message="Research request submitted successfully"
        )

    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error submitting research request: {str(e)}")

@app.get("/api/research/{research_id}/status")
async def get_research_status(research_id: str):
    """Get the status of a research request"""
    if research_id in pending_researches:
        future = pending_researches[research_id]
        if future.done():
            try:
                result = future.result()
                return {
                    "research_id": research_id,
                    "status": "completed",
                    "result": result
                }
            except Exception as e:
                return {
                    "research_id": research_id,
                    "status": "failed",
                    "error": str(e)
                }
        else:
            return {
                "research_id": research_id,
                "status": "processing",
                "message": "Research in progress"
            }
    else:
        raise HTTPException(status_code=404, detail="Research not found")

@app.get("/api/research/{research_id}/results")
async def get_research_results(research_id: str):
    """Get the results of a completed research request"""
    if research_id in pending_researches:
        future = pending_researches[research_id]
        if future.done():
            try:
                result = future.result()
                return {
                    "research_id": research_id,
                    "status": "completed",
                    "results": result
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error retrieving results: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="Research not yet completed")
    else:
        raise HTTPException(status_code=404, detail="Research not found")

@app.post("/api/research/{research_id}/cancel")
async def cancel_research(research_id: str):
    """Cancel a research request"""
    if research_id in pending_researches:
        future = pending_researches[research_id]
        if not future.done():
            future.cancel()
            pending_researches.pop(research_id, None)
            return {"message": "Research cancelled successfully"}
        else:
            return {"message": "Research already completed"}
    else:
        raise HTTPException(status_code=404, detail="Research not found")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "candidate-research-api"}


async def broadcast_to_websockets(research_id: str, message_type: str, data: dict):
    """Broadcast a message to all WebSocket connections for a research ID"""
    if research_id in websocket_connections:
        connections = websocket_connections[research_id][:]  # Copy to avoid modification during iteration
        message = {
            "type": message_type,
            "researchId": research_id,
            "data": data,
            "timestamp": str(asyncio.get_event_loop().time())
        }

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                # Remove disconnected websockets
                if websocket in websocket_connections[research_id]:
                    websocket_connections[research_id].remove(websocket)

@app.websocket("/ws/research/{research_id}")
async def websocket_endpoint(websocket: WebSocket, research_id: str):
    await websocket.accept()

    # Add this connection to the research ID
    if research_id not in websocket_connections:
        websocket_connections[research_id] = []
    websocket_connections[research_id].append(websocket)

    try:
        # Send initial status
        if research_id in pending_researches:
            future = pending_researches[research_id]
            if future.done():
                try:
                    result = future.result()
                    await websocket.send_json({
                        "type": "completion",
                        "researchId": research_id,
                        "data": {"status": "completed", "results": result},
                        "timestamp": str(asyncio.get_event_loop().time())
                    })
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "researchId": research_id,
                        "data": {"status": "failed", "error": str(e)},
                        "timestamp": str(asyncio.get_event_loop().time())
                    })
            else:
                await websocket.send_json({
                    "type": "stage_update",
                    "researchId": research_id,
                    "data": {"status": "processing", "stage": "initialization"},
                    "timestamp": str(asyncio.get_event_loop().time())
                })
        else:
            await websocket.send_json({
                "type": "error",
                "researchId": research_id,
                "data": {"status": "not_found", "message": "Research not found"},
                "timestamp": str(asyncio.get_event_loop().time())
            })

        # Keep connection alive
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    finally:
        # Remove this connection
        if research_id in websocket_connections and websocket in websocket_connections[research_id]:
            websocket_connections[research_id].remove(websocket)

@app.post("/mcp/research-result/{sessionId}/{agentId}")
async def mcp_research_result(sessionId: str, agentId: str, body: ResearchResult):
    print("Got result from agent: ", body.result)

    # Broadcast agent update to WebSocket connections
    await broadcast_to_websockets(sessionId, "agent_status", {
        "agent": agentId,
        "currentTask": f"Received result from {agentId}",
        "message": body.result
    })

    # Lookup pending search by sessionId
    future = pending_researches.get(sessionId)
    if not future:
        raise HTTPException(status_code=404, detail="No pending request for this session")

    if not future.done():
        future.set_result(body.result)
        # Broadcast completion
        await broadcast_to_websockets(sessionId, "completion", {
            "status": "completed",
            "results": body.result
        })
    return "Success"
