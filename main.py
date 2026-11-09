# VIKAS FNO V5 INTELLIGENT + SEPARATE TELEGRAM BOT - FULL 260 LINES - ZERO ERROR
import datetime
import csv
import os
import time
import requests
import pandas as pd
import yfinance as yf
import ta

# ================= CONFIG =================
REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)
TODAY = datetime.date.today().isoformat()
REPORT_FILE = f"{REPORT_DIR}/trades_FNO_{TODAY}.csv"

DISPLAY_SL_PCT = 1.0
HIDDEN_BUFFER_PCT = 0.4
TARGET_PCT = 1.5
SIDEWAYS_SL = 0.8
SIDEWAYS_TARGET = 1.2

SYMBOLS = [
    "ABB.NS","ABBOTINDIA.NS","ABCAPITAL.NS","ABFRL.NS","ACC.NS",
    "ADANIENT.NS","ADANIGREEN.NS","ADANIPORTS.NS","ADANIPOWER.NS","ALKEM.NS",
    "AMBUJACEM.NS","APOLLOHOSP.NS","APOLLOTYRE.NS","ASIANPAINT.NS","ASTRAL.NS",
    "ATGL.NS","AUROPHARMA.NS","DMART.NS","AXISBANK.NS","BAJAJ-AUTO.NS",
    "BAJFINANCE.NS","BAJAJFINSV.NS","BALKRISIND.NS","BANKBARODA.NS","BANKINDIA.NS",
    "BATAINDIA.NS","BEL.NS","BHARATFORG.NS","BHARTIARTL.NS","BHEL.NS",
    "BIOCON.NS","BOSCHLTD.NS","BPCL.NS","BRITANNIA.NS","BSE.NS",
    "BSOFT.NS","CAMS.NS","CANBK.NS","CDSL.NS","CESC.NS",
    "CGPOWER.NS","CHAMBLFERT.NS","CHOLAFIN.NS","CIPLA.NS","COALINDIA.NS",
    "COFORGE.NS","COLPAL.NS","CONCOR.NS","COROMANDEL.NS","CROMPTON.NS",
    "CUB.NS","CUMMINSIND.NS","DABUR.NS","DALBHARAT.NS","DEEPAKNTR.NS",
    "DELHIVERY.NS","DIVISLAB.NS","DIXON.NS","DLF.NS","DRREDDY.NS",
    "EICHERMOT.NS","ESCORTS.NS","EXIDEIND.NS","FEDERALBNK.NS","GAIL.NS",
    "GLENMARK.NS","GMRINFRA.NS","GNFC.NS","GODREJCP.NS","GODREJPROP.NS",
    "GRANULES.NS","GRASIM.NS","GUJGASLTD.NS","HAL.NS","HAVELLS.NS",
    "HCLTECH.NS","HDFCAMC.NS","HDFCBANK.NS","HDFCLIFE.NS","HEROMOTOCO.NS",
    "HINDALCO.NS","HINDCOPPER.NS","HINDPETRO.NS","HINDUNILVR.NS","ICICIBANK.NS",
    "ICICIGI.NS","ICICIPRULI.NS","IDEA.NS","IDFC.NS","IDFCFIRSTB.NS",
    "IEX.NS","IGL.NS","INDHOTEL.NS","INDIAMART.NS","INDIGO.NS",
    "INDUSINDBK.NS","INDUSTOWER.NS","INFY.NS","IOC.NS","IPCALAB.NS",
    "IRCTC.NS","IRFC.NS","ITC.NS","JINDALSTEL.NS","JKCEMENT.NS",
    "JSWENERGY.NS","JSWSTEEL.NS","JUBLFOOD.NS","KOTAKBANK.NS","KPITTECH.NS",
    "L&T.NS","LALPATHLAB.NS","LAURUSLABS.NS","LICHSGFIN.NS","LTIM.NS",
    "LTF.NS","LT.NS","LUPIN.NS","M&M.NS","M&MFIN.NS",
    "MANAPPURAM.NS","MARICO.NS","MARUTI.NS","MCX.NS","METROPOLIS.NS",
    "MFSL.NS","MGL.NS","MOTHERSON.NS","MPHASIS.NS","MRF.NS",
    "MUTHOOTFIN.NS","NATIONALUM.NS","NAUKRI.NS","NBCC.NS","NCC.NS",
    "NESTLEIND.NS","NHPC.NS","NMDC.NS","NTPC.NS","OBEROIRLTY.NS",
    "OFSS.NS","ONGC.NS","PAGEIND.NS","PATANJALI.NS","PEL.NS",
    "PERSISTENT.NS","PETRONET.NS","PFC.NS","PIDILITIND.NS","PIIND.NS",
    "PNB.NS","POLYCAB.NS","POWERGRID.NS","PRESTIGE.NS","PVRINOX.NS",
    "RAMCOCEM.NS","RBLBANK.NS","RECLTD.NS","RELIANCE.NS","SAIL.NS",
    "SBICARD.NS","SBILIFE.NS","SBIN.NS","SHREECEM.NS","SHRIRAMFIN.NS",
    "SIEMENS.NS","SJVN.NS","SONACOMS.NS","SRF.NS","SUNPHARMA.NS",
    "SUNTV.NS","SYNGENE.NS","TATACHEM.NS","TATACOMM.NS","TATACONSUM.NS",
    "TATAMOTORS.NS","TATAPOWER.NS","TATASTEEL.NS","TCS.NS","TECHM.NS",
    "TITAN.NS","TORNTPHARM.NS","TRENT.NS","TVSMOTOR.NS","ULTRACEMCO.NS",
    "UNIONBANK.NS","UPL.NS","VEDL.NS","VOLTAS.NS","WIPRO.NS",
    "ZOMATO.NS","ZYDUSLIFE.NS"
]

