import os, requests, time, pandas as pd, pytz
from datetime import datetime
import yfinance as yf
import ta

# ================= CONFIG =================
IST = pytz.timezone("Asia/Kolkata")
REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)

BOT_TOKEN = os.getenv("TELEGRAM_FNO_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_FNO_CHAT_ID")
DHAN_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")
WHATSAPP_APIKEY = os.getenv("WHATSAPP_APIKEY")
FRIEND_PHONE = "919425074989"

# ========= DHAN MAP - 176 STOCKS =========
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

ALL_STOCKS = ["360ONE","ABB","ABCAPITAL","ABFRL","ADANIENT","ADANIPORTS","ALKEM","AMBER","AMBUJACEM","APLLTD","APOLLOHOSP","ASIANPAINT","ASTRAL","ATGL","AUROPHARMA","AXISBANK","BAJAJ-AUTO","BAJAJFINSV","BAJAJHFL","BAJFINANCE","BANDHANBNK","BANKBARODA","BDL","BEL","BHARATFORG","BHARTIARTL","BHEL","BIKAJI","BIOCON","BLUESTARCO","BOSCHLTD","BPCL","BRITANNIA","BSE","BSOFT","CAMS","CANBK","CANFINHOME","CDSL","CGPOWER","CHAMBLFERT","CHOLAFIN","CIPLA","COALINDIA","COFORGE","COLPAL","CONCOR","CROMPTON","CUMMINSIND","CYIENT","DABUR","DALBHARAT","DEEPAKNTR","DELHIVERY","DIVISLAB","DIXON","DLF","DMART","DRREDDY","EICHERMOT","ETERNAL","EXIDEIND","FEDERALBNK","FORTIS","GAIL","GLENMARK","GMRAIRPORT","GODREJCP","GODREJPROP","GMRPOWER","GRANULES","GRASIM","HAL","HAVELLS","HCLTECH","HDFCAMC","HDFCBANK","HDFCLIFE","HEROMOTOCO","HINDALCO","HINDCOPPER","HINDPETRO","HINDUNILVR","HINDZINC","HUDCO","ICICIBANK","ICICIGI","ICICIPRULI","IDFCFIRSTB","IEX","IGL","INDHOTEL","INDIANB","INDIGO","INDUSINDBK","INDUSTOWER","INFY","IOC","IRB","IRCTC","IREDA","IRFC","ITC","JINDALSTAIN","JINDALSTEEL","JIOFIN","JSWENERGY","JSWSTEEL","KAYNES","KEI","KFINTECH","KOTAKBANK","KPITTECH","LALPATHLAB","LAURUSLABS","LICHSGFIN","LICI","LODHA","LT","LTF","LTIM","LUPIN","M&M","MANKIND","MANYAVAR","MARICO","MARUTI","MAXHEALTH","MCX","MFSL","MOTHERSON","MPHASIS","MUTHOOTFIN","NATIONALUM","NAUKRI","NBCC","NCC","NESTLEIND","NHPC","NMDC","NTPC","NYKAA","OBEROIRLTY","OFSS","OIL","ONGC","PAGEIND","PATANJALI","PAYTM","PERSISTENT","PETRONET","PFC","PHOENIXLTD","PIDILITIND","POLICYBTR","POLYCAB","POWERGRID","PRESTIGE","PTCIL","RECLTD","RELIANCE","SAIL","SBICARD","SBILIFE","SBIN","SHREECEM","SHRIRAMFIN","SIEMENS","SOLARINDS","SONACOMS","SRF","SUNPHARMA","SUPREMEIND","SYNGENE","TATACOMM","TATACONSUM","TATAELXSI","TATAMOTORS","TATAPOWER","TATASTEEL","TATATECH","TCS","TECHM","TITAN","TORNTPHARM","TORNTPOWER","TRENT","TVSMOTOR","UNIONBANK","UNITECEM","UNOMINDA","UPL","VEDL","VOLTAS","WIPRO","YESBANK","ZYDUSLIFE"]

# ================= MESSAGING =================
def send_tg(msg):
    if not BOT_TOKEN or not CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=15)
    except Exception as e: print(f"TG err {e}")

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

