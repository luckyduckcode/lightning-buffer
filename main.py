from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Any
import os
import requests
from datetime import datetime

from config import (
    BUFFER_PORT, 
    AUTOMATION_API_URL, 
    AUTOMATION_API_KEY, 
    AUTOMATIONS_HOST_DIR,
    DEFAULT_MODEL,
    BUFFER_API_KEY
)
from utils import generate_safe_filename, validate_and_join_path, get_container_path

app = FastAPI(title="FastAPI Buffer API")

# --- Models ---

class GenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = DEFAULT_MODEL
    filename: Optional[str] = None

class RunRequest(BaseModel):
    filename: str

class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

# --- Helpers ---

def call_docker_api(endpoint: str, payload: dict, timeout: int = 60) -> dict:
    """Helper to call the Docker Automation API"""
    url = f"{AUTOMATION_API_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if AUTOMATION_API_KEY:
        headers["Authorization"] = f"Bearer {AUTOMATION_API_KEY}" 
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling Docker API: {e}")
        # Return a standardized error structure or raise
        raise HTTPException(status_code=502, detail=f"Docker API Error: {str(e)}")

# --- Endpoints ---

@app.get("/health")
async def health_check():
    # Optional: Ping Docker API to see if it's alive
    docker_status = "unknown"
    try:
        # Assuming Docker API has a health check or we can try a lightweight call
        requests.get(f"{AUTOMATION_API_URL}/health", timeout=2) 
        docker_status = "connected"
    except:
        docker_status = "disconnected"
        
    return {
        "status": "ok", 
        "service": "FastAPI Buffer API", 
        "docker_api": docker_status
    }

@app.post("/generate", response_model=StandardResponse)
async def generate_code(req: GenerateRequest):
    """
    Generate code, optionally save it.
    """
    # 1. Determine filename
    if req.filename:
        safe_filename = req.filename 
        if not safe_filename.endswith(".py"):
            safe_filename += ".py"
    else:
        safe_filename = generate_safe_filename(req.prompt)

    # 2. Prepare path for Docker
    container_path = get_container_path(safe_filename)
    
    # 3. Call Docker API
    payload = {
        "prompt": req.prompt,
        "model": req.model,
        "save_path": container_path
    }
    
    try:
        result = call_docker_api("/generate", payload, timeout=120)
    except HTTPException as e:
        return StandardResponse(success=False, message=e.detail)

    # 4. Return result
    return StandardResponse(
        success=True, 
        message="Code generated and saved.",
        data={
            "filename": safe_filename,
            "code": result.get("code", ""), 
            "full_response": result
        }
    )

@app.post("/generate-and-run", response_model=StandardResponse)
async def generate_and_run(req: GenerateRequest):
    """
    Generate -> Save -> Execute immediately.
    """
    # 1. Determine filename
    if req.filename:
        safe_filename = req.filename
        if not safe_filename.endswith(".py"):
            safe_filename += ".py"
    else:
        safe_filename = generate_safe_filename(req.prompt)
        
    container_path = get_container_path(safe_filename)
    
    # 2. Generate
    gen_payload = {
        "prompt": req.prompt,
        "model": req.model,
        "save_path": container_path
    }
    
    try:
        gen_result = call_docker_api("/generate", gen_payload, timeout=120)
    except HTTPException as e:
        return StandardResponse(success=False, message=f"Generation failed: {e.detail}")

    # 3. Execute
    code = gen_result.get("code", "")
    
    exec_payload = {
        "code": code
    }
    
    try:
        exec_result = call_docker_api("/execute", exec_payload, timeout=60)
    except HTTPException as e:
        return StandardResponse(success=False, message=f"Execution failed: {e.detail}", data={"code": code})

    return StandardResponse(
        success=True,
        message="Generated and executed.",
        data={
            "filename": safe_filename,
            "code": code,
            "output": exec_result.get("output", ""), 
            "error": exec_result.get("error", "")
        }
    )

@app.post("/run", response_model=StandardResponse)
async def run_script(req: RunRequest):
    """
    Execute an existing script.
    """
    # 1. Validate filename and read content
    try:
        full_path = validate_and_join_path(req.filename)
        if not os.path.exists(full_path):
            return StandardResponse(success=False, message="File not found.")
            
        with open(full_path, "r", encoding="utf-8") as f:
            code = f.read()
    except ValueError as e:
        return StandardResponse(success=False, message=str(e))
    except Exception as e:
        return StandardResponse(success=False, message=f"Error reading file: {e}")

    # 2. Call Docker Execute
    payload = {"code": code}
    
    try:
        result = call_docker_api("/execute", payload, timeout=60)
    except HTTPException as e:
        return StandardResponse(success=False, message=e.detail)
        
    return StandardResponse(
        success=True,
        message="Executed successfully.",
        data={
            "output": result.get("output", ""),
            "error": result.get("error", "")
        }
    )

@app.get("/list", response_model=StandardResponse)
async def list_automations():
    """
    List all saved automation scripts.
    """
    try:
        files = []
        if os.path.exists(AUTOMATIONS_HOST_DIR):
            for f in os.listdir(AUTOMATIONS_HOST_DIR):
                if f.endswith(".py"):
                    full_path = os.path.join(AUTOMATIONS_HOST_DIR, f)
                    stats = os.stat(full_path)
                    files.append({
                        "filename": f,
                        "size": stats.st_size,
                        "modified": datetime.fromtimestamp(stats.st_mtime).isoformat()
                    })
        
        # Sort by modified desc
        files.sort(key=lambda x: x["modified"], reverse=True)
        
        return StandardResponse(success=True, message="List retrieved.", data=files)
    except Exception as e:
        return StandardResponse(success=False, message=f"Error listing files: {e}")

@app.post("/get", response_model=StandardResponse)
async def get_script(req: RunRequest):
    """
    Get content of a script.
    """
    try:
        full_path = validate_and_join_path(req.filename)
        if not os.path.exists(full_path):
            return StandardResponse(success=False, message="File not found.")
            
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        return StandardResponse(success=True, message="File read.", data={"code": content})
    except ValueError as e:
        return StandardResponse(success=False, message=str(e))
    except Exception as e:
        return StandardResponse(success=False, message=f"Error reading file: {e}")

@app.post("/delete", response_model=StandardResponse)
async def delete_script(req: RunRequest):
    """
    Delete a script.
    """
    try:
        full_path = validate_and_join_path(req.filename)
        if not os.path.exists(full_path):
            return StandardResponse(success=False, message="File not found.")
            
        os.remove(full_path)
        return StandardResponse(success=True, message=f"Deleted {req.filename}")
    except ValueError as e:
        return StandardResponse(success=False, message=str(e))
    except Exception as e:
        return StandardResponse(success=False, message=f"Error deleting file: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=BUFFER_PORT)
