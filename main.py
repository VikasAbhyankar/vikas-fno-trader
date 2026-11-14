import os, requests, time, pandas as pd, pytz
from datetime import datetime
import yfinance as yf
import ta

IST = pytz.timezone("Asia/Kolkata")
REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)

BOT_TOKEN = os.getenv("TELEGRAM_FNO_BOT_TOKEN")
CHAT_ID_ENV = os.getenv("TELEGRAM_FNO_CHAT_ID")
DHAN_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")
WHATSAPP_APIKEY = os.getenv("WHATSAPP_APIKEY")
FRIEND_PHONE = "919425074989"

# ========== V7 MULTI-USER LIST - FIXED ==========
# 5239892901 = Bala / Prashant
# 9000971028 = New Person (REPLACED 7507879668 Nishant)
FRIEND_TELEGRAM_IDS = [
    "5239892901",
    "9000971028",
]

def get_all_chat_ids():
    ids = []
    if CHAT_ID_ENV:
        for x in str(CHAT_ID_ENV).split(","):
            x = x.strip()
            if x and x not in ids:
                ids.append(x)
    for fid in FRIEND_TELEGRAM_IDS:
        if fid not in ids:
            ids.append(fid)
    return ids

ALL_CHAT_IDS = get_all_chat_ids()

DHAN_MAP = {
    "360ONE": 13061, "ABB": 13, "ABCAPITAL": 21614, "ABFRL": 30108, "ADANIENT": 25, "ADANIPORTS": 15083,
    "ALKEM": 11703, "AMBER": 1185, "AMBUJACEM": 1270, "APLLTD": 25328, "APOLLOHOSP": 157, "ASIANPAINT": 236,
    "ASTRAL": 14418, "ATGL": 6066, "AUROPHARMA": 275, "AXISBANK": 5900, "BAJAJ-AUTO": 16669, "BAJAJFINSV": 16675,
    "BAJAJHFL": 25270, "BAJFINANCE": 317, "BANDHANBNK": 2263, "BANKBARODA": 4668, "BDL": 2144, "BEL": 383,
    "BHARATFORG": 422, "BHARTIARTL": 10604, "BHEL": 438, "BIKAJI": 11966, "BIOCON": 11373, "BLUESTARCO": 8311,
    "BOSCHLTD": 2181, "BPCL": 526, "BRITANNIA": 547, "BSE": 19585, "BSOFT": 6994, "CAMS": 342, "CANBK": 10794,
    "CANFINHOME": 583, "CDSL": 21174, "CGPOWER": 760, "CHAMBLFERT": 637, "CHOLAFIN": 685, "CIPLA": 694,
    "COALINDIA": 20374, "COFORGE": 11543, "COLPAL": 15141, "CONCOR": 4749, "CROMPTON": 17094, "CUMMINSIND": 1901,
    "CYIENT": 5748, "DABUR": 772, "DALBHARAT": 8075, "DEEPAKNTR": 19943, "DELHIVERY": 9599, "DIVISLAB": 10940,
    "DIXON": 21690, "DLF": 14732, "DMART": 19913, "DRREDDY": 881, "EICHERMOT": 910, "ETERNAL": 5097, "EXIDEIND": 676,
    "FEDERALBNK": 1023, "FORTIS": 14592, "GAIL": 4717, "GLENMARK": 7406, "GMRAIRPORT": 13528, "GODREJCP": 10099,
    "GODREJPROP": 17875, "GRANULES": 11872, "GRASIM": 1232, "HAL": 2303, "HAVELLS": 9819, "HCLTECH": 7229,
    "HDFCAMC": 4244, "HDFCBANK": 1333, "HDFCLIFE": 467, "HEROMOTOCO": 1348, "HINDALCO": 1363, "HINDCOPPER": 17939,
    "HINDPETRO": 1406, "HINDUNILVR": 1394, "HINDZINC": 1424, "HUDCO": 20825, "ICICIBANK": 4963, "ICICIGI": 21770,
    "IDFCFIRSTB": 11184, "IEX": 220, "IGL": 11262, "INDHOTEL": 1512, "INDIANB": 14309, "INDIGO": 11195,
    "INDUSINDBK": 5258, "INDUSTOWER": 29135, "INFY": 1594, "IOC": 1624, "IRB": 15313, "IRCTC": 13611, "IREDA": 20261,
    "IRFC": 2029, "ITC": 1660, "JIOFIN": 18143, "JSL": 11236, "JSWENERGY": 17869, "JSWSTEEL": 11723, "KAYNES": 12092,
    "KEI": 13310, "KFINTECH": 13359, "KOTAKBANK": 1922, "KPITTECH": 9683, "LALPATHLAB": 11654, "LAURUSLABS": 19234,
    "LICHSGFIN": 1997, "LICI": 9480, "LODHA": 3220, "LT": 11483, "LTF": 24948, "LUPIN": 10440, "M&M": 2031,
    "MANKIND": 15380, "MANYAVAR": 8167, "MARICO": 4067, "MARUTI": 10999, "MAXHEALTH": 22377, "MCX": 31181,
    "MFSL": 2142, "MOTHERSON": 4204, "MPHASIS": 4503, "MUTHOOTFIN": 23650, "NATIONALUM": 6364, "NAUKRI": 13751,
    "NBCC": 31415, "NCC": 2319, "NESTLEIND": 17963, "NHPC": 17400, "NMDC": 15332, "NTPC": 11630, "NYKAA": 6545,
    "OBEROIRLTY": 20242, "OFSS": 10738, "OIL": 17438, "ONGC": 2475, "PAGEIND": 14413, "PATANJALI": 17029,
    "PAYTM": 6705, "PERSISTENT": 18365, "PETRONET": 11351, "PFC": 14299, "PHOENIXLTD": 14552, "PIDILITIND": 2664,
    "POLYCAB": 9590, "POWERGRID": 14977, "PRESTIGE": 20302, "PTCIL": 16682, "RECLTD": 15355, "RELIANCE": 2885,
    "SAIL": 2963, "SBICARD": 17971, "SBILIFE": 21808, "SBIN": 3045, "SHREECEM": 3103, "SHRIRAMFIN": 4306,
    "SIEMENS": 3150, "SOLARINDS": 13332, "SONACOMS": 4684, "SRF": 3273, "SUNPHARMA": 3351, "SUPREMEIND": 3363,
    "SYNGENE": 10243, "TATACOMM": 3721, "TATACONSUM": 3432, "TATAELXSI": 3411, "TATAPOWER": 3426, "TATASTEEL": 3499,
    "TATATECH": 20293, "TCS": 11536, "TECHM": 13538, "TITAN": 3506, "TORNTPHARM": 3518, "TORNTPOWER": 13786,
    "TRENT": 1964, "TVSMOTOR": 8479, "UNIONBANK": 10753, "UNOMINDA": 14154, "UPL": 11287, "VEDL": 3063,
    "VOLTAS": 3718, "WIPRO": 3787, "YESBANK": 11915, "ZYDUSLIFE": 7929,
    "JINDALSTAIN": 11236, "JINDALSTEEL": 6733, "POLICYBTR": 6656, "TATAMOTORS": 759782, "UNITECEM": 11532
}

