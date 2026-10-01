import yfinance as yf
import ta  # <-- ใช้ ta แทน pandas_ta
import pandas as pd
import time 

start_time = time.time()

# ===================================================================
# 🌎 1. "กลุ่มเป้าหมาย" (จากผลลัพธ์ V11 ของคุณ!)
# ===================================================================
HOLY_GRAIL_LIST = [
    "LRCX", "HOOD", "APH", "EQT", "MU", "DDOG", "NVDA", "WELL", "AMD", "BG", "PLTR", "FSLR", "CTRA"
]

print(f"--- 🚀 เริ่ม V12 'Trade Finder' ---")
print(f"กำลังสแกน 'Holy Grail' 13 ตัว ด้วย RSI และ Volume...")


# ===================================================================
# 🧠 ส่วนที่ 2 (V12): "ฟังก์ชันนักวิเคราะห์" (Pro Signal)
# ===================================================================
def calculate_pro_signals(ticker_symbol):
    """
    V12 - ดึงข้อมูลย้อนหลัง (History) เพื่อคำนวณ RSI และ Volume
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # ดึงข้อมูลย้อนหลัง 1 ปี
        hist = stock.history(period="1y") 
        
        if hist.empty:
            print(f"    [!] Error: ไม่สามารถดึง .history ของ {ticker_symbol}")
            return None

        # --- 1. คำนวณ RSI (ด้วย 'ta') ---
        # ใช้ ta.momentum.RSIIndicator แทน
        rsi_indicator = ta.momentum.RSIIndicator(close=hist['Close'], window=14)
        hist['RSI_14'] = rsi_indicator.rsi()
        latest_rsi = hist.iloc[-1]['RSI_14']

        # --- 2. คำนวณ Volume (ด้วย 'ta') ---
        # ใช้ ta.trend.SMAIndicator สำหรับ Volume
        volume_sma = ta.trend.SMAIndicator(close=hist['Volume'], window=20)
        hist['VOLUME_SMA_20'] = volume_sma.sma_indicator()
        
        latest_volume = hist.iloc[-1]['Volume']
        avg_volume = hist.iloc[-1]['VOLUME_SMA_20']
        
        return {
            'Ticker': ticker_symbol,
            'Latest_RSI_14': latest_rsi,
            'Latest_Volume': latest_volume,
            'Avg_Volume_20': avg_volume
        }

    except Exception as e:
        print(f"    [!] Error (Exception) วิเคราะห์ {ticker_symbol}: {e}") 
        return None

# ===================================================================
# 📥 ส่วนที่ 3 (Fetcher): V12 - (สแกน 13 ตัว)
# ===================================================================
all_stock_data = [] 

for i, ticker in enumerate(HOLY_GRAIL_LIST):
    print(f"  ({i+1}/{len(HOLY_GRAIL_LIST)}) ...สแกน {ticker}")
    metrics = calculate_pro_signals(ticker)
    
    if metrics is not None:
        all_stock_data.append(metrics)
        
    time.sleep(1) 

print(f"\n--- 🎉 ดึงข้อมูลเสร็จสิ้น! (วิเคราะห์สำเร็จ {len(all_stock_data)} ตัว) ---")


# ===================================================================
# 🔎 ส่วนที่ 4 (Analyzer): "คัดกรองสัญญาณซื้อ (Buy Signal)"
# ===================================================================
print("\n--- 3. เริ่มคัดกรอง (Screener) ด้วย 'Pro Signals' (V12) ---")

RULES_PRO_MOMENTUM = {
    'MIN_RSI': 50.0,
    'MIN_VOLUME_MULT': 1.0
}
print(f"กฎที่ใช้: RSI(14) > {RULES_PRO_MOMENTUM['MIN_RSI']}")
print(f"กฎที่ใช้ (ต่อ): Volume > (Volume SMA20 x {RULES_PRO_MOMENTUM['MIN_VOLUME_MULT']})")

trade_list = [] 

for stock in all_stock_data:
    rsi = stock['Latest_RSI_14']
    vol = stock['Latest_Volume']
    avg_vol = stock['Avg_Volume_20']

    if (rsi > RULES_PRO_MOMENTUM['MIN_RSI'] and
        vol > (avg_vol * RULES_PRO_MOMENTUM['MIN_VOLUME_MULT'])):
            
        trade_list.append(stock)

# ===================================================================
# 📋 ส่วนที่ 5: สรุปผล (V12)
# ===================================================================
print("\n=========================================================")
print(f"🎯 สรุปผลการคัดกรอง 'Trade Finder' (V12):")
print(f"(จาก 13 หุ้น 'Holy Grail')")
print(f"พบหุ้น 'สัญญาณแรง' (RSI+Volume) ทั้งหมด {len(trade_list)} ตัว")
print("=========================================================")

if len(trade_list) == 0:
    print("ไม่พบหุ้นที่ผ่านเกณฑ์ (หุ้น 13 ตัวอาจกำลัง 'พักตัว' หรือ 'ขึ้นแบบไม่มี Volume')")
else:
    for stock in trade_list:
        print(f"\n✅ {stock['Ticker']}")
        print(f"   RSI(14): {stock['Latest_RSI_14']:.2f} (กฎ: > {RULES_PRO_MOMENTUM['MIN_RSI']})")
        print(f"   Volume: {stock['Latest_Volume']:.0f}")
        print(f"   Avg Volume: {stock['Avg_Volume_20']:.0f} (สถานะ: ผ่าน)")

end_time = time.time()
print(f"\n--- ใช้เวลาทั้งหมด: {end_time - start_time:.2f} วินาที ---")