
# Long-running container for the Nexura HR Gradio app (Render / any Docker host).
# Gradio's request queue needs a persistent process, which Vercel serverless cannot provide.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# app.py binds 0.0.0.0 and reads PORT (Render injects PORT automatically)
CMD ["python", "app.py"]
