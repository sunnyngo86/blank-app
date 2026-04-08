import time
import requests
import json
import streamlit as st

st.set_page_config(
    page_title="Sunny Bot",
    page_icon=":rocket:",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# 禁用工具栏
hide_streamlit_style = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .viewerBadge_container__1QSob {display: none;}
        .stDeployButton {display: none;}
        .stApp [data-testid="stToolbar"] {display: none;}
        .stApp [data-testid="stDecoration"] {display: none;}
        .stApp [data-testid="stStatusWidget"] {display: none;}
        .stApp [data-testid="stHeader"] {display: none;}
        .stApp [data-testid="stSidebar"] {display: none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

hide_footer_js = """
    <script>
        function hideFooter() {
            const footer = document.querySelector("footer");
            if (footer) { footer.style.display = "none"; }
            const createdBy = document.querySelector("[data-testid='stFooter']");
            if (createdBy) { createdBy.style.display = "none"; }
        }
        setInterval(hideFooter, 100);
    </script>
"""
st.components.v1.html(hide_footer_js, height=0, width=0)

# ============================================================
# 通用 headers，模拟浏览器请求以绕过部分 IP/UA 封锁
# ============================================================
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# ============================================================
# 如果你有 Cloudflare Worker 代理，填入 URL（末尾不带 /）
# 例如: "https://my-proxy.xxx.workers.dev"
# Worker 需要支持: GET /?url=<encoded_target_url>
# 如果没有代理，留空字符串即可
# ============================================================
CF_WORKER_PROXY = ""


def fetch_json(url, method="GET", headers=None, json_body=None, timeout=10):
    """统一的请求函数，支持代理回退"""
    if headers is None:
        headers = BROWSER_HEADERS.copy()
    else:
        merged = BROWSER_HEADERS.copy()
        merged.update(headers)
        headers = merged

    try:
        if method == "POST":
            resp = requests.post(url, headers=headers, json=json_body, timeout=timeout)
        else:
            resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        # 如果直接请求失败且有代理，走代理重试
        if CF_WORKER_PROXY:
            try:
                proxy_url = f"{CF_WORKER_PROXY}/?url={requests.utils.quote(url, safe='')}"
                if method == "POST":
                    resp = requests.post(proxy_url, headers=headers, json=json_body, timeout=timeout)
                else:
                    resp = requests.get(proxy_url, headers=headers, timeout=timeout)
                resp.raise_for_status()
                return resp.json()
            except Exception:
                pass
        raise e


# ============================================================
# 各交易所 orderbook 抓取函数（全部使用 REST API，不依赖 ccxt）
# 返回: (ask_price, bid_price, ask_qty, bid_qty)
# ============================================================

def get_orderbook_binance(symbol):
    """Binance USDT-M 合约"""
    url = f"https://fapi.binance.com/fapi/v1/depth?symbol={symbol}USDT&limit=5"
    data = fetch_json(url)
    return data['asks'][0][0], data['bids'][0][0], data['asks'][0][1], data['bids'][0][1]


def get_orderbook_bybit(symbol):
    """Bybit 线性合约 (V5 API)"""
    url = f"https://api.bybit.com/v5/market/orderbook?category=linear&symbol={symbol}USDT&limit=1"
    data = fetch_json(url)
    book = data['result']
    return book['a'][0][0], book['b'][0][0], book['a'][0][1], book['b'][0][1]


def get_orderbook_bybit_spot(symbol):
    """Bybit 现货"""
    url = f"https://api.bybit.com/v5/market/orderbook?category=spot&symbol={symbol}USDT&limit=1"
    data = fetch_json(url)
    book = data['result']
    return book['a'][0][0], book['b'][0][0], book['a'][0][1], book['b'][0][1]


def get_orderbook_okx(symbol):
    """OKX 永续合约"""
    url = f"https://www.okx.com/api/v5/market/books?instId={symbol}-USDT-SWAP&sz=1"
    data = fetch_json(url)
    book = data['data'][0]
    return book['asks'][0][0], book['bids'][0][0], book['asks'][0][1], book['bids'][0][1]


def get_orderbook_bitget(symbol):
    """Bitget 永续合约 (V2 API)"""
    url = f"https://api.bitget.com/api/v2/mix/market/depth?productType=USDT-FUTURES&symbol={symbol}USDT&limit=1"
    data = fetch_json(url)
    book = data['data']
    return book['asks'][0][0], book['bids'][0][0], book['asks'][0][1], book['bids'][0][1]


def get_orderbook_mexc(symbol):
    """MEXC 合约"""
    url = f"https://contract.mexc.com/api/v1/contract/depth/{symbol}_USDT"
    data = fetch_json(url)
    return data['data']['asks'][0][0], data['data']['bids'][0][0], data['data']['asks'][0][1], data['data']['bids'][0][1]


def get_orderbook_mexc_spot(symbol):
    """MEXC 现货"""
    url = f"https://api.mexc.com/api/v3/depth?symbol={symbol}USDT&limit=5"
    data = fetch_json(url)
    return data['asks'][0][0], data['bids'][0][0], data['asks'][0][1], data['bids'][0][1]


def get_orderbook_gate(symbol):
    """Gate.io 永续合约"""
    url = f"https://api.gateio.ws/api/v4/futures/usdt/order_book?contract={symbol}_USDT&limit=1"
    data = fetch_json(url)
    return data['asks'][0]['p'], data['bids'][0]['p'], data['asks'][0]['s'], data['bids'][0]['s']


def get_orderbook_huobi(symbol):
    """HTX (Huobi) 合约"""
    url = f"https://api.hbdm.com/linear-swap-ex/market/depth?contract_code={symbol}-USDT&type=step0"
    data = fetch_json(url)
    tick = data['tick']
    return tick['asks'][0][0], tick['bids'][0][0], tick['asks'][0][1], tick['bids'][0][1]


def get_orderbook_coinex(symbol):
    """Coinex 永续合约"""
    url = f"https://api.coinex.com/v2/futures/depth?market={symbol}USDT&limit=5&interval=0"
    data = fetch_json(url)
    book = data['data']
    return book['asks'][0][0], book['bids'][0][0], book['asks'][0][1], book['bids'][0][1]


def get_orderbook_phemex(symbol):
    """Phemex"""
    url = f"https://api.phemex.com/md/v2/orderbook?symbol={symbol}USDT"
    data = fetch_json(url)
    book = data['result']['orderbook_p']
    return book['asks'][0][0], book['bids'][0][0], book['asks'][0][1], book['bids'][0][1]


def get_orderbook_xt(symbol):
    """XT 合约"""
    url = f"https://fapi.xt.com/future/market/v1/public/q/depth?symbol={symbol}_USDT&level=1"
    data = fetch_json(url)
    return data['result']['a'][0][0], data['result']['b'][0][0], data['result']['a'][0][1], data['result']['b'][0][1]


def get_orderbook_coincatch(symbol):
    """Coincatch"""
    url = f"https://api.coincatch.com/api/mix/v1/market/depth?symbol={symbol}USDT_UMCBL"
    data = fetch_json(url)
    return data['data']['asks'][0][0], data['data']['bids'][0][0], data['data']['asks'][0][1], data['data']['bids'][0][1]


def get_orderbook_bitmart(symbol):
    """Bitmart 合约"""
    url = f"https://api-cloud.bitmart.com/contract/public/depth?symbol={symbol}USDT"
    data = fetch_json(url)
    return data['data']['asks'][0][0], data['data']['bids'][0][0], data['data']['asks'][0][1], data['data']['bids'][0][1]


def get_orderbook_poinex(symbol):
    """Pionex"""
    url = f"https://api.pionex.com/api/v1/market/depth?symbol={symbol}_USDT"
    data = fetch_json(url)
    return data['data']['asks'][0][0], data['data']['bids'][0][0], data['data']['asks'][0][1], data['data']['bids'][0][1]


def get_orderbook_lbank(symbol):
    """Lbank"""
    url = f"https://lbkperp.lbank.com/cfd/openApi/v1/pub/marketOrder?depth=1&symbol={symbol}USDT"
    data = fetch_json(url)
    return (data['data']['asks'][0]['price'], data['data']['bids'][0]['price'],
            data['data']['asks'][0]['volume'], data['data']['bids'][0]['volume'])


def get_orderbook_aevo(symbol):
    """Aevo"""
    url = f"https://api.aevo.xyz/orderbook?instrument_name={symbol}-PERP"
    data = fetch_json(url)
    return data['asks'][0][0], data['bids'][0][0], data['asks'][0][1], data['bids'][0][1]


def get_orderbook_hyperliquid(symbol):
    """Hyperliquid"""
    url = "https://api.hyperliquid.xyz/info"
    body = {"type": "l2Book", "coin": symbol}
    data = fetch_json(url, method="POST", headers={"content-type": "application/json"}, json_body=body)
    if "levels" in data and isinstance(data["levels"], list) and len(data["levels"]) == 2:
        first_buy = max((float(tick["px"]), float(tick["sz"])) for tick in data["levels"][0])
        first_sell = min((float(tick["px"]), float(tick["sz"])) for tick in data["levels"][1])
        return first_sell[0], first_buy[0], first_sell[1], first_buy[1]
    raise ValueError("Hyperliquid 返回数据格式异常")


# ============================================================
# 交易所名称 → 函数映射
# ============================================================
EXCHANGE_FUNCS = {
    "Binance":      get_orderbook_binance,
    "Bybit":        get_orderbook_bybit,
    "BybitSPOT":    get_orderbook_bybit_spot,
    "OKX":          get_orderbook_okx,
    "Bitget":       get_orderbook_bitget,
    "MEXC":         get_orderbook_mexc,
    "MEXCSPOT":     get_orderbook_mexc_spot,
    "GateIO":       get_orderbook_gate,
    "Huobi":        get_orderbook_huobi,
    "Coinex":       get_orderbook_coinex,
    "Phemex":       get_orderbook_phemex,
    "XT":           get_orderbook_xt,
    "Coincatch":    get_orderbook_coincatch,
    "Bitmart":      get_orderbook_bitmart,
    "Poinex":       get_orderbook_poinex,
    "Lbank":        get_orderbook_lbank,
    "Aevo":         get_orderbook_aevo,
    "Hyperliquid":  get_orderbook_hyperliquid,
}

EXCHANGE_LIST = list(EXCHANGE_FUNCS.keys())


def get_orderbook(exchange_name, symbol):
    """统一入口：获取指定交易所的 orderbook"""
    max_retries = 3
    func = EXCHANGE_FUNCS.get(exchange_name)
    if func is None:
        st.error(f"不支持的交易所: {exchange_name}")
        return None, None, None, None

    for attempt in range(1, max_retries + 1):
        try:
            ask_px, bid_px, ask_qty, bid_qty = func(symbol)
            return ask_px, bid_px, ask_qty, bid_qty
        except Exception as e:
            if attempt < max_retries:
                st.warning(f"获取 {exchange_name} 数据失败 ({attempt}/{max_retries}): {e}")
                time.sleep(2)
            else:
                st.error(f"无法获取 {exchange_name} 订单簿数据: {e}")
                return None, None, None, None


# ============================================================
# Streamlit UI
# ============================================================
st.title('交易对差价监测')

symbol = st.text_input("币种:", value="BTC").upper()
exchange1 = st.selectbox("交易所1:", EXCHANGE_LIST, index=EXCHANGE_LIST.index("MEXC"))
exchange2 = st.selectbox("交易所2:", EXCHANGE_LIST, index=EXCHANGE_LIST.index("GateIO"))

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
    ex1_ask_px, ex1_bid_px, ex1_ask_qty, ex1_bid_qty = get_orderbook(exchange1, symbol)
    ex2_ask_px, ex2_bid_px, ex2_ask_qty, ex2_bid_qty = get_orderbook(exchange2, symbol)

    if ex1_ask_px is None or ex2_ask_px is None:
        return

    diff_long = percentage_diff(float(ex1_bid_px), float(ex2_ask_px))
    diff_long = "{:.3f}".format(diff_long)
    diffprice_long = price_diff(float(ex1_bid_px), float(ex2_ask_px))
    diffprice_long = "{:.6f}".format(diffprice_long)

    diff_short = percentage_diff(float(ex2_bid_px), float(ex1_ask_px))
    diff_short = "{:.3f}".format(diff_short)
    diffprice_short = price_diff(float(ex2_bid_px), float(ex1_ask_px))
    diffprice_short = "{:.6f}".format(diffprice_short)

    long_placeholder.markdown(
        f"<font size='4'>{exchange1} 空 | {exchange2} 多</font>\n"
        f"<font size='4'>{ex1_bid_px} | {ex2_ask_px}</font>",
        unsafe_allow_html=True
    )
    diff_long_placeholder.markdown(f"<b><font size='6'>价差: {diff_long}%</font></b>", unsafe_allow_html=True)
    diffprice_long_placeholder.markdown(f"<font size='4'>价格差: {diffprice_long}</font>", unsafe_allow_html=True)
    NA_placeholder.write(f"-----------------------------------------")
    short_placeholder.markdown(
        f"<font size='4'>{exchange1} 多 | {exchange2} 空</font>\n"
        f"<font size='4'>{ex1_ask_px} | {ex2_bid_px}</font>",
        unsafe_allow_html=True
    )
    diff_short_placeholder.markdown(f"<b><font size='6'>价差: {diff_short}%</font></b>", unsafe_allow_html=True)
    diffprice_short_placeholder.markdown(f"<font size='4'>价格差: {diffprice_short}</font>", unsafe_allow_html=True)

# 主循环
while True:
    update_display()
    time.sleep(1)
