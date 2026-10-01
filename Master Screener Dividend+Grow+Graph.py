import yfinance as yf
import pandas as pd
import requests
import time 

start_time = time.time()

# ===================================================================
# 🌎 1. "จักรวาลหุ้น" ของคุณ
# ===================================================================

MY_INTEREST_LIST = ["IONQ", "RGTI", "PLTR", "SOFI", "CRWD"]

# --- 💡 ตั้งค่าตรงนี้ ---
# (เราจะรัน Full Scan เลย เพราะนี่คือ V10 Master)
RUN_FULL_SCAN = True 
# ---------------------

tickers_list = []
if RUN_FULL_SCAN:
    print("--- 1. [V10 Full Scan] กำลังดึงรายชื่อหุ้น S&P 500... ---")
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {'User-Agent': 'Mozilla/5.0'}
        html_content = requests.get(url, headers=headers).text
        tables = pd.read_html(html_content)
        sp500_table = tables[0]
        sp500_list = sp500_table['Symbol'].str.replace('.', '-', regex=False).tolist()
        print(f"ดึง S&P 500 สำเร็จ: {len(sp500_list)} ตัว")
        combined_list = list(set(sp500_list + MY_INTEREST_LIST))
    except Exception as e:
        print(f"*** ไม่สามารถดึงรายชื่อ S&P 500 ได้: {e} ***")
        combined_list = ["AAPL", "MSFT", "NVDA", "HRL", "T", "IONQ"] # (List สำรอง)
else:
    print("--- 1. [Test Run] ใช้รายชื่อหุ้นทดสอบ... ---")
    combined_list = ["AAPL", "MSFT", "NVDA", "HRL", "T", "IONQ"]

print(f"--- 💡 หุ้นทั้งหมดที่จะตรวจสอบ: {len(combined_list)} ตัว ---")