# Separate bot secrets - Different from Nifty Future Bot
BOT_TOKEN = os.getenv("TELEGRAM_FNO_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_FNO_CHAT_ID")

def send_tg(msg):
    """Send to separate FNO V5 bot"""
    if not BOT_TOKEN or not CHAT_ID:
        print("TG secrets missing - Skipping")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        resp = requests.post(url, json=payload, timeout=15)
        print(f"TG Sent: {resp.status_code}")
    except Exception as e:
        print(f"TG error: {e}")

def safe_columns(df):
    """Fix yfinance multiindex issue"""
    if df is None or df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def get_market_regime():
    """Detect NIFTY regime for intelligent trading"""
    try:
        print("Fetching NIFTY for regime...")
        nifty = yf.download("^NSEI", period="60d", interval="1d", progress=False, auto_adjust=True)
        if nifty.empty or len(nifty) < 35:
            print("Nifty data low")
            return "SIDEWAYS", "Nifty data insufficient - Default Sideways"
        nifty = safe_columns(nifty)
        nifty['ema20'] = ta.trend.ema_indicator(nifty['Close'], 20)
        nifty['ema50'] = ta.trend.ema_indicator(nifty['Close'], 50)
        nifty['rsi'] = ta.momentum.rsi(nifty['Close'], 14)
        last = nifty.iloc[-1]
        close = float(last['Close'])
        ema50 = float(last['ema50'])
        rsi = float(last['rsi'])
        ema20 = float(last['ema20'])
        print(f"NIFTY Close {close} EMA50 {ema50} RSI {rsi}")
        if close > ema50 and rsi > 55 and ema20 > ema50:
            return "BULL", f"NIFTY {close:.0f} > 50EMA + RSI {rsi:.0f} - BULL"
        elif close < ema50 and rsi < 45 and ema20 < ema50:
            return "BEAR", f"NIFTY {close:.0f} < 50EMA + RSI {rsi:.0f} - BEAR"
        else:
            return "SIDEWAYS", f"NIFTY {close:.0f} ~ EMA + RSI {rsi:.0f} - SIDEWAYS"
    except Exception as e:
        print(f"Regime error {e}")
        return "SIDEWAYS", f"Error {e} - Default Sideways"

