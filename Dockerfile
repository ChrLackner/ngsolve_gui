FROM ghcr.io/cerbsim/ngapp-base:latest
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir --break-system-packages \
    "webgpu @ git+https://github.com/CERBSim/webgpu.git" \
    "ngsolve_webgpu @ git+https://github.com/CERBSim/ngsolve_webgpu.git" \
    "ngapp[e2e] @ git+https://github.com/CERBSim/ngapp.git" \
    plotly
RUN pip install --no-cache-dir --break-system-packages --pre --upgrade ngsolve
RUN pip install --no-cache-dir --break-system-packages --no-deps .
CMD ["pytest", "tests/", "-vv", "-s"]
