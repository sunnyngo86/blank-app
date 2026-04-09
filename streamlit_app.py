import time
import requests
import json
import streamlit as st
import base64

st.set_page_config(page_title="Sunny Bot", page_icon=":rocket:", layout="centered",
                   initial_sidebar_state="auto",
                   menu_items={'Get Help': None, 'Report a bug': None, 'About': None})

st.markdown("""<style>
#MainMenu,footer,header,.viewerBadge_container__1QSob,.stDeployButton,
.stApp [data-testid="stToolbar"],.stApp [data-testid="stDecoration"],
.stApp [data-testid="stStatusWidget"],.stApp [data-testid="stHeader"],
.stApp [data-testid="stSidebar"]{display:none!important;}
</style>""", unsafe_allow_html=True)
st.components.v1.html("""<script>setInterval(()=>{
document.querySelectorAll("footer,[data-testid='stFooter']").forEach(e=>e.style.display="none")
},100)</script>""", height=0, width=0)

# ============================================================
_P = base64.b64decode(
    "aHR0cHM6Ly9jdXJseS1tb29uLTE1NWUuc3VubnlzdW5ueS53b3JrZXJzLmRldi8=").decode()
CF_WORKER_PROXY = _P

PROXY_REQUIRED = {"Binance", "Binance-SPOT", "Bybit", "Bybit-SPOT", "Bitget", "Bitget-SPOT"}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


def fetch_json(url, method="GET", headers=None, json_body=None, timeout=10, use_proxy=False):
    h = {**HEADERS, **(headers or {})}

    def _req(u):
        r = (requests.post(u, headers=h, json=json_body, timeout=timeout) if method == "POST"
             else requests.get(u, headers=h, timeout=timeout))
        r.raise_for_status()
        return r.json()

    def _pu(u):
        return f"{CF_WORKER_PROXY}?url={requests.utils.quote(u, safe='')}" if CF_WORKER_PROXY else None

    if use_proxy:
        p = _pu(url)
        if p:
            return _req(p)
        raise RuntimeError("代理未设置")
    try:
        return _req(url)
    except Exception:
        p = _pu(url)
        if p:
            return _req(p)
        raise


# ============================================================
# 交易所函数
# ============================================================
def ob_binance(s, px=False):
    d = fetch_json(f"https://fapi.binance.com/fapi/v1/depth?symbol={s}USDT&limit=5", use_proxy=px)
    return d['asks'][0][0], d['bids'][0][0], d['asks'][0][1], d['bids'][0][1]

def ob_binance_spot(s, px=False):
    d = fetch_json(f"https://api.binance.com/api/v3/depth?symbol={s}USDT&limit=5", use_proxy=px)
    return d['asks'][0][0], d['bids'][0][0], d['asks'][0][1], d['bids'][0][1]

def ob_bybit(s, px=False):
    d = fetch_json(f"https://api.bybit.com/v5/market/orderbook?category=linear&symbol={s}USDT&limit=1", use_proxy=px)
    b = d['result']; return b['a'][0][0], b['b'][0][0], b['a'][0][1], b['b'][0][1]

def ob_bybit_spot(s, px=False):
    d = fetch_json(f"https://api.bybit.com/v5/market/orderbook?category=spot&symbol={s}USDT&limit=1", use_proxy=px)
    b = d['result']; return b['a'][0][0], b['b'][0][0], b['a'][0][1], b['b'][0][1]

def ob_okx(s, px=False):
    d = fetch_json(f"https://www.okx.com/api/v5/market/books?instId={s}-USDT-SWAP&sz=1", use_proxy=px)
    b = d['data'][0]; return b['asks'][0][0], b['bids'][0][0], b['asks'][0][1], b['bids'][0][1]

