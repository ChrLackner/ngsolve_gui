FROM ghcr.io/cerbsim/ngapp-base:latest
WORKDIR /app
COPY . .
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0.dev0
RUN pip install --no-cache-dir --break-system-packages \
    "webgpu @ git+https://github.com/CERBSim/webgpu.git" \
    "ngsolve_webgpu @ git+https://github.com/CERBSim/ngsolve_webgpu.git" \
    "ngapp[e2e] @ git+https://github.com/CERBSim/ngapp.git" \
    mkl==2025 ngsolve plotly .
CMD ["pytest", "tests/", "-vv", "-s"]