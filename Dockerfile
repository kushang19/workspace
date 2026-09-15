FROM python:3.12-slim

# Install Git, Node.js 22 and npm
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl gnupg git \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
       | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" \
       > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /etc/apt/sources.list.d/nodesource.list

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY streamlit_app.py .
COPY agent ./agent
COPY tools ./tools

EXPOSE 10000

CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=10000"]
