import yfinance as yf
import pandas as pd
import requests
import time 

start_time = time.time()

# ===================================================================
# 🌎 1. "จักรวาลหุ้น" ของคุณ (เหมือนเดิม)
# ===================================================================

MY_INTEREST_LIST = ["IONQ", "RGTI", "PLTR", "SOFI", "CRWD"]
TEST_RUN_LIST = ["LEN", "ADM", "HRL", "BEN", "AAPL", "MSFT"]

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
# 🧠 ส่วนที่ 2 (V5): "ฟังก์ชันนักวิเคราะห์" (แก้ชื่อคีย์แล้ว!)
# ===================================================================
def calculate_manual_metrics(ticker_symbol):
    """
    V5 - แก้ไขชื่อคีย์ตามผลลัพธ์จาก 'spy.py'
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        
        info = stock.info
        b_sheet = stock.balance_sheet
        i_sheet = stock.financials 
        
        # --- ตรวจสอบว่าโดนบล็อก (ได้ข้อมูลว่างเปล่า) หรือไม่ ---
        if info is None or len(info) <= 2: 
            print(f"    [!] Error: ไม่สามารถดึง '.info' ของ {ticker_symbol} (อาจถูกบล็อก)")
            return None
        if b_sheet.empty: 
            print(f"    [!] Error: ไม่สามารถดึง '.balance_sheet' ของ {ticker_symbol} (อาจถูกบล็อก)")
            return None
        if i_sheet.empty:
            print(f"    [!] Error: ไม่สามารถดึง '.financials' ของ {ticker_symbol} (อาจถูกบล็อก)")
            return None
        # ---------------------------------------------------

        b_sheet_latest = b_sheet.iloc[:, 0]
        i_sheet_latest = i_sheet.iloc[:, 0]

        price = info.get('currentPrice')
        shares_outstanding = info.get('sharesOutstanding')
        
        if price is None or shares_outstanding is None:
            print(f"    [!] ข้าม {ticker_symbol}: ไม่มี Price หรือ SharesOutstanding")
            return None

        # --- ❗️ V5-FIX ❗️ (ใช้ชื่อคีย์ที่ถูกต้องจาก 'spy.py') ---
        total_equity = b_sheet_latest.get('Stockholders Equity') 
        if total_equity is None: 
            print(f"    [!] ข้าม {ticker_symbol}: (V5) ไม่มี 'Stockholders Equity'")
            return None 

        net_income = i_sheet_latest.get('Net Income')
        if net_income is None or net_income <= 0: 
            print(f"    [!] ข้าม {ticker_symbol}: ไม่มี 'Net Income' หรือ ขาดทุน")
            return None 
        
        total_debt = b_sheet_latest.get('Total Debt', 0) 
        
        # --- ❗️ V5-FIX ❗️ (ใช้ชื่อคีย์ที่ถูกต้องจาก 'spy.py') ---
        current_assets = b_sheet_latest.get('Current Assets')
        current_liabilities = b_sheet_latest.get('Current Liabilities')
        
        if current_assets is None or current_liabilities is None: 
            print(f"    [!] ข้าม {ticker_symbol}: (V5) ไม่มี 'Current Assets/Liabilities'")
            return None
        # ---------------------------------------------------------
        
        # (คำนวณ)
        book_value_per_share = total_equity / shares_outstanding
        pb_ratio = price / book_value_per_share
        eps = net_income / shares_outstanding
        pe_ratio = price / eps
        de_ratio_pct = (total_debt / total_equity) * 100 
        current_ratio = current_assets / current_liabilities
        dividend_per_share = info.get('trailingAnnualDividendRate', 0) 
        
        # (ป้องกัน Error หารด้วย 0 ถ้า Price ไม่มี)
        if price == 0: return None
        dividend_yield_pct = (dividend_per_share / price) 
        
        return {
            'Ticker': ticker_symbol, 'Name': info.get('shortName', ticker_symbol), 
            'Sector': info.get('sector', 'N/A'),
            'PE': pe_ratio, 'PB': pb_ratio, 'DE_pct': de_ratio_pct,
            'CurrentRatio': current_ratio, 'DivYield_pct': dividend_yield_pct
        }

    except Exception as e:
        print(f"    [!] Error (Exception) วิเคราะห์ {ticker_symbol}: {e}") 
        return None

# ===================================================================
# 📥 ส่วนที่ 3 (Fetcher): V5 - (มี time.sleep)
# ===================================================================
print(f"\n--- 2. เริ่มดึงข้อมูลและคำนวณ (V5 - Final Version) ---")

all_stock_data = [] 

for i, ticker in enumerate(combined_list):
    print(f"  ({i+1}/{len(combined_list)}) ...วิเคราะห์ {ticker}")
    metrics = calculate_manual_metrics(ticker)
    
    if metrics is not None:
        all_stock_data.append(metrics)
        
    # --- หน่วงเวลา 1 วินาที (สำคัญมาก) ---
    time.sleep(1) 
    # ------------------------------------

print(f"\n--- 🎉 ดึงข้อมูลเสร็จสิ้น! (วิเคราะห์สำเร็จ {len(all_stock_data)} ตัว) ---")


# ===================================================================
# 🔎 ส่วนที่ 4 (Analyzer): "Deep Value" (เหมือนเดิม)
# ===================================================================
print("\n--- 3. เริ่มคัดกรอง (Screener) ด้วยข้อมูล 'V5' ที่แม่นยำ ---")

RULES_DEEP_VALUE = {
    'MAX_PE': 15.0,
    'MAX_PB': 1.5,
    'MAX_DEBT_EQUITY': 50.0, 
    'MIN_CURRENT_RATIO': 2.0,
    'MIN_DIVIDEND_YIELD': 0.02 
}
print(f"กฎที่ใช้: P/E < 15, P/B < 1.5, D/E < 50%, CR > 2.0, Div > 2%")

deep_value_list = [] 

for stock in all_stock_data:
    if (stock['PE'] < RULES_DEEP_VALUE['MAX_PE'] and
        stock['PB'] < RULES_DEEP_VALUE['MAX_PB'] and
        stock['DE_pct'] < RULES_DEEP_VALUE['MAX_DEBT_EQUITY'] and
        stock['CurrentRatio'] > RULES_DEEP_VALUE['MIN_CURRENT_RATIO'] and
        stock['DivYield_pct'] > RULES_DEEP_VALUE['MIN_DIVIDEND_YIELD']):
            
        deep_value_list.append(stock)

# ===================================================================
# 📋 ส่วนที่ 5: สรุปผล (เหมือนเดิม)
# ===================================================================
print("\n=========================================================")
print(f"💎 สรุปผลการคัดกรอง 'Deep Value V5' (ข้อมูลแม่นยำ):")
print(f"พบหุ้นที่ผ่านเกณฑ์ 'ส่วนต่างแห่งความปลอดภัย' ทั้งหมด {len(deep_value_list)} ตัว")
print("=========================================================")

if len(deep_value_list) == 0:
    print("ไม่พบหุ้นที่ผ่านเกณฑ์ (นี่เป็นเรื่องปกติ! หุ้น 'Deep Value' หายากมาก)")
else:
    for stock in deep_value_list:
        print(f"\n✅ {stock['Ticker']} ({stock['Name']})")
        print(f"   Sector: {stock['Sector']}")
        print(f"   P/E: {stock['PE']:.2f} (กฎ: < 15)")
        print(f"   P/B: {stock['PB']:.2f} (กฎ: < 1.5)")
        print(f"   D/E: {stock['DE_pct']:.2f}% (กฎ: < 50%)")
        print(f"   Current Ratio: {stock['CurrentRatio']:.2f} (กฎ: > 2.0)")
        print(f"   Dividend: {stock['DivYield_pct']*100:.2f}% (กฎ: > 2%)") 

end_time = time.time()
print(f"\n--- ใช้เวลาทั้งหมด: {end_time - start_time:.2f} วินาที ---")