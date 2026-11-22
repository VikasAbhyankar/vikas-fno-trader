# ============================================================
# FNO V8.3 FINAL - CLEAN - BOT 2 = TRADER ONLY
# Timing: 9:45 AM / 3:00 PM BTST / 4:30 PM IST - RUNS ANYTIME - NO TIME GUARD
# Data: Upstox Live (Entry, Nifty, VIX) + Yahoo History (EMA, RSI, ADX)
# Token: Upstox 1-Year Analytical - No Daily Refresh - Exp 2027-11-18
# Capital: Rs 5L Paper, Risk 1% = Rs 5000, Max 2 Trades
# Features: Regime + Choppy + Sideways S/R + Smart SL Anti-Hunt
#           + Sector + Gap + Event + Trailing + Top 2
#           + BALA AVWP: Day 15m AVWP +12, BTST 1H AVWP Filter +12
# Telegram: Your ID (Secret) + 5239892901 + 9000971028
# PAPER TRADING ONLY - BTST only. No live order, No real GTT.
# TIME GUARD: REMOVED - Manual run allowed anytime, any number of times.
# BTST WINDOW: 3:00 PM (2:55 - 3:40 PM) - But manual run treats as BTST if run in that window
# V8.3 FIX: + Bala AVWP, + get_data_tf, + paper double .NS fix, Expiry never blocks Upstox
# ============================================================
import os, json, requests, traceback, csv
from datetime import datetime, timedelta
import pytz
import yfinance as yf
import pandas as pd
import numpy as np

IST = pytz.timezone("Asia/Kolkata")
CAPITAL = 500000
RISK_PER_TRADE = 5000
MAX_TRADES = 2

BOT_TOKEN = os.getenv("TELEGRAM_FNO_BOT_TOKEN", "")
CHAT_ID_ENV = os.getenv("TELEGRAM_FNO_CHAT_ID", "")
UPSTOX_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN", "")
UPSTOX_EXPIRY = os.getenv("UPSTOX_TOKEN_EXPIRY", "2027-11-18")
UPSTOX_ENABLED = bool(UPSTOX_TOKEN and UPSTOX_TOKEN.strip())
UPSTOX_BASE = "https://api.upstox.com/v3"

FRIEND_IDS = ["5239892901", "9000971028"]
def get_all_ids():
    ids = []
    if CHAT_ID_ENV:
        for x in str(CHAT_ID_ENV).split(","):
            x = x.strip()
            if x and x not in ids:
                ids.append(x)
    for f in FRIEND_IDS:
        if f not in ids:
            ids.append(f)
    return ids
ALL_IDS = get_all_ids()

# ========== UPSTOX CLIENT - V8.3 ==========
def upstox_headers():
    return {"Authorization": f"Bearer {UPSTOX_TOKEN.strip()}", "Accept": "application/json"}

def upstox_live_price(instrument_key):
    if not UPSTOX_ENABLED:
        print("Upstox disabled - no token in secret")
        return None
    try:
        r = requests.get(f"{UPSTOX_BASE}/market-quote/quotes", headers=upstox_headers(), params={"instrument_key": instrument_key}, timeout=10)
        print(f"DEBUG Upstox quotes {instrument_key} status={r.status_code} resp={r.text[:300]}")
        if r.status_code == 200:
            data = r.json().get("data", {})
            q = data.get(instrument_key, {})
            lp = q.get("last_price") or q.get("ltp") or q.get("last_traded_price")
            if lp:
                return float(lp)
            print(f"DEBUG Upstox quotes empty for {instrument_key}, trying LTP")
    except Exception as e:
        print(f"Upstox quotes error {instrument_key} {e}")
    try:
        r2 = requests.get(f"{UPSTOX_BASE}/market-quote/ltp", headers=upstox_headers(), params={"instrument_key": instrument_key}, timeout=10)
        print(f"DEBUG Upstox LTP {instrument_key} status={r2.status_code} resp={r2.text[:300]}")
        if r2.status_code == 200:
            data = r2.json().get("data", {})
            q = data.get(instrument_key, {})
            lp = q.get("last_price") or q.get("ltp") or q.get("last_traded_price")
            if lp:
                return float(lp)
    except Exception as e:
        print(f"Upstox LTP error {instrument_key} {e}")
    try:
        r3 = requests.get("https://api.upstox.com/v2/market-quote/quotes", headers=upstox_headers(), params={"instrument_key": instrument_key}, timeout=10)
        print(f"DEBUG Upstox v2 {instrument_key} status={r3.status_code} resp={r3.text[:300]}")
        if r3.status_code == 200:
            data = r3.json().get("data", {})
            q = data.get(instrument_key, {})
            lp = q.get("last_price") or q.get("ltp")
            if lp:
                return float(lp)
    except Exception as e:
        print(f"Upstox v2 error {e}")
    return None

def upstox_candles(instrument_key, interval="15minute"):
    if not UPSTOX_ENABLED:
        return None
    try:
        r = requests.get(f"{UPSTOX_BASE}/market-candle/intraday/{instrument_key}/{interval}", headers=upstox_headers(), timeout=15)
        if r.status_code != 200:
            return None
        return r.json().get("data", {}).get("candles", [])
    except:
        return None

def to_upstox_key(yahoo_sym):
    base = yahoo_sym.replace(".NS", "").replace("-", "_").upper()
    return f"NSE_EQ|{base}"

