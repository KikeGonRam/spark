# Imagen liviana solo para el dashboard (main_dashboard.py) -- no para las
# demas unidades del curso, que dependen de librerias mucho mas pesadas
# (torch, tensorflow) que no hacen falta para correr el sitio de negocio.
FROM python:3.11-slim

# PySpark necesita un JRE real -- sin esto SparkSession.builder.getOrCreate()
# truena buscando "java" en el PATH.
RUN apt-get update \
    && apt-get install -y --no-install-recommends default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/default-java
WORKDIR /app

COPY requirements-dashboard.txt .
RUN pip install --no-cache-dir -r requirements-dashboard.txt

COPY config/ ./config/
COPY unidades/unidad_5_visualizacion/ ./unidades/unidad_5_visualizacion/

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=5 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "unidades/unidad_5_visualizacion/main_dashboard.py", \
     "--server.headless=true", "--server.port=8501", "--server.address=0.0.0.0"]