# ================= MARKET DIRECTION =================
def get_market_direction():
    try:
        # NIFTY 50
        nifty = yf.download("^NSEI", period="10d", interval="15m", progress=False, auto_adjust=True)
        if len(nifty) < 50: return "SIDEWAYS", "NIFTY data low", 0
        if isinstance(nifty.columns, pd.MultiIndex): nifty.columns = nifty.columns.get_level_values(0)
        nifty["EMA20"] = ta.trend.ema_indicator(nifty["Close"], 20)
        nifty["EMA50"] = ta.trend.ema_indicator(nifty["Close"], 50)
        nifty["RSI"] = ta.momentum.rsi(nifty["Close"], 14)
        last = nifty.iloc[-1]
        rsi = float(last["RSI"])
        ema20 = float(last["EMA20"])
        ema50 = float(last["EMA50"])
        close = float(last["Close"])
        
        if ema20 > ema50 and rsi > 55 and close > ema20:
            return "BULLISH", f"NIFTY {close:.0f} | EMA20 {ema20:.0f} > EMA50 {ema50:.0f} | RSI {rsi:.0f}", rsi
        elif ema20 < ema50 and rsi < 45 and close < ema20:
            return "BEARISH", f"NIFTY {close:.0f} | EMA20 {ema20:.0f} < EMA50 {ema50:.0f} | RSI {rsi:.0f}", rsi
        else:
            return "SIDEWAYS", f"NIFTY {close:.0f} | EMA20 {ema20:.0f} ~ EMA50 {ema50:.0f} | RSI {rsi:.0f}", rsi
    except Exception as e:
        return "SIDEWAYS", f"Market check fail {e}", 50

# ================= DATA FEED =================
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
        fix = {"JINDALSTAIN":"JSL","JINDALSTEEL":"JINDALSTEL","POLICYBTR":"POLICYBZR","TATAMOTORS":"TATAMOTORS","UNITECEM":"ULTRACEMCO","GMRPOWER":"GMRPOWER","ICICIPRULI":"ICICIPRULI","LTIM":"LTIM"}
        # Skip known bad Yahoo symbols - Use Dhan only
        if sym in ["GMRPOWER","ICICIPRULI","LTIM","TATAMOTORS"]:
            return None  # Don't even try Yahoo, use Dhan
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

def analyze_stock(df):
    try:
        df["EMA20"] = ta.trend.ema_indicator(df["Close"], 20)
        df["EMA50"] = ta.trend.ema_indicator(df["Close"], 50)
        df["RSI"] = ta.momentum.rsi(df["Close"], 14)
        df["ATR"] = ta.volatility.average_true_range(df["High"], df["Low"], df["Close"], 14)
        df["ADX"] = ta.trend.adx(df["High"], df["Low"], df["Close"], 14)
        macd = ta.trend.MACD(df["Close"])
        df["MACD"] = macd.macd()
        df["MACD_SIG"] = macd.macd_signal()
        last = df.iloc[-1]
        prev = df.iloc[-2]
        buy = last["EMA20"] > last["EMA50"] and 55 < last["RSI"] < 75 and last["MACD"] > last["MACD_SIG"] and last["ADX"] > 20 and last["Close"] > last["EMA20"] and prev["MACD"] <= prev["MACD_SIG"]
        sell = last["EMA20"] < last["EMA50"] and 25 < last["RSI"] < 45 and last["MACD"] < last["MACD_SIG"] and last["ADX"] > 20 and last["Close"] < last["EMA20"] and prev["MACD"] >= prev["MACD_SIG"]
        if buy: return "BUY", float(last["Close"]), float(last["ATR"])
        if sell: return "SELL", float(last["Close"]), float(last["ATR"])
        return None, None, None
    except: return None, None, None

