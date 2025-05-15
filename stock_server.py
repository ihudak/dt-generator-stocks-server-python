from flask import Flask, json, request
import requests
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base
import os
import random
import datetime
import string
import json
import data_dict
from urllib.parse import quote
import logging
import math

api = Flask(__name__)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
dateformat:str='%F %T.%f' #  "%B %d, %Y"
resp_header = {'ContentType':'application/json'}

# Load settings from env vars
db_usr:str|None = os.getenv("DT_PG_USER")
db_pwd:str|None = os.getenv("DT_PG_PASS")
db_srv:str|None = os.getenv("DBSRV")
db_prt:str|None = os.getenv("DBPORT")
db_dbn:str|None = os.getenv("DB_NAME")
init_st:str|None = os.getenv("INITSTOCKS")
max_st:str|None = os.getenv("MAXSTOCKS")

# failback to defaults if settings are not set (useful for running on dev machines)
if db_usr is None:
    db_usr = 'pguser'
db_pwd = quote('p@ssw0rD!', safe='') if db_pwd is None else quote(db_pwd, safe='')
if db_srv is None:
    db_srv = 'localhost'
if db_prt is None:
    db_prt = '5432'
if db_dbn is None:
    db_dbn = 'dt_stocks'

init_stocks:int=10 if init_st is None else int(init_st)
max_stocks:int=100000 if max_st is None else int(max_st)

# starting without hardwork simulator
simulate_hard_work:bool=False

Base = declarative_base()

class Country(Base):
    __tablename__ = 'countries'

    code:str = db.Column('code', db.String, primary_key=True)
    name:str = db.Column('name', db.String)

class Currency(Base):
    __tablename__ = 'currencies'

    code:str = db.Column('code', db.String, primary_key=True)
    country:str = db.Column('country', db.String)
    name:str = db.Column('name', db.String)

    def get_country(self)->type[Country]|None:
        return session.query(Country).filter(Country.code == self.country).first()

class Stock(Base):
    __tablename__ = 'stocks'

    isin:str = db.Column('isin', db.String, primary_key=True)
    name:str = db.Column('name', db.String)
    price:float = db.Column('price', db.Double)
    currency:str = db.Column('currency', db.String)
    timestamp:str = db.Column('timestamp', db.String)

    def get_currency(self)->type[Currency]|None:
        return session.query(Currency).filter(Currency.code == self.currency).first()

engine = db.create_engine(url="postgresql://{0}:{1}@{2}:{3}/{4}".format(db_usr, db_pwd, db_srv, db_prt, db_dbn))
metadata = db.MetaData()
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def get_timestamp()->str:
    return datetime.datetime.now().strftime(dateformat)[:-3]

if session.query(Currency).count() == 0:
    logger.error(f'CURRENCY MAKER: {get_timestamp()}: no currencies in the DB. creating currencies')
    for c in data_dict.currencies:
        session.execute(db.insert(Currency),
                        [
                            {
                                'code': c,
                                'name': data_dict.currencies[c],
                                'country': data_dict.curr_country[c]
                            }
                        ]
        )


if session.query(Country).count() == 0:
    logger.error(f'COUNTRY MAKER: {get_timestamp()}: no countries in the DB. creating countries')
    for c in data_dict.countries:
        session.execute(db.insert(Country),
                        [
                            {
                                'code': c,
                                'name': data_dict.countries[c]
                            }
                        ]
        )


def get_stock_by_isin(isin:str)->type[Stock]|None:
    try:
        st = session.query(Stock).filter(Stock.isin == isin).first()
        if st is None:
            logger.error(f'STOCK EXISTS: {get_timestamp()}: stock {isin} does not exist')
        else:
            logger.info(f'STOCK EXISTS: {get_timestamp()}: stock {isin} exists')
        return st
    except NoResultFound:
        logger.error(f'STOCK EXISTS: {get_timestamp()}: stock {isin} does not exist')
        return None


def check_stock_exists_by_isin(isin:str)->bool:
    return get_stock_by_isin(isin=isin) is not None


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
    logger.info(f'STOCK MAKER: {get_timestamp()}: making a random stock')
    stock: dict = {}
    stock['isin'] = randstr(6) if isin is None else isin
    stock['name'] = randstr(random.randint(5, 11))
    stock['price'] = random.random() * 10000.00
    stock['currency'] = list(data_dict.currencies.keys())[random.randint(0, len(data_dict.currencies) - 1)]
    stock['timestamp'] = get_timestamp()
    return stock


def make_stocks(qty: int = 0) -> list[dict]:
    if qty <= 0 or qty > max_stocks:
        qty = 100
    logger.info(f'STOCKS MAKER: {get_timestamp()}: creating {qty} stocks')
    stocks: list[dict] = []
    for _ in range(0, qty):
        st = make_stock()
        stocks.append(st)
        session.execute(db.insert(Stock),[st])
    return stocks


def get_stock_dict(s:type[Stock]) -> dict:
    curr = session.query(Currency).filter(Currency.code == s.currency).first()

    cntr = session.query(Country).filter(Country.code == curr.country).first()

    st = {
        'isin': s.isin,
        'name': s.name,
        'price': s.price,
        'timestamp': s.timestamp,
        'currency': {
            'code': s.currency,
            'name': curr.name,
            'country': {
                'code': curr.country,
                'name': cntr.name
            }
        }
    }

    logger.info(f'DICT: {get_timestamp()}: jsoning stock {s.isin}')
    return st

