FROM python:alpine
ARG FLAVOR=alpine
LABEL authors="ivan.gudak"
RUN mkdir -p /opt/app
WORKDIR /opt/app
COPY *.py .
COPY requirements.txt .

# install unzip and curl
RUN if [ "$FLAVOR" = "alpine" ]; then \
      apk add --no-cache --update libpq-dev; \
    else \
      apt-get update && \
      apt-get install -y libpq-dev && \
      rm -rf /var/lib/apt/lists/* ; \
    fi

RUN pip install psycopg2-binary
RUN pip install -r ./requirements.txt
ENTRYPOINT ["python", "./stock_server.py"]
EXPOSE 8080