def get_signal(symbol, regime):
    """Generate BUY/SELL per regime with volume breakout"""
    try:
        df = yf.download(symbol, period="60d", interval="1d", progress=False, auto_adjust=True, threads=False)
        if df.empty or len(df) < 35:
            return None, 0, ""
        df = safe_columns(df)
        # Indicators
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
        vol_avg = float(last['vol_avg']) if not pd.isna(last['vol_avg']) else vol
        rsi9 = float(last['rsi9'])
        rsi14 = float(last['rsi14'])
        ema8 = float(last['ema8'])
        ema20 = float(last['ema20'])
        high20 = float(df['20h'].iloc[-2]) if not pd.isna(df['20h'].iloc[-2]) else 0
        low20 = float(df['20l'].iloc[-2]) if not pd.isna(df['20l'].iloc[-2]) else 0
        curr_20l = float(df['20l'].iloc[-1]) if not pd.isna(df['20l'].iloc[-1]) else 0
        curr_20h = float(df['20h'].iloc[-1]) if not pd.isna(df['20h'].iloc[-1]) else 0
        turnover = close * vol
        # BULL
        if regime == "BULL":
            if close > high20 and rsi9 > 60 and ema8 > ema20 and vol > vol_avg * 1.3 and float(prev1['Volume']) < float(prev2['Volume']) and turnover > 300000000:
                return "BUY", close, "Bull Breakout Vol+"
        # BEAR
        elif regime == "BEAR":
            if close < low20 and rsi9 < 40 and ema8 < ema20 and vol > vol_avg * 1.3 and turnover > 300000000:
                return "SELL", close, "Bear Breakdown Vol+"
        # SIDEWAYS
        else:
            if close <= curr_20l * 1.02 and rsi14 < 38 and turnover > 200000000:
                return "BUY", close, "Sideways Oversold Bounce"
            if close >= curr_20h * 0.98 and rsi14 > 62 and turnover > 200000000:
                return "SELL", close, "Sideways Overbought Drop"
        return None, 0, ""
    except Exception as e:
        print(f"Signal error {symbol} {e}")
        return None, 0, ""

def get_ltp_close(symbol):
    """LTP on 5min close - Anti Hunt"""
    try:
        df = yf.download(symbol, period="1d", interval="5m", progress=False, auto_adjust=True, threads=False)
        if df.empty:
            return None
        df = safe_columns(df)
        return float(df['Close'].iloc[-1])
    except Exception as e:
        print(f"LTP error {symbol} {e}")
        return None

# ================= MAIN =================
print("=== VIKAS FNO V5 + SEPARATE TG BOT START ===")
regime, regime_reason = get_market_regime()
print(f"REGIME DETECTED: {regime} | {regime_reason}")

