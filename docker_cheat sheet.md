.devcontainer/
├── devcontainer.json      → tells VS Code how to use the container
├── docker-compose.yaml    → tells Docker how to run the container
└── Dockerfile             → tells Docker what to install inside it


====================  Images  ========================
# List images
docker images

# Build image
docker build -t react-ai-agent .

# Remove image
docker rmi react-ai-agent

# Remove unused images
docker image prune

====================  Containers  ========================
# List running containers
docker ps

# List ALL containers
docker ps -a

# Run container
docker run -it react-ai-agent

# Run with .env
docker run -it --env-file .env react-ai-agent

# Run with volume + port
docker run -it --env-file .env -v "${PWD}:/app" -p 5173:5173 react-ai-agent

# Stop container
docker stop <container_id>

# Start stopped container
docker start <container_id>

# Restart container
docker restart <container_id>

# Remove container
docker rm <container_id>

# Remove stopped containers
docker container prune

====================  Enter a running container  ========================
docker exec -it <container_id> bash

If bash isn't available:
docker exec -it <container_id> sh

====================  Logs  ========================
# View logs
docker logs <container_id>

# Follow logs
docker logs -f <container_id>

====================  Docker Compose  ========================
For your current .devcontainer/docker-compose.yaml:

# Validate Compose file
docker compose -f .devcontainer/docker-compose.yaml config

# Build
docker compose -f .devcontainer/docker-compose.yaml build

# Start
docker compose -f .devcontainer/docker-compose.yaml up -d

# Stop
docker compose -f .devcontainer/docker-compose.yaml stop

# Start again
docker compose -f .devcontainer/docker-compose.yaml start

# Stop + remove containers/network
docker compose -f .devcontainer/docker-compose.yaml down

# Build + start
docker compose -f .devcontainer/docker-compose.yaml up -d --build

# Check Compose containers
docker compose -f .devcontainer/docker-compose.yaml ps

# View logs
docker compose -f .devcontainer/docker-compose.yaml logs

# Follow logs
docker compose -f .devcontainer/docker-compose.yaml logs -f


Execute commands inside your app container:
docker compose -f .devcontainer/docker-compose.yaml exec app bash
docker compose -f .devcontainer/docker-compose.yaml exec app sh
docker compose -f .devcontainer/docker-compose.yaml exec app python app.py
docker compose -f .devcontainer/docker-compose.yaml exec app python app.py

====================  Rebuild Dev Container  ========================
In VS Code:
Ctrl + Shift + P
→ Dev Containers: Rebuild Container

====================  Cleanup  ========================
# Remove unused containers
docker container prune

# Remove unused images
docker image prune

# Remove unused networks
docker network prune

# General cleanup
docker system prune

Be careful with docker system prune — it removes unused Docker resources.