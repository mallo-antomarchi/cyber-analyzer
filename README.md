# Cybersecurity Analyzer

A web application for analyzing Python code for security vulnerabilities using AI-powered analysis with OpenAI and Semgrep.

## Prerequisites

- Node.js 20+
- Python 3.12+
- Docker (for containerized deployment)
- Environment variables in `.env` file:
  - `OPENAI_API_KEY`
  - `SEMGREP_APP_TOKEN`

## Running Locally

### Start the Backend Server

```bash
cd backend
uv run server.py
```

The backend API will be available at http://localhost:8000

### Start the Frontend Development Server

In a new terminal:

```bash
cd frontend
npm run dev
```

The frontend will be available at http://localhost:3000

### Stopping the Servers

- Backend: Press `Ctrl+C` in the backend terminal
- Frontend: Press `Ctrl+C` in the frontend terminal

## Running with Docker

### Build the Docker Image

```bash
docker build -t cyber-analyzer .
```

### Run the Container

```bash
docker run --rm -d --name cyber-analyzer -p 8000:8000 --env-file .env cyber-analyzer
```

The application will be available at http://localhost:8000

### View Container Logs

```bash
docker logs cyber-analyzer
```

### Stop the Container

```bash
docker stop cyber-analyzer
```

## Deployment

The Docker image is optimized for deployment on:
- Google Cloud Run
- Azure Container Instances
- Any container platform that supports Docker

The application exposes port 8000 and includes a health check endpoint at `/health`.
