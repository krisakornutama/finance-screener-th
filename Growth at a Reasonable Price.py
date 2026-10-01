import yfinance as yf
import pandas as pd
import requests
import time 

start_time = time.time()

# ===================================================================
# 🌎 1. "จักรวาลหุ้น" ของคุณ (เหมือนเดิม)
# ===================================================================

MY_INTEREST_LIST = ["IONQ", "RGTI", "PLTR", "SOFI", "CRWD"]
TEST_RUN_LIST = ["LEN", "ADM", "HRL", "BEN", "AAPL", "MSFT", "GOOGL", "NVDA"] # (เพิ่ม Tech เข้าไป)

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
# 🧠 ส่วนที่ 2 (V6): "ฟังก์ชันนักวิเคราะห์" (เพิ่ม 'PEG Ratio')
# ===================================================================
def calculate_manual_metrics(ticker_symbol):
    """
    V6 - ดึงค่า 'pegRatio' จาก .info เพิ่ม
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

        # --- (V5) คำนวณเอง (แม่นยำ) ---
        total_equity = b_sheet_latest.get('Stockholders Equity') 
        net_income = i_sheet_latest.get('Net Income')
        total_debt = b_sheet_latest.get('Total Debt', 0) 
        
        if total_equity is None or net_income is None: 
            print(f"    [!] ข้าม {ticker_symbol}: ไม่มี Equity/Net Income")
            return None 
        if net_income <= 0:
            print(f"    [!] ข้าม {ticker_symbol}: ขาดทุน (Net Income <= 0)")
            return None
        
        pe_ratio = price / (net_income / shares_outstanding)
        de_ratio_pct = (total_debt / total_equity) * 100 
        
        # --- ❗️ V6-UPDATE ❗️ (ดึง 'PEG Ratio' จาก .info) ---
        # เราเชื่อค่านี้ เพราะ "การเติบโต" (G) นิยามได้หลายแบบ
        # ให้ yfinance สรุปมาให้เลยง่ายกว่า
        peg_ratio = info.get('pegRatio')
        # --------------------------------------------------
        
        return {
            'Ticker': ticker_symbol, 'Name': info.get('shortName', ticker_symbol), 
            'Sector': info.get('sector', 'N/A'),
            'PE': pe_ratio, 
            'DE_pct': de_ratio_pct,
            'PEG_Ratio': peg_ratio # <-- เพิ่มค่าใหม่
        }

    except Exception as e:
        print(f"    [!] Error (Exception) วิเคราะห์ {ticker_symbol}: {e}") 
        return None

# ===================================================================
# 📥 ส่วนที่ 3 (Fetcher): V6 - (มี time.sleep)
# ===================================================================
print(f"\n--- 2. เริ่มดึงข้อมูลและคำนวณ (V6 - GARP Version) ---")

all_stock_data = [] 

for i, ticker in enumerate(combined_list):
    print(f"  ({i+1}/{len(combined_list)}) ...วิเคราะห์ {ticker}")
    metrics = calculate_manual_metrics(ticker)
    
    if metrics is not None:
        all_stock_data.append(metrics)
        
    time.sleep(1) # (ยังคงสำคัญมาก)

print(f"\n--- 🎉 ดึงข้อมูลเสร็จสิ้น! (วิเคราะห์สำเร็จ {len(all_stock_data)} ตัว) ---")


# ===================================================================
# 🔎 ส่วนที่ 4 (Analyzer): "อัลกอริทึม ปีเตอร์ ลินช์ (GARP)"
# ===================================================================
print("\n--- 3. เริ่มคัดกรอง (Screener) ด้วยอัลกอริทึม 'GARP' (V6) ---")

# --- 💡 นี่คือ "กฎ" ของ ปีเตอร์ ลินช์ (GARP) ---
RULES_GARP = {
    # 1. กฎ "ราคาที่สมเหตุสมผล" (Reasonable Price)
    'MAX_PEG_RATIO': 1.0,  # กฎทอง: ต้อง < 1.0 (โตเร็วกว่า P/E)
    'MIN_PEG_RATIO': 0.0,  # ต้องเป็นบวก (กำลังเติบโต)
    
    # 2. กฎ "คุณภาพ" (Quality)
    'MIN_PE_RATIO': 5.0,   # ต้องมีกำไร (ไม่เอา P/E 0-5)
    'MAX_PE_RATIO': 40.0,  # ไม่แพงเว่อร์ (ไม่เอา P/E 100+)
    'MAX_DEBT_EQUITY': 100.0 # ผ่อนคลายเรื่องหนี้ (จาก 50% เป็น 100%)
}
print(f"กฎที่ใช้: 0.0 < PEG < {RULES_GARP['MAX_PEG_RATIO']}, {RULES_GARP['MIN_PE_RATIO']} < P/E < {RULES_GARP['MAX_PE_RATIO']}, D/E < {RULES_GARP['MAX_DEBT_EQUITY']}%")

garp_list = [] 

for stock in all_stock_data:
    # --- ดึงค่า (ป้องกัน Error ถ้าไม่มี 'PEG_Ratio') ---
    peg = stock.get('PEG_Ratio') or float('inf') # ถ้าไม่มี PEG ให้ = 'แพง'
    pe = stock['PE']
    de = stock['DE_pct']

    if (peg > RULES_GARP['MIN_PEG_RATIO'] and      # 1. PEG > 0
        peg < RULES_GARP['MAX_PEG_RATIO'] and      # 2. PEG < 1.0
        pe > RULES_GARP['MIN_PE_RATIO'] and        # 3. P/E > 5
        pe < RULES_GARP['MAX_PE_RATIO'] and        # 4. P/E < 40
        de < RULES_GARP['MAX_DEBT_EQUITY']):       # 5. D/E < 100%
            
        garp_list.append(stock)

# ===================================================================
# 📋 ส่วนที่ 5: สรุปผล
# ===================================================================
print("\n=========================================================")
print(f"📈 สรุปผลการคัดกรอง 'GARP - Peter Lynch' (V6):")
print(f"พบหุ้น 'โตเร็ว ราคาเหมาะสม' ทั้งหมด {len(garp_list)} ตัว")
print("=========================================================")

if len(garp_list) == 0:
    print("ไม่พบหุ้นที่ผ่านเกณฑ์ (ตลาดอาจไม่มีหุ้น GARP ที่เข้าเกณฑ์นี้เลย)")
else:
    for stock in garp_list:
        print(f"\n✅ {stock['Ticker']} ({stock['Name']})")
        print(f"   Sector: {stock['Sector']}")
        print(f"   PEG Ratio: {stock['PEG_Ratio']:.2f} (กฎ: < {RULES_GARP['MAX_PEG_RATIO']})")
        print(f"   P/E: {stock['PE']:.2f} (กฎ: {RULES_GARP['MIN_PE_RATIO']}-{RULES_GARP['MAX_PE_RATIO']})")
        print(f"   D/E: {stock['DE_pct']:.2f}% (กฎ: < {RULES_GARP['MAX_DEBT_EQUITY']}%)")

end_time = time.time()
print(f"\n--- ใช้เวลาทั้งหมด: {end_time - start_time:.2f} วินาที ---")