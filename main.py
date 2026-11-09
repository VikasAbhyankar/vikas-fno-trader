# VIKAS FNO TRADER V5 FINAL - INTELLIGENT ANTI-HUNT - ZERO ERROR
# Features: Auto Regime + Long/Short + 1% SL (1.4% hidden) + 1.5% Target + 3:15 Sq Off
import datetime, csv, os, time
import pandas as pd
import yfinance as yf
import ta

REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)
TODAY = datetime.date.today().isoformat()
REPORT_FILE = f"{REPORT_DIR}/trades_FNO_{TODAY}.csv"

# CONFIG
DISPLAY_SL_PCT = 1.0   # What you see
HIDDEN_BUFFER_PCT = 0.4  # Extra hidden buffer to avoid hunt -> Actual 1.4%
TARGET_PCT = 1.5       # As per your wish
SIDEWAYS_SL = 0.8
SIDEWAYS_TARGET = 1.2

SYMBOLS = [
    "ABB.NS","ADANIENT.NS","ADANIPORTS.NS","APOLLOHOSP.NS","ASIANPAINT.NS","AUROPHARMA.NS","AXISBANK.NS",
    "BAJAJ-AUTO.NS","BAJFINANCE.NS","BANKBARODA.NS","BEL.NS","BHARTIARTL.NS","BPCL.NS","BRITANNIA.NS","CANBK.NS",
    "CHOLAFIN.NS","CIPLA.NS","COALINDIA.NS","COFORGE.NS","CONCOR.NS","DABUR.NS","DIVISLAB.NS","DLF.NS","DRREDDY.NS",
    "EICHERMOT.NS","FEDERALBNK.NS","GAIL.NS","GRASIM.NS","HAL.NS","HAVELLS.NS","HCLTECH.NS","HDFCBANK.NS",
    "HDFCLIFE.NS","HEROMOTOCO.NS","HINDALCO.NS","ICICIBANK.NS","INDHOTEL.NS","INDIGO.NS","INFY.NS","IOC.NS",
    "IRCTC.NS","ITC.NS","JSWSTEEL.NS","KOTAKBANK.NS","LT.NS","LUPIN.NS","M&M.NS","MARUTI.NS","NTPC.NS","ONGC.NS",
    "PERSISTENT.NS","PFC.NS","POWERGRID.NS","RELIANCE.NS","SBIN.NS","SUNPHARMA.NS","TATAMOTORS.NS","TATASTEEL.NS",
    "TCS.NS","TECHM.NS","TITAN.NS","TRENT.NS","ULTRACEMCO.NS","WIPRO.NS"
]

def safe_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def get_market_regime():
    try:
        nifty = yf.download("^NSEI", period="60d", interval="1d", progress=False, auto_adjust=True)
        if nifty.empty or len(nifty) < 35:
            return "SIDEWAYS", "Nifty data low - Default Sideways"
        nifty = safe_columns(nifty)
        nifty['ema20'] = ta.trend.ema_indicator(nifty['Close'], 20)
        nifty['ema50'] = ta.trend.ema_indicator(nifty['Close'], 50)
        nifty['rsi'] = ta.momentum.rsi(nifty['Close'], 14)
        last = nifty.iloc[-1]
        close = float(last['Close']); ema50 = float(last['ema50']); rsi = float(last['rsi'])
        if close > ema50 and rsi > 55:
            return "BULL", f"NIFTY {close:.0f} > 50EMA + RSI {rsi:.0f} - BULL"
        elif close < ema50 and rsi < 45:
            return "BEAR", f"NIFTY {close:.0f} < 50EMA + RSI {rsi:.0f} - BEAR"
        else:
            return "SIDEWAYS", f"NIFTY {close:.0f} ~ EMA + RSI {rsi:.0f} - SIDEWAYS"
    except Exception as e:
        print(f"Regime error {e}, default SIDEWAYS")
        return "SIDEWAYS", "Error - Default Sideways"