def upstox_token_health():
    try:
        clean = str(UPSTOX_EXPIRY).strip().strip('"').strip("'").strip()
        if " " in clean:
            clean = clean.split(" ")[0]
        print(f"DEBUG Expiry raw='{UPSTOX_EXPIRY}' clean='{clean}'")
        exp = datetime.strptime(clean, "%Y-%m-%d").date()
        today = datetime.now(IST).date()
        days = (exp - today).days
        print(f"DEBUG Expiry days left={days}")
        if days < 0:
            return "EXPIRED", days
        if days < 30:
            return f"EXPIRING in {days}d - Renew Soon", days
        return f"OK - {days}d left", days
    except Exception as e:
        print(f"DEBUG Expiry parse fail '{UPSTOX_EXPIRY}' err {e} - treating as OK")
        return "OK", 999

# ========== PAPER TRADING - BTST ONLY ==========
PAPER_FILE = "paper_trades.csv"
PAPER_QTY_DEFAULT = 100

def btst_gtt_plan(entry, sl, tgt, direction="BUY"):
    try:
        entry = float(entry)
        sl = float(sl)
        tgt = float(tgt)
        if direction == "BUY":
            sl_gtt = round(sl * 0.995, 2)
            t1 = round(entry + (tgt - entry) * 0.5, 2)
            t2 = round(tgt, 2)
        else:
            sl_gtt = round(sl * 1.005, 2)
            t1 = round(entry - (entry - tgt) * 0.5, 2)
            t2 = round(tgt, 2)
        return {"entry": round(entry, 2), "sl_gtt": sl_gtt, "t1": t1, "t2": t2}
    except Exception as e:
        print(f"btst_gtt_plan err {e}")
        return {"entry": round(float(entry), 2), "sl_gtt": round(float(sl), 2), "t1": round(float(tgt), 2), "t2": round(float(tgt), 2)}

def record_btst_paper(symbol, entry, sl, tgt, direction="BUY", qty=None):
    try:
        plan = btst_gtt_plan(entry, sl, tgt, direction)
        if qty is None:
            qty = PAPER_QTY_DEFAULT
        file_exists = os.path.exists(PAPER_FILE)
        if file_exists:
            try:
                with open(PAPER_FILE, "r") as rf:
                    rows = list(csv.DictReader(rf))
                    today = datetime.now(IST).strftime("%Y-%m-%d")
                    for r in rows:
                        if r.get("date") == today and r.get("bot") == "BOT2_BTST" and r.get("symbol") == symbol and r.get("status") == "OPEN":
                            print(f"Paper duplicate skip BOT2_BTST {symbol}")
                            return plan
            except Exception:
                pass
        with open(PAPER_FILE, "a", newline="") as f:
            w = csv.writer(f)
            if not file_exists:
                w.writerow(["date", "bot", "symbol", "entry", "sl", "t1", "t2", "qty", "status", "exit_price", "pnl", "exit_reason"])
            w.writerow([datetime.now(IST).strftime("%Y-%m-%d"), "BOT2_BTST", symbol, plan["entry"], plan["sl_gtt"], plan["t1"], plan["t2"], qty, "OPEN", "", "", ""])
        print(f"Paper BTST recorded {symbol} Entry {plan['entry']} SL {plan['sl_gtt']} T1 {plan['t1']} T2 {plan['t2']}")
        return plan
    except Exception as e:
        print(f"record_btst_paper err {e}")
        return btst_gtt_plan(entry, sl, tgt, direction)

def check_paper_trades():
    updates = []
    if not os.path.exists(PAPER_FILE):
        return updates
    try:
        with open(PAPER_FILE, "r") as f:
            rows = list(csv.DictReader(f))
        if not rows:
            return updates
        changed = False
        for r in rows:
            if r.get("status") != "OPEN":
                continue
            symbol = r.get("symbol", "")
            try:
                entry = float(r.get("entry") or 0)
                sl = float(r.get("sl") or 0)
                t1 = float(r.get("t1") or 0)
                t2 = float(r.get("t2") or 0)
                qty = float(r.get("qty") or PAPER_QTY_DEFAULT)
                if entry <= 0:
                    continue
                cmp_price = None
                try:
                    if UPSTOX_ENABLED:
                        yahoo_sym = symbol if symbol.endswith(".NS") else symbol + ".NS"
                        cmp_price = upstox_live_price(to_upstox_key(yahoo_sym))
                except Exception:
                    cmp_price = None
                if not cmp_price:
                    try:
                        yahoo_sym = symbol if symbol.endswith(".NS") else symbol + ".NS"
                        df = get_data(yahoo_sym, period="5d", interval="1d")
                        if df is not None and len(df) > 0:
                            cmp_price = float(df['Close'].iloc[-1])
                    except Exception:
                        cmp_price = None
                if not cmp_price or cmp_price <= 0:
                    continue
                pnl_pct = (cmp_price - entry) / entry * 100 if entry else 0
                if cmp_price <= sl:
                    pnl = round((cmp_price - entry) * qty, 2)
                    r["status"] = "CLOSED_SL"
                    r["exit_price"] = cmp_price
                    r["pnl"] = pnl
                    r["exit_reason"] = "SL HIT"
                    updates.append(f"{symbol} ({r.get('bot')}) PAPER EXIT - SL HIT @ {cmp_price:.0f} P&L {pnl_pct:.1f}% Rs {pnl:.0f} (PAPER)")
                    changed = True
                elif t2 > 0 and cmp_price >= t2:
                    pnl = round((cmp_price - entry) * qty, 2)
                    r["status"] = "CLOSED_T2"
                    r["exit_price"] = cmp_price
                    r["pnl"] = pnl
                    r["exit_reason"] = "T2 HIT"
                    updates.append(f"{symbol} ({r.get('bot')}) PAPER EXIT - T2 HIT @ {cmp_price:.0f} P&L {pnl_pct:.1f}% Rs {pnl:.0f} (PAPER)")
                    changed = True
                elif t1 > 0 and cmp_price >= t1:
                    if r.get("exit_reason") != "T1_HIT":
                        pnl_50 = round((t1 - entry) * (qty * 0.5), 2)
                        r["exit_reason"] = "T1_HIT"
                        updates.append(f"{symbol} ({r.get('bot')}) PAPER T1 HIT @ {t1:.0f} P&L {pnl_pct:.1f}% Book 50% Rs {pnl_50:.0f} | Trail SL to Entry {entry:.0f} (PAPER)")
                        changed = True
            except Exception as e:
                print(f"check_paper {symbol} err {e}")
                continue
        if changed:
            with open(PAPER_FILE, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["date", "bot", "symbol", "entry", "sl", "t1", "t2", "qty", "status", "exit_price", "pnl", "exit_reason"])
                w.writeheader()
                w.writerows(rows)
        return updates
    except Exception as e:
        print(f"check_paper_trades err {e}")
        return updates