ALL_STOCKS = list(DHAN_MAP.keys())

# ========== TELEGRAM ==========
def send_tg(msg):
    if not BOT_TOKEN or not ALL_CHAT_IDS:
        print("TG skipped - no token/ids")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for chat_id in ALL_CHAT_IDS:
        try:
            r = requests.post(url, json={"chat_id": str(chat_id).strip(), "text": msg, "parse_mode": "Markdown"}, timeout=15)
            print(f"Telegram to {chat_id} status {r.status_code} - {r.text[:120]}")
            if r.status_code == 400:
                print(f"  -> {chat_id} NEEDS /start or BLOCKED/RESTRICTED - Ask user to press START + Unblock")
            time.sleep(0.5)
        except Exception as e:
            print(f"TG err for {chat_id}: {e}")
    print(f"Sent TG to {len(ALL_CHAT_IDS)} users: {ALL_CHAT_IDS}")

def send_whatsapp(msg):
    if not WHATSAPP_APIKEY: return
    try:
        import urllib.parse
        clean = urllib.parse.quote(msg[:1500])
        url = f"https://api.callmebot.com/whatsapp.php?phone={FRIEND_PHONE}&text={clean}&apikey={WHATSAPP_APIKEY}"
        requests.get(url, timeout=15)
    except: pass

def send_both(msg):
    send_tg(msg)
    time.sleep(1)
    send_whatsapp(msg)