# ===================================================================
# 🧠 ส่วนที่ 2 (V10): "ฟังก์ชันนักวิเคราะห์" (ดึงทุกอย่าง!)
# ===================================================================
def calculate_master_metrics(ticker_symbol):
    """
    V10 - ดึงข้อมูลดิบสำหรับ V7, V8, V9 ในครั้งเดียว
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        
        info = stock.info
        b_sheet = stock.balance_sheet
        i_sheet = stock.financials 
        
        if info is None or len(info) <= 2 or b_sheet.empty or i_sheet.empty:
            print(f"    [!] Error: ข้อมูลของ {ticker_symbol} ว่างเปล่า (อาจถูกบล็อก)")
            return None

        b_sheet_latest = b_sheet.iloc[:, 0]
        i_sheet_latest = i_sheet.iloc[:, 0]

        price = info.get('currentPrice')
        shares_outstanding = info.get('sharesOutstanding')
        
        if price is None or shares_outstanding is None:
            print(f"    [!] ข้าม {ticker_symbol}: ไม่มี Price/Shares")
            return None

        # --- คำนวณ V7 (Dividend) + V5 (Base) ---
        total_equity = b_sheet_latest.get('Stockholders Equity') 
        net_income = i_sheet_latest.get('Net Income')
        total_debt = b_sheet_latest.get('Total Debt', 0) 
        
        if total_equity is None or net_income is None: 
            print(f"    [!] ข้าม {ticker_symbol}: ไม่มี Equity/Net Income")
            return None 

        de_ratio_pct = (total_debt / total_equity) * 100 
        
        # (ต้องเช็กว่ามีกำไรไหม)
        pe_ratio = None
        payout_ratio = float('inf') # (ถ้าขาดทุน = จ่ายเกินตัว)
        
        if net_income > 0 and shares_outstanding > 0 and price > 0:
            eps = net_income / shares_outstanding
            pe_ratio = price / eps
            
            dividend_per_share = info.get('trailingAnnualDividendRate', 0) 
            dividend_yield_pct = (dividend_per_share / price) 
            payout_ratio = dividend_per_share / eps 
        else:
             dividend_yield_pct = 0.0 # (ถ้าขาดทุน ก็ไม่นับปันผล)

        # --- ดึงข้อมูล V8 (Growth) ---
        revenue_growth = info.get('revenueGrowth')
        
        # --- ดึงข้อมูล V9 (Momentum) ---
        sma_200 = info.get('twoHundredDayAverage')
        sma_50 = info.get('fiftyDayAverage')
        
        if sma_200 is None or sma_50 is None:
            print(f"    [!] ข้าม {ticker_symbol}: ไม่มีข้อมูล SMA")
            return None
            
        return {
            'Ticker': ticker_symbol, 'Name': info.get('shortName', ticker_symbol),
            # V7 Data
            'DivYield_pct': dividend_yield_pct,
            'PayoutRatio': payout_ratio,
            'DE_pct': de_ratio_pct,
            # V8 Data
            'RevenueGrowth': revenue_growth,
            'PE': pe_ratio,
            # V9 Data
            'Price': price,
            'SMA_200': sma_200,
            'SMA_50': sma_50
        }

    except Exception as e:
        print(f"    [!] Error (Exception) วิเคราะห์ {ticker_symbol}: {e}") 
        return None

# ===================================================================
# 📥 ส่วนที่ 3 (Fetcher): V10 - (ต้องช้า!)
# ===================================================================
print(f"\n--- 2. เริ่มดึงข้อมูล (V10 - Master Version) ---")
print("...นี่คือโหมด 'Full Scan' ที่ช้าที่สุด (15-20 นาที)...")

all_stock_data = [] 

for i, ticker in enumerate(combined_list):
    print(f"  ({i+1}/{len(combined_list)}) ...วิเคราะห์ {ticker}")
    metrics = calculate_master_metrics(ticker)
    
    if metrics is not None:
        all_stock_data.append(metrics)
        
    time.sleep(1) # (สำคัญที่สุด! กันโดนบล็อก)

print(f"\n--- 🎉 ดึงข้อมูลเสร็จสิ้น! (วิเคราะห์สำเร็จ {len(all_stock_data)} ตัว) ---")


# ===================================================================
# 🔎 ส่วนที่ 4 (Analyzer): "คัดกรอง 3 กลยุทธ์พร้อมกัน"
# ===================================================================
print("\n--- 3. เริ่มคัดกรอง (Screener) ด้วย 3 อัลกอริทึม (V10) ---")

# --- 💡 "กฎ" ทั้ง 3 ชุด ---
RULES_DIVIDEND = { # (V7)
    'MIN_DIVIDEND_YIELD': 0.04,  
    'MAX_PAYOUT_RATIO': 0.70,  
    'MIN_PAYOUT_RATIO': 0.01,  
    'MAX_DEBT_EQUITY': 150.0 
}
RULES_GROWTH = { # (V8)
    'MIN_REVENUE_GROWTH': 0.25,  
    'MIN_PE_RATIO': 0.0, 
    'MAX_DEBT_EQUITY': 150.0 
}
RULES_MOMENTUM = { # (V9)
    'USE_MOMENTUM': True # (เราเช็ก Price > SMA)
}
print("กำลังคัดกรอง V7 (Dividend), V8 (Growth), V9 (Momentum)...")

# --- "ตะกร้า" ผู้ชนะ 3 ใบ ---
dividend_list = [] 
growth_list = []
momentum_list = []

for stock in all_stock_data:
    # --- ดึงค่า (ป้องกัน Error ถ้าไม่มี) ---
    de = stock['DE_pct']
    
    # --- 1. เช็กเลนส์ V7 (Dividend) ---
    div = stock['DivYield_pct']
    payout = stock['PayoutRatio']
    if (div > RULES_DIVIDEND['MIN_DIVIDEND_YIELD'] and
        payout < RULES_DIVIDEND['MAX_PAYOUT_RATIO'] and
        payout > RULES_DIVIDEND['MIN_PAYOUT_RATIO'] and
        de < RULES_DIVIDEND['MAX_DEBT_EQUITY']):
        dividend_list.append(stock)

    # --- 2. เช็กเลนส์ V8 (Growth) ---
    growth = stock.get('RevenueGrowth') or 0.0
    pe = stock.get('PE') or -1.0 # (ถ้าไม่มี PE = ขาดทุน)
    if (growth > RULES_GROWTH['MIN_REVENUE_GROWTH'] and
        pe > RULES_GROWTH['MIN_PE_RATIO'] and
        de < RULES_GROWTH['MAX_DEBT_EQUITY']):
        growth_list.append(stock)
        
    # --- 3. เช็กเลนส์ V9 (Momentum) ---
    if (stock['Price'] > stock['SMA_200'] and
        stock['Price'] > stock['SMA_50']):
        momentum_list.append(stock)

# ===================================================================
# 📋 ส่วนที่ 5: สรุปผล (และ "จุดตัด"!)
# ===================================================================
print("\n=========================================================")
print(f"📊 สรุปผล 'Master Screener V10'")
print(f"(วิเคราะห์ข้อมูลทั้งหมด {len(all_stock_data)} ตัว)")
print("=========================================================")

print(f"💰 V7 (Dividend): พบ {len(dividend_list)} ตัว")
print(f"🚀 V8 (Pure Growth): พบ {len(growth_list)} ตัว")
print(f"📈 V9 (Momentum): พบ {len(momentum_list)} ตัว")

# --- 💡 นี่คือส่วนที่สำคัญที่สุด: "จุดตัด" (Intersections) ---
print("\n=========================================================")
print(f"🔥 'จุดตัด' ที่น่าสนใจ (The Holy Grails)")
print("=========================================================")

# สร้าง Set ของ Ticker เพื่อหาจุดตัด
dividend_tickers = {s['Ticker'] for s in dividend_list}
growth_tickers = {s['Ticker'] for s in growth_list}
momentum_tickers = {s['Ticker'] for s in momentum_list}

# --- จุดตัดที่ 1: Growth + Momentum ---
gm_list = growth_tickers.intersection(momentum_tickers)
print(f"\n🚀 (V8 ∩ V9) 'โตเร็ว + กราฟสวย': {len(gm_list)} ตัว")
if len(gm_list) > 0:
    print(f"   -> {', '.join(gm_list)}")

# --- จุดตัดที่ 2: Dividend + Momentum ---
dm_list = dividend_tickers.intersection(momentum_tickers)
print(f"\n💰 (V7 ∩ V9) 'ปันผลดี + กราฟสวย': {len(dm_list)} ตัว")
if len(dm_list) > 0:
    print(f"   -> {', '.join(dm_list)}")

end_time = time.time()
print(f"\n--- ใช้เวลาทั้งหมด: {end_time - start_time:.2f} วินาที ---")