def ob_bitget(s, px=False):
    # 用 ticker 代替 depth，避免 403
    d = fetch_json(f"https://api.bitget.com/api/v2/mix/market/ticker?productType=USDT-FUTURES&symbol={s}USDT", use_proxy=px)
    t = d['data'][0] if isinstance(d['data'], list) else d['data']
    return t['askPr'], t['bidPr'], t.get('askSz', '0'), t.get('bidSz', '0')

def ob_bitget_spot(s, px=False):
    d = fetch_json(f"https://api.bitget.com/api/v2/spot/market/tickers?symbol={s}USDT", use_proxy=px)
    t = d['data'][0] if isinstance(d['data'], list) else d['data']
    return t['askPr'], t['bidPr'], t.get('askSz', '0'), t.get('bidSz', '0')

def ob_mexc(s, px=False):
    d = fetch_json(f"https://contract.mexc.com/api/v1/contract/depth/{s}_USDT", use_proxy=px)
    b = d['data']; return b['asks'][0][0], b['bids'][0][0], b['asks'][0][1], b['bids'][0][1]

def ob_mexc_spot(s, px=False):
    d = fetch_json(f"https://api.mexc.com/api/v3/depth?symbol={s}USDT&limit=5", use_proxy=px)
    return d['asks'][0][0], d['bids'][0][0], d['asks'][0][1], d['bids'][0][1]

def ob_gate(s, px=False):
    d = fetch_json(f"https://api.gateio.ws/api/v4/futures/usdt/order_book?contract={s}_USDT&limit=1", use_proxy=px)
    return d['asks'][0]['p'], d['bids'][0]['p'], d['asks'][0]['s'], d['bids'][0]['s']

def ob_huobi(s, px=False):
    d = fetch_json(f"https://api.hbdm.com/linear-swap-ex/market/depth?contract_code={s}-USDT&type=step0", use_proxy=px)
    t = d['tick']; return t['asks'][0][0], t['bids'][0][0], t['asks'][0][1], t['bids'][0][1]

def ob_phemex(s, px=False):
    d = fetch_json(f"https://api.phemex.com/md/v2/orderbook?symbol={s}USDT", use_proxy=px)
    b = d['result']['orderbook_p']; return b['asks'][0][0], b['bids'][0][0], b['asks'][0][1], b['bids'][0][1]

def ob_poinex(s, px=False):
    d = fetch_json(f"https://api.pionex.com/api/v1/market/depth?symbol={s}_USDT", use_proxy=px)
    return d['data']['asks'][0][0], d['data']['bids'][0][0], d['data']['asks'][0][1], d['data']['bids'][0][1]

def ob_lbank(s, px=False):
    d = fetch_json(f"https://lbkperp.lbank.com/cfd/openApi/v1/pub/marketOrder?depth=1&symbol={s}USDT", use_proxy=px)
    return d['data']['asks'][0]['price'], d['data']['bids'][0]['price'], d['data']['asks'][0]['volume'], d['data']['bids'][0]['volume']

def ob_aevo(s, px=False):
    d = fetch_json(f"https://api.aevo.xyz/orderbook?instrument_name={s}-PERP", use_proxy=px)
    return d['asks'][0][0], d['bids'][0][0], d['asks'][0][1], d['bids'][0][1]

def ob_hyperliquid(s, px=False):
    d = fetch_json("https://api.hyperliquid.xyz/info", method="POST",
                   headers={"content-type": "application/json"},
                   json_body={"type": "l2Book", "coin": s}, use_proxy=px)
    if "levels" in d and len(d["levels"]) == 2:
        buy = max((float(t["px"]), float(t["sz"])) for t in d["levels"][0])
        sell = min((float(t["px"]), float(t["sz"])) for t in d["levels"][1])
        return sell[0], buy[0], sell[1], buy[1]
    raise ValueError("数据异常")

def ob_kucoin(s, px=False):
    kc = "XBT" if s == "BTC" else s
    d = fetch_json(f"https://api-futures.kucoin.com/api/v1/level2/depth20?symbol={kc}USDTM", use_proxy=px)
    b = d['data']; return b['asks'][0][0], b['bids'][0][0], b['asks'][0][1], b['bids'][0][1]