def format_paper_updates(paper_updates):
    if not paper_updates:
        return ""
    txt = "\n--- PAPER TRADE UPDATES (VIRTUAL) ---\n"
    for u in paper_updates:
        txt += f"{u}\n"
    txt += "-----------------------------------\n"
    return txt

FNO_STOCKS = [
"RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS","SBIN.NS","LT.NS","ITC.NS",
"TITAN.NS","AXISBANK.NS","KOTAKBANK.NS","HINDUNILVR.NS","ASIANPAINT.NS","MARUTI.NS",
"BAJFINANCE.NS","BAJAJFINSV.NS","TATAMOTORS.NS","TATASTEEL.NS","JSWSTEEL.NS","HINDALCO.NS",
"NTPC.NS","POWERGRID.NS","ONGC.NS","COALINDIA.NS","BPCL.NS","ADANIENT.NS","ADANIPORTS.NS",
"GRASIM.NS","ULTRACEMCO.NS","SHRIRAMFIN.NS","M&M.NS","EICHERMOT.NS","HEROMOTOCO.NS",
"BAJAJ-AUTO.NS","DRREDDY.NS","SUNPHARMA.NS","CIPLA.NS","DIVISLAB.NS","APOLLOHOSP.NS",
"WIPRO.NS","TECHM.NS","HCLTECH.NS","LTIM.NS","TATACONSUM.NS","NESTLEIND.NS","BRITANNIA.NS",
"VEDL.NS","SAIL.NS","NHPC.NS","TATAPOWER.NS","SIEMENS.NS","HAVELLS.NS","BEL.NS","HAL.NS",
"IRCTC.NS","ZOMATO.NS","PAYTM.NS","NYKAA.NS","DMART.NS","TRENT.NS","PIDILIT.NS","AMBUJACEM.NS",
"ACC.NS","BHARTIARTL.NS","JIOFIN.NS","HDFCLIFE.NS","SBILIFE.NS","ICICIPRULI.NS","LICI.NS",
"RECLTD.NS","PFC.NS","CANBK.NS","PNB.NS","BANKBARODA.NS","INDUSINDBK.NS","FEDERALBNK.NS",
"IDFCFIRSTB.NS","MUTHOOTFIN.NS","CHOLAFIN.NS","TATACHEM.NS","UPL.NS","SRF.NS","PIIND.NS",
"ALKEM.NS","TORNTPHARM.NS","AUROPHARMA.NS","LUPIN.NS","BIOCON.NS","COLPAL.NS","DABUR.NS",
"MARICO.NS","GODREJCP.NS","UBL.NS","INDIGO.NS","MCDOWELL-N.NS","TATACOMM.NS","BOSCHLTD.NS",
"ABB.NS","CUMMINSIND.NS","LTTS.NS","PERSISTENT.NS","COFORGE.NS","MPHASIS.NS","HINDPETRO.NS",
"GAIL.NS","PETRONET.NS","IGL.NS","MGL.NS","CONCOR.NS","NMDC.NS","HINDCOPPER.NS","JINDALSTEL.NS",
"ASHOKLEY.NS","TVSMOTOR.NS","BALKRISIND.NS","MRF.NS","APOLLOTYRE.NS","EXIDEIND.NS","AMARAJABAT.NS",
"VOLTAS.NS","BLUESTARCO.NS","CROMPTON.NS","DIXON.NS","KAYNES.NS","CGPOWER.NS","SUZLON.NS",
"BHEL.NS","IRFC.NS","RVNL.NS","MAZAGON.NS","COCHINSHIP.NS","HUDCO.NS","IREDA.NS","NBCC.NS",
"PNBHOUSING.NS","MANAPPURAM.NS","POONAWALLA.NS","ABCAPITAL.NS","AUBANK.NS","YESBANK.NS",
"UNIONBANK.NS","INDIANB.NS","BANKINDIA.NS","MAHABANK.NS","CENTRALBK.NS","IOB.NS","UCOBANK.NS",
"PSB.NS","J&KBANK.NS","KARURVYSYA.NS","CITYUNION.NS","RBLBANK.NS","BANDHANBNK.NS"
]

