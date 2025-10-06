import os
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
from agents import Agent, Runner, trace

from context import SECURITY_RESEARCHER_INSTRUCTIONS, get_analysis_prompt, enhance_summary
from mcp_servers import create_semgrep_server

load_dotenv()

app = FastAPI(title="Cybersecurity Analyzer API")
api_router = APIRouter()

# Configure CORS for development and production
cors_origins = [
    "http://localhost:3000",    # Local development
    "http://frontend:3000",     # Docker development
]

# In production, allow same-origin requests (static files served from same domain)
if os.getenv("ENVIRONMENT") == "production":
    cors_origins.append("*")  # Allow all origins in production since we serve frontend from same domain

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    code: str


class SecurityIssue(BaseModel):
    title: str = Field(description="Brief title of the security vulnerability")
    description: str = Field(
        description="Detailed description of the security issue and its potential impact"
    )
    code: str = Field(
        description="The specific vulnerable code snippet that demonstrates the issue"
    )
    fix: str = Field(description="Recommended code fix or mitigation strategy")
    cvss_score: float = Field(description="CVSS score from 0.0 to 10.0 representing severity")
    severity: str = Field(description="Severity level: critical, high, medium, or low")


class SecurityReport(BaseModel):
    summary: str = Field(description="Executive summary of the security analysis")
    issues: List[SecurityIssue] = Field(description="List of identified security vulnerabilities")


def validate_request(request: AnalyzeRequest) -> None:
    """Validate the analysis request."""
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="No code provided for analysis")


def check_api_keys() -> None:
    """Verify required API keys are configured."""
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")


def create_security_agent(semgrep_server) -> Agent:
    """Create and configure the security analysis agent."""
    return Agent(
        name="Security Researcher",
        instructions=SECURITY_RESEARCHER_INSTRUCTIONS,
        model="gpt-4.1-mini",
        mcp_servers=[semgrep_server],
        output_type=SecurityReport,
    )


async def run_security_analysis(code: str) -> SecurityReport:
    """Execute the security analysis workflow."""
    with trace("Security Researcher"):
        async with create_semgrep_server() as semgrep:
            agent = create_security_agent(semgrep)
            result = await Runner.run(agent, input=get_analysis_prompt(code))
            return result.final_output_as(SecurityReport)


def format_analysis_response(code: str, report: SecurityReport) -> SecurityReport:
    """Format the final analysis response."""
    enhanced_summary = enhance_summary(len(code), report.summary)
    return SecurityReport(summary=enhanced_summary, issues=report.issues)


@api_router.post("/analyze", response_model=SecurityReport)
async def analyze_code(request: AnalyzeRequest) -> SecurityReport:
    """
    Analyze Python code for security vulnerabilities using OpenAI Agents and Semgrep.

    This endpoint combines static analysis via Semgrep with AI-powered security analysis
    to provide comprehensive vulnerability detection and remediation guidance.
    """
    validate_request(request)
    check_api_keys()

    try:
        report = await run_security_analysis(request.code)
        return format_analysis_response(request.code, report)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in analyze_code: {error_details}")  # Log to console
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@api_router.get("/health")
async def health():
    """Health check endpoint."""
    return {"message": "Cybersecurity Analyzer API"}

@api_router.get("/debug")
async def debug():
    """Debug endpoint to check imports and dependencies."""
    import sys
    import subprocess
    
    results = {
        "python_version": sys.version,
        "python_path": sys.executable,
    }
    
    # Check if uvx is available
    try:
        uvx_result = subprocess.run(["which", "uvx"], capture_output=True, text=True, timeout=5)
        results["uvx_available"] = uvx_result.returncode == 0
        results["uvx_path"] = uvx_result.stdout.strip()
    except Exception as e:
        results["uvx_check_error"] = str(e)
    
    # Check if we can import agents
    try:
        import agents
        results["agents_imported"] = True
        results["agents_version"] = getattr(agents, "__version__", "unknown")
    except Exception as e:
        results["agents_import_error"] = str(e)
        import traceback
        results["agents_import_traceback"] = traceback.format_exc()
    
    # Check if we can import mcp
    try:
        import mcp
        results["mcp_imported"] = True
        results["mcp_version"] = getattr(mcp, "__version__", "unknown")
    except Exception as e:
        results["mcp_import_error"] = str(e)
    
    return results

@api_router.get("/network-test")
async def network_test():
    """Test network connectivity to Semgrep API."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://semgrep.dev/api/v1/")
            return {
                "semgrep_api_reachable": True,
                "status_code": response.status_code,
                "response_size": len(response.content)
            }
    except Exception as e:
        return {
            "semgrep_api_reachable": False,
            "error": str(e)
        }

@api_router.get("/semgrep-test")
async def semgrep_test():
    """Test if semgrep CLI can be installed and run."""
    import subprocess
    import tempfile
    import os
    
    try:
        # Test if we can install semgrep via pip
        result = subprocess.run(
            ["pip", "install", "semgrep"], 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        
        if result.returncode != 0:
            return {
                "semgrep_install": False,
                "error": f"Install failed: {result.stderr}"
            }
        
        # Test if semgrep --version works
        version_result = subprocess.run(
            ["semgrep", "--version"], 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        return {
            "semgrep_install": True,
            "version_check": version_result.returncode == 0,
            "version_output": version_result.stdout,
            "version_error": version_result.stderr
        }
        
    except subprocess.TimeoutExpired:
        return {
            "semgrep_install": False,
            "error": "Timeout during semgrep installation or version check"
        }
    except Exception as e:
        return {
            "semgrep_install": False,
            "error": str(e)
        }

# Mount API router FIRST - this ensures API routes have priority
app.include_router(api_router, prefix="/api")

# Mount static files at root - StaticFiles will only handle file requests, not API
try:
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
except RuntimeError:
    pass  # static directory doesn't exist, skip mounting


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