def ob_aster(s, px=False):
    d = fetch_json(f"https://fapi.asterdex.com/fapi/v1/depth?symbol={s}USDT&limit=5", use_proxy=px)
    return d['asks'][0][0], d['bids'][0][0], d['asks'][0][1], d['bids'][0][1]

def ob_backpack(s, px=False):
    d = fetch_json(f"https://api.backpack.exchange/api/v1/ticker?symbol={s}_USDC_PERP", use_proxy=px)
    return d.get('bestAsk', d.get('lastPrice')), d.get('bestBid', d.get('lastPrice')), d.get('bestAskSize', '0'), d.get('bestBidSize', '0')

def ob_coinw(s, px=False):
    d = fetch_json(f"https://api.coinw.com/v1/perpumPublic/depth?instrument={s}&level=1", use_proxy=px)
    b = d['data']; return b['asks'][0][0], b['bids'][0][0], b['asks'][0][1], b['bids'][0][1]


# 合约在前，SPOT 在后 (带 "-" 字眼)
EXCHANGE_FUNCS = {
    "Binance": ob_binance, "Bybit": ob_bybit, "OKX": ob_okx,
    "Bitget": ob_bitget, "MEXC": ob_mexc, "GateIO": ob_gate,
    "Huobi": ob_huobi, "Phemex": ob_phemex, "Poinex": ob_poinex,
    "Lbank": ob_lbank, "Aevo": ob_aevo, "Hyperliquid": ob_hyperliquid,
    "KuCoin": ob_kucoin, "Aster": ob_aster, "Backpack": ob_backpack,
    "CoinW": ob_coinw,
    "Binance-SPOT": ob_binance_spot, "Bybit-SPOT": ob_bybit_spot,
    "Bitget-SPOT": ob_bitget_spot, "MEXC-SPOT": ob_mexc_spot,
}
EXCHANGE_LIST = list(EXCHANGE_FUNCS.keys())


def get_orderbook(ex, sym):
    func = EXCHANGE_FUNCS.get(ex)
    if not func:
        return None, None, None, None
    px = ex in PROXY_REQUIRED
    for att in range(1, 4):
        try:
            return func(sym, proxy=px)
        except Exception as e:
            if att >= 3:
                # 隐藏 URL，只显示交易所名和简短错误
                msg = str(e)
                if "http" in msg.lower():
                    # 去掉 URL 部分
                    parts = msg.split("for url:")
                    msg = parts[0].strip() if len(parts) > 1 else msg
                    # 再去掉可能残留的 https://...
                    import re
                    msg = re.sub(r'https?://\S+', '', msg).strip()
                st.toast(f"❌ {ex}: {msg}", icon="⚠️")
                return None, None, None, None
            time.sleep(1)


# ============================================================
DOORBELL = """<script>try{var c=new(window.AudioContext||window.webkitAudioContext)(),
o=c.createOscillator(),g=c.createGain();o.type='sine';o.frequency.value=830;
g.gain.setValueAtTime(.6,c.currentTime);g.gain.exponentialRampToValueAtTime(.01,c.currentTime+.4);
o.connect(g);g.connect(c.destination);o.start(c.currentTime);o.stop(c.currentTime+.4);
var o2=c.createOscillator(),g2=c.createGain();o2.type='sine';o2.frequency.value=660;
g2.gain.setValueAtTime(.6,c.currentTime+.25);g2.gain.exponentialRampToValueAtTime(.01,c.currentTime+.7);
o2.connect(g2);g2.connect(c.destination);o2.start(c.currentTime+.25);o2.stop(c.currentTime+.7)}catch(e){}</script>"""

# ============================================================
st.title('交易对差价监测')

symbol = st.text_input("币种:", value="BTC").upper()

c1, c2 = st.columns(2)
with c1:
    exchange1 = st.selectbox("交易所1:", EXCHANGE_LIST, index=0)