SECTOR_MAP = {
"RELIANCE.NS":"^CNXENERGY","HDFCBANK.NS":"^NSEBANK","ICICIBANK.NS":"^NSEBANK","SBIN.NS":"^NSEBANK",
"AXISBANK.NS":"^NSEBANK","KOTAKBANK.NS":"^NSEBANK","INFY.NS":"^CNXIT","TCS.NS":"^CNXIT",
"WIPRO.NS":"^CNXIT","TECHM.NS":"^CNXIT","HCLTECH.NS":"^CNXIT","TATAMOTORS.NS":"^CNXAUTO",
"M&M.NS":"^CNXAUTO","MARUTI.NS":"^CNXAUTO","BAJAJ-AUTO.NS":"^CNXAUTO","HEROMOTOCO.NS":"^CNXAUTO",
"TATASTEEL.NS":"^CNXMETAL","JSWSTEEL.NS":"^CNXMETAL","HINDALCO.NS":"^CNXMETAL","SUNPHARMA.NS":"^CNXPHARMA",
"DRREDDY.NS":"^CNXPHARMA","CIPLA.NS":"^CNXPHARMA","DIVISLAB.NS":"^CNXPHARMA","ITC.NS":"^CNXFMCG",
"HINDUNILVR.NS":"^CNXFMCG","NESTLEIND.NS":"^CNXFMCG","TATAPOWER.NS":"^CNXENERGY","NTPC.NS":"^CNXENERGY",
"ONGC.NS":"^CNXENERGY","POWERGRID.NS":"^CNXENERGY",
}

def send_tg(msg):
    if not BOT_TOKEN:
        print("No BOT_TOKEN")
        return
    for cid in ALL_IDS:
        try:
            r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": cid, "text": msg, "parse_mode": "HTML"}, timeout=20)
            print(f"Telegram to {cid} {r.status_code}")
        except Exception as e:
            print(f"TG fail {cid} {e}")

def get_data(sym, period="3mo", interval="1d"):
    try:
        df = yf.download(sym, period=period, interval=interval, progress=False, auto_adjust=True)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        return df
    except:
        return None

def get_data_tf(sym, interval="1wk"):
    try:
        if interval == "1wk":
            return get_data(sym, period="2y", interval="1wk")
        if interval == "1mo":
            return get_data(sym, period="5y", interval="1mo")
        if interval == "1h":
            return get_data(sym, period="1mo", interval="1h")
        if interval == "15m":
            return get_data(sym, period="5d", interval="15m")
        if interval == "1d":
            return get_data(sym, period="2y", interval="1d")
        return get_data(sym, period="3mo", interval=interval)
    except:
        return None

def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()

def rsi_calc(s, n=14):
    d = s.diff()
    g = d.clip(lower=0)
    l = -d.clip(upper=0)
    ag = g.ewm(alpha=1/n, adjust=False).mean()
    al = l.ewm(alpha=1/n, adjust=False).mean()
    rs = ag / (al + 1e-9)
    return 100 - (100 / (1 + rs))

def atr_calc(df, n=14):
    h = df['High']
    l = df['Low']
    c = df['Close']
    pc = c.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()

