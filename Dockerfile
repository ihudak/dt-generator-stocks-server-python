FROM python:alpine
LABEL authors="ivan.gudak"
RUN mkdir -p /opt/app
WORKDIR /opt/app
COPY stock_server.py .
COPY requirements.txt .
RUN pip install -r ./requirements.txt
ENTRYPOINT ["python", "./stock_server.py"]
EXPOSE 8080
