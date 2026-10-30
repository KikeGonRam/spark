FROM python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337

ARG TARGETARCH
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-${TARGETARCH} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SPARK_LOCAL_DIRS=/tmp/spark \
    SPARK_LOCAL_IP=127.0.0.1 \
    HOME=/home/analytics

RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 analytics \
    && useradd --uid 10001 --gid analytics --create-home analytics

WORKDIR /app
COPY requirements-dashboard.txt requirements-dashboard.lock ./
RUN --mount=type=cache,target=/root/.cache/pip \
    PIP_CACHE_DIR=/root/.cache/pip pip install --only-binary=:all: --no-binary=pyspark --require-hashes --timeout 180 --retries 8 --index-url https://pypi.org/simple -r requirements-dashboard.lock
RUN python -m pip install --only-binary=:all: --no-cache-dir --index-url https://pypi.org/simple --upgrade pip==26.2.2

COPY --chown=analytics:analytics config/ ./config/
COPY --chown=analytics:analytics dashboard/ ./dashboard/
COPY --chown=analytics:analytics .streamlit/ ./.streamlit/
RUN mkdir -p /app/spark-warehouse /app/data \
    && chown -R analytics:analytics /app/spark-warehouse /app/data
USER 10001:10001

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=4)" || exit 1

CMD ["streamlit", "run", "dashboard/app.py", "--server.headless=true", "--server.port=8501", "--server.address=0.0.0.0", "--browser.gatherUsageStats=false"]