def get_signal(symbol, regime):
    try:
        df = yf.download(symbol, period="60d", interval="1d", progress=False, auto_adjust=True, threads=False)
        if df.empty or len(df) < 35:
            return None, 0, ""
        df = safe_columns(df)
        df['ema8'] = ta.trend.ema_indicator(df['Close'], 8)
        df['ema20'] = ta.trend.ema_indicator(df['Close'], 20)
        df['rsi9'] = ta.momentum.rsi(df['Close'], 9)
        df['rsi14'] = ta.momentum.rsi(df['Close'], 14)
        df['20h'] = df['High'].rolling(20).max()
        df['20l'] = df['Low'].rolling(20).min()
        df['vol_avg'] = df['Volume'].rolling(20).mean()
        
        last = df.iloc[-1]
        prev1 = df.iloc[-2]
        prev2 = df.iloc[-3]
        
        close = float(last['Close'])
        vol = float(last['Volume'])
        vol_avg = float(last['vol_avg'])
        rsi9 = float(last['rsi9'])
        rsi14 = float(last['rsi14'])
        ema8 = float(last['ema8'])
        ema20 = float(last['ema20'])
        high20 = float(df['20h'].iloc[-2]) if not pd.isna(df['20h'].iloc[-2]) else 0
        low20 = float(df['20l'].iloc[-2]) if not pd.isna(df['20l'].iloc[-2]) else 0
        prev_vol = float(prev1['Volume'])
        prev2_vol = float(prev2['Volume'])
        
        turnover = close * vol
        
        # BULL Regime
        if regime == "BULL":
            if close > high20 and rsi9 > 60 and ema8 > ema20 and vol > vol_avg * 1.3 and prev_vol < prev2_vol and turnover > 300000000:
                return "BUY", close, "Bull Breakout Vol+"
        # BEAR Regime
        elif regime == "BEAR":
            if close < low20 and rsi9 < 40 and ema8 < ema20 and vol > vol_avg * 1.3 and turnover > 300000000:
                return "SELL", close, "Bear Breakdown Vol+"
        # SIDEWAYS Regime - Mean Reversion
        else:
            curr_20l = float(df['20l'].iloc[-1])
            curr_20h = float(df['20h'].iloc[-1])
            if close <= curr_20l * 1.02 and rsi14 < 38 and turnover > 200000000:
                return "BUY", close, "Sideways Oversold Bounce"
            if close >= curr_20h * 0.98 and rsi14 > 62 and turnover > 200000000:
                return "SELL", close, "Sideways Overbought Drop"
        
        return None, 0, ""
    except Exception as e:
        # print(f"{symbol} error {e}")
        return None, 0, ""

def get_ltp_close(symbol):
    try:
        df = yf.download(symbol, period="1d", interval="5m", progress=False, auto_adjust=True, threads=False)
        if df.empty:
            return None
        df = safe_columns(df)
        return float(df['Close'].iloc[-1])
    except:
        return None

# ========= MAIN =========
print("=== VIKAS V5 START ===")
regime, regime_reason = get_market_regime()
print(f"REGIME: {regime} | {regime_reason}")

