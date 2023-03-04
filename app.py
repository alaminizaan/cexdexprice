from flask import Flask, render_template, request
import ccxt.async_support as ccxt
import asyncio
import aiohttp

app = Flask(__name__)

# Set up the list of exchanges
cex_exchanges = ['binance', 'bitfinex', 'bitstamp', 'coinbase', 'gemini', 'kraken', 'kucoin', 'okex', 'poloniex']
dex_exchanges = ['uniswap', 'sushiswap', 'pancakeswap', 'quickswap']

async def fetch_exchange_ticker(exchange, symbol):
    try:
        async with aiohttp.ClientSession() as session:
            exchange_obj = getattr(ccxt.async_support, exchange)({
                'enableRateLimit': True,
                'session': session,
            })
            ticker = await exchange_obj.fetch_ticker(symbol)
            return ticker
    except Exception as e:
        print(f"Error fetching {symbol} ticker from {exchange}: {e}")
        return None

async def fetch_exchange_data(exchange):
    try:
        async with aiohttp.ClientSession() as session:
            exchange_obj = getattr(ccxt.async_support, exchange)({
                'enableRateLimit': True,
                'session': session,
            })
            tickers = await exchange_obj.fetch_tickers()
            return tickers
    except Exception as e:
        print(f"Error fetching data from {exchange}: {e}")
        return None

async def fetch_all_exchange_data(exchanges):
    tasks = [fetch_exchange_data(exchange) for exchange in exchanges]
    results = await asyncio.gather(*tasks)
    return dict(zip(exchanges, results))

async def get_all_prices(exchange):
    tickers = await fetch_exchange_data(exchange)
    prices = {}
    for symbol, ticker in tickers.items():
        prices[symbol] = {
            'last_price': ticker['last'],
            'volume': ticker['quoteVolume'],
            'liquidity': ticker['baseVolume']
        }
    return prices

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        exchange = request.form['exchange']
        exchange_type = request.form['exchange_type']
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if exchange_type == 'cex':
            prices = loop.run_until_complete(get_all_prices(exchange))
            return render_template('cex_prices.html', prices=prices, exchange=exchange)
        else:
            tickers = loop.run_until_complete(fetch_exchange_data(exchange))
            return render_template('dex_prices.html', tickers=tickers, exchange=exchange)
    else:
        return render_template('index.html', cex_exchanges=cex_exchanges, dex_exchanges=dex_exchanges)

if __name__ == '__main__':
    app.run(debug=True)