@api.route('/stocks', methods=['GET'])
def get_all_stocks():
    if session.query(Stock).count() == 0:
        num_stocks:int=init_stocks
        logger.warning(f'GET ALL STOCKS: {get_timestamp()}: no stocks. creating random {num_stocks} stocks')
        make_stocks(qty=num_stocks)
    else:
        hw_simulator()

    # make 1:N query problem
    stocks = session.query(Stock).all()

    json_stocks:list[dict] = []
    for s in stocks:
        json_stocks.append(get_stock_dict(s))
        logger.info(f'GET ALL STOCKS: {get_timestamp()}: jsoning stock {s.isin} to return')
    return json.dumps(json_stocks), 200, resp_header


@api.route('/stocks/<id>', methods=['GET'])
def get_stock(id: str):
    # make 1:N query problem
    s = get_stock_by_isin(isin=id)
    if s is None:
        logger.error(f'GET STOCK: {get_timestamp()}: stock {id} is not found')
        return json.dumps({'message': f'stock {id} is not found'}), 404, resp_header
    logger.info(f'GET STOCK: {get_timestamp()}: jsoning stock {s.isin} to return')
    return json.dumps(get_stock_dict(s)), 200, resp_header

@api.route('/stocks', methods=['POST'])
def create_stock():
    new_stock = request.get_json()['stock']

    if check_stock_exists_by_isin(isin=new_stock['isin']):
        logger.error(f'CREATE STOCK: {get_timestamp()}: stock {id} already exists')
        return json.dumps({'message': f'stock {id} already exists'}), 409, resp_header

    stock: dict = {
        'isin': new_stock['isin'],
        'name': new_stock['name'],
        'price': float(new_stock['price']),
        'currency': new_stock['currency'] if 'currency' in new_stock else list(data_dict.currencies.keys())[random.randint(0, len(data_dict.currencies) - 1)],
        'timestamp': get_timestamp()
    }

    session.execute(db.insert(Stock),[stock])

    s = get_stock_by_isin(isin=new_stock['isin'])
    logger.info(f'CREATE STOCK: {get_timestamp()}: jsoning stock {s.isin} to return')
    return json.dumps(get_stock_dict(s)), 200, resp_header


@api.route('/stocks/<id>', methods=['PATCH'])
def update_stock(id):
    updating_stock = request.get_json()['stock']

    if not check_stock_exists_by_isin(isin=id):
        logger.error(f'UPDATE STOCK: {get_timestamp()}: stock {id} is not found')
        return json.dumps({'message': f'stock {id} is not found'}), 404, resp_header

    logger.info(f'UPDATE STOCK: {get_timestamp()}: updating stock {id}')
    session.execute(
        db.update(Stock).where(Stock.isin == id).values(
            name = updating_stock['name'],
            price = float(updating_stock['price']),
            currency = updating_stock['currency'],
            timestamp = get_timestamp()
        )
    )
    s = get_stock_by_isin(isin=id)
    logger.info(f'UPDATE STOCK: {get_timestamp()}: jsoning stock {s.isin} to return')
    return json.dumps(get_stock_dict(s)), 200, resp_header


@api.route('/stocks/<id>', methods=['DELETE'])
def delete_stock(id: str):
    if not check_stock_exists_by_isin(isin=id):
        logger.error(f'DELETE STOCK: {get_timestamp()}: stock {id} is not found')
        return json.dumps({'message': f'stock {id} is not found'}), 404, resp_header

    logger.warning(f'DELETE STOCK: {get_timestamp()}: deleting stock {id}')
    session.execute(db.delete(Stock).where(Stock.isin == id))
    return json.dumps({'message': f'stock {id} is deleted'}), 200, resp_header


@api.route('/hardwork', methods=['POST'])
def toggle_hard_work():
    updating_stock = request.get_json()
    global simulate_hard_work
    simulate_hard_work = updating_stock['hw']
    logger.info(f'HARDWORK TOGGLE: {get_timestamp()}: Setting HW: {simulate_hard_work}')
    return json.dumps({'message': f'Hard Work is set to {simulate_hard_work}'}), 200, resp_header


def hw_simulator():
    if not simulate_hard_work:
        logger.info(f'HARDWORKER: {get_timestamp()}: No HW')
        return
    stocks = session.query(Stock).all()
    logger.error(f'HARDWORKER: {get_timestamp()}: Working Hard...')
    prices:list=[]
    for s in stocks:
        new_price = math.sqrt(math.sqrt(s.price * s.price * s.price))

        #### START OF THE HARDWORK BLOCK
        prices.append(s.price)
        prices.append(s.price * s.price * s.price)
        prices.append(math.sqrt(s.price * s.price * s.price))
        prices.append(math.sqrt(math.sqrt(s.price * s.price * s.price)))
        prices.append(math.sqrt(new_price * new_price * new_price))
        prices.append(math.sqrt(new_price * new_price * s.price))
        prices.append(math.sqrt(new_price * s.price * s.price))
        prices.append(math.sqrt(math.sqrt(new_price * new_price * new_price)))
        prices.append(math.sqrt(math.sqrt(new_price * new_price * s.price)))
        prices.append(math.sqrt(math.sqrt(new_price * s.price * s.price)))
        #### END OF HARDWORK BLOCK

        logger.info(f'HARDWORKER: {get_timestamp()}: Stock {s.isin} price has changed from {s.price} to {new_price}')
        session.execute(
            db.update(Stock).where(Stock.isin == s.isin).values(
                price = new_price,
                timestamp = get_timestamp()
            )
        )


if __name__ == '__main__':
    port:int=8080
    logger.info(f'INIT: {get_timestamp()}: starting server on port {port}')
    api.run(host="0.0.0.0", port=port)
