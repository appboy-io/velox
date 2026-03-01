FROM eclipse-temurin:21-jre-jammy

ARG GATLING_VERSION=3.9.5
ARG PYTHON_VERSION=3.10

# Install Python
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv unzip curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Gatling
RUN curl -fsSL https://repo1.maven.org/maven2/io/gatling/highcharts/gatling-charts-highcharts-bundle/${GATLING_VERSION}/gatling-charts-highcharts-bundle-${GATLING_VERSION}-bundle.zip \
        -o /tmp/gatling.zip && \
    unzip /tmp/gatling.zip -d /opt && \
    mv /opt/gatling-charts-highcharts-bundle-${GATLING_VERSION} /opt/gatling && \
    rm /tmp/gatling.zip

ENV GATLING_HOME=/opt/gatling
ENV PATH="${GATLING_HOME}/bin:${PATH}"

# Install Velox
WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
RUN pip3 install --no-cache-dir .

WORKDIR /tests
ENTRYPOINT ["velox"]
