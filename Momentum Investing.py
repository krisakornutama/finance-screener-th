import yfinance as yf
import pandas as pd
import requests
import time 

start_time = time.time()

# ===================================================================
# 🌎 1. "จักรวาลหุ้น" ของคุณ (เปลี่ยน Test Run!)
# ===================================================================

MY_INTEREST_LIST = ["IONQ", "RGTI", "PLTR", "SOFI", "CRWD"]
# (เปลี่ยน Test Run ไปดูหุ้นหลากหลาย - Growth, Value, Dividend)
TEST_RUN_LIST = ["NVDA", "HRL", "T", "AAPL", "FSLR", "IONQ"] 

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
# 🧠 ส่วนที่ 2 (V9): "ฟังก์ชันนักวิเคราะห์" (ง่ายและเร็ว!)
# ===================================================================
def calculate_momentum_metrics(ticker_symbol):
    """
    V9 - ไม่ต้องดึงงบการเงิน! ดึงแค่ .info
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info # <-- ดึงแค่ .info อย่างเดียว
        
        if info is None or len(info) <= 2:
            print(f"    [!] Error: .info ว่างเปล่า {ticker_symbol}")
            return None

        # --- ❗️ V9-UPDATE ❗️ ---
        price = info.get('currentPrice')
        sma_200 = info.get('twoHundredDayAverage')
        sma_50 = info.get('fiftyDayAverage')
        # -------------------------

        if price is None or sma_200 is None or sma_50 is None:
            print(f"    [!] ข้าม {ticker_symbol}: ไม่มีข้อมูล SMA")
            return None
        
        return {
            'Ticker': ticker_symbol, 'Name': info.get('shortName', ticker_symbol),
            'Sector': info.get('sector', 'N/A'),
            'Price': price,
            'SMA_200': sma_200,
            'SMA_50': sma_50
        }

    except Exception as e:
        print(f"    [!] Error (Exception) วิเคราะห์ {ticker_symbol}: {e}") 
        return None

# ===================================================================
# 📥 ส่วนที่ 3 (Fetcher): V9 - (เร็วกว่าเดิม!)
# ===================================================================
print(f"\n--- 2. เริ่มดึงข้อมูล (V9 - Momentum Version) ---")
print("...V9 นี้จะเร็วกว่า V5-V8 เพราะดึงแค่ .info...")

all_stock_data = [] 

for i, ticker in enumerate(combined_list):
    print(f"  ({i+1}/{len(combined_list)}) ...วิเคราะห์ {ticker}")
    metrics = calculate_momentum_metrics(ticker)
    
    if metrics is not None:
        all_stock_data.append(metrics)
        
    # --- ไม่ต้อง time.sleep(1) แล้ว! ---
    # (เพราะเรายิง API แค่ 1 call ต่อหุ้น)

print(f"\n--- 🎉 ดึงข้อมูลเสร็จสิ้น! (วิเคราะห์สำเร็จ {len(all_stock_data)} ตัว) ---")


# ===================================================================
# 🔎 ส่วนที่ 4 (Analyzer): "อัลกอริทึม Momentum"
# ===================================================================
print("\n--- 3. เริ่มคัดกรอง (Screener) ด้วยอัลกอริทึม 'Momentum' (V9) ---")

# --- 💡 นี่คือ "กฎ" ของ นักลงทุนสาย Momentum ---
# (เราไม่สร้าง RULES_MOMENTUM เพราะมันง่ายมาก)
print(f"กฎที่ใช้: Price > 200-Day SMA (เทรนด์ยาวขาขึ้น)")
print(f"กฎที่ใช้ (ต่อ): Price > 50-Day SMA (เทรนด์สั้นขาขึ้น)")

momentum_list = [] 

for stock in all_stock_data:
    if (stock['Price'] > stock['SMA_200'] and  # 1. เทรนด์ยาว
        stock['Price'] > stock['SMA_50']):   # 2. เทรนด์สั้น
            
        momentum_list.append(stock)

# ===================================================================
# 📋 ส่วนที่ 5: สรุปผล
# ===================================================================
print("\n=========================================================")
print(f"📈 สรุปผลการคัดกรอง 'Momentum' (V9):")
print(f"พบหุ้น 'กราฟขาขึ้น' (Uptrend) ทั้งหมด {len(momentum_list)} ตัว")
print("=========================================================")

if len(momentum_list) == 0:
    print("ไม่พบหุ้นที่ผ่านเกณฑ์ (ตลาดอาจกำลังเป็นขาลง!)")
else:
    for stock in momentum_list:
        print(f"\n✅ {stock['Ticker']} ({stock['Name']})")
        print(f"   Sector: {stock['Sector']}")
        print(f"   Price: {stock['Price']:.2f}")
        print(f"   SMA 200: {stock['SMA_200']:.2f} (สถานะ: ผ่าน)")
        print(f"   SMA 50: {stock['SMA_50']:.2f} (สถานะ: ผ่าน)")

end_time = time.time()
print(f"\n--- ใช้เวลาทั้งหมด: {end_time - start_time:.2f} วินาที ---")