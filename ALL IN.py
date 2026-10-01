import yfinance as yf
import pandas as pd
import requests
import time 

start_time = time.time()

# ===================================================================
# 🌎 1. "จักรวาลหุ้น" V11.1 (S&P 500 + NASDAQ-100!)
# ===================================================================

MY_INTEREST_LIST = ["IONQ", "RGTI", "PLTR", "SOFI", "CRWD"]

# --- 💡 ตั้งค่าตรงนี้ ---
RUN_FULL_SCAN = True 
# ---------------------

sp500_list = []
nasdaq100_list = []

if RUN_FULL_SCAN:
    # --- 1.1 ดึง S&P 500 (เหมือนเดิม) ---
    print("--- 1. [V11.1] กำลังดึงรายชื่อหุ้น S&P 500... ---")
    try:
        url_sp500 = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {'User-Agent': 'Mozilla/5.0'}
        html_content = requests.get(url_sp500, headers=headers).text
        tables = pd.read_html(html_content)
        sp500_table = tables[0]
        sp500_list = sp500_table['Symbol'].str.replace('.', '-', regex=False).tolist()
        print(f"ดึง S&P 500 สำเร็จ: {len(sp500_list)} ตัว")
    except Exception as e:
        print(f"*** ไม่สามารถดึงรายชื่อ S&P 500 ได้: {e} ***")

    # --- ❗️ 1.2 (ใหม่!) ดึง NASDAQ-100 ---
    print("--- 1. [V11.1] กำลังดึงรายชื่อหุ้น NASDAQ-100... ---")
    try:
        url_ndx = 'https://en.wikipedia.org/wiki/Nasdaq-100'
        headers = {'User-Agent': 'Mozilla/5.0'}
        html_content = requests.get(url_ndx, headers=headers).text
        tables = pd.read_html(html_content)
        # (ตารางที่ 4 ในหน้านี้ คือรายชื่อ Ticker)
        nasdaq_table = tables[4] 
        nasdaq100_list = nasdaq_table['Ticker'].tolist()
        print(f"ดึง NASDAQ-100 สำเร็จ: {len(nasdaq100_list)} ตัว")
    except Exception as e:
        print(f"*** ไม่สามารถดึงรายชื่อ NASDAQ-100 ได้: {e} ***")

    # --- 1.3 "หลอมรวม" 3 Lists! ---
    # (ใช้ set() เพื่อ "ลบตัวซ้ำ" อัตโนมัติ)
    combined_list = list(set(sp500_list + nasdaq100_list + MY_INTEREST_LIST))
    
    if len(combined_list) < 10: # (กรณีฉุกเฉิน ถ้าเน็ตล่ม)
        combined_list = ["AAPL", "MSFT", "NVDA", "HRL", "T", "IONQ"]

else:
    print("--- 1. [Test Run] ใช้รายชื่อหุ้นทดสอบ... ---")
    combined_list = ["AAPL", "MSFT", "NVDA", "HRL", "T", "IONQ"]

print(f"--- 💡 หุ้นทั้งหมดที่จะตรวจสอบ (Expanded): {len(combined_list)} ตัว ---")