# Load existing
rows = []
if os.path.exists(REPORT_FILE):
    try:
        with open(REPORT_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        print(f"Loaded {len(rows)} existing rows")
    except Exception as e:
        print(f"Load error {e}")
        rows = []

# Check OPEN trades with Anti-Hunt Close based
for r in rows:
    if r.get('status') == 'OPEN':
        try:
            sym_full = r['symbol'] + ".NS"
            ltp = get_ltp_close(sym_full)
            if ltp is None:
                print(f"No LTP for {r['symbol']}")
                continue
            entry = float(r['entry'])
            disp_sl = float(r['sl'])
            target = float(r['target'])
            side = r.get('side', 'BUY')
            # Anti-Hunt actual levels
            if side == 'BUY':
                actual_sl = disp_sl * (1 - HIDDEN_BUFFER_PCT / 100.0)
                if ltp <= actual_sl:
                    r['exit'] = str(round(ltp, 2))
                    r['exit_time'] = datetime.datetime.now().strftime('%H:%M')
                    r['pnl'] = str(round(ltp - entry, 2))
                    r['status'] = 'SL_HIT_ANTI_HUNT'
                    send_tg(f"🔴 *SL HIT* {r['symbol']} {side} @ {ltp}\nEntry: {entry}\nLoss: {r['pnl']}\nRegime: {regime}\nAnti-Hunt 1.4% protected")
                    print(f"SL HIT {r['symbol']} {ltp}")
                elif ltp >= target:
                    r['exit'] = str(round(ltp, 2))
                    r['exit_time'] = datetime.datetime.now().strftime('%H:%M')
                    r['pnl'] = str(round(ltp - entry, 2))
                    r['status'] = 'TARGET_HIT'
                    send_tg(f"✅ *TARGET HIT* {r['symbol']} {side} @ {ltp}\nEntry: {entry}\nProfit: +{r['pnl']}\n1.5% Done")
                    print(f"TARGET {r['symbol']}")
            else:  # SELL
                actual_sl = disp_sl * (1 + HIDDEN_BUFFER_PCT / 100.0)
                if ltp >= actual_sl:
                    r['exit'] = str(round(ltp, 2))
                    r['exit_time'] = datetime.datetime.now().strftime('%H:%M')
                    r['pnl'] = str(round(entry - ltp, 2))
                    r['status'] = 'SL_HIT_ANTI_HUNT'
                    send_tg(f"🔴 *SL HIT* {r['symbol']} {side} @ {ltp}\nEntry: {entry}\nLoss: {r['pnl']}\nRegime: {regime}")
                elif ltp <= target:
                    r['exit'] = str(round(ltp, 2))
                    r['exit_time'] = datetime.datetime.now().strftime('%H:%M')
                    r['pnl'] = str(round(entry - ltp, 2))
                    r['status'] = 'TARGET_HIT'
                    send_tg(f"✅ *TARGET HIT* {r['symbol']} {side} @ {ltp}\nEntry: {entry}\nProfit: +{r['pnl']}")
        except Exception as e:
            print(f"Check OPEN error {e}")
            continue

# Generate new signals
new_trades = []
for sym in SYMBOLS:
    try:
        clean = sym.replace(".NS", "")
        # Skip if already open
        if any(x.get('symbol') == clean and x.get('status') == 'OPEN' for x in rows):
            continue
        sig, price, reason = get_signal(sym, regime)
        if sig and price > 0:
            sl_pct = SIDEWAYS_SL if regime == "SIDEWAYS" else DISPLAY_SL_PCT
            tgt_pct = SIDEWAYS_TARGET if regime == "SIDEWAYS" else TARGET_PCT
            if sig == "BUY":
                sl = round(price * (1 - sl_pct / 100), 2)
                tgt = round(price * (1 + tgt_pct / 100), 2)
                sl_actual = round(sl * (1 - HIDDEN_BUFFER_PCT / 100), 2)
            else:
                sl = round(price * (1 + sl_pct / 100), 2)
                tgt = round(price * (1 - tgt_pct / 100), 2)
                sl_actual = round(sl * (1 + HIDDEN_BUFFER_PCT / 100), 2)
            row = {
                "symbol": clean, "side": sig, "regime": regime,
                "entry": str(round(price, 2)), "sl": str(sl), "sl_actual": str(sl_actual),
                "target": str(tgt), "entry_time": datetime.datetime.now().strftime('%H:%M'),
                "exit": "", "exit_time": "", "pnl": "", "status": "OPEN",
                "reason": f"{reason} | {regime_reason}"
            }
            rows.append(row)
            new_trades.append(row)
            send_tg(f"🚀 *NEW TRADE* {clean} *{sig}* @ {price}\nRegime: {regime}\n{regime_reason}\nReason: {reason}\nSL: {sl} (Hidden {sl_actual} Anti-Hunt)\nTarget: {tgt} (1.5%)\nTime: {row['entry_time']}")
            print(f"NEW {clean} {sig} {price}")
        time.sleep(0.2)
    except Exception as e:
        print(f"Loop error {sym} {e}")
        continue

# Square off at 3:15 PM IST = 09:45 UTC
now_utc = datetime.datetime.utcnow()
is_sq_time = (now_utc.hour == 9 and now_utc.minute >= 45) or (now_utc.hour == 10 and now_utc.minute <= 10)
if is_sq_time:
    sq_count = 0
    for r in rows:
        if r.get('status') == 'OPEN':
            try:
                ltp = get_ltp_close(r['symbol'] + ".NS") or float(r['entry'])
                entry = float(r['entry'])
                side = r.get('side', 'BUY')
                pnl = round(ltp - entry, 2) if side == 'BUY' else round(entry - ltp, 2)
                r['exit'] = str(round(ltp, 2))
                r['exit_time'] = "15:15"
                r['pnl'] = str(pnl)
                r['status'] = "SQUARED_OFF_3_15"
                sq_count += 1
                send_tg(f"⏰ *SQ OFF 3:15* {r['symbol']} {side} @ {ltp}\nPnL: {pnl}")
            except:
                continue
    send_tg(f"📊 *EOD SUMMARY FNO V5 Separate Bot*\nRegime: {regime}\n{regime_reason}\nSquared: {sq_count}\nDate: {TODAY}")

if new_trades and not is_sq_time:
    send_tg(f"📈 *Market Regime Today: {regime}* - {regime_reason}\nNew Signals: {len(new_trades)}")

# Save
fieldnames = ["symbol","side","regime","entry","sl","sl_actual","target","entry_time","exit","exit_time","pnl","status","reason"]
with open(REPORT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"=== DONE | Regime {regime} | New {len(new_trades)} | Total {len(rows)} | TG Separate Bot ===")
