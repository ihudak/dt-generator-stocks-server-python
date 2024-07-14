from flask import Flask, json, request
import requests
import random
import datetime
import string
import json
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    DEFAULT_COMPRESSION,
    DEFAULT_ENDPOINT,
    DEFAULT_TIMEOUT,
    DEFAULT_TRACES_EXPORT_PATH,
    OTLPSpanExporter,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.resources import SERVICE_NAME, Resource


# Service name is required for most backends
resource = Resource(attributes={
    SERVICE_NAME: "stock_server_python"
})
provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:14499/otlp/v1/traces")
processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(processor)
# Sets the global default tracer provider
trace.set_tracer_provider(provider)

# Creates a tracer from the global tracer provider
tracer = trace.get_tracer("stock.server.python")

api = Flask(__name__)


@tracer.start_as_current_span("rand_str")
def randstr(length: int) -> str:
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


@tracer.start_as_current_span("modify_stock")
def modify_stock(isin: str, stock: dict) -> dict:
    new_st = make_stock(isin)
    if isin is not None and len(isin) > 3:
        new_st['isin'] = isin
    if 'name' in stock and len(stock['name']) > 3:
        new_st['name'] = stock['name']
    if 'price' in stock and float(stock['price']) > 0.01:
        new_st['price'] = stock['price']
    return new_st


@tracer.start_as_current_span("create_stock")
def make_stock(isin: str = None) -> dict:
    stock: dict = {}
    stock['isin'] = randstr(6) if isin is None else isin
    stock['name'] = randstr(random.randint(5, 11))
    stock['price'] = random.random() * 10000.00
    stock['timestamp'] = datetime.datetime.now().strftime("%B %d, %Y")
    return stock


@tracer.start_as_current_span("create_stocks")
def make_stocks(qty: int = 0) -> list[dict]:
    if qty <= 0 or qty > 1000:
        qty = 10
    stocks: list[dict] = []
    for i in range(0, qty):
        stocks.append(make_stock())
    return stocks


@tracer.start_as_current_span("get_all_stocks")
@api.route('/stocks', methods=['GET'])
def get_all_stocks():
    return json.dumps(make_stocks(10))


@tracer.start_as_current_span("get_stock")
@api.route('/stocks/<id>', methods=['GET'])
def get_stock(id: str):
    return json.dumps(make_stock(id))


@tracer.start_as_current_span("create_stock")
@api.route('/stocks', methods=['POST'])
def create_stock():
    new_stock = request.get_json()['stock']
    return json.dumps(modify_stock(new_stock['isin'], new_stock))


@tracer.start_as_current_span("update_stock")
@api.route('/stocks/<id>', methods=['PATCH'])
def update_stock(id):
    updating_stock = request.get_json()
    return json.dumps(modify_stock(id, updating_stock))


@tracer.start_as_current_span("delete_stock")
@api.route('/stocks/<id>', methods=['DELETE'])
def delete_stock(id: str):
    return json.dumps({'message': f'stock {id} is deleted'})



if __name__ == '__main__':
    api.run(host="localhost", port=8080)


