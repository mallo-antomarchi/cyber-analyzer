from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Cybersecurity Analyzer API")

class AnalyzeRequest(BaseModel):
    code: str

class SecurityIssue(BaseModel):
    title: str
    description: str
    code: str
    fix: str
    cvss_score: float
    severity: str  # "critical", "high", "medium", "low"

class AnalysisResponse(BaseModel):
    summary: str
    issues: List[SecurityIssue]

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_code(request: AnalyzeRequest):
    """
    Analyze Python code for security vulnerabilities.
    """
    # Hardcoded response for now
    hardcoded_issues = [
        SecurityIssue(
            title="SQL Injection Vulnerability",
            description="Direct string concatenation in SQL query allows for SQL injection attacks.",
            code="cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")",
            fix="Use parameterized queries: cursor.execute(\"SELECT * FROM users WHERE id = %s\", (user_id,))",
            cvss_score=9.1,
            severity="critical"
        ),
        SecurityIssue(
            title="Hardcoded Secret",
            description="API key is hardcoded in the source code, exposing sensitive credentials.",
            code="API_KEY = \"sk-1234567890abcdef\"",
            fix="Store secrets in environment variables: API_KEY = os.getenv('API_KEY')",
            cvss_score=7.5,
            severity="high"
        ),
        SecurityIssue(
            title="Insecure Random Generator",
            description="Using predictable random number generator for security-sensitive operations.",
            code="import random\ntoken = random.randint(1000, 9999)",
            fix="Use cryptographically secure random: import secrets\ntoken = secrets.randbelow(9000) + 1000",
            cvss_score=5.3,
            severity="medium"
        ),
        SecurityIssue(
            title="Missing Input Validation",
            description="User input is not validated before processing, potentially allowing malicious data.",
            code="user_input = request.form['data']\nprocess_data(user_input)",
            fix="Validate input: if user_input and len(user_input) < 100 and user_input.isalnum(): process_data(user_input)",
            cvss_score=4.2,
            severity="low"
        )
    ]
    
    return AnalysisResponse(
        summary=f"Analyzed {len(request.code)} characters of Python code. Found {len(hardcoded_issues)} security issues requiring attention. Critical vulnerabilities detected that need immediate remediation.",
        issues=hardcoded_issues
    )

@app.get("/")
async def root():
    return {"message": "Cybersecurity Analyzer API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)