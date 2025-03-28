from flask import Flask, json, request
import requests
import random
import datetime
import string
import json


api = Flask(__name__)


def randstr(length: int) -> str:
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def modify_stock(isin: str, stock: dict) -> dict:
    new_st = make_stock(isin)
    if isin is not None and len(isin) > 3:
        new_st['isin'] = isin
    if 'name' in stock and len(stock['name']) > 3:
        new_st['name'] = stock['name']
    if 'price' in stock and float(stock['price']) > 0.01:
        new_st['price'] = stock['price']
    return new_st


def make_stock(isin: str = None) -> dict:
    stock: dict = {}
    stock['isin'] = randstr(6) if isin is None else isin
    stock['name'] = randstr(random.randint(5, 11))
    stock['price'] = random.random() * 10000.00
    stock['timestamp'] = datetime.datetime.now().strftime("%B %d, %Y")
    return stock


def make_stocks(qty: int = 0) -> list[dict]:
    if qty <= 0 or qty > 1000:
        qty = 10
    stocks: list[dict] = []
    for _ in range(0, qty):
        stocks.append(make_stock())
    return stocks


@api.route('/stocks', methods=['GET'])
def get_all_stocks():
    return json.dumps(make_stocks(10))


@api.route('/stocks/<id>', methods=['GET'])
def get_stock(id: str):
    return json.dumps(make_stock(id))


@api.route('/stocks', methods=['POST'])
def create_stock():
    new_stock = request.get_json()['stock']
    return json.dumps(modify_stock(new_stock['isin'], new_stock))


@api.route('/stocks/<id>', methods=['PATCH'])
def update_stock(id):
    updating_stock = request.get_json()
    return json.dumps(modify_stock(id, updating_stock))


@api.route('/stocks/<id>', methods=['DELETE'])
def delete_stock(id: str):
    return json.dumps({'message': f'stock {id} is deleted'})



if __name__ == '__main__':
    api.run(host="localhost", port=8080)


