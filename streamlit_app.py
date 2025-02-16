import ccxt
import time
import requests
import json
import streamlit as st

# 获取交易所实例
def get_exchange_instance(exchange_name):
    if exchange_name == 'Binance':
        return ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'future'}})
    elif exchange_name == 'Bybit':
        return ccxt.bybit({'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
    elif exchange_name == 'MEXC':
        return ccxt.mexc({'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
    elif exchange_name == 'MEXCSPOT':
        return ccxt.mexc({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})
    elif exchange_name == 'OKX':
        return ccxt.okx({'enableRateLimit': True, 'options': {'defaultType': 'future'}})
    elif exchange_name == 'Bitget':
        return ccxt.bitget({'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
    elif exchange_name == 'Huobi':
        return ccxt.huobi({'enableRateLimit': True,'options': {'defaultType': 'future'}})
    elif exchange_name == 'Coinex':
        return ccxt.coinex({'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
    elif exchange_name == 'GateIO':
        return ccxt.gate({'enableRateLimit': True, 'options': {'defaultType': 'swap'}})

# Streamlit UI
st.title('交易对差价监测')

# 输入框和下拉菜单
symbol = st.text_input("币种:", value="BTC")
exchange1 = st.selectbox("交易所1:", ["MEXC", "GateIO", "Bitget", "Phemex", "Lbank", "Hyperliquid", "Aevo", "Huobi", "Coincatch", "Poinex", "XT", "Binance X", "Bybit X", "BybitSPOT X", "MEXCSPOT X", "OKX X","Coinex X", "Bitmart X"], index=0)
exchange2 = st.selectbox("交易所2:", ["MEXC", "GateIO", "Bitget", "Phemex", "Lbank", "Hyperliquid", "Aevo", "Huobi", "Coincatch", "Poinex", "XT", "Binance X", "Bybit X", "BybitSPOT X", "MEXCSPOT X", "OKX X","Coinex X", "Bitmart X"], index=1)

# 根据用户选择的币种和交易所更新参数
def update_parameters():
    global symbol, exchange1_instance, exchange2_instance, pair1, pair2
    symbol = symbol.upper()
    exchange1_instance = get_exchange_instance(exchange1)
    exchange2_instance = get_exchange_instance(exchange2)

    # Update pair1 based on exchange1
    if exchange1_instance and (exchange1_instance.name == "MEXC Global" or exchange1_instance.name == 'Gate.io'):
        pair1 = '_USDT'
    elif exchange1_instance and (exchange1_instance.name == 'Binance' or exchange1_instance.name == 'Bybit' or exchange1_instance.name == 'Coinex'):
        pair1 = 'USDT'
    elif exchange1_instance and exchange1_instance.name == "OKX":
        pair1 = '-USDT-SWAP'
    elif exchange1_instance and exchange1_instance.name == "Bitget":
        pair1 = 'USDT'
    elif exchange1_instance and exchange1_instance.name == "HTX":
        pair1 = '-USDT'
    elif exchange1_instance and exchange1_instance.name == "Phemex":
        pair1 = 'USDT'


    # Update pair2 based on exchange2
    if exchange2_instance and (exchange2_instance.name == "MEXC Global" or exchange2_instance.name == 'Gate.io'):
        pair2 = '_USDT'
    elif exchange2_instance and (exchange2_instance.name == 'Binance' or exchange2_instance.name == 'Bybit' or exchange2_instance.name == 'Coinex'):
        pair2 = 'USDT'
    elif exchange2_instance and exchange2_instance.name == "OKX":
        pair2 = '-USDT-SWAP'
    elif exchange2_instance and exchange2_instance.name == "Bitget":
        pair2 = 'USDT'
    elif exchange2_instance and exchange2_instance.name == "HTX":
        pair2 = '-USDT'
    elif exchange2_instance and exchange2_instance.name == "Phemex":
        pair2 = 'USDT'

# 获取订单簿数据
def ex1_getOrderbook(symbol):
    max_retries = 5  # 最大重试次数
    retry_count = 0

    while retry_count < max_retries:
        try:
            if exchange1 == 'Phemex':
                url = f'https://api.phemex.com/md/v2/orderbook?symbol={symbol}USDT'
                response = requests.get(url).json()
                ex1_ask_px = response['result']['orderbook_p']['asks'][0][0]
                ex1_bid_px = response['result']['orderbook_p']['bids'][0][0]
                ex1_ask_qty = response['result']['orderbook_p']['asks'][0][1]
                ex1_bid_qty = response['result']['orderbook_p']['bids'][0][1]
                return ex1_ask_px, ex1_bid_px, ex1_ask_qty, ex1_bid_qty
            elif exchange1 == 'XT':
                url = f'https://fapi.xt.com/future/market/v1/public/q/depth?symbol={symbol}_USDT&level=1'
                response = requests.get(url).json()
                ex1_ask_px = response['result']['a'][0][0]
                ex1_bid_px = response['result']['b'][0][0]
                ex1_ask_qty = response['result']['a'][0][1]
                ex1_bid_qty = response['result']['b'][0][1]
                return ex1_ask_px, ex1_bid_px, ex1_ask_qty, ex1_bid_qty
            elif exchange1 == 'Coincatch':
                url = f'https://api.coincatch.com/api/mix/v1/market/depth?symbol={symbol}USDT_UMCBL'
                response = requests.get(url).json()
                ex1_bid_px = response['data']['bids'][0][0]
                ex1_ask_px = response['data']['asks'][0][0]
                ex1_bid_qty = response['data']['bids'][0][1]
                ex1_ask_qty = response['data']['asks'][0][1]
                return ex1_ask_px, ex1_bid_px, ex1_ask_qty, ex1_bid_qty
            elif exchange1 == 'Bitmart':
                url = f'https://api-cloud.bitmart.com/contract/public/depth?symbol={symbol}USDT'
                response = requests.get(url).json()
                ex1_bid_px = response['data']['bids'][0][0]
                ex1_ask_px = response['data']['asks'][0][0]
                ex1_bid_qty = response['data']['bids'][0][1]
                ex1_ask_qty = response['data']['asks'][0][1]
                return ex1_ask_px, ex1_bid_px, ex1_ask_qty, ex1_bid_qty
            elif exchange1 == 'Poinex':
                url = f'https://api.pionex.com/api/v1/market/depth?symbol={symbol}_USDT'
                response = requests.get(url).json()
                ex1_bid_px = response['data']['bids'][0][0]
                ex1_ask_px = response['data']['asks'][0][0]
                ex1_bid_qty = response['data']['bids'][0][1]
                ex1_ask_qty = response['data']['asks'][0][1]
                return ex1_ask_px, ex1_bid_px, ex1_ask_qty, ex1_bid_qty
            elif exchange1 == 'BybitSPOT':
                url = f'https://api.bybit.com/spot/v3/public/quote/depth?symbol={symbol}USDT'
                response = requests.get(url).json()
                ex1_ask_px = response['result']['asks'][0][0]
                ex1_bid_px = response['result']['bids'][0][0]
                ex1_ask_qty = response['result']['asks'][0][1]
                ex1_bid_qty = response['result']['bids'][0][1]
                return ex1_ask_px, ex1_bid_px, ex1_ask_qty, ex1_bid_qty
            elif exchange1 == 'Lbank':
                url = f'https://lbkperp.lbank.com/cfd/openApi/v1/pub/marketOrder?depth=1&symbol={symbol}USDT'
                response = requests.get(url).json()
                ex1_bid_px = response['data']['bids'][0]['price']
                ex1_ask_px = response['data']['asks'][0]['price']
                ex1_bid_qty = response['data']['bids'][0]['volume']
                ex1_ask_qty = response['data']['asks'][0]['volume']
                return ex1_ask_px, ex1_bid_px, ex1_ask_qty, ex1_bid_qty
            elif exchange1 == 'Aevo':
                url = f'https://api.aevo.xyz/orderbook?instrument_name={symbol}-PERP'
                response = requests.get(url).json()
                ex1_ask_px = response['asks'][0][0]
                ex1_bid_px = response['bids'][0][0]
                ex1_ask_qty = response['asks'][0][1]
                ex1_bid_qty = response['bids'][0][1]
                return ex1_ask_px, ex1_bid_px, ex1_ask_qty, ex1_bid_qty
            elif exchange1 == 'Hyperliquid':
                url = "https://api.hyperliquid.xyz/info"
                headers = {
                    "content-type": "application/json"
                }
                data = {
                    "type": "l2Book",
                    "coin": symbol
                }
                response = requests.post(url, headers=headers, data=json.dumps(data))
                response.raise_for_status()  # Raise an exception if the response is not successful
                book = response.json()
                if "levels" in book and isinstance(book["levels"], list) and len(book["levels"]) == 2:
                    first_buy = max((float(tick["px"]), float(tick["sz"])) for tick in book["levels"][0])
                    first_sell = min((float(tick["px"]), float(tick["sz"])) for tick in book["levels"][1])
                ex1_bid_px = first_buy[0]
                ex1_ask_px = first_sell[0]
                ex1_bid_qty = first_buy[1]
                ex1_ask_qty = first_sell[1]
                return ex1_ask_px, ex1_bid_px, ex1_ask_qty, ex1_bid_qty
            else:
                response = exchange1_instance.fetchOrderBook(symbol + pair1)
                ex1_ask_px = response['asks'][0][0]
                ex1_bid_px = response['bids'][0][0]
                ex1_ask_qty = response['asks'][0][1]
                ex1_bid_qty = response['bids'][0][1]
                return ex1_ask_px, ex1_bid_px, ex1_ask_qty, ex1_bid_qty
        except (ccxt.ExchangeError, ccxt.NetworkError, ccxt.InvalidOrder, ccxt.RequestTimeout, Exception) as e:
            retry_count += 1
            st.warning(f"获取 {exchange1} 订单簿数据失败，重试中... ({retry_count}/{max_retries})")
            time.sleep(3)
            continue

    st.error(f"无法获取 {exchange1} 订单簿数据，请检查网络或 API 限制。")
    return None, None, None, None

def ex2_getOrderbook(symbol):
    max_retries = 5  # 最大重试次数
    retry_count = 0

    while retry_count < max_retries:
        try:
            if exchange2 == 'Phemex':
                url = f'https://api.phemex.com/md/v2/orderbook?symbol={symbol}USDT'
                response = requests.get(url).json()
                ex2_ask_px = response['result']['orderbook_p']['asks'][0][0]
                ex2_bid_px = response['result']['orderbook_p']['bids'][0][0]
                ex2_ask_qty = response['result']['orderbook_p']['asks'][0][1]
                ex2_bid_qty = response['result']['orderbook_p']['bids'][0][1]
                return ex2_ask_px, ex2_bid_px, ex2_ask_qty, ex2_bid_qty
            elif exchange2 == 'XT':
                url = f'https://fapi.xt.com/future/market/v1/public/q/depth?symbol={symbol}_USDT&level=1'
                response = requests.get(url).json()
                ex2_ask_px = response['result']['a'][0][0]
                ex2_bid_px = response['result']['b'][0][0]
                ex2_ask_qty = response['result']['a'][0][1]
                ex2_bid_qty = response['result']['b'][0][1]
                return ex2_ask_px, ex2_bid_px, ex2_ask_qty, ex2_bid_qty
            elif exchange2 == 'Coincatch':
                url = f'https://api.coincatch.com/api/mix/v1/market/depth?symbol={symbol}USDT_UMCBL'
                response = requests.get(url).json()
                ex2_bid_px = response['data']['bids'][0][0]
                ex2_ask_px = response['data']['asks'][0][0]
                ex2_bid_qty = response['data']['bids'][0][1]
                ex2_ask_qty = response['data']['asks'][0][1]
                return ex2_ask_px, ex2_bid_px, ex2_ask_qty, ex2_bid_qty
            elif exchange2 == 'Bitmart':
                url = f'https://api-cloud.bitmart.com/contract/public/depth?symbol={symbol}USDT'
                response = requests.get(url).json()
                ex2_bid_px = response['data']['bids'][0][0]
                ex2_ask_px = response['data']['asks'][0][0]
                ex2_bid_qty = response['data']['bids'][0][1]
                ex2_ask_qty = response['data']['asks'][0][1]
                return ex2_ask_px, ex2_bid_px, ex2_ask_qty, ex2_bid_qty
            elif exchange2 == 'Poinex':
                url = f'https://api.pionex.com/api/v1/market/depth?symbol={symbol}_USDT'
                response = requests.get(url).json()
                ex2_bid_px = response['data']['bids'][0][0]
                ex2_ask_px = response['data']['asks'][0][0]
                ex2_bid_qty = response['data']['bids'][0][1]
                ex2_ask_qty = response['data']['asks'][0][1]
                return ex2_ask_px, ex2_bid_px, ex2_ask_qty, ex2_bid_qty
            elif exchange2 == 'Lbank':
                url = f'https://lbkperp.lbank.com/cfd/openApi/v1/pub/marketOrder?depth=1&symbol={symbol}USDT'
                response = requests.get(url).json()
                ex2_bid_px = response['data']['bids'][0]['price']
                ex2_ask_px = response['data']['asks'][0]['price']
                ex2_bid_qty = response['data']['bids'][0]['volume']
                ex2_ask_qty = response['data']['asks'][0]['volume']
                return ex2_ask_px, ex2_bid_px, ex2_ask_qty, ex2_bid_qty
            elif exchange2 == 'BybitSPOT':
                url = f'https://api.bybit.com/spot/v3/public/quote/depth?symbol={symbol}USDT'
                response = requests.get(url).json()
                ex2_ask_px = response['result']['asks'][0][0]
                ex2_bid_px = response['result']['bids'][0][0]
                ex2_ask_qty = response['result']['asks'][0][1]
                ex2_bid_qty = response['result']['bids'][0][1]
                return ex2_ask_px, ex2_bid_px, ex2_ask_qty, ex2_bid_qty
            elif exchange2 == 'Aevo':
                url = f'https://api.aevo.xyz/orderbook?instrument_name={symbol}-PERP'
                response = requests.get(url).json()
                ex2_ask_px = response['asks'][0][0]
                ex2_bid_px = response['bids'][0][0]
                ex2_ask_qty = response['asks'][0][1]
                ex2_bid_qty = response['bids'][0][1]
                return ex2_ask_px, ex2_bid_px, ex2_ask_qty, ex2_bid_qty
            elif exchange2 == 'Hyperliquid':
                url = "https://api.hyperliquid.xyz/info"
                headers = {
                    "content-type": "application/json"
                }
                data = {
                    "type": "l2Book",
                    "coin": symbol
                }
                response = requests.post(url, headers=headers, data=json.dumps(data))
                response.raise_for_status()  # Raise an exception if the response is not successful
                book = response.json()
                if "levels" in book and isinstance(book["levels"], list) and len(book["levels"]) == 2:
                    first_buy = max((float(tick["px"]), float(tick["sz"])) for tick in book["levels"][0])
                    first_sell = min((float(tick["px"]), float(tick["sz"])) for tick in book["levels"][1])
                ex2_bid_px = first_buy[0]
                ex2_ask_px = first_sell[0]
                ex2_bid_qty = first_buy[1]
                ex2_ask_qty = first_sell[1]
                return ex2_ask_px, ex2_bid_px, ex2_ask_qty, ex2_bid_qty
            else:
                response = exchange2_instance.fetchOrderBook(symbol + pair2)
                ex2_ask_px = response['asks'][0][0]
                ex2_bid_px = response['bids'][0][0]
                ex2_ask_qty = response['asks'][0][1]
                ex2_bid_qty = response['bids'][0][1]
                return ex2_ask_px, ex2_bid_px, ex2_ask_qty, ex2_bid_qty
        except (ccxt.ExchangeError, ccxt.NetworkError, ccxt.InvalidOrder, ccxt.RequestTimeout, Exception) as e:
            retry_count += 1
            st.warning(f"获取 {exchange2} 订单簿数据失败，重试中... ({retry_count}/{max_retries})")
            time.sleep(3)
            continue

    st.error(f"无法获取 {exchange2} 订单簿数据，请检查网络或 API 限制。")
    return None, None, None, None

# 计算百分比差异
def percentage_diff(start, end):
    return ((start - end)) / ((start + end) / 2) * 100

# 计算价格差异
def price_diff(start, end):
    return (start - end)

# 创建占位符
long_placeholder = st.empty()
diff_long_placeholder = st.empty()
diffprice_long_placeholder = st.empty()
NA_placeholder = st.empty()
short_placeholder = st.empty()
diff_short_placeholder = st.empty()
diffprice_short_placeholder = st.empty()

# 更新显示
def update_display():
    ex1_ask_px, ex1_bid_px, ex1_ask_qty, ex1_bid_qty = ex1_getOrderbook(symbol)
    ex2_ask_px, ex2_bid_px, ex2_ask_qty, ex2_bid_qty = ex2_getOrderbook(symbol)

    if ex1_ask_px is None or ex2_ask_px is None:
        return  # 如果数据获取失败，直接返回

    diff_long = percentage_diff(float(ex1_bid_px), float(ex2_ask_px))
    diff_long = "{:.3f}".format(diff_long)
    diffprice_long = price_diff(float(ex1_bid_px), float(ex2_ask_px))
    diffprice_long = "{:.6f}".format(diffprice_long)

    diff_short = percentage_diff(float(ex2_bid_px), float(ex1_ask_px))
    diff_short = "{:.3f}".format(diff_short)
    diffprice_short = price_diff(float(ex2_bid_px), float(ex1_ask_px))
    diffprice_short = "{:.6f}".format(diffprice_short)

    # 更新占位符内容
    long_placeholder.write(f"{exchange1} 空 | {exchange2} 多 \n{ex1_bid_px} | {ex2_ask_px}")
    diff_long_placeholder.write(f"差价: {diff_long}%")
    diffprice_long_placeholder.write(f"价格差: {diffprice_long}")
    NA_placeholder.write(f"-----------------------------------------")
    short_placeholder.write(f"{exchange1} 多 | {exchange2} 空 \n{ex1_ask_px} | {ex2_bid_px}")
    diff_short_placeholder.write(f"差价: {diff_short}%")
    diffprice_short_placeholder.write(f"价格差: {diffprice_short}")

# 更新参数
update_parameters()

# 主循环
while True:
    update_display()
    time.sleep(1)  # 每秒刷新