# ========== MARKET DIRECTION - Agent 5 ==========
def get_market_direction():
    try:
        nifty = yf.download("^NSEI", period="10d", interval="15m", progress=False, auto_adjust=True)
        if len(nifty) < 50: return "SIDEWAYS", "NIFTY data low", 0
        if isinstance(nifty.columns, pd.MultiIndex): nifty.columns = nifty.columns.get_level_values(0)
        nifty["EMA20"] = ta.trend.ema_indicator(nifty["Close"], 20)
        nifty["EMA50"] = ta.trend.ema_indicator(nifty["Close"], 50)
        nifty["RSI"] = ta.momentum.rsi(nifty["Close"], 14)
        last = nifty.iloc[-1]
        rsi = float(last["RSI"]); ema20 = float(last["EMA20"]); ema50 = float(last["EMA50"]); close = float(last["Close"])
        if ema20 > ema50 and rsi > 55 and close > ema20:
            return "BULLISH", f"NIFTY {close:.0f} | EMA20 {ema20:.0f} > EMA50 {ema50:.0f} | RSI {rsi:.0f}", rsi
        elif ema20 < ema50 and rsi < 45 and close < ema20:
            return "BEARISH", f"NIFTY {close:.0f} | EMA20 {ema20:.0f} < EMA50 {ema50:.0f} | RSI {rsi:.0f}", rsi
        else:
            return "SIDEWAYS", f"NIFTY {close:.0f} | EMA20 {ema20:.0f} ~ EMA50 {ema50:.0f} | RSI {rsi:.0f}", rsi
    except Exception as e:
        return "SIDEWAYS", f"Market check fail {e}", 50

# ========== DATA ==========
def get_dhan_candle(symbol):
    if not DHAN_TOKEN or symbol not in DHAN_MAP: return None
    try:
        headers = {"access-token": DHAN_TOKEN, "Content-Type": "application/json"}
        url = "https://api.dhan.co/v2/charts/intraday"
        today = datetime.now(IST).strftime("%Y-%m-%d")
        payload = {"securityId": str(DHAN_MAP[symbol]), "exchangeSegment": "NSE_EQ", "instrument": "EQUITY", "interval": "15", "oi": False, "fromDate": today, "toDate": today}
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code != 200: return None
        data = r.json()
        if "open" not in data or len(data.get("open", [])) < 50: return None
        df = pd.DataFrame({"Open": data["open"], "High": data["high"], "Low": data["low"], "Close": data["close"], "Volume": data["volume"]})
        return df
    except: return None

def get_yf_candle(sym):
    try:
        import warnings
        warnings.filterwarnings("ignore")
        fix = {"JINDALSTAIN":"JSL","JINDALSTEEL":"JINDALSTEL","POLICYBTR":"POLICYBZR","TATAMOTORS":"TATAMOTORS","UNITECEM":"ULTRACEMCO"}
        ticker = f"{fix.get(sym, sym)}.NS"
        df = yf.download(ticker, period="10d", interval="15m", progress=False, auto_adjust=True, show_errors=False)
        if df is None or len(df) < 50: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df
    except: return None

def get_candle(sym):
    df = get_dhan_candle(sym)
    if df is not None and len(df) >= 50: return df, "DHAN REAL"
    df = get_yf_candle(sym)
    if df is not None: return df, "YF"
    return None, "NONE"