with c2:
    exchange2 = st.selectbox("交易所2:", EXCHANGE_LIST, index=5)

# 币种不存在的提示占位
ex1_err = st.empty()
ex2_err = st.empty()

# ---- 警报 ----
st.markdown("<small><b>价差警报</b></small>", unsafe_allow_html=True)
a1a, a1b = st.columns([3, 2])
with a1a:
    m1 = st.radio(f"{exchange1}空|{exchange2}多", ["不使用", "< 小于", "> 大于"], index=0, horizontal=True, key="m1")
with a1b:
    v1 = st.number_input("阈值", min_value=-100.0, max_value=100.0, value=0.0, step=0.01, format="%.2f", key="v1", label_visibility="collapsed")

a2a, a2b = st.columns([3, 2])
with a2a:
    m2 = st.radio(f"{exchange1}多|{exchange2}空", ["不使用", "< 小于", "> 大于"], index=0, horizontal=True, key="m2")
with a2b:
    v2 = st.number_input("阈值", min_value=-100.0, max_value=100.0, value=0.0, step=0.01, format="%.2f", key="v2", label_visibility="collapsed")

st.markdown("---")

pct = lambda a, b: ((a - b)) / ((a + b) / 2) * 100

ph_l = st.empty()
ph_dl = st.empty()
ph_pl = st.empty()
ph_sep = st.empty()
ph_s = st.empty()
ph_ds = st.empty()
ph_ps = st.empty()
ph_snd = st.empty()

def chk(val, thr, mode):
    if mode == "不使用": return False
    return val > thr if mode == "> 大于" else val < thr

while True:
    r1 = get_orderbook(exchange1, symbol)
    r2 = get_orderbook(exchange2, symbol)

    # 币种不存在检测
    no1 = r1[0] is None
    no2 = r2[0] is None
    ex1_err.markdown(f"<span style='color:red;font-size:13px'>币种不存在</span>" if no1 else "", unsafe_allow_html=True)
    ex2_err.markdown(f"<span style='color:red;font-size:13px'>币种不存在</span>" if no2 else "", unsafe_allow_html=True)

    if no1 or no2:
        time.sleep(2)
        continue

    a1, b1, aq1, bq1 = r1
    a2, b2, aq2, bq2 = r2

    dl = pct(float(b1), float(a2))
    ds = pct(float(b2), float(a1))
    pl = float(b1) - float(a2)
    ps = float(b2) - float(a1)

    ph_l.markdown(f"<font size='4'>{exchange1} 空 | {exchange2} 多</font>\n<font size='4'>{b1} | {a2}</font>", unsafe_allow_html=True)
    ph_dl.markdown(f"<b><font size='6'>价差: {dl:.3f}%</font></b>", unsafe_allow_html=True)
    ph_pl.markdown(f"<font size='4'>价格差: {pl:.6f}</font>", unsafe_allow_html=True)
    ph_sep.write("-----------------------------------------")
    ph_s.markdown(f"<font size='4'>{exchange1} 多 | {exchange2} 空</font>\n<font size='4'>{a1} | {b2}</font>", unsafe_allow_html=True)
    ph_ds.markdown(f"<b><font size='6'>价差: {ds:.3f}%</font></b>", unsafe_allow_html=True)
    ph_ps.markdown(f"<font size='4'>价格差: {ps:.6f}</font>", unsafe_allow_html=True)

    ring = False
    if chk(dl, v1, m1):
        ring = True; st.toast(f"🔔 {exchange1}空|{exchange2}多 {dl:.3f}%", icon="🔔")
    if chk(ds, v2, m2):
        ring = True; st.toast(f"🔔 {exchange1}多|{exchange2}空 {ds:.3f}%", icon="🔔")
    if ring:
        ph_snd.empty(); st.components.v1.html(DOORBELL, height=0, width=0)
    else:
        ph_snd.empty()

    time.sleep(1)
