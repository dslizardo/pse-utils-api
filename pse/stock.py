from . import redis_store
import json

class Stock:
    def __init__(self, security_symbol, price, day_change ):
        self.security_symbol=security_symbol
        self.price=price
        self.day_change=day_change

    def get_stocks(key):
        stocks=[]
        data=redis_store.get('stocks:'+key)
        if data is not None:
            data=json.loads(data)
            if key == 'most_active':
                data=data['records']
            for stock in data:
                s=Stock(stock['securitySymbol'],stock['lastTradedPrice'],str(stock['percChangeClose'])+'%')
                stocks.append(s.serialize())
        return stocks

    def get_stock(key):
        data=redis_store.get('stocks:'+key)
        if data is not None:
            stock=json.loads(data)
            stock=Stock(stock['securitySymbol'],stock['lastTradedPrice'],str(stock['percChangeClose'])+'%')
            data=stock.serialize()
        return data


    def serialize(self):
        return {
            'security_symbol':self.security_symbol,
            'price':self.price,
            'day_change':self.day_change
        }