import os
import tempfile
import uuid
from fastapi import FastAPI, Query, Body, HTTPException, File, UploadFile, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from dotenv import load_dotenv
import httpx
import aiohttp
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
    },
    "send-initial-request": {
        "transport": {
            "type": "http",
            "url": THIS_HOST + "/mcp/send-initial-request"
        },
        "toolSchema": {
          "name": "get-initial-request",
          "description": "Retrieve the initial research request with candidate data for this session.",
          "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
          }
        }
    }
}
# we use the same agent graph, so lets keep it here
agentGraphRequest = {
    "agents": [
        {},
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
                "GITHUB_PERSONAL_ACCESS_TOKEN": {"type": "string", "value": GH_PAT}
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
                "MODEL_API_KEY": {"type": "string", "value": OPENAI_KEY}
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
                "MODEL_API_KEY": {"type": "string", "value": OPENAI_KEY}
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
                "MODEL_API_KEY": {"type": "string", "value": OPENAI_KEY}
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
                "linkedin",
                "github",
                "person-research",
                "company-research",
                "role-requirements-builder",
                "match-evaluation"]],
    "customTools": customTools
}

def create_app_graph_request():
    interface_agent = {
        "id": {"name": "interface", "version": "0.0.1"},
        "name": "interface",
        "coralPlugins": [],
        "provider": {"type": "local", "runtime": "executable"},
        "blocking": True,
        "options": {
            "MODEL_API_KEY": {"type": "string", "value": OPENAI_KEY}
        },
        "customToolAccess": ["search-result", "send-initial-request"],
    }
    final_req = agentGraphRequest
    final_req["agents"][0] = interface_agent
    print("FINAL_REQ")
    print(json.dumps(final_req, indent=4))
    return final_req


pending_researches: dict[str, asyncio.Future] = {}
websocket_connections: Dict[str, List[WebSocket]] = {}
initial_requests: dict[str, str] = {}  # Store initial research data by session ID

