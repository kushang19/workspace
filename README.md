React AI Agent

=====================  Development Environment  =========================

Start

From the project root:

docker compose -f .devcontainer/docker-compose.yaml up -d

Check:

docker compose -f .devcontainer/docker-compose.yaml ps

Open the project in VS Code using the Dev Container.

Inside the Dev Container:

streamlit run streamlit_app.py --server.address=0.0.0.0 --server.port=8501

Open:

http://localhost:8501

Stop

From Windows:

docker compose -f .devcontainer/docker-compose.yaml down

===================== Production Environment — Local Test ==========================

Build

From the project root:

docker build -t react-ai-agent .

Run

Windows CMD:

docker run --rm -p 10000:10000 -p 5173:5173 --env-file .env -v "%cd%:/workspace" react-ai-agent

Open Streamlit:

http://localhost:10000

Generated React apps:

http://localhost:5173

Generated projects are written to the Windows project directory through:

Windows project folder <-> /workspace

Check

Open another CMD:

docker ps

Then:

docker exec <CONTAINER_ID> pwd

Expected:

/workspace

Check files:

docker exec <CONTAINER_ID> ls -la /workspace

Stop

Press:

Ctrl + C

The container is automatically removed because it was started with --rm.

Useful Docker Commands

Running containers:

docker ps

All containers:

docker ps -a

Images:

docker images

Rebuild:

docker build -t react-ai-agent .

Rebuild without cache:

docker build --no-cache -t react-ai-agent .

Remove image:

docker rmi react-ai-agent

Environment Variables

.env:

GEMINI_API_KEY=your_actual_gemini_api_key

.env must not be committed.

.env.example:

GEMINI_API_KEY=your_gemini_api_key_here

Ports

Environment

Service

Port

Development

Streamlit

8501

Development

React/Vite

5173

Production Test

Streamlit

10000

Production Test

React/Vite

5173

Deployment

GitHub
   ↓
Render
   ↓
Streamlit + Python Agent + Gemini
   ↓
Generated React Application
   ↓
Cloudflare Pages