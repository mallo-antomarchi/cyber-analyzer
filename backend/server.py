import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
from agents import Agent, Runner

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
    description: str = Field(description="Detailed description of the security issue and its potential impact")
    code: str = Field(description="The specific vulnerable code snippet that demonstrates the issue")
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
        # Create security researcher agent
        instructions = """
        You are a cybersecurity researcher. You are given Python code to analyze.
        You analyze it for security vulnerabilities and provide detailed findings.
        Include all severity levels: critical, high, medium, and low vulnerabilities.
        
        For each vulnerability found, provide:
        - A clear title
        - Detailed description of the security issue and potential impact
        - The specific vulnerable code snippet
        - Recommended fix or mitigation
        - CVSS score (0.0-10.0)
        - Severity level (critical/high/medium/low)
        
        Be thorough but practical in your analysis.
        """
        
        agent = Agent(
            name="Security Researcher", 
            instructions=instructions, 
            model="gpt-4o-mini", 
            output_type=SecurityReport
        )
        
        # Get first 20 characters for verification
        code_preview = request.code[:20] if request.code else ""
        
        # Run the security analysis
        result = await Runner.run(
            agent, 
            input=f"Please analyze the following Python code for security vulnerabilities:\n\n{request.code}"
        )
        
        report = result.final_output_as(SecurityReport)
        
        # Add code preview to summary for testing roundtrip
        enhanced_summary = f"Analyzed {len(request.code)} characters of Python code (starting with: '{code_preview}'). {report.summary}"
        
        return SecurityReport(
            summary=enhanced_summary,
            issues=report.issues
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Cybersecurity Analyzer API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)