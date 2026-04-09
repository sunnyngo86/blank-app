import time, requests, json, re, base64
import streamlit as st

st.set_page_config(page_title="Sunny Bot", page_icon=":rocket:", layout="centered",
                   initial_sidebar_state="auto",
                   menu_items={'Get Help': None, 'Report a bug': None, 'About': None})
st.markdown("""<style>
#MainMenu,footer,header,.viewerBadge_container__1QSob,.stDeployButton,
.stApp [data-testid="stToolbar"],.stApp [data-testid="stDecoration"],
.stApp [data-testid="stStatusWidget"],.stApp [data-testid="stHeader"],
.stApp [data-testid="stSidebar"]{display:none!important;}
</style>""", unsafe_allow_html=True)
st.components.v1.html('<script>setInterval(()=>{document.querySelectorAll("footer,[data-testid=stFooter]").forEach(e=>e.style.display="none")},100)</script>', height=0, width=0)

_P = base64.b64decode("aHR0cHM6Ly9jdXJseS1tb29uLTE1NWUuc3VubnlzdW5ueS53b3JrZXJzLmRldi8=").decode()
CF = _P
NEED_PROXY = {"Binance","Binance-SPOT","Bybit","Bybit-SPOT","Bitget","Bitget-SPOT"}
H = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36","Accept":"application/json"}

def fj(url, method="GET", headers=None, jb=None, timeout=10, proxy=False):
    h = {**H, **(headers or {})}
    def _r(u):
        r = requests.post(u,headers=h,json=jb,timeout=timeout) if method=="POST" else requests.get(u,headers=h,timeout=timeout)
        r.raise_for_status(); return r.json()
    pu = f"{CF}?url={requests.utils.quote(url,safe='')}" if CF else None
    if proxy:
        if pu: return _r(pu)
        raise RuntimeError("代理未设置")
    try: return _r(url)
    except:
        if pu: return _r(pu)
        raise

# ---- 交易所函数 ----
# 返回 (ask, bid, ask_qty, bid_qty) 或 raise

class CoinNotFound(Exception): pass

def _cn(ex, sym):
    raise CoinNotFound(f"{ex} 没有 {sym} 交易对")

def ob_binance(s, px=False):
    d = fj(f"https://fapi.binance.com/fapi/v1/depth?symbol={s}USDT&limit=5", proxy=px)
    if not d.get('asks'): _cn("Binance", s)
    return d['asks'][0][0], d['bids'][0][0], d['asks'][0][1], d['bids'][0][1]

def ob_binance_spot(s, px=False):
    d = fj(f"https://api.binance.com/api/v3/depth?symbol={s}USDT&limit=5", proxy=px)
    if not d.get('asks'): _cn("Binance-SPOT", s)
    return d['asks'][0][0], d['bids'][0][0], d['asks'][0][1], d['bids'][0][1]

def ob_bybit(s, px=False):
    d = fj(f"https://api.bybit.com/v5/market/orderbook?category=linear&symbol={s}USDT&limit=1", proxy=px)
    b = d['result']
    if not b.get('a'): _cn("Bybit", s)
    return b['a'][0][0], b['b'][0][0], b['a'][0][1], b['b'][0][1]

def ob_bybit_spot(s, px=False):
    d = fj(f"https://api.bybit.com/v5/market/orderbook?category=spot&symbol={s}USDT&limit=1", proxy=px)
    b = d['result']
    if not b.get('a'): _cn("Bybit-SPOT", s)
    return b['a'][0][0], b['b'][0][0], b['a'][0][1], b['b'][0][1]

def ob_okx(s, px=False):
    d = fj(f"https://www.okx.com/api/v5/market/books?instId={s}-USDT-SWAP&sz=1", proxy=px)
    if not d.get('data') or not d['data']: _cn("OKX", s)
    b = d['data'][0]; return b['asks'][0][0], b['bids'][0][0], b['asks'][0][1], b['bids'][0][1]

def ob_bitget(s, px=False):
    """Bitget V1 ticker — bestAsk/bestBid，不会被 WAF 封"""
    d = fj(f"https://api.bitget.com/api/mix/v1/market/ticker?symbol={s}USDT_UMCBL", proxy=px)
    if d.get('code') != '00000': _cn("Bitget", s)
    t = d['data']
    return t['bestAsk'], t['bestBid'], t.get('askSz','0'), t.get('bidSz','0')

