import nest_asyncio
nest_asyncio.apply()  # Patches the asyncio loop to allow nested Playwright calls inside Uvicorn

import json
import logging
from fastapi import FastAPI, Request, HTTPException, Depends, Header
# ... rest of your existing main.py code remains exactly the same ...
import json
import logging
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import litellm
from tools.browser_control import execute_browser_task

# Configure logging for MLOps tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AI-OS-ROUTER")

# Initialize FastAPI app
app = FastAPI(title="AI OS Core Engine")

# Lower the drawbridge for frontend communication (supports multi-tenant port shifts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    prompt: str
    session_id: str

def execute_waterfall_completion(prompt: str, key_pool: list) -> tuple[str, str]:
    """
    Executes an LLM request across a sequential list of user-provided keys.
    Catches 429/Authentication errors and falls back instantly.
    """
    # 1. Map user keys to LiteLLM compatible model definitions
    execution_pipeline = []
    for item in key_pool:
        provider = item.get("provider", "").lower()
        key = item.get("key", "").strip()
        if not key:
            continue
            
        if provider == "gemini":
            execution_pipeline.append({
                "model": "gemini/gemini-1.5-flash",
                "api_key": key
            })
        elif provider == "groq":
            execution_pipeline.append({
                "model": "groq/llama-3.3-70b-versatile",
                "api_key": key
            })
        elif provider == "openai":
            execution_pipeline.append({
                "model": "openai/gpt-4o-mini",
                "api_key": key
            })
        elif provider == "deepseek":
            execution_pipeline.append({
                "model": "deepseek/deepseek-chat",
                "api_key": key
            })

    # 2. Append the absolute local fallback (Ollama) to the end of the line
    execution_pipeline.append({
        "model": "ollama/qwen2.5:7b",
        "api_base":"http://127.0.0.1:11434"
    })

    # 3. Iterate through the pipeline until a model successfully executes
    for target in execution_pipeline:
        model_name = target["model"]
        logger.info(f"Attempting execution utilizing model: {model_name}")
        
        try:
            # Build specific configuration parameters per execution block
            params = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "timeout": 15.0
            }
            if "api_key" in target:
                params["api_key"] = target["api_key"]
            if "api_base" in target:
                params["api_base"] = target["api_base"]

            response = litellm.completion(**params)
            content = response.choices[0].message.content
            
            # Determine system tracking state
            system_state = "OLLAMA_FALLBACK" if "ollama" in model_name else f"CLOUD_ACTIVE_{model_name.upper()}"
            return content, system_state

        except Exception as error:
            logger.warning(f"Model execution failed for {model_name}: {str(error)}. Cascading to next fallback...")
            continue

    raise HTTPException(status_code=503, detail="All cloud API execution targets exhausted and local deployment unreachable.")

@app.post("/api/v1/chat")
async def chat_endpoint(request: Request, body: ChatRequest):
    key_pool_header = request.headers.get("X-Key-Pool", "[]")
    try:
        key_pool = json.loads(key_pool_header)
    except Exception:
        key_pool = []

    logger.info(f"Incoming execution request for session: {body.session_id}")
    
    # --- NEW AUTOMATION INTERCEPTION ROUTE ---
    prompt_lower = body.prompt.lower()
    if any(keyword in prompt_lower for keyword in ["open", "search", "play"]):
        logger.info("Automation signature detected. Routing to Browser Execution Engine...")
        try:
            automation_result = await execute_browser_task(body.prompt)
            return {
                "response": f"JARVIS Action Executed:\n{automation_result}",
                "system_state": "DESKTOP_AUTOMATION_ACTIVE",
                "session_id": body.session_id
            }
        except Exception as automation_error:
            logger.error(f"Automation execution collapsed: {str(automation_error)}")
            return {
                "response": f"Automation Fault: Failed to complete desktop task. System log: {str(automation_error)}",
                "system_state": "AUTOMATION_ERROR",
                "session_id": body.session_id
            }
    # ------------------------------------------

    # Default fallback to text completions (Waterfall Cloud / Ollama)
    response_text, system_state = execute_waterfall_completion(body.prompt, key_pool)
    
    return {
        "response": response_text,
        "system_state": system_state,
        "session_id": body.session_id
    }

@app.post("/login")
def login_mock():
    # Simple handshake logic for local dashboard access verification
    return {"access_token": "mock-admin-token-123", "token_type": "bearer"}