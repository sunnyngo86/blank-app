import time
import requests
import json
import streamlit as st
import base64

st.set_page_config(
    page_title="Sunny Bot",
    page_icon=":rocket:",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

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
# CF Worker 代理 (编码存储)
# ============================================================
_P = base64.b64decode("aHR0cHM6Ly9jdXJseS1tb29uLTE1NWUuc3VubnlzdW5ueS53b3JrZXJzLmRldi8=").decode()
CF_WORKER_PROXY = _P

PROXY_REQUIRED = {"Binance", "BinanceSPOT", "Bybit", "BybitSPOT", "Bitget"}

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_json(url, method="GET", headers=None, json_body=None, timeout=10, use_proxy=False):
    if headers is None:
        headers = BROWSER_HEADERS.copy()
    else:
        merged = BROWSER_HEADERS.copy()
        merged.update(headers)
        headers = merged

    def _do_request(target_url, hdrs):
        if method == "POST":
            resp = requests.post(target_url, headers=hdrs, json=json_body, timeout=timeout)
        else:
            resp = requests.get(target_url, headers=hdrs, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    def _proxy_url(original_url):
        if not CF_WORKER_PROXY:
            return None
        return f"{CF_WORKER_PROXY}?url={requests.utils.quote(original_url, safe='')}"

    if use_proxy:
        proxy = _proxy_url(url)
        if proxy:
            return _do_request(proxy, headers)
        else:
            raise RuntimeError("代理未设置")

    try:
        return _do_request(url, headers)
    except Exception:
        proxy = _proxy_url(url)
        if proxy:
            return _do_request(proxy, headers)
        raise


# ============================================================
# 各交易所 orderbook 函数
# ============================================================

def get_orderbook_binance(symbol, proxy=False):
    url = f"https://fapi.binance.com/fapi/v1/depth?symbol={symbol}USDT&limit=5"
    data = fetch_json(url, use_proxy=proxy)
    return data['asks'][0][0], data['bids'][0][0], data['asks'][0][1], data['bids'][0][1]

def get_orderbook_binance_spot(symbol, proxy=False):
    url = f"https://api.binance.com/api/v3/depth?symbol={symbol}USDT&limit=5"
    data = fetch_json(url, use_proxy=proxy)
    return data['asks'][0][0], data['bids'][0][0], data['asks'][0][1], data['bids'][0][1]

def get_orderbook_bybit(symbol, proxy=False):
    url = f"https://api.bybit.com/v5/market/orderbook?category=linear&symbol={symbol}USDT&limit=1"
    data = fetch_json(url, use_proxy=proxy)
    b = data['result']
    return b['a'][0][0], b['b'][0][0], b['a'][0][1], b['b'][0][1]

def get_orderbook_bybit_spot(symbol, proxy=False):
    url = f"https://api.bybit.com/v5/market/orderbook?category=spot&symbol={symbol}USDT&limit=1"
    data = fetch_json(url, use_proxy=proxy)
    b = data['result']
    return b['a'][0][0], b['b'][0][0], b['a'][0][1], b['b'][0][1]

def get_orderbook_okx(symbol, proxy=False):
    url = f"https://www.okx.com/api/v5/market/books?instId={symbol}-USDT-SWAP&sz=1"
    data = fetch_json(url, use_proxy=proxy)
    b = data['data'][0]
    return b['asks'][0][0], b['bids'][0][0], b['asks'][0][1], b['bids'][0][1]

def get_orderbook_bitget(symbol, proxy=False):
    url = f"https://api.bitget.com/api/v2/mix/market/depth?productType=USDT-FUTURES&symbol={symbol}USDT&limit=1"
    data = fetch_json(url, use_proxy=proxy)
    b = data['data']
    return b['asks'][0][0], b['bids'][0][0], b['asks'][0][1], b['bids'][0][1]

def get_orderbook_mexc(symbol, proxy=False):
    url = f"https://contract.mexc.com/api/v1/contract/depth/{symbol}_USDT"
    data = fetch_json(url, use_proxy=proxy)
    d = data['data']
    return d['asks'][0][0], d['bids'][0][0], d['asks'][0][1], d['bids'][0][1]

def get_orderbook_mexc_spot(symbol, proxy=False):
    url = f"https://api.mexc.com/api/v3/depth?symbol={symbol}USDT&limit=5"
    data = fetch_json(url, use_proxy=proxy)
    return data['asks'][0][0], data['bids'][0][0], data['asks'][0][1], data['bids'][0][1]

def get_orderbook_gate(symbol, proxy=False):
    url = f"https://api.gateio.ws/api/v4/futures/usdt/order_book?contract={symbol}_USDT&limit=1"
    data = fetch_json(url, use_proxy=proxy)
    return data['asks'][0]['p'], data['bids'][0]['p'], data['asks'][0]['s'], data['bids'][0]['s']

def get_orderbook_huobi(symbol, proxy=False):
    url = f"https://api.hbdm.com/linear-swap-ex/market/depth?contract_code={symbol}-USDT&type=step0"
    data = fetch_json(url, use_proxy=proxy)
    t = data['tick']
    return t['asks'][0][0], t['bids'][0][0], t['asks'][0][1], t['bids'][0][1]

def get_orderbook_phemex(symbol, proxy=False):
    url = f"https://api.phemex.com/md/v2/orderbook?symbol={symbol}USDT"
    data = fetch_json(url, use_proxy=proxy)
    b = data['result']['orderbook_p']
    return b['asks'][0][0], b['bids'][0][0], b['asks'][0][1], b['bids'][0][1]

def get_orderbook_poinex(symbol, proxy=False):
    url = f"https://api.pionex.com/api/v1/market/depth?symbol={symbol}_USDT"
    data = fetch_json(url, use_proxy=proxy)
    return data['data']['asks'][0][0], data['data']['bids'][0][0], data['data']['asks'][0][1], data['data']['bids'][0][1]

def get_orderbook_lbank(symbol, proxy=False):
    url = f"https://lbkperp.lbank.com/cfd/openApi/v1/pub/marketOrder?depth=1&symbol={symbol}USDT"
    data = fetch_json(url, use_proxy=proxy)
    return (data['data']['asks'][0]['price'], data['data']['bids'][0]['price'],
            data['data']['asks'][0]['volume'], data['data']['bids'][0]['volume'])

def get_orderbook_aevo(symbol, proxy=False):
    url = f"https://api.aevo.xyz/orderbook?instrument_name={symbol}-PERP"
    data = fetch_json(url, use_proxy=proxy)
    return data['asks'][0][0], data['bids'][0][0], data['asks'][0][1], data['bids'][0][1]

def get_orderbook_hyperliquid(symbol, proxy=False):
    url = "https://api.hyperliquid.xyz/info"
    body = {"type": "l2Book", "coin": symbol}
    data = fetch_json(url, method="POST", headers={"content-type": "application/json"},
                      json_body=body, use_proxy=proxy)
    if "levels" in data and isinstance(data["levels"], list) and len(data["levels"]) == 2:
        first_buy = max((float(tick["px"]), float(tick["sz"])) for tick in data["levels"][0])
        first_sell = min((float(tick["px"]), float(tick["sz"])) for tick in data["levels"][1])
        return first_sell[0], first_buy[0], first_sell[1], first_buy[1]
    raise ValueError("Hyperliquid 返回数据格式异常")

def get_orderbook_kucoin(symbol, proxy=False):
    kc_symbol = "XBT" if symbol == "BTC" else symbol
    url = f"https://api-futures.kucoin.com/api/v1/level2/depth20?symbol={kc_symbol}USDTM"
    data = fetch_json(url, use_proxy=proxy)
    b = data['data']
    return b['asks'][0][0], b['bids'][0][0], b['asks'][0][1], b['bids'][0][1]

def get_orderbook_aster(symbol, proxy=False):
    url = f"https://fapi.asterdex.com/fapi/v1/depth?symbol={symbol}USDT&limit=5"
    data = fetch_json(url, use_proxy=proxy)
    return data['asks'][0][0], data['bids'][0][0], data['asks'][0][1], data['bids'][0][1]

def get_orderbook_backpack(symbol, proxy=False):
    """Backpack — 用 ticker 取 best bid/ask，更可靠"""
    url = f"https://api.backpack.exchange/api/v1/ticker?symbol={symbol}_USDC_PERP"
    data = fetch_json(url, use_proxy=proxy)
    # ticker 返回: {"bestAsk":"xxx","bestBid":"xxx","bestAskSize":"xxx","bestBidSize":"xxx",...}
    ask_px = data.get('bestAsk') or data.get('lastPrice')
    bid_px = data.get('bestBid') or data.get('lastPrice')
    ask_qty = data.get('bestAskSize', '0')
    bid_qty = data.get('bestBidSize', '0')
    return ask_px, bid_px, ask_qty, bid_qty


# ============================================================
# 映射表
# ============================================================
EXCHANGE_FUNCS = {
    "Binance":      get_orderbook_binance,
    "BinanceSPOT":  get_orderbook_binance_spot,
    "Bybit":        get_orderbook_bybit,
    "BybitSPOT":    get_orderbook_bybit_spot,
    "OKX":          get_orderbook_okx,
    "Bitget":       get_orderbook_bitget,
    "MEXC":         get_orderbook_mexc,
    "MEXCSPOT":     get_orderbook_mexc_spot,
    "GateIO":       get_orderbook_gate,
    "Huobi":        get_orderbook_huobi,
    "Phemex":       get_orderbook_phemex,
    "Poinex":       get_orderbook_poinex,
    "Lbank":        get_orderbook_lbank,
    "Aevo":         get_orderbook_aevo,
    "Hyperliquid":  get_orderbook_hyperliquid,
    "KuCoin":       get_orderbook_kucoin,
    "Aster":        get_orderbook_aster,
    "Backpack":     get_orderbook_backpack,
}

EXCHANGE_LIST = list(EXCHANGE_FUNCS.keys())


def get_orderbook(exchange_name, symbol):
    max_retries = 3
    func = EXCHANGE_FUNCS.get(exchange_name)
    if func is None:
        return None, None, None, None
    use_proxy = exchange_name in PROXY_REQUIRED
    for attempt in range(1, max_retries + 1):
        try:
            return func(symbol, proxy=use_proxy)
        except Exception as e:
            if attempt >= max_retries:
                st.toast(f"❌ {exchange_name}: {e}", icon="⚠️")
                return None, None, None, None
            time.sleep(1)


# ============================================================
# 门铃音
# ============================================================
DOORBELL_JS = """
<script>
try {
    var ctx = new (window.AudioContext || window.webkitAudioContext)();
    var o1 = ctx.createOscillator(), g1 = ctx.createGain();
    o1.type='sine'; o1.frequency.value=830;
    g1.gain.setValueAtTime(0.6,ctx.currentTime);
    g1.gain.exponentialRampToValueAtTime(0.01,ctx.currentTime+0.4);
    o1.connect(g1); g1.connect(ctx.destination);
    o1.start(ctx.currentTime); o1.stop(ctx.currentTime+0.4);
    var o2 = ctx.createOscillator(), g2 = ctx.createGain();
    o2.type='sine'; o2.frequency.value=660;
    g2.gain.setValueAtTime(0.6,ctx.currentTime+0.25);
    g2.gain.exponentialRampToValueAtTime(0.01,ctx.currentTime+0.7);
    o2.connect(g2); g2.connect(ctx.destination);
    o2.start(ctx.currentTime+0.25); o2.stop(ctx.currentTime+0.7);
} catch(e){}
</script>
"""

# ============================================================
# UI
# ============================================================
st.title('交易对差价监测')

symbol = st.text_input("币种:", value="BTC").upper()

col_ex1, col_ex2 = st.columns(2)
with col_ex1:
    exchange1 = st.selectbox("交易所1:", EXCHANGE_LIST, index=EXCHANGE_LIST.index("MEXC"))
with col_ex2:
    exchange2 = st.selectbox("交易所2:", EXCHANGE_LIST, index=EXCHANGE_LIST.index("GateIO"))

# ============================================================
# 价差警报 — 紧凑布局
# ============================================================
st.markdown("<small><b>价差警报</b></small>", unsafe_allow_html=True)

# 方向1
c1a, c1b, c1c = st.columns([2, 1.5, 1.5])
with c1a:
    alert1_mode = st.radio(
        f"{exchange1}空|{exchange2}多",
        ["不使用", "< 小于", "> 大于"],
        index=0, horizontal=True, key="a1m"
    )
with c1b:
    alert1_val = st.number_input("阈值%", min_value=-100.0, max_value=100.0,
                                  value=0.0, step=0.01, format="%.2f", key="a1v",
                                  label_visibility="collapsed")

# 方向2
c2a, c2b, c2c = st.columns([2, 1.5, 1.5])
with c2a:
    alert2_mode = st.radio(
        f"{exchange1}多|{exchange2}空",
        ["不使用", "< 小于", "> 大于"],
        index=0, horizontal=True, key="a2m"
    )
with c2b:
    alert2_val = st.number_input("阈值%", min_value=-100.0, max_value=100.0,
                                  value=0.0, step=0.01, format="%.2f", key="a2v",
                                  label_visibility="collapsed")

st.markdown("---")


def percentage_diff(start, end):
    return ((start - end)) / ((start + end) / 2) * 100

def price_diff(start, end):
    return (start - end)

def check_alert(value, threshold, mode):
    if mode == "不使用":
        return False
    if mode == "> 大于":
        return value > threshold
    else:  # "< 小于"
        return value < threshold


# 占位符
long_placeholder = st.empty()
diff_long_placeholder = st.empty()
diffprice_long_placeholder = st.empty()
NA_placeholder = st.empty()
short_placeholder = st.empty()
diff_short_placeholder = st.empty()
diffprice_short_placeholder = st.empty()
sound_placeholder = st.empty()


def update_display():
    ex1_ask_px, ex1_bid_px, ex1_ask_qty, ex1_bid_qty = get_orderbook(exchange1, symbol)
    ex2_ask_px, ex2_bid_px, ex2_ask_qty, ex2_bid_qty = get_orderbook(exchange2, symbol)

    if ex1_ask_px is None or ex2_ask_px is None:
        return

    diff_long_val = percentage_diff(float(ex1_bid_px), float(ex2_ask_px))
    diff_long = "{:.3f}".format(diff_long_val)
    diffprice_long = "{:.6f}".format(price_diff(float(ex1_bid_px), float(ex2_ask_px)))

    diff_short_val = percentage_diff(float(ex2_bid_px), float(ex1_ask_px))
    diff_short = "{:.3f}".format(diff_short_val)
    diffprice_short = "{:.6f}".format(price_diff(float(ex2_bid_px), float(ex1_ask_px)))

    long_placeholder.markdown(
        f"<font size='4'>{exchange1} 空 | {exchange2} 多</font>\n"
        f"<font size='4'>{ex1_bid_px} | {ex2_ask_px}</font>",
        unsafe_allow_html=True
    )
    diff_long_placeholder.markdown(f"<b><font size='6'>价差: {diff_long}%</font></b>", unsafe_allow_html=True)
    diffprice_long_placeholder.markdown(f"<font size='4'>价格差: {diffprice_long}</font>", unsafe_allow_html=True)
    NA_placeholder.write("-----------------------------------------")
    short_placeholder.markdown(
        f"<font size='4'>{exchange1} 多 | {exchange2} 空</font>\n"
        f"<font size='4'>{ex1_ask_px} | {ex2_bid_px}</font>",
        unsafe_allow_html=True
    )
    diff_short_placeholder.markdown(f"<b><font size='6'>价差: {diff_short}%</font></b>", unsafe_allow_html=True)
    diffprice_short_placeholder.markdown(f"<font size='4'>价格差: {diffprice_short}</font>", unsafe_allow_html=True)

    # 警报检查
    triggered = False
    if check_alert(diff_long_val, alert1_val, alert1_mode):
        triggered = True
        st.toast(f"🔔 {exchange1}空|{exchange2}多 {diff_long}%", icon="🔔")
    if check_alert(diff_short_val, alert2_val, alert2_mode):
        triggered = True
        st.toast(f"🔔 {exchange1}多|{exchange2}空 {diff_short}%", icon="🔔")

    if triggered:
        sound_placeholder.empty()
        st.components.v1.html(DOORBELL_JS, height=0, width=0)
    else:
        sound_placeholder.empty()


while True:
    update_display()
    time.sleep(1)