def ob_bitget_spot(s, px=False):
    d = fj(f"https://api.bitget.com/api/v2/spot/market/tickers?symbol={s}USDT", proxy=px)
    lst = d.get('data', [])
    if not lst: _cn("Bitget-SPOT", s)
    t = lst[0] if isinstance(lst, list) else lst
    return t.get('askPr', t.get('lastPr')), t.get('bidPr', t.get('lastPr')), t.get('askSz','0'), t.get('bidSz','0')

def ob_mexc(s, px=False):
    d = fj(f"https://contract.mexc.com/api/v1/contract/depth/{s}_USDT", proxy=px)
    if not d.get('data') or not d['data'].get('asks'): _cn("MEXC", s)
    b = d['data']; return b['asks'][0][0], b['bids'][0][0], b['asks'][0][1], b['bids'][0][1]

def ob_mexc_spot(s, px=False):
    d = fj(f"https://api.mexc.com/api/v3/depth?symbol={s}USDT&limit=5", proxy=px)
    if not d.get('asks'): _cn("MEXC-SPOT", s)
    return d['asks'][0][0], d['bids'][0][0], d['asks'][0][1], d['bids'][0][1]

def ob_gate(s, px=False):
    d = fj(f"https://api.gateio.ws/api/v4/futures/usdt/order_book?contract={s}_USDT&limit=1", proxy=px)
    if not d.get('asks'): _cn("GateIO", s)
    return d['asks'][0]['p'], d['bids'][0]['p'], d['asks'][0]['s'], d['bids'][0]['s']

def ob_huobi(s, px=False):
    d = fj(f"https://api.hbdm.com/linear-swap-ex/market/depth?contract_code={s}-USDT&type=step0", proxy=px)
    t = d.get('tick')
    if not t or not t.get('asks'): _cn("Huobi", s)
    return t['asks'][0][0], t['bids'][0][0], t['asks'][0][1], t['bids'][0][1]

def ob_phemex(s, px=False):
    d = fj(f"https://api.phemex.com/md/v2/orderbook?symbol={s}USDT", proxy=px)
    b = d.get('result',{}).get('orderbook_p',{})
    if not b.get('asks'): _cn("Phemex", s)
    return b['asks'][0][0], b['bids'][0][0], b['asks'][0][1], b['bids'][0][1]

def ob_poinex(s, px=False):
    d = fj(f"https://api.pionex.com/api/v1/market/depth?symbol={s}_USDT", proxy=px)
    if not d.get('data') or not d['data'].get('asks'): _cn("Poinex", s)
    return d['data']['asks'][0][0], d['data']['bids'][0][0], d['data']['asks'][0][1], d['data']['bids'][0][1]

def ob_lbank(s, px=False):
    d = fj(f"https://lbkperp.lbank.com/cfd/openApi/v1/pub/marketOrder?depth=1&symbol={s}USDT", proxy=px)
    if not d.get('data') or not d['data'].get('asks'): _cn("Lbank", s)
    return d['data']['asks'][0]['price'], d['data']['bids'][0]['price'], d['data']['asks'][0]['volume'], d['data']['bids'][0]['volume']

def ob_aevo(s, px=False):
    d = fj(f"https://api.aevo.xyz/orderbook?instrument_name={s}-PERP", proxy=px)
    if not d.get('asks'): _cn("Aevo", s)
    return d['asks'][0][0], d['bids'][0][0], d['asks'][0][1], d['bids'][0][1]

def ob_hyper(s, px=False):
    d = fj("https://api.hyperliquid.xyz/info", method="POST",
           headers={"content-type":"application/json"},
           jb={"type":"l2Book","coin":s}, proxy=px)
    if "levels" not in d or len(d["levels"]) < 2 or not d["levels"][0]:
        _cn("Hyperliquid", s)
    buy = max((float(t["px"]),float(t["sz"])) for t in d["levels"][0])
    sell = min((float(t["px"]),float(t["sz"])) for t in d["levels"][1])
    return sell[0], buy[0], sell[1], buy[1]