@app.post("/research")
async def search(q: str = Query(..., description="Research linkedin")):
    future_id = "FROM_SESSION"


    payload = {
        "privacyKey": "priv",
        "applicationId": "app",
        "sessionId": "",
        "agentGraphRequest": create_app_graph_request(),
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

    # Store initial research data for interface agent
    if future_id:
        initial_requests[future_id] = q
        print(f"Stored initial research data for session {future_id}")

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
        "agentGraphRequest": create_app_graph_request(),
    }

    # Submit to Coral server
    try:
        print(f"Submitting request to Coral server: {CORAL_SERVER_HOST}/api/v1/sessions")
        print(f"Payload keys: {list(payload.keys())}")

        async with httpx.AsyncClient() as client:
            response = await client.post(CORAL_SERVER_HOST + "/api/v1/sessions", json=payload)

            print(f"Coral server response status: {response.status_code}")
            print(f"Coral server response headers: {dict(response.headers)}")

            if response.status_code != 200:
                error_body = response.text
                print(f"Coral server error response: {error_body}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Coral server returned {response.status_code}: {error_body}"
                )

            try:
                data = response.json()
                print(f"Coral server response data: {data}")
            except Exception as json_error:
                print(f"Failed to parse Coral server response as JSON: {json_error}")
                print(f"Raw response: {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Invalid JSON response from Coral server: {response.text}"
                )

            session_id = data.get("sessionId")
            if not session_id:
                print(f"No sessionId in response: {data}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Coral server did not return sessionId: {data}"
                )

        # Store initial research data for interface agent
        initial_requests[session_id] = research_query
        print(f"Stored initial research data for session {session_id}")

        # Set up future for this research
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        pending_researches[session_id] = future

        print(f"Successfully created research session: {session_id}")

        return ResearchResponse(
            research_id=session_id,
            status="initiated",
            message="Research request submitted successfully"
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except httpx.RequestError as e:
        print(f"HTTP request error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network error connecting to Coral server: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

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


# Test endpoint for complete candidate research workflow
class CandidateResearchTestRequest(BaseModel):
    candidate_linkedin_url: str = "https://linkedin.com/in/john-doe"
    job_description: str = "Senior Software Engineer role requiring Python, React, and 5+ years experience"
    company_linkedin_url: Optional[str] = "https://linkedin.com/company/tech-company"
    single_task_mode: bool = True

@app.post("/api/test/candidate-research")
async def test_candidate_research_workflow(request: CandidateResearchTestRequest):
    """Test endpoint for complete candidate research workflow"""
    try:
        print(f"[TEST] Received candidate research test request")
        print(f"[TEST] Candidate: {request.candidate_linkedin_url}")
        print(f"[TEST] Job: {request.job_description}")

        # Create test prompt for interface agent
        test_prompt = f"""
Execute complete candidate research workflow:

Candidate LinkedIn: {request.candidate_linkedin_url}
Job Description: {request.job_description}
Company LinkedIn: {request.company_linkedin_url or "Not provided"}

Required workflow:
1. Parse inputs and extract candidate/job information
2. Create job specification using role-requirements-builder
3. Research candidate profile using person-research agent
4. Research company profile using company-research agent
5. Generate final match evaluation with score and justification using match-evaluation agent
6. Return complete results to user

CRITICAL: Complete the full workflow and provide final match score and justification. Do not endlessly chat between agents.
"""

        # Create a special research session for testing
        session_id = str(uuid.uuid4())

        # Create agent graph request with all necessary agents for candidate research
        agent_graph_request = {
            "agents": [
                {
                    "id": {"name": "interface", "version": "0.0.1"},
                    "name": "interface",
                    "coralPlugins": [],
                    "provider": {"type": "local", "runtime": "executable"},
                    "blocking": True,
                    "options": {
                        "MODEL_API_KEY": {"type": "string", "value": os.getenv("MODEL_API_KEY", "")},
                        "SINGLE_TASK_MODE": {"type": "string", "value": "true" if request.single_task_mode else "false"},
                        "USER_REQUEST": {"type": "string", "value": test_prompt}
                    },
                    "customToolAccess": ["search-result"]
                },
                {
                    "id": {"name": "role-requirements-builder", "version": "0.0.1"},
                    "name": "role-requirements-builder",
                    "coralPlugins": [],
                    "provider": {"type": "local", "runtime": "executable"},
                    "blocking": True,
                    "options": {
                        "MODEL_API_KEY": {"type": "string", "value": os.getenv("MODEL_API_KEY", "")},
                        "COMPANY_RESEARCH_AGENT_ID": {"type": "string", "value": "company-research"}
                    },
                    "customToolAccess": []
                },
                {
                    "id": {"name": "person-research", "version": "0.0.1"},
                    "name": "person-research",
                    "coralPlugins": [],
                    "provider": {"type": "local", "runtime": "executable"},
                    "blocking": True,
                    "options": {
                        "MODEL_API_KEY": {"type": "string", "value": os.getenv("MODEL_API_KEY", "")}
                    },
                    "customToolAccess": []
                },
                {
                    "id": {"name": "company-research", "version": "0.0.1"},
                    "name": "company-research",
                    "coralPlugins": [],
                    "provider": {"type": "local", "runtime": "executable"},
                    "blocking": True,
                    "options": {
                        "MODEL_API_KEY": {"type": "string", "value": os.getenv("MODEL_API_KEY", "")}
                    },
                    "customToolAccess": []
                },
                {
                    "id": {"name": "match-evaluation", "version": "0.0.1"},
                    "name": "match-evaluation",
                    "coralPlugins": [],
                    "provider": {"type": "local", "runtime": "executable"},
                    "blocking": True,
                    "options": {
                        "MODEL_API_KEY": {"type": "string", "value": os.getenv("MODEL_API_KEY", "")}
                    },
                    "customToolAccess": []
                }
            ],
            "groups": [["interface", "role-requirements-builder", "person-research", "company-research", "match-evaluation"]],
            "customTools": {
                "search-result": {
                    "transport": {"type": "http", "url": "http://localhost:8000/mcp/search-result"},
                    "toolSchema": {
                        "name": "send-research-result",
                        "description": "Send a single result of your research. You can call this multiple times as you find more info.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"result": {"type": "string", "description": "The text of the result, as markdown"}},
                            "required": ["result"]
                        }
                    }
                }
            }
        }

        # Submit to Coral server
        coral_payload = {
            "privacyKey": "priv",
            "applicationId": "app",
            "sessionId": session_id,
            "agentGraphRequest": agent_graph_request
        }

        print(f"[TEST] Submitting test request to Coral server")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:5555/api/v1/sessions",
                json=coral_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    coral_response = await response.json()
                    test_session_id = coral_response.get("sessionId", session_id)
                    print(f"[TEST] Successfully created test session: {test_session_id}")

                    return {
                        "test_session_id": test_session_id,
                        "status": "test_started",
                        "message": "Complete candidate research workflow initiated",
                        "candidate": request.candidate_linkedin_url,
                        "job_description": request.job_description,
                        "expected_output": "Final match score and justification from match-evaluation agent",
                        "note": "Monitor Coral server logs for agent workflow execution"
                    }
                else:
                    error_text = await response.text()
                    print(f"[TEST] Coral server error: {response.status} - {error_text}")
                    raise HTTPException(status_code=500, detail=f"Coral server error: {error_text}")

    except Exception as e:
        print(f"[TEST] Error in test endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


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

@app.post("/mcp/send-initial-request/{sessionId}/{agentId}")
async def mcp_send_initial_request(sessionId: str, agentId: str):
    """MCP endpoint for interface agent to retrieve initial research data"""
    print(f"Agent {agentId} requesting initial data for session {sessionId}")

    # Check if we have initial request data for this session
    initial_data = initial_requests.get(sessionId)
    if not initial_data:
        # Return empty if no initial data available
        return {"research_data": "No initial research data available"}

    print(f"Sending initial research data to agent {agentId}: {initial_data[:100]}...")
    return {"research_data": initial_data}
