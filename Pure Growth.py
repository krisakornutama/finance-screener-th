import yfinance as yf
import pandas as pd
import requests
import time 

start_time = time.time()

# ===================================================================
# 🌎 1. "จักรวาลหุ้น" ของคุณ (เหมือนเดิม)
# ===================================================================

MY_INTEREST_LIST = ["IONQ", "RGTI", "PLTR", "SOFI", "CRWD"]
TEST_RUN_LIST = ["NVDA", "TSLA", "PLTR", "SOFI", "CRWD", "IONQ"] 

# --- 💡 ตั้งค่าตรงนี้ ---
RUN_FULL_SCAN = True # (ยังคงใช้ Test Run)
# ---------------------

tickers_list = []
if RUN_FULL_SCAN:
    # (ส่วนนี้เหมือนเดิม)
    print("--- 1. [Full Scan] กำลังดึงรายชื่อหุ้น S&P 500... ---")
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
        combined_list = TEST_RUN_LIST
else:
    print("--- 1. [Test Run] ใช้รายชื่อหุ้นทดสอบ... ---")
    combined_list = TEST_RUN_LIST

print(f"--- 💡 หุ้นทั้งหมดที่จะตรวจสอบ: {len(combined_list)} ตัว ---")


# ===================================================================
# 🧠 ส่วนที่ 2 (V8): "ฟังก์ชันนักวิเคราะห์" (เหมือนเดิม)
# ===================================================================
def calculate_manual_metrics(ticker_symbol):
    """
    V8 - ดึง 'revenueGrowth' และ 'PE' จาก .info 
    (Growth ไม่สน P/B แต่สนว่า "มีกำไร" หรือยัง)
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

        revenue_growth = info.get('revenueGrowth')
        pe_ratio = info.get('trailingPE')

        total_equity = b_sheet_latest.get('Stockholders Equity') 
        total_debt = b_sheet_latest.get('Total Debt', 0) 
        
        if total_equity is None: 
            print(f"    [!] ข้าม {ticker_symbol}: ไม่มี Equity")
            return None 

        de_ratio_pct = (total_debt / total_equity) * 100 
        
        return {
            'Ticker': ticker_symbol, 'Name': info.get('shortName', ticker_symbol), 
            'Sector': info.get('sector', 'N/A'),
            'DE_pct': de_ratio_pct,
            'RevenueGrowth': revenue_growth,
            'PE': pe_ratio
        }

    except Exception as e:
        print(f"    [!] Error (Exception) วิเคราะห์ {ticker_symbol}: {e}") 
        return None

# ===================================================================
# 📥 ส่วนที่ 3 (Fetcher): V8 - (เหมือนเดิม)
# ===================================================================
print(f"\n--- 2. เริ่มดึงข้อมูลและคำนวณ (V8 - Pure Growth Version) ---")
all_stock_data = [] 
for i, ticker in enumerate(combined_list):
    print(f"  ({i+1}/{len(combined_list)}) ...วิเคราะห์ {ticker}")
    metrics = calculate_manual_metrics(ticker)
    
    if metrics is not None:
        all_stock_data.append(metrics)
    time.sleep(1) 
print(f"\n--- 🎉 ดึงข้อมูลเสร็จสิ้น! (วิเคราะห์สำเร็จ {len(all_stock_data)} ตัว) ---")


# ===================================================================
# 🔎 ส่วนที่ 4 (Analyzer): "อัลกอริทึม Pure Growth" (เหมือนเดิม)
# ===================================================================
print("\n--- 3. เริ่มคัดกรอง (Screener) ด้วยอัลกอริทึม 'Pure Growth' (V8) ---")
RULES_GROWTH = {
    'MIN_REVENUE_GROWTH': 0.25,  
    'MIN_PE_RATIO': 0.0, 
    'MAX_DEBT_EQUITY': 150.0 
}
print(f"กฎที่ใช้: Revenue Growth > {RULES_GROWTH['MIN_REVENUE_GROWTH']*100}%, P/E > 0, D/E < {RULES_GROWTH['MAX_DEBT_EQUITY']}%")

growth_list = [] 
for stock in all_stock_data:
    growth = stock.get('RevenueGrowth') or 0.0 
    pe = stock.get('PE') or -1.0
    de = stock['DE_pct']

    if (growth > RULES_GROWTH['MIN_REVENUE_GROWTH'] and
        pe > RULES_GROWTH['MIN_PE_RATIO'] and
        de < RULES_GROWTH['MAX_DEBT_EQUITY']):       
            
        growth_list.append(stock)

# ===================================================================
# 📋 ส่วนที่ 5: สรุปผล (V8.1 - แก้บั๊กแล้ว)
# ===================================================================
print("\n=========================================================")
print(f"🚀 สรุปผลการคัดกรอง 'Pure Growth' (V8.1):")
print(f"พบหุ้น 'โตเร็วและมีกำไร' ทั้งหมด {len(growth_list)} ตัว")
print("=========================================================")

if len(growth_list) == 0:
    print("ไม่พบหุ้นที่ผ่านเกณฑ์ (หุ้นที่โตเร็วมักจะ 'ขาดทุน' หรือ 'หนี้สูง')")
else:
    for stock in growth_list:
        print(f"\n✅ {stock['Ticker']} ({stock['Name']})")
        print(f"   Sector: {stock['Sector']}")
        print(f"   Revenue Growth: {stock['RevenueGrowth']*100:.2f}% (กฎ: > {RULES_GROWTH['MIN_REVENUE_GROWTH']*100}%)")
        print(f"   P/E: {stock['PE']:.2f} (กฎ: > 0)")
        
        # --- ❗️ V8.1-FIX ❗️ (ลบวรรคที่ผิดออก) ---
        print(f"   D/E: {stock['DE_pct']:.2f}% (กฎ: < {RULES_GROWTH['MAX_DEBT_EQUITY']}%)")
        # ---------------------------------------

end_time = time.time()
print(f"\n--- ใช้เวลาทั้งหมด: {end_time - start_time:.2f} วินาที ---")