def ob_kucoin(s, px=False):
    kc = "XBT" if s == "BTC" else s
    d = fj(f"https://api-futures.kucoin.com/api/v1/level2/depth20?symbol={kc}USDTM", proxy=px)
    b = d.get('data',{})
    if not b.get('asks'): _cn("KuCoin", s)
    return b['asks'][0][0], b['bids'][0][0], b['asks'][0][1], b['bids'][0][1]

def ob_aster(s, px=False):
    d = fj(f"https://fapi.asterdex.com/fapi/v1/depth?symbol={s}USDT&limit=5", proxy=px)
    if not d.get('asks'): _cn("Aster", s)
    return d['asks'][0][0], d['bids'][0][0], d['asks'][0][1], d['bids'][0][1]

def ob_backpack(s, px=False):
    d = fj(f"https://api.backpack.exchange/api/v1/ticker?symbol={s}_USDC_PERP", proxy=px)
    a = d.get('bestAsk'); b = d.get('bestBid')
    if not a or not b: _cn("Backpack", s)
    return a, b, d.get('bestAskSize','0'), d.get('bestBidSize','0')

def ob_coinw(s, px=False):
    """CoinW 公开 depth — 参数是 base (小写)"""
    d = fj(f"https://api.coinw.com/v1/perpumPublic/depth?base={s.lower()}", proxy=px)
    b = d.get('data',{})
    if not b.get('asks'): _cn("CoinW", s)
    return b['asks'][0][0], b['bids'][0][0], b['asks'][0][1], b['bids'][0][1]


# 合约在前, SPOT 在后
EX = {
    "Binance":ob_binance,"Bybit":ob_bybit,"OKX":ob_okx,
    "Bitget":ob_bitget,"MEXC":ob_mexc,"GateIO":ob_gate,
    "Huobi":ob_huobi,"Phemex":ob_phemex,"Poinex":ob_poinex,
    "Lbank":ob_lbank,"Aevo":ob_aevo,"Hyperliquid":ob_hyper,
    "KuCoin":ob_kucoin,"Aster":ob_aster,"Backpack":ob_backpack,
    "CoinW":ob_coinw,
    "Binance-SPOT":ob_binance_spot,"Bybit-SPOT":ob_bybit_spot,
    "Bitget-SPOT":ob_bitget_spot,"MEXC-SPOT":ob_mexc_spot,
}
EL = list(EX.keys())

def get_ob(ex, sym):
    """返回 (ask, bid, aq, bq, error_type)
    error_type: None=正常, 'not_found'=币种不存在, 'fail'=连接失败"""
    f = EX.get(ex)
    if not f: return None,None,None,None,'fail'
    px = ex in NEED_PROXY
    for att in range(1,4):
        try:
            a,b,aq,bq = f(sym, px=px)
            return a,b,aq,bq,None
        except CoinNotFound:
            return None,None,None,None,'not_found'
        except Exception as e:
            if att >= 3:
                msg = re.sub(r'https?://\S+','',str(e)).strip()
                msg = msg.split("for url:")[0].strip() if "for url:" in msg else msg
                st.toast(f"❌ {ex}: {msg}", icon="⚠️")
                return None,None,None,None,'fail'
            time.sleep(1)

BELL = '<script>try{var c=new(window.AudioContext||window.webkitAudioContext)(),o=c.createOscillator(),g=c.createGain();o.type="sine";o.frequency.value=830;g.gain.setValueAtTime(.6,c.currentTime);g.gain.exponentialRampToValueAtTime(.01,c.currentTime+.4);o.connect(g);g.connect(c.destination);o.start(c.currentTime);o.stop(c.currentTime+.4);var o2=c.createOscillator(),g2=c.createGain();o2.type="sine";o2.frequency.value=660;g2.gain.setValueAtTime(.6,c.currentTime+.25);g2.gain.exponentialRampToValueAtTime(.01,c.currentTime+.7);o2.connect(g2);g2.connect(c.destination);o2.start(c.currentTime+.25);o2.stop(c.currentTime+.7)}catch(e){}</script>'

# ============ UI ============
st.title('交易对差价监测')
symbol = st.text_input("币种:", value="BTC").upper()

