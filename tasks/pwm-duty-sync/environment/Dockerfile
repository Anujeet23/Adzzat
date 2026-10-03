FROM --platform=linux/amd64 python:3.12.11-slim-bookworm@sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7
RUN apt-get update && apt-get install -y --no-install-recommends bash git tmux procps iverilog build-essential make && rm -rf /var/lib/apt/lists/*
ENV PYTHONDONTWRITEBYTECODE=1
RUN pip install --no-cache-dir cocotb==2.1.0
WORKDIR /app
RUN mkdir -p /app/repo /app/submission && chmod 777 /app/submission
COPY pwm_gen.v /app/repo/pwm_gen.v
COPY TASK_CONTRACT.md /app/TASK_CONTRACT.md
COPY reproduce.py /app/reproduce.py
COPY reproduce_test.py /app/reproduce_test.py
COPY Makefile /app/Makefile