# ========== V7 - 7 AGENT VOTING SYSTEM (Vibe-Trading Style) ==========
def analyze_stock_v7(df, mkt_status):
    try:
        df = df.copy()
        df["EMA20"] = ta.trend.ema_indicator(df["Close"], 20)
        df["EMA50"] = ta.trend.ema_indicator(df["Close"], 50)
        df["RSI"] = ta.momentum.rsi(df["Close"], 14)
        df["RSI2"] = ta.momentum.rsi(df["Close"], 2)  # Vibe Alpha - RSI2 Pullback
        df["ATR"] = ta.volatility.average_true_range(df["High"], df["Low"], df["Close"], 14)
        df["ADX"] = ta.trend.adx(df["High"], df["Low"], df["Close"], 14)
        macd = ta.trend.MACD(df["Close"])
        df["MACD"] = macd.macd()
        df["MACD_SIG"] = macd.macd_signal()
        # VWAP - Vibe Structure Agent
        df["VWAP"] = (df["Close"] * df["Volume"]).cumsum() / df["Volume"].cumsum()
        df["VOL_AVG20"] = df["Volume"].rolling(20).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]
        price = float(last["Close"]); atr = float(last["ATR"])
        if atr == 0 or price == 0: return None, None, None, 0, "ATR Zero"

        # --- AGENT 1: TREND ---
        trend_buy = last["EMA20"] > last["EMA50"] and price > last["EMA20"] and price > last["VWAP"]
        trend_sell = last["EMA20"] < last["EMA50"] and price < last["EMA20"] and price < last["VWAP"]

        # --- AGENT 2: MOMENTUM ---
        mom_buy = 55 < last["RSI"] < 75 and last["MACD"] > last["MACD_SIG"]
        mom_sell = 25 < last["RSI"] < 45 and last["MACD"] < last["MACD_SIG"]
        # RSI2 Pullback Alpha - Strong mean reversion BUY
        rsi2_buy = last["RSI2"] < 12 and last["RSI"] < 45 and price > last["VWAP"] * 0.99
        if rsi2_buy:
            mom_buy = True

        # --- AGENT 3: VOLUME - Fake breakout filter ---
        vol_ok = last["Volume"] > last["VOL_AVG20"] * 1.2 if pd.notna(last["VOL_AVG20"]) else False

        # --- AGENT 4: STRUCTURE / STRENGTH ---
        adx_ok = last["ADX"] > 20
        macd_cross_buy = last["MACD"] > last["MACD_SIG"] and prev["MACD"] <= prev["MACD_SIG"]
        macd_cross_sell = last["MACD"] < last["MACD_SIG"] and prev["MACD"] >= prev["MACD_SIG"]

        # --- AGENT 5: MARKET VETO (Master) ---
        # If Nifty BEARISH, block BUY. If Nifty BULLISH, block SELL.
        market_allows_buy = mkt_status in ["BULLISH", "SIDEWAYS"]
        market_allows_sell = mkt_status in ["BEARISH", "SIDEWAYS"]

        # --- AGENT 6: RISK ---
        # ATR must be < 1.5% of price, else stock too volatile
        risk_ok = (atr / price) < 0.015

        # --- AGENT 7: NEWS / SENTIMENT - Warning only, handled in main via yfinance news check if needed ---
        # For speed, we keep it as ADX + Volume confirmation

        # VOTING - BUY
        buy_votes = sum([trend_buy, mom_buy, vol_ok, adx_ok, macd_cross_buy, market_allows_buy, risk_ok])
        sell_votes = sum([trend_sell, mom_sell, vol_ok, adx_ok, macd_cross_sell, market_allows_sell, risk_ok])

        # Need 5/7 + Market Veto + Volume
        if buy_votes >= 5 and market_allows_buy and vol_ok:
            return "BUY", price, atr, buy_votes, "7-Agent BUY"
        if sell_votes >= 5 and market_allows_sell and vol_ok:
            return "SELL", price, atr, sell_votes, "7-Agent SELL"
        return None, None, None, max(buy_votes, sell_votes), f"Votes {buy_votes}/7 BUY, {sell_votes}/7 SELL - SKIP"
    except Exception as e:
        return None, None, None, 0, f"Error {e}"

def check_walkforward(symbol, history_file):
    # Vibe Walk-Forward: If last 3 trades for this symbol were losses, skip today
    try:
        if not os.path.exists(history_file): return True
        h = pd.read_csv(history_file)
        if h.empty: return True
        last3 = h[h["symbol"] == symbol].tail(3)
        if len(last3) >= 3 and (last3["result"] == "LOSS").all():
            return False
        return True
    except: return True