# Load existing report
rows = []
if os.path.exists(REPORT_FILE):
    try:
        with open(REPORT_FILE, 'r', newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
    except:
        rows = []

# 1. Check OPEN positions - Anti-Hunt Close Based SL
for r in rows:
    if r.get('status') == 'OPEN':
        try:
            ltp = get_ltp_close(r['symbol'] + ".NS")
            if ltp is None:
                continue
            entry = float(r['entry'])
            disp_sl = float(r['sl'])
            target = float(r['target'])
            side = r.get('side', 'BUY')
            
            # Actual hidden SL with buffer
            if side == 'BUY':
                actual_sl = disp_sl * (1 - HIDDEN_BUFFER_PCT/100.0)  # e.g. 1% -> 1.4% actual
                if ltp <= actual_sl:
                    r['exit'] = str(round(ltp, 2))
                    r['exit_time'] = datetime.datetime.now().strftime('%H:%M')
                    r['pnl'] = str(round(ltp - entry, 2))
                    r['status'] = 'SL_HIT_ANTI_HUNT'
                elif ltp >= target:
                    r['exit'] = str(round(ltp, 2))
                    r['exit_time'] = datetime.datetime.now().strftime('%H:%M')
                    r['pnl'] = str(round(ltp - entry, 2))
                    r['status'] = 'TARGET_HIT'
            else: # SELL
                actual_sl = disp_sl * (1 + HIDDEN_BUFFER_PCT/100.0)
                if ltp >= actual_sl:
                    r['exit'] = str(round(ltp, 2))
                    r['exit_time'] = datetime.datetime.now().strftime('%H:%M')
                    r['pnl'] = str(round(entry - ltp, 2))
                    r['status'] = 'SL_HIT_ANTI_HUNT'
                elif ltp <= target:
                    r['exit'] = str(round(ltp, 2))
                    r['exit_time'] = datetime.datetime.now().strftime('%H:%M')
                    r['pnl'] = str(round(entry - ltp, 2))
                    r['status'] = 'TARGET_HIT'
        except Exception as e:
            print(f"Check error {r['symbol']} {e}")
            continue

# 2. Find new signals based on regime
for sym in SYMBOLS:
    try:
        # Avoid duplicate OPEN for same symbol
        clean = sym.replace(".NS", "")
        if any(x.get('symbol') == clean and x.get('status') == 'OPEN' for x in rows):
            continue
        
        sig, price, reason = get_signal(sym, regime)
        if sig and price > 0:
            if regime == "SIDEWAYS":
                sl_pct = SIDEWAYS_SL
                tgt_pct = SIDEWAYS_TARGET
            else:
                sl_pct = DISPLAY_SL_PCT
                tgt_pct = TARGET_PCT
            
            if sig == "BUY":
                sl = round(price * (1 - sl_pct/100), 2)
                tgt = round(price * (1 + tgt_pct/100), 2)
            else:
                sl = round(price * (1 + sl_pct/100), 2)
                tgt = round(price * (1 - tgt_pct/100), 2)
            
            rows.append({
                "symbol": clean,
                "side": sig,
                "regime": regime,
                "entry": str(round(price, 2)),
                "sl": str(sl),
                "sl_actual": str(round(sl * (1 - HIDDEN_BUFFER_PCT/100) if sig=="BUY" else sl * (1 + HIDDEN_BUFFER_PCT/100), 2)),
                "target": str(tgt),
                "entry_time": datetime.datetime.now().strftime('%H:%M'),
                "exit": "",
                "exit_time": "",
                "pnl": "",
                "status": "OPEN",
                "reason": f"{reason} | {regime_reason}"
            })
            print(f"NEW {sig} {clean} @ {price} | {reason}")
        time.sleep(0.2)  # Avoid yfinance rate limit
    except Exception as e:
        print(f"Signal error {sym} {e}")
        continue

# 3. AUTO SQUARE OFF AT 3:15 PM IST = 09:45 UTC
now_utc = datetime.datetime.utcnow()
is_sq_time = (now_utc.hour == 9 and now_utc.minute >= 45) or (now_utc.hour == 10 and now_utc.minute <= 10)
print(f"UTC Now {now_utc.hour}:{now_utc.minute} | SquareOff Time? {is_sq_time}")

if is_sq_time:
    for r in rows:
        if r.get('status') == 'OPEN':
            try:
                ltp = get_ltp_close(r['symbol'] + ".NS")
                if ltp is None:
                    ltp = float(r['entry'])
                entry = float(r['entry'])
                side = r.get('side', 'BUY')
                pnl = round(ltp - entry, 2) if side == 'BUY' else round(entry - ltp, 2)
                r['exit'] = str(round(ltp, 2))
                r['exit_time'] = "15:15"
                r['pnl'] = str(pnl)
                r['status'] = "SQUARED_OFF_3_15"
                print(f"SQ OFF {r['symbol']} @ {ltp}")
            except Exception as e:
                print(f"SQ error {e}")
                continue

# Save
fieldnames = ["symbol","side","regime","entry","sl","sl_actual","target","entry_time","exit","exit_time","pnl","status","reason"]
with open(REPORT_FILE, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

open_cnt = len([x for x in rows if x.get('status') == 'OPEN'])
closed_cnt = len([x for x in rows if x.get('status') != 'OPEN'])
print(f"=== V5 DONE | Regime {regime} | Open {open_cnt} | Closed {closed_cnt} | Total {len(rows)} | Saved {REPORT_FILE} ===")
