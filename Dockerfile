# Slim runtime Dockerfile for UpstreamDrift.
#
# Mirrors the fleet-wide slim-runtime standard documented in
# Repository_Management/docs/operations/slim_docker_runtime_standard.md.
#
# - Base: python:3.12-slim (Debian trixie) instead of miniconda3 (~7 GB savings).
# - Two stages: builder (compiles wheels into /opt/venv) + runtime (ships venv).
# - Optional training stage extends runtime with CUDA/PyTorch for ML workloads.
#
# Budget: runtime stage must stay under 4 GB (enforced in CI).

# --- Stage 1: builder -------------------------------------------------------
FROM python:3.12-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build toolchain for any wheels that need compilation.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    cmake \
    pkg-config \
    libeigen3-dev \
    libboost-all-dev \
    liburdfdom-dev \
    liboctomap-dev \
    libassimp-dev \
    && rm -rf /var/lib/apt/lists/*

# Create an isolated virtualenv we can copy into the runtime stage.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip to a version that carries recent security fixes.
RUN pip install --upgrade "pip>=25.3" setuptools wheel

# Install from requirements.lock. Strip comments/blank lines first.
COPY requirements.lock /tmp/requirements.txt
RUN grep -v '^#' /tmp/requirements.txt | grep -v '^$' > /tmp/filtered_requirements.txt && \
    pip install -r /tmp/filtered_requirements.txt

# Physics engines + API server runtime dependencies.
# simpleeval pinned >=1.0.5 to pick up CVE fix observed in prior Trivy scan.
RUN pip install \
    mujoco>=3.2.3 \
    drake \
    meshcat \
    pin-pink \
    qpsolvers \
    osqp \
    mediapipe>=0.10.0 \
    "imageio[ffmpeg]>=2.31.0" \
    trimesh>=4.0.0 \
    robot_descriptions>=1.12.0 \
    fastapi>=0.126.0 \
    "uvicorn[standard]>=0.24.0" \
    slowapi>=0.1.9 \
    "pydantic[email]>=2.5.0" \
    python-multipart \
    sqlalchemy>=2.0.0 \
    bcrypt>=4.1.0 \
    "PyJWT>=2.10.1" \
    "cryptography>=44.0.1" \
    httpx>=0.25.0 \
    aiofiles \
    python-dateutil \
    websockets \
    "simpleeval>=1.0.5" \
    structlog>=24.1.0 \
    colorama>=0.4.6 \
    # Packages that used to come transitively from the conda base but are
    # imported at module top level by shared code. Keep explicit until they
    # land in requirements.lock (see standard doc, section
    # "Required explicit runtime deps").
    "pandas>=2.0.0" \
    "matplotlib>=3.7.0" \
    "sympy>=1.12" \
    "defusedxml>=0.7.1"


# --- Stage 2: runtime -------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Headless GL/X11 + ffmpeg + curl (for /health probe).
# Trixie package renames are captured in the fleet runbook.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libosmesa6 \
    libglew2.2 \
    libegl1 \
    libglib2.0-0t64 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-keysyms1 \
    libxcb-image0 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxcb-xkb1 \
    libdbus-1-3 \
    patchelf \
    ffmpeg \
    xvfb \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user.
ARG USER_NAME=golfer
ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g ${GROUP_ID} ${USER_NAME} && \
    useradd -m -u ${USER_ID} -g ${GROUP_ID} -s /bin/bash ${USER_NAME}

# Copy the prebuilt venv from the builder.
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/workspace"

RUN mkdir -p /workspace && chown -R ${USER_NAME}:${USER_NAME} /workspace

WORKDIR /workspace

# Ship only what the API needs at runtime.
COPY --chown=${USER_NAME}:${USER_NAME} src/ ./src/
COPY --chown=${USER_NAME}:${USER_NAME} pyproject.toml ./
COPY --chown=${USER_NAME}:${USER_NAME} launch_golf_suite.py ./
COPY --chown=${USER_NAME}:${USER_NAME} start_api_server.py ./
COPY --chown=${USER_NAME}:${USER_NAME} .env.example ./.env.example

USER ${USER_NAME}

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["python3", "-m", "uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8001"]


# --- Stage 3: training (optional) ------------------------------------------
# Extends runtime with CUDA/PyTorch + RL stack for GPU workloads.
FROM runtime AS training

USER root

# PyTorch CUDA wheels are published on the official index.
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cu121 \
    "torch" \
    "torchvision" \
    "torchaudio"

RUN pip install --no-cache-dir \
    gymnasium>=0.29.0 \
    stable-baselines3>=2.0.0 \
    "tensorboard>=2.14.0" \
    "ray[rllib]>=2.9.0"

USER ${USER_NAME}

CMD ["/bin/bash"]