# ===================================================================
# 🧠 ส่วนที่ 2 (V11): "ฟังก์ชันนักวิเคราะห์" (เหมือนเดิมเป๊ะ)
# ===================================================================
def calculate_master_metrics(ticker_symbol):
    """
    V11 - ดึงข้อมูลดิบสำหรับทุกกลยุทธ์!
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

        # --- คำนวณ V5 (Value) + V7 (Dividend) ---
        total_equity = b_sheet_latest.get('Stockholders Equity') 
        net_income = i_sheet_latest.get('Net Income')
        total_debt = b_sheet_latest.get('Total Debt', 0) 
        current_assets = b_sheet_latest.get('Current Assets')
        current_liabilities = b_sheet_latest.get('Current Liabilities')
        
        if total_equity is None or net_income is None or current_assets is None or current_liabilities is None: 
            print(f"    [!] ข้าม {ticker_symbol}: ไม่มี Equity/Income/Current")
            return None 

        de_ratio_pct = (total_debt / total_equity) * 100 
        current_ratio = current_assets / current_liabilities
        pb_ratio = price / (total_equity / shares_outstanding)
        
        pe_ratio = None
        payout_ratio = float('inf') 
        
        if net_income > 0 and shares_outstanding > 0 and price > 0:
            eps = net_income / shares_outstanding
            pe_ratio = price / eps
            
            dividend_per_share = info.get('trailingAnnualDividendRate', 0) 
            dividend_yield_pct = (dividend_per_share / price) 
            payout_ratio = dividend_per_share / eps 
        else:
             dividend_yield_pct = 0.0

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
            'PB': pb_ratio, 'CurrentRatio': current_ratio,
            'DivYield_pct': dividend_yield_pct, 'PayoutRatio': payout_ratio,
            'DE_pct': de_ratio_pct, 'RevenueGrowth': revenue_growth,
            'PE': pe_ratio, 'Price': price, 'SMA_200': sma_200, 'SMA_50': sma_50
        }

    except Exception as e:
        print(f"    [!] Error (Exception) วิเคราะห์ {ticker_symbol}: {e}") 
        return None

# ===================================================================
# 📥 ส่วนที่ 3 (Fetcher): V11 (เหมือนเดิมเป๊ะ)
# ===================================================================
print(f"\n--- 2. เริ่มดึงข้อมูล (V11.1 - Dashboard Version) ---")
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
# 🔎 ส่วนที่ 4 (Analyzer): V11 (เหมือนเดิมเป๊ะ)
# ===================================================================
print("\n--- 3. เริ่มคัดกรอง (Screener) ด้วยทุกอัลกอริทึม (V11) ---")

# --- 💡 "กฎ" ทั้ง 4 ชุด ---
RULES_DEEP_VALUE = { # (V5)
    'MAX_PE': 15.0, 'MAX_PB': 1.5, 'MAX_DEBT_EQUITY': 50.0, 
    'MIN_CURRENT_RATIO': 2.0, 'MIN_DIVIDEND_YIELD': 0.02 
}
RULES_DIVIDEND = { # (V7)
    'MIN_DIVIDEND_YIELD': 0.04, 'MAX_PAYOUT_RATIO': 0.70,  
    'MIN_PAYOUT_RATIO': 0.01, 'MAX_DEBT_EQUITY': 150.0 
}
RULES_GROWTH = { # (V8)
    'MIN_REVENUE_GROWTH': 0.25, 'MIN_PE_RATIO': 0.0, 
    'MAX_DEBT_EQUITY': 150.0 
}
print("กำลังคัดกรอง V5 (Value), V7 (Dividend), V8 (Growth), V9 (Momentum)...")

# --- "ตะกร้า" ผู้ชนะ 4 ใบ ---
deep_value_list = [] 
dividend_list = [] 
growth_list = []
momentum_list = []

for stock in all_stock_data:
    de = stock['DE_pct']
    pe = stock.get('PE') or -1.0
    div = stock['DivYield_pct']
    
    # --- 1. เช็กเลนส์ V5 (Deep Value) ---
    pb = stock['PB']
    cr = stock['CurrentRatio']
    if (pe > 0 and pe < RULES_DEEP_VALUE['MAX_PE'] and
        pb < RULES_DEEP_VALUE['MAX_PB'] and
        de < RULES_DEEP_VALUE['MAX_DEBT_EQUITY'] and
        cr > RULES_DEEP_VALUE['MIN_CURRENT_RATIO'] and
        div > RULES_DEEP_VALUE['MIN_DIVIDEND_YIELD']):
        deep_value_list.append(stock)

    # --- 2. เช็กเลนส์ V7 (Dividend) ---
    payout = stock['PayoutRatio']
    if (div > RULES_DIVIDEND['MIN_DIVIDEND_YIELD'] and
        payout < RULES_DIVIDEND['MAX_PAYOUT_RATIO'] and
        payout > RULES_DIVIDEND['MIN_PAYOUT_RATIO'] and
        de < RULES_DIVIDEND['MAX_DEBT_EQUITY']):
        dividend_list.append(stock)

    # --- 3. เช็กเลนส์ V8 (Growth) ---
    growth = stock.get('RevenueGrowth') or 0.0
    if (growth > RULES_GROWTH['MIN_REVENUE_GROWTH'] and
        pe > RULES_GROWTH['MIN_PE_RATIO'] and
        de < RULES_GROWTH['MAX_DEBT_EQUITY']):
        growth_list.append(stock)
        
    # --- 4. เช็กเลนส์ V9 (Momentum) ---
    if (stock['Price'] > stock['SMA_200'] and
        stock['Price'] > stock['SMA_50']):
        momentum_list.append(stock)

# ===================================================================
# 📋 ส่วนที่ 5: "แผงหน้าปัด" (Dashboard V11) (เหมือนเดิมเป๊ะ)
# ===================================================================
print("\n\n=========================================================")
print(f"📊 แผงหน้าปัด 'Market Health Dashboard V11.1 (Expanded)'")
print(f" (วิเคราะห์ข้อมูลทั้งหมด {len(all_stock_data)} ตัว)")
print("=========================================================")

# --- 1. คำนวณ "อุณหภูมิ" ตลาด (Market Sentiment) ---
momentum_score_pct = (len(momentum_list) / len(all_stock_data)) * 100
market_sentiment = "Neutral"
sentiment_emoji = "🌡️"

if momentum_score_pct > 50:
    market_sentiment = "'กระทิงเต็มตัว' (Greed - ขาขึ้น)"
    sentiment_emoji = "🔥"
elif momentum_score_pct > 30:
    market_sentiment = "'ค่อนข้างดี' (Warm - ขาขึ้น)"
    sentiment_emoji = "📈"
elif momentum_score_pct < 20:
    market_sentiment = "'หมี' (Fear - ขาลง)"
    sentiment_emoji = "🧊"

print(f"\n### {sentiment_emoji} 1. อุณหภูมิตลาด (Market Sentiment)")
print(f"* หุ้น V9 (กราฟสวย): {len(momentum_list)} / {len(all_stock_data)} ตัว ({momentum_score_pct:.1f}%)")
print(f"* แปลผล: ตลาดอยู่ในสภาวะ {market_sentiment}")

# --- 2. คำนวณ "กลยุทธ์ที่ตลาด 'รัก'" (What's Working) ---
print(f"\n### 🚀 2. กลยุทธ์ที่ 'เวิร์ค' ในตอนนี้")

# (V8 ∩ V9)
growth_tickers = {s['Ticker'] for s in growth_list}
momentum_tickers = {s['Ticker'] for s in momentum_list}
gm_list = growth_tickers.intersection(momentum_tickers)
gm_pct = (len(gm_list) / len(growth_list)) * 100 if len(growth_list) > 0 else 0

print(f"* V8 (Growth): พบ {len(growth_list)} ตัว -> {len(gm_list)} ตัวมี Momentum ({gm_pct:.0f}%)")

# (V7 ∩ V9)
dividend_tickers = {s['Ticker'] for s in dividend_list}
dm_list = dividend_tickers.intersection(momentum_tickers)
dm_pct = (len(dm_list) / len(dividend_list)) * 100 if len(dividend_list) > 0 else 0

print(f"* V7 (Dividend): พบ {len(dividend_list)} ตัว -> {len(dm_list)} ตัวมี Momentum ({dm_pct:.0f}%)")

# (V5 ∩ V9)
value_tickers = {s['Ticker'] for s in deep_value_list}
vm_list = value_tickers.intersection(momentum_tickers)
vm_pct = (len(vm_list) / len(deep_value_list)) * 100 if len(deep_value_list) > 0 else 0

print(f"* V5 (Deep Value): พบ {len(deep_value_list)} ตัว -> {len(vm_list)} ตัวมี Momentum ({vm_pct:.0f}%)")


# --- 3. "คำแนะนำ" จาก Dashboard ---
print(f"\n### 💡 3. 'คำแนะนำ' จาก Dashboard")

if momentum_score_pct > 30: # (ตลาดขาขึ้น)
    print(f"* สถานการณ์: 'ตามน้ำ' (Follow the Trend)")
    print(f"* ตลาดกำลัง 'ให้รางวัล' หุ้น Growth (V8) อย่างชัดเจน")
    print(f"* กลยุทธ์ที่ควรโฟกัส: V8 (Growth) และ V9 (Momentum)")
    print("\n--- 'Holy Grail' (V8 ∩ V9): โตเร็ว + กราฟสวย ---")
    print(f"   -> พบ {len(gm_list)} ตัว: {', '.join(gm_list) if len(gm_list) > 0 else 'N/A'}")

else: # (ตลาดขาลง)
    print(f"* สถานการณ์: 'สวนกระแส' (Contrarian / Fear)")
    print(f"* ตลาดกำลัง 'กลัว' (V9 ต่ำ) นี่คือเวลาหาของถูก")
    print(f"* กลยุทธ์ที่ควรโฟกัส: V5 (Deep Value) และ V7 (Dividend)")
    print("\n--- 'Bargain Bin' (V7): ปันผลดี (กราฟอาจจะพัง) ---")
    print(f"   -> พบ {len(dividend_list)} ตัว: {', '.join(dividend_tickers) if len(dividend_list) > 0 else 'N/A'}")
    print("\n--- 'Hidden Gem' (V5): ถูกสุดๆ (กราฟอาจจะพัง) ---")
    print(f"   -> พบ {len(deep_value_list)} ตัว: {', '.join(value_tickers) if len(deep_value_list) > 0 else 'N/A'}")

end_time = time.time()
print(f"\n--- ใช้เวลาทั้งหมด: {end_time - start_time:.2f} วินาที ---")