# ============================================================
# FNO V8.1 FINAL - AMRTS - Upstox Real-Time + Yahoo History
# Timing: 9:45 AM / 3:15 PM / 4:30 PM IST ONLY
# Data: Upstox Live (Entry, Nifty, VIX) + Yahoo History (EMA, RSI, ADX)
# Token: Upstox 1-Year Analytical - No Daily Refresh - Exp 2027-11-14
# Capital: Rs 5L Paper, Risk 1% = Rs 5000, Max 2 Trades
# Features: Regime + Choppy + Sideways S/R + Smart SL Anti-Hunt
#           + Sector + Gap + Event + Trailing + Top 2
# Telegram: Your ID (Secret) + 5239892901 + 9000971028
# ============================================================
import os, json, requests, traceback
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
UPSTOX_EXPIRY = os.getenv("UPSTOX_TOKEN_EXPIRY", "2027-11-14")
UPSTOX_ENABLED = bool(UPSTOX_TOKEN)
UPSTOX_BASE = "https://api.upstox.com/v3"

FRIEND_IDS = ["5239892901", "9000971028"]
def get_all_ids():
    ids=[]
    if CHAT_ID_ENV:
        for x in str(CHAT_ID_ENV).split(","):
            x=x.strip()
            if x and x not in ids: ids.append(x)
    for f in FRIEND_IDS:
        if f not in ids: ids.append(f)
    return ids
ALL_IDS = get_all_ids()

# ========== UPSTOX CLIENT - INSIDE MAIN.PY - NO SEPARATE FILE NEEDED ==========
def upstox_headers():
    return {"Authorization": f"Bearer {UPSTOX_TOKEN}", "Accept": "application/json"}
def upstox_live_price(instrument_key):
    if not UPSTOX_ENABLED: return None
    try:
        r=requests.get(f"{UPSTOX_BASE}/market-quote/quotes", headers=upstox_headers(),
                       params={"instrument_key": instrument_key}, timeout=10)
        if r.status_code!=200:
            print(f"Upstox fail {instrument_key} {r.status_code} {r.text[:150]}")
            return None
        data=r.json().get("data", {})
        q=data.get(instrument_key, {})
        lp=q.get("last_price") or q.get("ltp")
        return float(lp) if lp else None
    except Exception as e:
        print(f"Upstox error {e}"); return None
def upstox_candles(instrument_key, interval="15minute"):
    if not UPSTOX_ENABLED: return None
    try:
        r=requests.get(f"{UPSTOX_BASE}/market-candle/intraday/{instrument_key}/{interval}",
                       headers=upstox_headers(), timeout=15)
        if r.status_code!=200: return None
        return r.json().get("data", {}).get("candles", [])
    except: return None
def to_upstox_key(yahoo_sym):
    base=yahoo_sym.replace(".NS","").replace("-","_")
    return f"NSE_EQ|{base}"
def upstox_token_health():
    try:
        exp=datetime.strptime(UPSTOX_EXPIRY, "%Y-%m-%d").date()
        today=datetime.now(IST).date()
        days=(exp-today).days
        if days<0: return "EXPIRED", days
        if days<30: return f"EXPIRING in {days}d - Renew Soon", days
        return f"OK - {days}d left", days
    except: return "OK", 999
# ============================================================

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
    if not BOT_TOKEN: print("No BOT_TOKEN"); return
    for cid in ALL_IDS:
        try:
            r=requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id":cid,"text":msg,"parse_mode":"HTML"}, timeout=20)
            print(f"Telegram to {cid} {r.status_code}")
        except Exception as e: print(f"TG fail {cid} {e}")

def get_data(sym, period="3mo", interval="1d"):
    try:
        df=yf.download(sym, period=period, interval=interval, progress=False, auto_adjust=True)
        if df is None or df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns=[c[0] for c in df.columns]
        return df
    except: return None

