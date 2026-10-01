import yfinance as yf
import pandas as pd
import requests
import time

start_time = time.time()

# ===================================================================
# 🌎 1. "จักรวาลหุ้น" ของคุณ (ส่วนที่คุณกำหนดเอง)
# ===================================================================

MY_INTEREST_LIST = [
    "IONQ", "RGTI", "PLTR", "SOFI", "CRWD"
]

print("--- 1. กำลังดึงรายชื่อหุ้น S&P 500... ---")
sp500_list = []
try:
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    html_content = requests.get(url, headers=headers).text
    tables = pd.read_html(html_content)
    sp500_table = tables[0]
    sp500_list = sp500_table['Symbol'].str.replace('.', '-', regex=False).tolist()
    print(f"ดึง S&P 500 สำเร็จ: {len(sp500_list)} ตัว")

except Exception as e:
    print(f"*** ไม่สามารถดึงรายชื่อ S&P 500 ได้: {e} ***")
    sp500_list = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]

combined_list = list(set(sp500_list + MY_INTEREST_LIST))
print(f"--- 💡 หุ้นทั้งหมดที่จะตรวจสอบ: {len(combined_list)} ตัว ---")


# ===================================================================
# 📥 ส่วนที่ 1 (Fetcher): ดึงข้อมูล (เพิ่ม Current Ratio, Dividend)
# ===================================================================
print(f"\n--- 2. เริ่มดึงข้อมูลปัจจัยพื้นฐาน (นี่คือ 'ไฟล์ที่ 1') ---")

all_stock_data = [] # List ที่จะเก็บ "วัตถุดิบ"

for i, ticker in enumerate(combined_list):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        print(f"  ({i+1}/{len(combined_list)}) ...ดึง {ticker}")

        # เก็บข้อมูลที่ "จำเป็น" สำหรับการวิเคราะห์ (เพิ่ม 2 ตัว)
        stock_data = {
            'Ticker': ticker,
            'Name': info.get('shortName'),
            'Sector': info.get('sector'),
            'Price': info.get('currentPrice'),
            'ForwardPE': info.get('forwardPE'), 
            'PB': info.get('priceToBook'),
            'ROE': info.get('returnOnEquity'),
            'DE': info.get('debtToEquity'), 
            'CurrentRatio': info.get('currentRatio'), # <-- เพิ่มตัวที่ 1 (ความปลอดภัย)
            'DividendYield': info.get('dividendYield') # <-- เพิ่มตัวที่ 2 (ความสม่ำเสมอ)
        }
        all_stock_data.append(stock_data)

    except Exception as e:
        print(f"  *** เกิดข้อผิดพลาด/ไม่มีข้อมูลสำหรับ {ticker} (ข้าม) ***")

print(f"\n--- 🎉 ดึงข้อมูลเสร็จสิ้น! (ดึงสำเร็จ {len(all_stock_data)} ตัว) ---")


# ===================================================================
# 🔎 ส่วนที่ 2 (Analyzer): อัลกอริทึม "Deep Value"
# ===================================================================
print("\n--- 3. เริ่มคัดกรอง (Screener) ด้วยอัลกอริทึม 'Deep Value' ---")

# --- 💡 นี่คือ "กฎ" ของ เบนจามิน เกรแฮม (เข้มงวดสุดๆ) ---
RULES_DEEP_VALUE = {
    # 1. กฎด้าน "ราคา" (Price)
    'MAX_FORWARD_PE': 15.0,  # P/E คาดการณ์ ไม่เกิน 15
    'MAX_PB': 1.5,           # P/B ไม่เกิน 1.5
    
    # 2. กฎด้าน "ความปลอดภัย" (Safety)
    'MAX_DEBT_EQUITY': 50.0, # หนี้สินต่อทุน (D/E) ไม่เกิน 50% (คือ 0.5)
    'MIN_CURRENT_RATIO': 2.0,# อัตราส่วนทุนหมุนเวียน (Current Ratio) ต้อง > 2
                           # (สินทรัพย์หมุนเวียน > หนี้สินหมุนเวียน 2 เท่า = ปลอดภัยมาก)
    
    # 3. กฎด้าน "ความสม่ำเสมอ" (Stability)
    'MIN_DIVIDEND_YIELD': 0.02, # ต้องจ่ายปันผลอย่างน้อย 2% (คือ 0.02)
    'MIN_PE_GREATER_THAN': 0    # ต้องมีกำไร (P/E > 0)
}
print(f"กฎที่ใช้: P/E < {RULES_DEEP_VALUE['MAX_FORWARD_PE']}, P/B < {RULES_DEEP_VALUE['MAX_PB']}, D/E < {RULES_DEEP_VALUE['MAX_DEBT_EQUITY']}%")
print(f"กฎที่ใช้ (ต่อ): Current Ratio > {RULES_DEEP_VALUE['MIN_CURRENT_RATIO']}, Dividend > {RULES_DEEP_VALUE['MIN_DIVIDEND_YIELD']*100}%")

