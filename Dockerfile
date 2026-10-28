FROM python:3.12-slim

# LightGBM needs libgomp for OpenMP (even with OMP_NUM_THREADS=1)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download sentence-transformers model so the container works fully offline
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code and artifacts
COPY risk_model/ risk_model/
COPY compliance_assistant/ compliance_assistant/
COPY dashboard/ dashboard/
COPY knowledge_graph/ knowledge_graph/
COPY data/processed/ data/processed/

# Thread-safety: prevent LightGBM + PyTorch OpenMP deadlock
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV TOKENIZERS_PARALLELISM=false
ENV TRANSFORMERS_OFFLINE=1

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