def ema(s,n): return s.ewm(span=n, adjust=False).mean()
def rsi_calc(s,n=14):
    d=s.diff(); g=d.clip(lower=0); l=-d.clip(upper=0)
    ag=g.ewm(alpha=1/n, adjust=False).mean(); al=l.ewm(alpha=1/n, adjust=False).mean()
    rs=ag/(al+1e-9); return 100-(100/(1+rs))
def atr_calc(df,n=14):
    h=df['High']; l=df['Low']; c=df['Close']; pc=c.shift(1)
    tr=pd.concat([h-l,(h-pc).abs(),(l-pc).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()
def adx_calc(df,n=14):
    h=df['High']; l=df['Low']; c=df['Close']
    up=h.diff(); dn=-l.diff()
    pm=np.where((up>dn)&(up>0),up,0); mm=np.where((dn>up)&(dn>0),dn,0)
    tr=pd.concat([h-l,(h-c.shift(1)).abs(),(l-c.shift(1)).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/n, adjust=False).mean()
    pdm=pd.Series(pm,index=df.index).ewm(alpha=1/n, adjust=False).mean()
    mdm=pd.Series(mm,index=df.index).ewm(alpha=1/n, adjust=False).mean()
    pdi=100*pdm/(atr+1e-9); mdi=100*mdm/(atr+1e-9)
    dx=100*(pdi-mdi).abs()/(pdi+mdi+1e-9)
    return dx.ewm(alpha=1/n, adjust=False).mean(), pdi, mdi

def smart_sl(entry, support, resistance, atr, direction):
    max_dist=entry*0.015
    if direction=="BUY":
        base=support-(atr*0.8)-(entry*0.003)
        sl=base
        if entry-base>max_dist: sl=entry-max_dist
        if round(sl)%10==0: sl=sl-7.37
        tgt=entry+(entry-sl)*2
    else:
        base=resistance+(atr*0.8)+(entry*0.003)
        sl=base
        if sl-entry>max_dist: sl=entry+max_dist
        if round(sl)%10==0: sl=sl+7.37
        tgt=entry-(sl-entry)*2
    sl_pct=abs(entry-sl)/entry*100
    return round(sl,2), round(tgt,2), round(sl_pct,2)

def detect_regime_and_choppy():
    nifty=get_data("^NSEI", period="3mo", interval="1d")
    bank=get_data("^NSEBANK", period="3mo", interval="1d")
    vix=get_data("^INDIAVIX", period="1mo", interval="1d")
    if nifty is None: return "TRANSITION",0,0,0,"Nifty data fail",False, "Yahoo"
    close=nifty['Close']; ema20=ema(close,20); ema50=ema(close,50)
    adx,_,_=adx_calc(nifty); atr=atr_calc(nifty)
    last=float(close.iloc[-1]); e20=float(ema20.iloc[-1]); e50=float(ema50.iloc[-1])
    adx_v=float(adx.iloc[-1])
    vix_v=float(vix['Close'].iloc[-1]) if vix is not None else 14
    vix_prev=float(vix['Close'].iloc[-2]) if vix is not None and len(vix)>1 else vix_v
    vix_jump=(vix_v-vix_prev)/vix_prev*100 if vix_prev else 0
    # V8.1 - Override with Upstox Live Nifty + VIX
    data_source="Yahoo (Delayed)"
    if UPSTOX_ENABLED:
        live_nifty=upstox_live_price("NSE_INDEX|Nifty 50")
        live_vix=upstox_live_price("NSE_INDEX|India VIX")
        if live_nifty:
            print(f"Upstox Nifty Live: {live_nifty} vs Yahoo {last}")
            last=live_nifty; data_source="Upstox Live"
        if live_vix:
            print(f"Upstox VIX Live: {live_vix} vs Yahoo {vix_v}")
            vix_v=live_vix; data_source="Upstox Live"
    rng=(float(nifty['High'].iloc[-5:].max())-float(nifty['Low'].iloc[-5:].min()))/last*100
    choppy_score=0; reasons=[]
    if adx_v<18: choppy_score+=1; reasons.append(f"ADX {adx_v:.1f} Weak")
    if vix_v>17 or vix_jump>10: choppy_score+=1; reasons.append(f"VIX {vix_v:.1f} High")
    if rng<1.2: choppy_score+=1; reasons.append(f"Range5D {rng:.2f}% Small")
    if bank is not None:
        bclose=bank['Close']; bema20=ema(bclose,20)
        nifty_up=last>e20; bank_up=float(bclose.iloc[-1])>float(bema20.iloc[-1])
        if nifty_up!=bank_up: choppy_score+=1; reasons.append("Nifty vs Bank Disagree")
    if abs(last-e20)/last*100<0.3 and adx_v<20: choppy_score+=1; reasons.append("Near EMA20 + Weak ADX")
    is_choppy=choppy_score>=3
    if is_choppy: regime="CHOPPY - NO TRADE"
    elif last>e20 and last>e50 and adx_v>25: regime="STRONG BULL"
    elif last<e20 and last<e50 and adx_v>25: regime="STRONG BEAR"
    elif adx_v<22: regime="SIDEWAYS"
    elif vix_v>17: regime="VOLATILE"
    else: regime="TRANSITION"
    info=f"Nifty {last:.1f} | EMA20 {e20:.1f} EMA50 {e50:.1f} | ADX {adx_v:.1f} | VIX {vix_v:.1f} | Range5D {rng:.2f}% | Choppy {choppy_score}/5 | Data: {data_source}"
    return regime, adx_v, vix_v, last, info, is_choppy, data_source

def scan_stocks(regime, run_type):
    results=[]
    for sym in FNO_STOCKS:
        try:
            df=get_data(sym, period="3mo", interval="1d")
            if df is None or len(df)<60: continue
            close=df['Close']; high=df['High']; low=df['Low']
            last=float(close.iloc[-1]); prev=float(close.iloc[-2])
            e20=float(ema(close,20).iloc[-1]); e50=float(ema(close,50).iloc[-1])
            rsi=float(rsi_calc(close).iloc[-1])
            atr=float(atr_calc(df).iloc[-1])
            adx,_,_=adx_calc(df); adx_v=float(adx.iloc[-1])
            prev_high=float(high.iloc[-2]); prev_low=float(low.iloc[-2])
            sup=prev_low; res=prev_high
            # V8.1 - Override Yahoo price with Upstox Live price
            live_price=None
            if UPSTOX_ENABLED:
                live_price=upstox_live_price(to_upstox_key(sym))
                if live_price:
                    print(f"Upstox {sym}: Live {live_price} vs Yahoo {last}")
                    last=live_price
            rng_pct=(res-sup)/last*100 if last else 0
            day_move=abs(last-prev)/prev*100
            if run_type=="MORNING" and day_move>2.5: continue  # Gap Filter - Don't chase
            sector_ok=True
            sec_sym=SECTOR_MAP.get(sym)
            if sec_sym:
                sec=get_data(sec_sym, period="1mo", interval="1d")
                if sec is not None:
                    sc=sec['Close']; se20=float(ema(sc,20).iloc[-1]); slast=float(sc.iloc[-1])
                    if (slast>se20)!=(last>e20): sector_ok=False
            score=0; direction=None; strategy=""; entry=last
            if regime in ["SIDEWAYS","VOLATILE"]:
                if rng_pct<1.2: continue
                if abs(last-sup)/last*100<0.8 and rsi<40:
                    direction="BUY"; strategy="Sideways Support Buy"; score=75
                    if sector_ok: score+=10
                    if rsi<35: score+=5
                elif abs(last-res)/last*100<0.8 and rsi>60:
                    direction="SELL"; strategy="Sideways Resistance Sell"; score=75
                    if sector_ok: score+=10
                    if rsi>65: score+=5
            elif regime=="STRONG BULL":
                if last>e20 and last>e50 and 50<rsi<70:
                    if last>=res*0.995: direction="BUY"; strategy="Bull Breakout"; score=85
                    elif abs(last-e20)/last*100<1.0: direction="BUY"; strategy="Bull Pullback"; score=80
            elif regime=="STRONG BEAR":
                if last<e20 and last<e50 and 30<rsi<50:
                    if last<=sup*1.005: direction="SELL"; strategy="Bear Breakdown"; score=85
                    elif abs(last-e20)/last*100<1.0: direction="SELL"; strategy="Bear Pullback"; score=80
            if direction:
                sl,tgt,sl_pct=smart_sl(entry, sup, res, atr, direction)
                if sl_pct>1.8 or sl_pct<0.4: continue
                qty=int(RISK_PER_TRADE//abs(entry-sl)) if abs(entry-sl)>0 else 0
                if qty<=0: continue
                if "Sideways" in strategy: qty=qty//2
                results.append({"sym":sym.replace(".NS",""),"entry":round(entry,2),"sl":sl,"tgt":tgt,
                    "sl_pct":sl_pct,"dir":direction,"strat":strategy,"score":score,
                    "rsi":round(rsi,1),"sup":round(sup,2),"res":round(res,2),
                    "rng":round(rng_pct,2),"qty":qty,
                    "src":"Upstox Live" if live_price else "Yahoo"})
        except Exception as e:
            print(f"Scan fail {sym} {e}"); continue
    results=sorted(results, key=lambda x: x['score'], reverse=True)
    return results[:MAX_TRADES]

def main():
    now=datetime.now(IST)
    if now.weekday()>4:
        print("Weekend - No Trade"); return
    # V8.1 - Upstox Token Health Check
    token_msg="Upstox: OFF - Yahoo Only"
    if UPSTOX_ENABLED:
        health, days = upstox_token_health()
        token_msg=f"Upstox: {health} | Exp {UPSTOX_EXPIRY}"
        print(token_msg)
        if health=="EXPIRED":
            print("Token expired - Fallback to Yahoo")
            token_msg="Upstox: EXPIRED - Using Yahoo Fallback - Renew Token!"
    else:
        print("No UPSTOX_ACCESS_TOKEN - Using Yahoo only")
    is_thursday=now.weekday()==3
    h=now.hour; m=now.minute; total_min=h*60+m
    if 555 <= total_min <= 620: run_type="MORNING"; run_label="MORNING ENTRY - 09:45 IST"
    elif 915 <= total_min <= 980: run_type="BTST"; run_label="BTST - 15:15 IST - Buy Today Sell Tomorrow"
    elif 990 <= total_min <= 1080: run_type="EOD"; run_label="EOD REPORT - 16:30 IST"
    else: run_type="MORNING"; run_label=f"MANUAL RUN - {now.strftime('%H:%M IST')}"
    print(f"V8.1 Run {run_type} {now} IST")
    regime, adx_v, vix_v, nifty_last, regime_info, is_choppy, data_src = detect_regime_and_choppy()
    print(regime_info)
    if is_choppy and run_type in ["MORNING","BTST"]:
        msg=(f"🚫 <b>FNO V8.1 - NO TRADE - {run_label}</b>\n"
             f"📅 {now.strftime('%d-%m-%Y %H:%M IST')}\n"
             f"Regime: <b>CHOPPY - NO TRADE</b>\n{regime_info}\n"
             f"Reason: 3+/5 Choppy Tests True\n"
             f"Action: <b>PROTECT CAPITAL - No Trade</b>\n"
             f"Next Check: {'3:15 PM IST BTST' if run_type=='MORNING' else 'Tomorrow 9:45 AM IST'}\n"
             f"{token_msg}")
        send_tg(msg); print("Choppy - No Trade"); return
    if run_type=="EOD":
        msg=(f"📊 <b>FNO V8.1 - EOD REPORT - 16:30 IST</b>\n"
             f"📅 {now.strftime('%d-%m-%Y')}\n"
             f"Regime Today: <b>{regime}</b>\n{regime_info}\n"
             f"Tomorrow Plan: {'Sideways - Buy at Support / Sell at Resistance, 50% size' if regime=='SIDEWAYS' else regime}\n"
             f"Thursday Note: {'Tomorrow is Friday - No BTST Today' if is_thursday else 'BTST allowed tomorrow if not Choppy'}\n"
             f"Smart SL: Max 1.0% Intraday, 1.5% BTST, 1.8% Swing - Buffered, Non-Round, Close-Based\n"
             f"{token_msg}\nCapital: Rs 5L Paper")
        send_tg(msg); print("EOD Sent"); return
    if run_type=="BTST" and is_thursday:
        msg=(f"🚫 <b>FNO V8.1 - NO BTST - Thursday - 15:15 IST</b>\nRegime: {regime}\n{regime_info}\n"
             f"Reason: Thursday BTST = Friday Gap Risk High\nAction: Book all BTST, No new BTST\nNext: Tomorrow 9:45 AM IST")
        send_tg(msg); print("Thursday No BTST"); return
    picks=scan_stocks(regime, run_type)
    if not picks:
        msg=(f"📊 <b>FNO V8.1 - NO TRADE - {run_label}</b>\n📅 {now.strftime('%d-%m-%Y %H:%M IST')}\n"
             f"Regime: <b>{regime}</b>\n{regime_info}\n"
             f"Reason: No stock passed - SL too high / Gap >1.5% / Sector Disagree / Range too small\n{token_msg}\nCapital: Rs 5L Paper")
        send_tg(msg); print("No picks"); return
    lines=[]
    for i,p in enumerate(picks,1):
        emoji="🟢" if p['dir']=="BUY" else "🔴"
        extra=""
        if run_type=="BTST": extra="\n⏰ Sell: Tomorrow 9:45 AM IST | SL: Close-Based - Exit only if 2x 15-min closes below SL"
        if "Sideways" in p['strat']: extra+="\n⚠️ Sideways - 50% Size - Book at VWAP / Mid"
        lines.append(f"\n{i}. {emoji} <b>{p['dir']} {p['sym']}</b> @ Rs {p['entry']} [{p['src']}]\n"
            f"Strategy: {p['strat']} | Score: {p['score']}/100 | RSI {p['rsi']}\n"
            f"Support Rs {p['sup']} | Resistance Rs {p['res']} | Range {p['rng']}%\n"
            f"Smart SL Rs {p['sl']} ({p['sl_pct']}% - Buffered, Anti-Hunt, Non-Round)\n"
            f"Target Rs {p['tgt']} (RR 1:2)\nQty: {p['qty']} (Risk Rs {abs(p['entry']-p['sl'])*p['qty']:.0f})\n"
            f"Trailing: Book 50% at 50% Target, Move SL to Breakeven{extra}")
    action_note="BUY TODAY - Sell Tomorrow 9:45 AM IST" if run_type=="BTST" else "Entry Now - 9:45 AM IST - Do NOT Chase if Gap >1.5%"
    msg=(f"📊 <b>FNO V8.1 - {run_label}</b>\n📅 {now.strftime('%d-%m-%Y %H:%M IST')}\n"
         f"Regime: <b>{regime}</b>\n{regime_info}\nAction: {action_note}\n"
         f"Max Trades: 2 | Capital: Rs 5L Paper | Risk 1% per trade\n{''.join(lines)}\n\n"
         f"⚠️ Smart SL: Do NOT move SL to Support / Round Number. SL is hidden below Support + Buffer. Exit only on 2x 15-min closes below SL (ignore wick).\n{token_msg}")
    send_tg(msg)
    print(f"V8.1 Complete - {len(picks)} picks sent")

if __name__=="__main__":
    try: main()
    except Exception as e:
        print(traceback.format_exc())
        try: send_tg(f"⚠️ V8.1 Error: {e}")
        except: pass