deep_value_list = [] # List ที่จะเก็บ "หุ้นเพชรแท้"

# วนลูปอ่านข้อมูลที่ดึงมา (all_stock_data)
for stock in all_stock_data:
    try:
        # --- ดึงค่าจาก "วัตถุดิบ" (ป้องกัน Error ถ้าไม่มีข้อมูล) ---
        pe = stock.get('ForwardPE') or float('inf') 
        pb = stock.get('PB') or float('inf')
        de = stock.get('DE') or float('inf')
        cr = stock.get('CurrentRatio') or 0.0 # ถ้าไม่มี Current Ratio, ให้เป็น 0 (ไม่ผ่าน)
        div = stock.get('DividendYield') or 0.0 # ถ้าไม่จ่ายปันผล, ให้เป็น 0 (ไม่ผ่าน)

        # --- ตรรกะการคัดกรอง (Deep Value) ---
        if (pe > RULES_DEEP_VALUE['MIN_PE_GREATER_THAN'] and # 1. ต้องมีกำไร
            pe < RULES_DEEP_VALUE['MAX_FORWARD_PE'] and      # 2. P/E < 15
            pb < RULES_DEEP_VALUE['MAX_PB'] and              # 3. P/B < 1.5
            de < RULES_DEEP_VALUE['MAX_DEBT_EQUITY'] and     # 4. D/E < 50%
            cr > RULES_DEEP_VALUE['MIN_CURRENT_RATIO'] and   # 5. Current Ratio > 2.0
            div > RULES_DEEP_VALUE['MIN_DIVIDEND_YIELD']):   # 6. Dividend > 2%
            
            # ถ้าผ่านทุกข้อ (โคตรยาก) -> เพิ่มเข้าไปใน List
            deep_value_list.append(stock)
            
    except Exception as e:
        print(f"เกิด Error ตอนวิเคราะห์ {stock['Ticker']}: {e}")


# ===================================================================
# 📋 ส่วนที่ 3: สรุปผล
# ===================================================================
print("\n=========================================================")
print(f"💎 สรุปผลการคัดกรอง 'Deep Value' (เต็มสูบ):")
print(f"พบหุ้นที่ผ่านเกณฑ์ 'ส่วนต่างแห่งความปลอดภัย' ทั้งหมด {len(deep_value_list)} ตัว")
print("=========================================================")

if len(deep_value_list) == 0:
    print("ไม่พบหุ้นที่ผ่านเกณฑ์ (นี่เป็นเรื่องปกติ! หุ้น 'Deep Value' หายากมาก)")
    print("ลองปรับกฎใน 'RULES_DEEP_VALUE' ให้ผ่อนคลายลงเล็กน้อย")
else:
    # พิมพ์ผลลัพธ์
    for stock in deep_value_list:
        print(f"\n✅ {stock['Ticker']} ({stock['Name']})")
        print(f"   Sector: {stock.get('Sector', 'N/A')}")
        print(f"   P/E (Fwd): {stock['ForwardPE']:.2f} (กฎ: < {RULES_DEEP_VALUE['MAX_FORWARD_PE']})")
        print(f"   P/B: {stock['PB']:.2f} (กฎ: < {RULES_DEEP_VALUE['MAX_PB']})")
        print(f"   D/E: {stock['DE']:.2f}% (กฎ: < {RULES_DEEP_VALUE['MAX_DEBT_EQUITY']}%)")
        print(f"   Current Ratio: {stock['CurrentRatio']:.2f} (กฎ: > {RULES_DEEP_VALUE['MIN_CURRENT_RATIO']})")
        print(f"   Dividend: {stock['DividendYield']*100:.2f}% (กฎ: > {RULES_DEEP_VALUE['MIN_DIVIDEND_YIELD']*100}%)")

# 4. สรุปเวลา
end_time = time.time()
print(f"\n--- ใช้เวลาทั้งหมด: {end_time - start_time:.2f} วินาที ---")