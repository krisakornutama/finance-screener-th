import yfinance as yf
import pandas as pd
import requests
import time 

start_time = time.time()

# ===================================================================
# 🌎 1. "จักรวาลหุ้น" ของคุณ (เหมือนเดิม)
# ===================================================================

MY_INTEREST_LIST = ["IONQ", "RGTI", "PLTR", "SOFI", "CRWD"]
# (เปลี่ยน Test Run ไปหาหุ้นปันผล)
TEST_RUN_LIST = ["HRL", "AAPL", "T", "VZ", "KO", "NEE"] # (T, VZ, KO คือหุ้นปันผล)

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
# 🧠 ส่วนที่ 2 (V7): "ฟังก์ชันนักวิเคราะห์" (เพิ่ม 'Payout Ratio')
# ===================================================================
def calculate_manual_metrics(ticker_symbol):
    """
    V7 - คำนวณ Payout Ratio เอง
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
            print(f"    [!] ข้าม {ticker_symbol}: ไม่มี Price หรือ SharesOutstanding")
            return None

        # (V5) คำนวณเอง
        total_equity = b_sheet_latest.get('Stockholders Equity') 
        net_income = i_sheet_latest.get('Net Income')
        total_debt = b_sheet_latest.get('Total Debt', 0) 
        
        if total_equity is None or net_income is None: 
            print(f"    [!] ข้าม {ticker_symbol}: ไม่มี Equity/Net Income")
            return None 
        if net_income <= 0:
            print(f"    [!] ข้าม {ticker_symbol}: ขาดทุน (Net Income <= 0)")
            return None
        
        # --- ❗️ V7-UPDATE ❗️ (คำนวณ Payout Ratio) ---
        eps = net_income / shares_outstanding
        dividend_per_share = info.get('trailingAnnualDividendRate', 0) 
        
        if price == 0: return None
        dividend_yield_pct = (dividend_per_share / price) 
        
        payout_ratio = dividend_per_share / eps # (ปันผล / กำไร)
        # -----------------------------------------------
        
        de_ratio_pct = (total_debt / total_equity) * 100 
        
        return {
            'Ticker': ticker_symbol, 'Name': info.get('shortName', ticker_symbol), 
            'Sector': info.get('sector', 'N/A'),
            'DE_pct': de_ratio_pct,
            'DivYield_pct': dividend_yield_pct, # <-- เรามีค่านี้จาก V5
            'PayoutRatio': payout_ratio      # <-- เพิ่มค่าใหม่
        }

    except Exception as e:
        print(f"    [!] Error (Exception) วิเคราะห์ {ticker_symbol}: {e}") 
        return None

# ===================================================================
# 📥 ส่วนที่ 3 (Fetcher): V7 - (มี time.sleep)
# ===================================================================
print(f"\n--- 2. เริ่มดึงข้อมูลและคำนวณ (V7 - Dividend Version) ---")

all_stock_data = [] 

for i, ticker in enumerate(combined_list):
    print(f"  ({i+1}/{len(combined_list)}) ...วิเคราะห์ {ticker}")
    metrics = calculate_manual_metrics(ticker)
    
    if metrics is not None:
        all_stock_data.append(metrics)
        
    time.sleep(1) # (ยังคงสำคัญมาก)

print(f"\n--- 🎉 ดึงข้อมูลเสร็จสิ้น! (วิเคราะห์สำเร็จ {len(all_stock_data)} ตัว) ---")


# ===================================================================
# 🔎 ส่วนที่ 4 (Analyzer): "อัลกอริทึมเน้นปันผล"
# ===================================================================
print("\n--- 3. เริ่มคัดกรอง (Screener) ด้วยอัลกอริทึม 'Dividend Yield' (V7) ---")

# --- 💡 นี่คือ "กฎ" ของ นักลงทุนเน้นปันผล ---
RULES_DIVIDEND = {
    # 1. กฎ "ผลตอบแทน" (Yield)
    'MIN_DIVIDEND_YIELD': 0.04,  # ต้องปันผลสูงกว่า 4%
    
    # 2. กฎ "ความยั่งยืน" (Sustainability)
    'MAX_PAYOUT_RATIO': 0.70,  # ต้องจ่ายไม่เกิน 70% ของกำไร
    'MIN_PAYOUT_RATIO': 0.01,  # (ต้องจ่ายจริง)
    
    # 3. กฎ "ความปลอดภัย" (Safety)
    'MAX_DEBT_EQUITY': 150.0 # ผ่อนคลายเรื่องหนี้ แต่ไม่มากเกินไป
}
print(f"กฎที่ใช้: Div Yield > {RULES_DIVIDEND['MIN_DIVIDEND_YIELD']*100}%, Payout < {RULES_DIVIDEND['MAX_PAYOUT_RATIO']*100}%, D/E < {RULES_DIVIDEND['MAX_DEBT_EQUITY']}%")

dividend_list = [] 

for stock in all_stock_data:
    div = stock['DivYield_pct']
    payout = stock['PayoutRatio']
    de = stock['DE_pct']

    if (div > RULES_DIVIDEND['MIN_DIVIDEND_YIELD'] and      # 1. ปันผล > 4%
        payout < RULES_DIVIDEND['MAX_PAYOUT_RATIO'] and  # 2. จ่ายไหว (< 70%)
        payout > RULES_DIVIDEND['MIN_PAYOUT_RATIO'] and  # 3. จ่ายจริง (> 0)
        de < RULES_DIVIDEND['MAX_DEBT_EQUITY']):       # 4. หนี้ไม่สูง (< 150%)
            
        dividend_list.append(stock)

# ===================================================================
# 📋 ส่วนที่ 5: สรุปผล
# ===================================================================
print("\n=========================================================")
print(f"💰 สรุปผลการคัดกรอง 'Dividend Investing' (V7):")
print(f"พบหุ้น 'ปันผลสูงและยั่งยืน' ทั้งหมด {len(dividend_list)} ตัว")
print("=========================================================")

if len(dividend_list) == 0:
    print("ไม่พบหุ้นที่ผ่านเกณฑ์")
else:
    for stock in dividend_list:
        print(f"\n✅ {stock['Ticker']} ({stock['Name']})")
        print(f"   Sector: {stock['Sector']}")
        print(f"   Dividend Yield: {stock['DivYield_pct']*100:.2f}% (กฎ: > {RULES_DIVIDEND['MIN_DIVIDEND_YIELD']*100}%)")
        print(f"   Payout Ratio: {stock['PayoutRatio']*100:.2f}% (กฎ: < {RULES_DIVIDEND['MAX_PAYOUT_RATIO']*100}%)")
        print(f"   D/E: {stock['DE_pct']:.2f}% (กฎ: < {RULES_DIVIDEND['MAX_DEBT_EQUITY']}%)")

end_time = time.time()
print(f"\n--- ใช้เวลาทั้งหมด: {end_time - start_time:.2f} วินาที ---")