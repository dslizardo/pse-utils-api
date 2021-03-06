from . import redis_store
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from . import app
import requests
import json
import datetime
import decimal

HOST = 'http://www.pse.com.ph/stockMarket/home.html'
HEADERS = {'Referer': HOST}

executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}

job_defaults = {
    'coalesce': True,
    'max_instances': 3
}


def store_stocks():
    scheduler = BackgroundScheduler(executors=executors, job_defaults=job_defaults)
    scheduler.add_job(retrieve_stocks, CronTrigger.from_crontab(app.config['TICKER_CRON']))
    scheduler.start()


def retrieve_stocks():
    print("Getting new stocks " + str(datetime.datetime.now()))
    try:
        r = requests.get(HOST + '?method=getSecuritiesAndIndicesForPublic&ajax=true', headers=HEADERS, timeout=5)
        stocks = r.json()
        if len(stocks) != 0:
            price_as_of = stocks[0]['securityAlias']
            for stock in stocks:
                stock['price_as_of'] = price_as_of
                redis_store.set('stocks:' + stock['securitySymbol'], json.dumps(stock))
            stocks = json.dumps(stocks[1:])
            redis_store.set('stocks:all', stocks)
            top_gainers = get_top_gainers_or_losers(stocks, True)
            redis_store.set('stocks:top_gainers', json.dumps(top_gainers))
            top_losers = get_top_gainers_or_losers(stocks, False)
            redis_store.set('stocks:top_losers', json.dumps(top_losers))
            r = requests.get(HOST + '?method=getTopSecurity&limit=10&ajax=true', headers=HEADERS)
            most_active = (r.json())['records']
            for stock in most_active:
                stock['price_as_of'] = price_as_of
            redis_store.set('stocks:most_active', json.dumps(most_active).replace('lastTradePrice', 'lastTradedPrice'))
    except requests.exceptions.Timeout as err:
        print(err)


def get_top_gainers_or_losers(json_data, flag):
    data = json.loads(json_data)
    sorted_data = sorted(data[1:], key=lambda x: decimal.Decimal(x['percChangeClose']), reverse=flag)
    return sorted_data[:10]
