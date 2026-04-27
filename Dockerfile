FROM ghcr.io/cerbsim/ngapp-base:latest
WORKDIR /app
COPY . .
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0.dev0
RUN pip install --no-cache-dir --break-system-packages .
CMD ["pytest", "tests/", "-vv", "-s"]