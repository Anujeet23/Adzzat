FROM --platform=linux/amd64 python:3.12.11-slim-bookworm@sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7
RUN apt-get update && apt-get install -y --no-install-recommends bash git tmux procps && rm -rf /var/lib/apt/lists/*
ENV PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
WORKDIR /app
RUN mkdir -p /app/repo /app/submission && chmod 777 /app/submission
COPY eigensolve /app/repo/eigensolve
COPY TASK_CONTRACT.md /app/TASK_CONTRACT.md
COPY reproduce.py /app/reproduce.py
ENV PYTHONPATH=/app/repo
