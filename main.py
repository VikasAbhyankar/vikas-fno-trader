# VIKAS GITHUB F&O TRADER - Single Scan - Saves Minutes
import datetime, csv, os, pandas as pd
import yfinance as yf
import ta
REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)
TODAY = datetime.date.today().isoformat()
REPORT_FILE = f"{REPORT_DIR}/trades_FNO_{TODAY}.csv"
SYMBOLS = ["ABB.NS","ABCAPITAL.NS","ADANIENT.NS","ADANIPORTS.NS","ALKEM.NS","AMBUJACEM.NS","APOLLOHOSP.NS","ASHOKLEY.NS","ASIANPAINT.NS","AUROPHARMA.NS","AXISBANK.NS","BAJAJ-AUTO.NS","BAJAJFINSV.NS","BAJFINANCE.NS","BALKRISIND.NS","BANDHANBNK.NS","BANKBARODA.NS","BEL.NS","BHARATFORG.NS","BHARTIARTL.NS","BHEL.NS","BIOCON.NS","BOSCHLTD.NS","BPCL.NS","BRITANNIA.NS","BSOFT.NS","CANBK.NS","CHOLAFIN.NS","CIPLA.NS","COALINDIA.NS","COFORGE.NS","COLPAL.NS","CONCOR.NS","COROMANDEL.NS","CROMPTON.NS","CUB.NS","CUMMINSIND.NS","DABUR.NS","DALBHARAT.NS","DIVISLAB.NS","DIXON.NS","DLF.NS","DRREDDY.NS","EICHERMOT.NS","ESCORTS.NS","EXIDEIND.NS","FEDERALBNK.NS","GAIL.NS","GLENMARK.NS","GODREJCP.NS","GODREJPROP.NS","GRANULES.NS","GRASIM.NS","GUJGASLTD.NS","HAL.NS","HAVELLS.NS","HCLTECH.NS","HDFCAMC.NS","HDFCBANK.NS","HDFCLIFE.NS","HEROMOTOCO.NS","HINDALCO.NS","HINDPETRO.NS","HINDUNILVR.NS","ICICIBANK.NS","ICICIGI.NS","ICICIPRULI.NS","IDEA.NS","IDFCFIRSTB.NS","INDHOTEL.NS","INDIGO.NS","INDUSINDBK.NS","INDUSTOWER.NS","INFY.NS","IOC.NS","IPCALAB.NS","IRCTC.NS","ITC.NS","JINDALSTEL.NS","JSWSTEEL.NS","JUBLFOOD.NS","KOTAKBANK.NS","LTF.NS","LT.NS","LTIM.NS","LUPIN.NS","M&M.NS","MARICO.NS","MARUTI.NS","MUTHOOTFIN.NS","NATIONALUM.NS","NAUKRI.NS","NTPC.NS","ONGC.NS","PAGEIND.NS","PERSISTENT.NS","PETRONET.NS","PFC.NS","PIDILITIND.NS","PEL.NS","POLICYBZR.NS","POLYCAB.NS","POWERGRID.NS","PVRINOX.NS","RECLTD.NS","RELIANCE.NS","SAIL.NS","SBILIFE.NS","SBIN.NS","SHREECEM.NS","SHRIRAMFIN.NS","SIEMENS.NS","SRF.NS","SUNPHARMA.NS","TATACONSUM.NS","TATAMOTORS.NS","TATAPOWER.NS","TATASTEEL.NS","TCS.NS","TECHM.NS","TITAN.NS","TORNTPHARM.NS","TRENT.NS","TVSMOTOR.NS","ULTRACEMCO.NS","UPL.NS","VEDL.NS","WIPRO.NS","ZYDUSLIFE.NS"]
def check(symbol):
    try:
        df = yf.download(symbol, period="60d", interval="1d", progress=False, auto_adjust=True)
        if len(df) < 35: return False,0
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df['ema8']=ta.trend.ema_indicator(df['Close'],8); df['ema20']=ta.trend.ema_indicator(df['Close'],20); df['ema50']=ta.trend.ema_indicator(df['Close'],50)
        df['rsi9']=ta.momentum.rsi(df['Close'],9); df['20d_high']=df['High'].rolling(20).max(); df['pct']=df['Close'].pct_change()*100; df['vol_20_avg']=df['Volume'].rolling(20).mean()
        last=df.iloc[-1]; prev1=df.iloc[-2]; prev2=df.iloc[-3]
        cond = last['Close']>df['20d_high'].iloc[-2] and last['Close']>prev1['High'] and last['Close']>prev1['Close']*1.02 and last['pct']>=2 and last['rsi9']>60 and last['ema8']>last['ema20'] and prev1['Volume']<prev2['Volume'] and (last['Close']*last['Volume'])>300000000 and last['ema20']>last['ema50'] and last['Volume']>last['vol_20_avg']*1.5
        return cond, float(last['Close'])
    except: return False,0
existing=[]
if os.path.exists(REPORT_FILE):
    with open(REPORT_FILE) as f: existing=list(csv.DictReader(f))
found=0
for sym in SYMBOLS:
    sig, price = check(sym)
    clean = sym.replace(".NS","")
    if sig and not any(e['symbol']==clean for e in existing):
        existing.append({"symbol":clean,"entry":round(price,2),"sl":round(price*0.992,2),"target":round(price*1.02,2),"entry_time":datetime.datetime.now().strftime('%H:%M'),"exit":"","exit_time":"","pnl":"","status":"OPEN","reason":"C5+V Breakout"})
        found+=1
with open(REPORT_FILE,'w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=["symbol","entry","sl","target","entry_time","exit","exit_time","pnl","status","reason"]); w.writeheader(); w.writerows(existing)
print(f"Scanned {len(SYMBOLS)} | New {found} | Total {len(existing)}")
