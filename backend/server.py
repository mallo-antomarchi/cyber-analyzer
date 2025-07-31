import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio, create_static_tool_filter

# Load environment variables
load_dotenv()

app = FastAPI(title="Cybersecurity Analyzer API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],  # Frontend origins
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


@app.post("/api/analyze", response_model=SecurityReport)
async def analyze_code(request: AnalyzeRequest):
    """
    Analyze Python code for security vulnerabilities using OpenAI Agents.
    """
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="No code provided for analysis")

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    try:
        # Get Semgrep app token
        semgrep_app_token = os.getenv("SEMGREP_APP_TOKEN")
        semgrep_params = {
            "command": "uvx",
            "args": ["semgrep-mcp"],
            "env": {"SEMGREP_APP_TOKEN": semgrep_app_token},
        }

        # Create security researcher agent with enhanced instructions
        instructions = """
        You are a cybersecurity researcher. You are given Python code to analyze.
        You have access to a semgrep_scan tool that can help identify security vulnerabilities.
        
        CRITICAL REQUIREMENTS: 
        1. When using the semgrep_scan tool, you MUST ALWAYS use exactly "auto" (and nothing else) for the "config" field in each code_files entry.
        2. You MUST call the semgrep_scan tool ONLY ONCE. Do not call it multiple times with the same code.
        
        DO NOT use any other config values like:
        - "p/sql-injection, p/python-eval" (WRONG)
        - "security" (WRONG) 
        - "python" (WRONG)
        - Any rule names or patterns (WRONG)
        
        ONLY use: "auto"
        
        Correct format: {"code_files": [{"filename": "analysis.py", "content": "the actual code", "config": "auto"}]}
        
        IMPORTANT: Call semgrep_scan once, get the results, then proceed with your own analysis. Do not repeat the tool call.
        
        Your analysis process should be:
        1. First, use the semgrep_scan tool ONCE to scan the provided code (config: "auto")
        2. Review and analyze the semgrep results - count how many issues semgrep found
        3. Do NOT call semgrep_scan again - you already have the results
        4. Conduct your own additional security analysis to identify issues that semgrep might have missed
        5. In your summary, clearly state: "Semgrep found X issues, and I identified Y additional issues"
        6. Combine both semgrep findings and your own analysis into a comprehensive report
        
        Include all severity levels: critical, high, medium, and low vulnerabilities.
        
        For each vulnerability found (from both semgrep and your own analysis), provide:
        - A clear title
        - Detailed description of the security issue and potential impact
        - The specific vulnerable code snippet
        - Recommended fix or mitigation
        - CVSS score (0.0-10.0)
        - Severity level (critical/high/medium/low)
        
        Be thorough and practical in your analysis. Don't duplicate issues between semgrep results and your own findings.
        """

        # Set up MCP server and run analysis
        with trace("Security Researcher"):
            async with MCPServerStdio(
                params=semgrep_params,
                client_session_timeout_seconds=120,
                tool_filter=create_static_tool_filter(allowed_tool_names=["semgrep_scan"]),
            ) as semgrep:
                agent = Agent(
                    name="Security Researcher",
                    instructions=instructions,
                    model="gpt-4.1-mini",
                    mcp_servers=[semgrep],
                    output_type=SecurityReport,
                )

                # Run the security analysis
                result = await Runner.run(
                    agent,
                    input=f"Please analyze the following Python code for security vulnerabilities:\n\n{request.code}",
                )

        report = result.final_output_as(SecurityReport)

        # Use the agent's summary which should include Semgrep vs Agent issue counts
        enhanced_summary = (
            f"Analyzed {len(request.code)} characters of Python code. {report.summary}"
        )

        return SecurityReport(summary=enhanced_summary, issues=report.issues)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/")
async def root():
    return {"message": "Cybersecurity Analyzer API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