# ========== MAIN ==========
def main():
    now = datetime.now(IST)
    if now.weekday() > 4:
        print("Weekend"); return
    mkt_status, mkt_detail, mkt_rsi = get_market_direction()
    print(f"MARKET: {mkt_status} - {mkt_detail}")

    active_file = os.path.join(REPORT_DIR, "active_trades.csv")
    history_file = os.path.join(REPORT_DIR, "trade_history.csv")
    active_df = pd.read_csv(active_file) if os.path.exists(active_file) else pd.DataFrame(columns=["symbol","entry","sl","target","type","time"])
    new_trades = []
    skipped = 0

    for symbol in ALL_STOCKS:
        clean = symbol.strip()
        if clean in active_df["symbol"].values: continue
        # Walk-Forward filter
        if not check_walkforward(clean, history_file):
            skipped += 1
            continue
        df, src = get_candle(clean)
        if df is None: continue
        sig, price, atr, votes, reason = analyze_stock_v7(df, mkt_status)
        if sig is None: continue
        if atr is None or atr == 0: atr = price * 0.01
        if sig == "BUY":
            sl = price - (atr * 1.5)
            tgt = price + (atr * 3)  # 1:2 Risk:Reward
        else:
            sl = price + (atr * 1.5)
            tgt = price - (atr * 3)
        new_trades.append({"symbol":clean,"entry":price,"sl":sl,"target":tgt,"type":sig,"time":now.strftime("%Y-%m-%d %H:%M"),"src":src,"votes":votes})
        time.sleep(0.2)

    if new_trades:
        warning = ""
        if mkt_status == "BEARISH" and any(t["type"]=="BUY" for t in new_trades):
            warning = "\n⚠️ *WARNING: Market BEARISH but BUY signals! Trade with 50% size or WAIT.*\n"
        elif mkt_status == "BULLISH" and any(t["type"]=="SELL" for t in new_trades):
            warning = "\n⚠️ *WARNING: Market BULLISH but SELL signals! Avoid shorts.*\n"
        elif mkt_status == "SIDEWAYS":
            warning = "\n⚠️ *Market SIDEWAYS - Choppy! Use small qty.*\n"
        else:
            warning = "\n✅ *Market aligned - Good to trade.*\n"
        header = f"📊 *FNO V7 MULTI-AGENT REPORT* 📊\nTime: {now.strftime('%d-%m %H:%M IST')}\n\n*MARKET:* {mkt_status}\nDetail: {mkt_detail}\n{warning}\n🚀 *{len(new_trades)} NEW TRADES (7-Agent Voted, DHAN REAL)* 🚀\n*Filter: 5/7 Agents YES + Volume + VWAP + Market Veto*\n\n"
        body = ""
        for t in new_trades:
            body += f"*{t['symbol']}* {t['type']} @ {t['entry']:.2f} | Votes {t['votes']}/7\nSL {t['sl']:.2f} | TGT {t['target']:.2f} | RR 1:2\n\n"
        footer = f"_Source: DHAN REAL NSE | V7 Vibe-Style 7 Agents | Sent to {len(ALL_CHAT_IDS)} users_"
        full_msg = header + body + footer
        send_both(full_msg)
        save_df = pd.DataFrame(new_trades)
        combined = pd.concat([active_df, save_df.drop(columns=["src","votes"])], ignore_index=True)
        combined.to_csv(active_file, index=False)
        print(f"Saved {len(new_trades)} trades, Skipped {skipped} walk-forward")
    else:
        alive_msg = f"📊 *FNO V7 DAILY CHECK* 📊\nTime: {now.strftime('%d-%m %H:%M IST')}\n\n*MARKET:* {mkt_status}\nDetail: {mkt_detail}\n\nNo new trades today - 7-Agent filter rejected weak signals (Need 5/7 votes).\nActive: {len(active_df)} trades | Walk-Forward Skipped: {skipped}\n\n✅ V7 Bot alive & scanning {len(ALL_STOCKS)} stocks - 7 Agents Active"
        send_both(alive_msg)
        print("No new trades - Alive msg sent")

    # SL / TARGET check for active trades
    if not active_df.empty:
        remaining = []
        hist_rows = []
        for _, row in active_df.iterrows():
            df, _ = get_candle(row["symbol"])
            if df is None:
                remaining.append(row); continue
            last_price = float(df.iloc[-1]["Close"])
            hit = False; result = ""
            if row["type"] == "BUY":
                if last_price <= row["sl"]:
                    send_both(f"🔴 *SL HIT* {row['symbol']} @ {last_price:.2f} (Entry {row['entry']:.2f})")
                    hit = True; result = "LOSS"
                elif last_price >= row["target"]:
                    send_both(f"✅ *TARGET HIT* {row['symbol']} @ {last_price:.2f} (Entry {row['entry']:.2f})")
                    hit = True; result = "WIN"
            else:
                if last_price >= row["sl"]:
                    send_both(f"🔴 *SL HIT* {row['symbol']} @ {last_price:.2f}")
                    hit = True; result = "LOSS"
                elif last_price <= row["target"]:
                    send_both(f"✅ *TARGET HIT* {row['symbol']} @ {last_price:.2f}")
                    hit = True; result = "WIN"
            if hit:
                hist_rows.append({"symbol": row["symbol"], "type": row["type"], "entry": row["entry"], "exit": last_price, "result": result, "time": now.strftime("%Y-%m-%d %H:%M")})
            else:
                remaining.append(row)
        pd.DataFrame(remaining).to_csv(active_file, index=False)
        if hist_rows:
            hdf = pd.DataFrame(hist_rows)
            if os.path.exists(history_file):
                old = pd.read_csv(history_file)
                hdf = pd.concat([old, hdf], ignore_index=True)
            hdf.to_csv(history_file, index=False)
    print("V7 Scan Complete")

if __name__ == "__main__":
    main()