c1, c2 = st.columns(2)
with c1: exchange1 = st.selectbox("交易所1:", EL, index=0)
with c2: exchange2 = st.selectbox("交易所2:", EL, index=4)

# 币种不存在提示（固定位置）
e1_ph = st.empty()
e2_ph = st.empty()

# ---- 警报 (固定, 不依赖交易所名) ----
st.markdown("<small><b>价差警报</b></small>", unsafe_allow_html=True)

# 用 container 固定布局，避免切换交易所时跳动
alert_container = st.container()
with alert_container:
    r1c1, r1c2, r1c3 = st.columns([2.5, 2.5, 1.5])
    with r1c1:
        st.markdown(f"<small>方向1 (空|多)</small>", unsafe_allow_html=True)
    with r1c2:
        m1 = st.radio("m1", ["不使用","<",">"], index=0, horizontal=True, key="m1", label_visibility="collapsed")
    with r1c3:
        v1 = st.number_input("v1", min_value=-100.0, max_value=100.0, value=0.0, step=0.01, format="%.2f", key="v1", label_visibility="collapsed")

    r2c1, r2c2, r2c3 = st.columns([2.5, 2.5, 1.5])
    with r2c1:
        st.markdown(f"<small>方向2 (多|空)</small>", unsafe_allow_html=True)
    with r2c2:
        m2 = st.radio("m2", ["不使用","<",">"], index=0, horizontal=True, key="m2", label_visibility="collapsed")
    with r2c3:
        v2 = st.number_input("v2", min_value=-100.0, max_value=100.0, value=0.0, step=0.01, format="%.2f", key="v2", label_visibility="collapsed")

st.markdown("---")

pct = lambda a, b: ((a-b))/((a+b)/2)*100
chk = lambda val,thr,mode: (val>thr if mode==">" else val<thr) if mode!="不使用" else False

pl = st.empty(); pdl = st.empty(); ppl = st.empty()
sep = st.empty()
ps = st.empty(); pds = st.empty(); pps = st.empty()
snd = st.empty()

while True:
    a1,b1,aq1,bq1,err1 = get_ob(exchange1, symbol)
    a2,b2,aq2,bq2,err2 = get_ob(exchange2, symbol)

    # 币种不存在 only when exchange connected but pair missing
    e1_ph.markdown(f"<span style='color:red;font-size:13px'>币种不存在</span>" if err1=='not_found' else "", unsafe_allow_html=True)
    e2_ph.markdown(f"<span style='color:red;font-size:13px'>币种不存在</span>" if err2=='not_found' else "", unsafe_allow_html=True)

    if a1 is None or a2 is None:
        time.sleep(2); continue

    dl = pct(float(b1),float(a2)); ds = pct(float(b2),float(a1))
    _pl = float(b1)-float(a2); _ps = float(b2)-float(a1)

    pl.markdown(f"<font size='4'>{exchange1} 空 | {exchange2} 多</font>\n<font size='4'>{b1} | {a2}</font>", unsafe_allow_html=True)
    pdl.markdown(f"<b><font size='6'>价差: {dl:.3f}%</font></b>", unsafe_allow_html=True)
    ppl.markdown(f"<font size='4'>价格差: {_pl:.6f}</font>", unsafe_allow_html=True)
    sep.write("-----------------------------------------")
    ps.markdown(f"<font size='4'>{exchange1} 多 | {exchange2} 空</font>\n<font size='4'>{a1} | {b2}</font>", unsafe_allow_html=True)
    pds.markdown(f"<b><font size='6'>价差: {ds:.3f}%</font></b>", unsafe_allow_html=True)
    pps.markdown(f"<font size='4'>价格差: {_ps:.6f}</font>", unsafe_allow_html=True)

    ring = False
    if chk(dl,v1,m1):
        ring=True; st.toast(f"🔔 {exchange1}空|{exchange2}多 {dl:.3f}%", icon="🔔")
    if chk(ds,v2,m2):
        ring=True; st.toast(f"🔔 {exchange1}多|{exchange2}空 {ds:.3f}%", icon="🔔")
    if ring: snd.empty(); st.components.v1.html(BELL, height=0, width=0)
    else: snd.empty()

    time.sleep(1)
