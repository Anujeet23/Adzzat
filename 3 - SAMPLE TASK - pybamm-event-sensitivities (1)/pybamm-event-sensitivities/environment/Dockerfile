FROM --platform=linux/amd64 python:3.12.11-slim-bookworm@sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7
RUN apt-get update && apt-get install -y --no-install-recommends bash git tmux procps asciinema libgomp1 && rm -rf /var/lib/apt/lists/*
ENV PYBAMM_DISABLE_TELEMETRY=true OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg MPLCONFIGDIR=/tmp/matplotlib
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --only-binary=:all: -r /tmp/requirements.txt
WORKDIR /app
COPY upstream.tar.gz /tmp/upstream.tar.gz
RUN mkdir -p /app/repo /app/submission && tar -xzf /tmp/upstream.tar.gz -C /app/repo && rm /tmp/upstream.tar.gz && printf "version = '25.4.0'\n" > /app/repo/src/pybamm/_version.py && chmod 777 /app/submission
COPY TASK_CONTRACT.md /app/TASK_CONTRACT.md
COPY reproduce.py /app/reproduce.py
ENV PYTHONPATH=/app/repo/src