def adx_calc(df, n=14):
    h = df['High']
    l = df['Low']
    c = df['Close']
    up = h.diff()
    dn = -l.diff()
    pm = np.where((up > dn) & (up > 0), up, 0)
    mm = np.where((dn > up) & (dn > 0), dn, 0)
    tr = pd.concat([h - l, (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/n, adjust=False).mean()
    pdm = pd.Series(pm, index=df.index).ewm(alpha=1/n, adjust=False).mean()
    mdm = pd.Series(mm, index=df.index).ewm(alpha=1/n, adjust=False).mean()
    pdi = 100 * pdm / (atr + 1e-9)
    mdi = 100 * mdm / (atr + 1e-9)
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi + 1e-9)
    return dx.ewm(alpha=1/n, adjust=False).mean(), pdi, mdi

def safe_float(x, default=0.0):
    try:
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return default
        return float(x)
    except:
        return default

# ===== BALA AVWP - V8.3 NEW =====
def _get_swing_lows(df, left=5, right=5):
    lows = []
    try:
        for i in range(left, len(df) - right):
            window = df['Low'].iloc[i-left:i+right+1]
            if df['Low'].iloc[i] == window.min():
                lows.append((df.index[i], safe_float(df['Low'].iloc[i])))
    except Exception as e:
        print(f"Bala swing err {e}")
    return lows

def _anchored_vwap(df, anchor_idx):
    try:
        sub = df.iloc[anchor_idx:].copy()
        tp = (sub['High'] + sub['Low'] + sub['Close']) / 3
        pv = (tp * sub['Volume']).cumsum()
        vv = sub['Volume'].cumsum().replace(0, np.nan)
        return safe_float((pv / vv).iloc[-1])
    except:
        return 0

def bala_day_15m_check(sym):
    # MORNING: 15-min Low AVWP within 0.4%
    try:
        df_15 = get_data_tf(sym, interval="15m")
        if df_15 is None or len(df_15) < 60:
            return None
        swings = _get_swing_lows(df_15, 5, 5)
        if len(swings) < 2:
            return None
        latest_idx = df_15.index.get_loc(swings[-1][0])
        avwp = _anchored_vwap(df_15, latest_idx)
        if avwp <= 0:
            return None
        price = safe_float(df_15['Close'].iloc[-1])
        swing_low = swings[-1][1]
        if abs(price - avwp) / avwp <= 0.004 and price >= avwp:
            sl = round(swing_low * 0.996, 2)
            if sl % 1 == 0:
                sl -= 0.30
            risk = price - sl
            if risk <= 0:
                return None
            return {"type": "DAY", "avwp": round(avwp, 2), "price": round(price, 2), "sl_avwp": sl, "swing_low": swing_low, "t1": round(price + risk * 1.5, 2), "t2": round(price + risk * 2.5, 2)}
        return None
    except Exception as e:
        print(f"Bala Day {sym} err {e}")
        return None

def bala_btst_1h_check(sym):
    # BTST: Close must be > 1H Low AVWP, else SKIP BTST for this stock
    try:
        df_1h = get_data_tf(sym, interval="1h")
        if df_1h is None or len(df_1h) < 60:
            return {"btst_valid": True, "reason": "No 1H data - allow, not block", "avwp": 0}
        swings = _get_swing_lows(df_1h, 5, 5)
        if len(swings) < 2:
            return {"btst_valid": True, "reason": "No swing - allow", "avwp": 0}
        latest_idx = df_1h.index.get_loc(swings[-1][0])
        avwp = _anchored_vwap(df_1h, latest_idx)
        if avwp <= 0:
            return {"btst_valid": True, "reason": "No AVWP", "avwp": 0}
        price = safe_float(df_1h['Close'].iloc[-1])
        swing_low = swings[-1][1]
        sl = round(swing_low * 0.996, 2)
        if sl % 1 == 0:
            sl -= 0.30
        if price > avwp:
            return {"btst_valid": True, "avwp": round(avwp, 2), "close": round(price, 2), "sl_avwp": sl, "swing_low": swing_low}
        return {"btst_valid": False, "avwp": round(avwp, 2), "close": round(price, 2), "sl_avwp": sl, "reason": "Close below 1H AVWP - SKIP BTST"}
    except Exception as e:
        print(f"Bala BTST {sym} err {e}")
        return {"btst_valid": True, "reason": str(e), "avwp": 0}

def bala_full_check(sym, df_daily):
    # Full Bala: Chartink + Monthly RSI + Daily/Weekly 200>=400 + 1H AVWP - for +12 boost in BTST
    try:
        if df_daily is None or len(df_daily) < 220:
            return None
        df = df_daily.copy()
        close = df['Close']
        e20 = safe_float(ema(close, 20).iloc[-1])
        e50 = safe_float(ema(close, 50).iloc[-1])
        e200 = safe_float(ema(close, 200).iloc[-1])
        e400 = safe_float(ema(close, 400).iloc[-1])
        c = safe_float(close.iloc[-1])
        l = safe_float(df['Low'].iloc[-1])
        o = safe_float(df['Open'].iloc[-1])
        rsi_d = safe_float(rsi_calc(close).iloc[-1])
        vol_ema20 = safe_float(df['Volume'].ewm(span=20, adjust=False).mean().iloc[-1])
        if not (e20 > e50 and c > e200 and l <= e20 * 1.03 and c >= e20 * 0.97 and c <= e20 * 1.04 and c > o and c > 100 and 42 <= rsi_d <= 63 and vol_ema20 > 300000):
            return None
        mo = get_data_tf(sym, interval="1mo")
        if mo is None or len(mo) < 15:
            return None
        rsi_m = safe_float(rsi_calc(mo['Close']).iloc[-1])
        if not (rsi_m > 60):
            return None
        wk = get_data_tf(sym, interval="1wk")
        if wk is None or len(wk) < 50:
            return None
        w200 = safe_float(ema(wk['Close'], 200).iloc[-1])
        w400 = safe_float(ema(wk['Close'], 400).iloc[-1])
        if np.isnan(w400) or w400 == 0:
            w400 = safe_float(ema(wk['Close'], 100).iloc[-1])
        if not (e200 >= e400 and w200 >= w400):
            return None
        bt = bala_btst_1h_check(sym)
        if not bt.get("btst_valid"):
            return None
        # Also need price within 0.4% of AVWP for early entry
        df_1h = get_data_tf(sym, interval="1h")
        if df_1h is None:
            return None
        price_1h = safe_float(df_1h['Close'].iloc[-1])
        avwp = bt.get("avwp", 0)
        if avwp > 0 and abs(price_1h - avwp) / avwp > 0.004:
            return None
        return {"avwp": avwp, "sl_avwp": bt.get("sl_avwp", 0), "rsi_d": round(rsi_d, 1), "rsi_m": round(rsi_m, 1)}
    except Exception as e:
        print(f"Bala Full {sym} err {e}")
        return None

def smart_sl(entry, support, resistance, atr, direction):
    max_dist = entry * 0.015
    if direction == "BUY":
        base = support - (atr * 0.8) - (entry * 0.003)
        sl = base
        if entry - base > max_dist:
            sl = entry - max_dist
        if round(sl) % 10 == 0:
            sl = sl - 7.37
        tgt = entry + (entry - sl) * 2
    else:
        base = resistance + (atr * 0.8) + (entry * 0.003)
        sl = base
        if sl - entry > max_dist:
            sl = entry + max_dist
        if round(sl) % 10 == 0:
            sl = sl + 7.37
        tgt = entry - (sl - entry) * 2
    sl_pct = abs(entry - sl) / entry * 100
    return round(sl, 2), round(tgt, 2), round(sl_pct, 2)

def detect_regime_and_choppy():
    nifty = get_data("^NSEI", period="3mo", interval="1d")
    bank = get_data("^NSEBANK", period="3mo", interval="1d")
    vix = get_data("^INDIAVIX", period="1mo", interval="1d")
    if nifty is None:
        return "TRANSITION", 0, 0, 0, "Nifty data fail", False, "Yahoo"
    close = nifty['Close']
    ema20 = ema(close, 20)
    ema50 = ema(close, 50)
    adx, _, _ = adx_calc(nifty)
    atr = atr_calc(nifty)
    last = float(close.iloc[-1])
    e20 = float(ema20.iloc[-1])
    e50 = float(ema50.iloc[-1])
    adx_v = float(adx.iloc[-1])
    vix_v = float(vix['Close'].iloc[-1]) if vix is not None else 14
    vix_prev = float(vix['Close'].iloc[-2]) if vix is not None and len(vix) > 1 else vix_v
    vix_jump = (vix_v - vix_prev) / vix_prev * 100 if vix_prev else 0
    data_source = "Yahoo (Delayed)"
    if UPSTOX_ENABLED:
        live_nifty = upstox_live_price("NSE_INDEX|Nifty 50")
        live_vix = upstox_live_price("NSE_INDEX|India VIX")
        if live_nifty:
            print(f"Upstox Nifty Live: {live_nifty} vs Yahoo {last}")
            last = live_nifty
            data_source = "Upstox Live"
        if live_vix:
            print(f"Upstox VIX Live: {live_vix} vs Yahoo {vix_v}")
            vix_v = live_vix
            data_source = "Upstox Live"
    rng = (float(nifty['High'].iloc[-5:].max()) - float(nifty['Low'].iloc[-5:].min())) / last * 100
    choppy_score = 0
    reasons = []
    if adx_v < 18:
        choppy_score += 1
        reasons.append(f"ADX {adx_v:.1f} Weak")
    if vix_v > 17 or vix_jump > 10:
        choppy_score += 1
        reasons.append(f"VIX {vix_v:.1f} High")
    if rng < 1.2:
        choppy_score += 1
        reasons.append(f"Range5D {rng:.2f}% Small")
    if bank is not None:
        bclose = bank['Close']
        bema20 = ema(bclose, 20)
        nifty_up = last > e20
        bank_up = float(bclose.iloc[-1]) > float(bema20.iloc[-1])
        if nifty_up != bank_up:
            choppy_score += 1
            reasons.append("Nifty vs Bank Disagree")
    if abs(last - e20) / last * 100 < 0.3 and adx_v < 20:
        choppy_score += 1
        reasons.append("Near EMA20 + Weak ADX")
    is_choppy = choppy_score >= 3
    if is_choppy:
        regime = "CHOPPY - NO TRADE"
    elif last > e20 and last > e50 and adx_v > 25:
        regime = "STRONG BULL"
    elif last < e20 and last < e50 and adx_v > 25:
        regime = "STRONG BEAR"
    elif adx_v < 22:
        regime = "SIDEWAYS"
    elif vix_v > 17:
        regime = "VOLATILE"
    else:
        regime = "TRANSITION"
    info = f"Nifty {last:.1f} | EMA20 {e20:.1f} EMA50 {e50:.1f} | ADX {adx_v:.1f} | VIX {vix_v:.1f} | Range5D {rng:.2f}% | Choppy {choppy_score}/5 | Data: {data_source}"
    return regime, adx_v, vix_v, last, info, is_choppy, data_source

def scan_stocks(regime, run_type):
    results = []
    for sym in FNO_STOCKS:
        try:
            df = get_data(sym, period="3mo", interval="1d")
            if df is None or len(df) < 60:
                continue
            close = df['Close']
            high = df['High']
            low = df['Low']
            last = float(close.iloc[-1])
            prev = float(close.iloc[-2])
            e20 = float(ema(close, 20).iloc[-1])
            e50 = float(ema(close, 50).iloc[-1])
            rsi = float(rsi_calc(close).iloc[-1])
            atr = float(atr_calc(df).iloc[-1])
            adx, _, _ = adx_calc(df)
            adx_v = float(adx.iloc[-1])
            prev_high = float(high.iloc[-2])
            prev_low = float(low.iloc[-2])
            sup = prev_low
            res = prev_high
            live_price = None
            if UPSTOX_ENABLED:
                live_price = upstox_live_price(to_upstox_key(sym))
                if live_price:
                    print(f"Upstox {sym}: Live {live_price} vs Yahoo {last}")
                    last = live_price
            rng_pct = (res - sup) / last * 100 if last else 0
            day_move = abs(last - prev) / prev * 100
            if run_type == "MORNING" and day_move > 2.5:
                continue
            sector_ok = True
            sec_sym = SECTOR_MAP.get(sym)
            if sec_sym:
                sec = get_data(sec_sym, period="1mo", interval="1d")
                if sec is not None:
                    sc = sec['Close']
                    se20 = float(ema(sc, 20).iloc[-1])
                    slast = float(sc.iloc[-1])
                    if (slast > se20) != (last > e20):
                        sector_ok = False
            score = 0
            direction = None
            strategy = ""
            entry = last
            bala_data = None
            bala_avwp = False
            # BALA AVWP - MORNING Day 15m
            if run_type == "MORNING" and regime in ["STRONG BULL", "SIDEWAYS", "TRANSITION", "VOLATILE"]:
                bd = bala_day_15m_check(sym)
                if bd:
                    bala_data = bd
                    bala_avwp = True
            # BALA AVWP - BTST 1H Filter + Full Check
            if run_type == "BTST":
                bt = bala_btst_1h_check(sym)
                if not bt.get("btst_valid"):
                    print(f"BTST SKIP {sym} - {bt.get('reason')} AVWP {bt.get('avwp')} Close {bt.get('close')}")
                    continue
                # Full Bala for +12 boost
                df_full = get_data(sym, period="2y", interval="1d")
                bf = bala_full_check(sym, df_full) if df_full is not None else None
                if bf:
                    bala_data = bf
                    bala_avwp = True
            if regime in ["SIDEWAYS", "VOLATILE"]:
                if rng_pct < 1.2:
                    continue
                if abs(last - sup) / last * 100 < 0.8 and rsi < 40:
                    direction = "BUY"
                    strategy = "Sideways Support Buy"
                    score = 75
                    if sector_ok:
                        score += 10
                    if rsi < 35:
                        score += 5
                elif abs(last - res) / last * 100 < 0.8 and rsi > 60:
                    direction = "SELL"
                    strategy = "Sideways Resistance Sell"
                    score = 75
                    if sector_ok:
                        score += 10
                    if rsi > 65:
                        score += 5
            elif regime == "STRONG BULL":
                if last > e20 and last > e50 and 50 < rsi < 70:
                    if last >= res * 0.995:
                        direction = "BUY"
                        strategy = "Bull Breakout"
                        score = 85
                    elif abs(last - e20) / last * 100 < 1.0:
                        direction = "BUY"
                        strategy = "Bull Pullback"
                        score = 80
            elif regime == "STRONG BEAR":
                if last < e20 and last < e50 and 30 < rsi < 50:
                    if last <= sup * 1.005:
                        direction = "SELL"
                        strategy = "Bear Breakdown"
                        score = 85
                    elif abs(last - e20) / last * 100 < 1.0:
                        direction = "SELL"
                        strategy = "Bear Pullback"
                        score = 80
            # If Bala Day passed but no other strategy matched, still allow Bala as standalone BUY
            if bala_avwp and direction is None and run_type == "MORNING":
                if last > e20 and last > e50:
                    direction = "BUY"
                    strategy = "Bala AVWP Day"
                    score = 80
            if bala_avwp and direction == "BUY":
                score += 12
                score = min(95, score)
                if "Bala" not in strategy:
                    strategy = strategy + " + Bala AVWP"
                else:
                    strategy = strategy
            if direction:
                sl, tgt, sl_pct = smart_sl(entry, sup, res, atr, direction)
                # Bala SL override - tighter
                if bala_avwp and bala_data and bala_data.get("sl_avwp"):
                    bala_sl = bala_data["sl_avwp"]
                    if direction == "BUY" and bala_sl < entry and bala_sl > entry * 0.97:
                        sl = round(min(sl, bala_sl), 2)
                        tgt = round(entry + (entry - sl) * 2, 2)
                        sl_pct = round(abs(entry - sl) / entry * 100, 2)
                if sl_pct > 1.8 or sl_pct < 0.4:
                    continue
                qty = int(RISK_PER_TRADE // abs(entry - sl)) if abs(entry - sl) > 0 else 0
                if qty <= 0:
                    continue
                if "Sideways" in strategy:
                    qty = qty // 2
                results.append({"sym": sym.replace(".NS", ""), "entry": round(entry, 2), "sl": sl, "tgt": tgt,
                    "sl_pct": sl_pct, "dir": direction, "strat": strategy, "score": score,
                    "rsi": round(rsi, 1), "sup": round(sup, 2), "res": round(res, 2),
                    "rng": round(rng_pct, 2), "qty": qty,
                    "src": "Upstox Live" if live_price else "Yahoo",
                    "bala_avwp": bala_avwp, "bala_data": bala_data})
        except Exception as e:
            print(f"Scan fail {sym} {e}")
            continue
    results = sorted(results, key=lambda x: x['score'], reverse=True)
    return results[:MAX_TRADES]

def get_run_type(now):
    total = now.hour * 60 + now.minute
    if 580 <= total <= 610:
        return "MORNING"
    if 895 <= total <= 940:
        return "BTST"
    if 985 <= total <= 1015:
        return "EOD"
    return None

def main():
    now = datetime.now(IST)
    total = now.hour * 60 + now.minute
    run_type = get_run_type(now)
    if run_type is None:
        if total >= 870 and total < 970:
            run_type = "BTST"
        elif total >= 970:
            run_type = "EOD"
        else:
            run_type = "MORNING"
    print(f"Manual run - Treated as {run_type} at {now.strftime('%H:%M IST')} - Time guard disabled - V8.3")
    if run_type == "MORNING":
        run_label = "MORNING ENTRY - 09:45 IST"
    elif run_type == "BTST":
        run_label = "BTST - 15:00 IST - Buy Today Sell Tomorrow"
    else:
        run_label = "EOD REPORT - 16:30 IST"
    token_msg = "Upstox: OFF - Yahoo Only"
    if UPSTOX_ENABLED:
        health, days = upstox_token_health()
        token_msg = f"Upstox: {health} | Exp {UPSTOX_EXPIRY.strip()}"
        print(token_msg)
        print("Token health is info only - will still try Upstox Live (auto-refresh token)")
    else:
        print("No UPSTOX_ACCESS_TOKEN - Using Yahoo only")
    paper_updates = []
    try:
        paper_updates = check_paper_trades()
        if paper_updates:
            print(f"Paper updates: {paper_updates}")
    except Exception as e:
        print(f"Paper check skip {e}")
    paper_txt = format_paper_updates(paper_updates)
    is_thursday = now.weekday() == 3
    print(f"V8.3 Run {run_type} {now} IST")
    regime, adx_v, vix_v, nifty_last, regime_info, is_choppy, data_src = detect_regime_and_choppy()
    print(regime_info)
    if is_choppy and run_type in ["MORNING", "BTST"]:
        msg = (f"🚫 <b>FNO V8.3 - NO TRADE - {run_label}</b>\n"
             f"📅 {now.strftime('%d-%m-%Y %H:%M IST')}\n"
             f"Regime: <b>CHOPPY - NO TRADE</b>\n{regime_info}\n"
             f"Reason: 3+/5 Choppy Tests True\n"
             f"Action: <b>PROTECT CAPITAL - No Trade</b>\n"
             f"Next Check: {'3:00 PM IST BTST' if run_type == 'MORNING' else 'Tomorrow 9:45 AM IST'}\n"
             f"{paper_txt}"
             f"{token_msg}")
        send_tg(msg)
        print("Choppy - No Trade")
        return
    if run_type == "EOD":
        msg = (f"📊 <b>FNO V8.3 - EOD REPORT - 16:30 IST</b>\n"
             f"📅 {now.strftime('%d-%m-%Y')}\n"
             f"Regime Today: <b>{regime}</b>\n{regime_info}\n"
             f"Tomorrow Plan: {'Sideways - Buy at Support / Sell at Resistance, 50% size' if regime == 'SIDEWAYS' else regime}\n"
             f"Thursday Note: {'Tomorrow is Friday - No BTST Today' if is_thursday else 'BTST allowed tomorrow if not Choppy'}\n"
             f"Smart SL: Max 1.0% Intraday, 1.5% BTST, 1.8% Swing - Buffered, Non-Round, Close-Based\n"
             f"{paper_txt}"
             f"{token_msg}\nCapital: Rs 5L Paper")
        send_tg(msg)
        print("EOD Sent")
        return
    if run_type == "BTST" and is_thursday:
        msg = (f"🚫 <b>FNO V8.3 - NO BTST - Thursday - 15:00 IST</b>\nRegime: {regime}\n{regime_info}\n"
             f"Reason: Thursday BTST = Friday Gap Risk High\nAction: Book all BTST, No new BTST\nNext: Tomorrow 9:45 AM IST\n{paper_txt}")
        send_tg(msg)
        print("Thursday No BTST")
        return
    picks = scan_stocks(regime, run_type)
    if not picks:
        msg = (f"📊 <b>FNO V8.3 - NO TRADE - {run_label}</b>\n📅 {now.strftime('%d-%m-%Y %H:%M IST')}\n"
             f"Regime: <b>{regime}</b>\n{regime_info}\n"
             f"Reason: No stock passed - SL too high / Gap >1.5% / Sector Disagree / Range too small / BTST below AVWP\n{paper_txt}{token_msg}\nCapital: Rs 5L Paper")
        send_tg(msg)
        print("No picks")
        return
    btst_plans = {}
    if run_type == "BTST":
        for p in picks:
            try:
                if p['dir'] == "BUY":
                    plan = record_btst_paper(p['sym'], p['entry'], p['sl'], p['tgt'], direction="BUY", qty=p['qty'])
                    btst_plans[p['sym']] = plan
                else:
                    btst_plans[p['sym']] = btst_gtt_plan(p['entry'], p['sl'], p['tgt'], direction="SELL")
            except Exception as e:
                print(f"Paper BTST record skip {p['sym']} {e}")
    lines = []
    for i, p in enumerate(picks, 1):
        emoji = "🟢" if p['dir'] == "BUY" else "🔴"
        extra = ""
        if run_type == "BTST":
            extra = "\n⏰ Sell: Tomorrow 9:45 AM IST | SL: Close-Based - Exit only if 2x 15-min closes below SL"
        if "Sideways" in p['strat']:
            extra += "\n⚠️ Sideways - 50% Size - Book at VWAP / Mid"
        paper_line = ""
        if run_type == "BTST":
            plan = btst_plans.get(p['sym'])
            if plan:
                if p['dir'] == "BUY":
                    paper_line = f"\n📝 PAPER BTST: Buy Avg {plan['entry']} | SL GTT {plan['sl_gtt']} (100%) | T1 GTT {plan['t1']} (50%) | T2 GTT {plan['t2']} (50%) | Qty {p['qty']} VIRTUAL - No real order"
                else:
                    paper_line = f"\n📝 PAPER: SELL BTST not tracked as Paper Long - GTT for info only: SL {plan['sl_gtt']} T1 {plan['t1']} T2 {plan['t2']}"
        bala_tag = " 🟢 BALA AVWP" if p.get("bala_avwp") else ""
        bala_line = ""
        if p.get("bala_data") and p["bala_data"].get("avwp"):
            bala_line = f"\nAVWP Rs {p['bala_data']['avwp']} | SL_AVWP Rs {p['bala_data'].get('sl_avwp', p['sl'])} Early Entry"
        lines.append(f"\n{i}. {emoji} <b>{p['dir']} {p['sym']}</b> @ Rs {p['entry']} [{p['src']}]{bala_tag}\n"
            f"Strategy: {p['strat']} | Score: {p['score']}/100 | RSI {p['rsi']}{bala_line}\n"
            f"Support Rs {p['sup']} | Resistance Rs {p['res']} | Range {p['rng']}%\n"
            f"Smart SL Rs {p['sl']} ({p['sl_pct']}% - Buffered, Anti-Hunt, Non-Round)\n"
            f"Target Rs {p['tgt']} (RR 1:2)\nQty: {p['qty']} (Risk Rs {abs(p['entry']-p['sl'])*p['qty']:.0f})\n"
            f"Trailing: Book 50% at 50% Target, Move SL to Breakeven{extra}{paper_line}")
    action_note = "BUY TODAY - Sell Tomorrow 9:45 AM IST" if run_type == "BTST" else "Entry Now - 9:45 AM IST - Do NOT Chase if Gap >1.5%"
    paper_header = "\n<b>PAPER TRADE ONLY - BTST</b> - No real order placed\n" if run_type == "BTST" else ""
    msg = (f"📊 <b>FNO V8.3 - {run_label}</b>\n📅 {now.strftime('%d-%m-%Y %H:%M IST')}\n"
         f"Regime: <b>{regime}</b>\n{regime_info}\nAction: {action_note}\n"
         f"Max Trades: 2 | Capital: Rs 5L Paper | Risk 1% per trade\n{paper_header}{paper_txt}"
         f"{''.join(lines)}\n\n"
         f"⚠️ Smart SL: Do NOT move SL to Support / Round Number. SL is hidden below Support + Buffer. Exit only on 2x 15-min closes below SL (ignore wick).\n{token_msg}")
    send_tg(msg)
    print(f"V8.3 Complete - {len(picks)} picks sent")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(traceback.format_exc())
        try:
            send_tg(f"⚠️ V8.3 Error: {e}")
        except:
            pass