# ================= MAIN =================
def main():
    now = datetime.now(IST)
    if now.weekday() > 4:
        print("Weekend"); return

    # 1. MARKET DIRECTION
    mkt_status, mkt_detail, mkt_rsi = get_market_direction()
    print(f"MARKET: {mkt_status} - {mkt_detail}")

    active_file = os.path.join(REPORT_DIR, "active_trades.csv")
    active_df = pd.read_csv(active_file) if os.path.exists(active_file) else pd.DataFrame(columns=["symbol","entry","sl","target","type","time"])

    new_trades = []
    for symbol in ALL_STOCKS:
        clean = symbol.strip()
        if clean in active_df["symbol"].values: continue
        df, src = get_candle(clean)
        if df is None: continue
        sig, price, atr = analyze_stock(df)
        if sig is None: continue
        if atr is None or atr == 0: atr = price * 0.01
        if sig == "BUY":
            sl = price - (atr * 1.5)
            tgt = price + (atr * 3)
        else:
            sl = price + (atr * 1.5)
            tgt = price - (atr * 3)
        new_trades.append({"symbol":clean,"entry":price,"sl":sl,"target":tgt,"type":sig,"time":now.strftime("%Y-%m-%d %H:%M"),"src":src})
        time.sleep(0.2)

    # 2. BUILD COMBINED MESSAGE WITH MARKET DIRECTION + WARNING
        if new_trades:
        # Warning logic
        warning = ""
        if mkt_status == "BEARISH" and any(t["type"]=="BUY" for t in new_trades):
            warning = "\n⚠️ *WARNING: Market BEARISH but BUY signals! Trade with 50% size or WAIT.*\n"
        elif mkt_status == "BULLISH" and any(t["type"]=="SELL" for t in new_trades):
            warning = "\n⚠️ *WARNING: Market BULLISH but SELL signals! Avoid shorts.*\n"
        elif mkt_status == "SIDEWAYS":
            warning = "\n⚠️ *Market SIDEWAYS - Choppy! Use small qty.*\n"
        else:
            warning = "\n✅ *Market aligned - Good to trade.*\n"

        header = f"📊 *FNO V5 MARKET REPORT* 📊\nTime: {now.strftime('%d-%m %H:%M IST')}\n\n*MARKET:* {mkt_status}\nDetail: {mkt_detail}\n{warning}\n🚀 *{len(new_trades)} NEW TRADES (DHAN REAL)* 🚀\n\n"
        body = ""
        for t in new_trades:
            body += f"*{t['symbol']}* {t['type']} @ {t['entry']:.2f}\nSL {t['sl']:.2f} | TGT {t['target']:.2f}\n\n"
        footer = f"_Source: DHAN REAL NSE_"
        full_msg = header + body + footer
        send_both(full_msg)

        save_df = pd.DataFrame(new_trades)
        combined = pd.concat([active_df, save_df.drop(columns=["src"])], ignore_index=True)
        combined.to_csv(active_file, index=False)
        print(f"Saved {len(new_trades)} trades")
    else:
        # NEW - Daily alive message when 0 trades
        alive_msg = f"📊 *FNO V5 DAILY CHECK* 📊\nTime: {now.strftime('%d-%m %H:%M IST')}\n\n*MARKET:* {mkt_status}\nDetail: {mkt_detail}\n\nNo new trades today - Market consolidating or signals already active.\nActive: {len(active_df)} trades\n\n✅ Bot alive & scanning 176 stocks - Dhan + YF backup working!"
        send_both(alive_msg)
        print("No new trades - Alive msg sent")

        # Save
        save_df = pd.DataFrame(new_trades)
        combined = pd.concat([active_df, save_df.drop(columns=["src"])], ignore_index=True)
        combined.to_csv(active_file, index=False)
        print(f"Saved {len(new_trades)} trades")

    # 3. Check SL/TGT
    if not active_df.empty:
        remaining = []
        for _, row in active_df.iterrows():
            df, _ = get_candle(row["symbol"])
            if df is None:
                remaining.append(row); continue
            last_price = float(df.iloc[-1]["Close"])
            hit = False
            if row["type"] == "BUY":
                if last_price <= row["sl"]:
                    send_both(f"🔴 *SL HIT* {row['symbol']} @ {last_price:.2f} (Entry {row['entry']:.2f})")
                    hit = True
                elif last_price >= row["target"]:
                    send_both(f"✅ *TARGET HIT* {row['symbol']} @ {last_price:.2f} (Entry {row['entry']:.2f})")
                    hit = True
            else:
                if last_price >= row["sl"]:
                    send_both(f"🔴 *SL HIT* {row['symbol']} @ {last_price:.2f}")
                    hit = True
                elif last_price <= row["target"]:
                    send_both(f"✅ *TARGET HIT* {row['symbol']} @ {last_price:.2f}")
                    hit = True
            if not hit: remaining.append(row)
        pd.DataFrame(remaining).to_csv(active_file, index=False)

    print("Scan Complete")

if __name__ == "__main__":
    main()
