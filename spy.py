import yfinance as yf

# --- เราจะส่องแค่ 1 ตัว (AAPL) เพื่อดูชื่อคีย์ ---
ticker_symbol = "AAPL"

print(f"--- 🕵️‍♂️ กำลังส่งสปายไปส่อง Ticker: {ticker_symbol} ---")

try:
    stock = yf.Ticker(ticker_symbol)

    # --- 1. ส่องงบดุล (Balance Sheet) ---
    b_sheet = stock.balance_sheet
    if b_sheet.empty:
        print("[!] ไม่สามารถดึง Balance Sheet (อาจโดนบล็อกชั่วคราว)")
    else:
        print("\n--- 🔑 คีย์ทั้งหมดใน งบดุล (Balance Sheet) ---")
        # .index คือ "ชื่อแถว" ทั้งหมด
        for key_name in b_sheet.index:
            print(f"  -> {key_name}")

    # --- 2. ส่องงบกำไรขาดทุน (Income Statement) ---
    i_sheet = stock.financials
    if i_sheet.empty:
        print("\n[!] ไม่สามารถดึง Income Statement (อาจโดนบล็อกชั่วคราว)")
    else:
        print("\n--- 🔑 คีย์ทั้งหมดใน งบกำไรขาดทุน (Income Statement) ---")
        # .index คือ "ชื่อแถว" ทั้งหมด
        for key_name in i_sheet.index:
            print(f"  -> {key_name}")

    print("\n--- ภารกิจสอดแนมเสร็จสิ้น ---")

except Exception as e:
    print(f"\n*** เกิด Error ร้ายแรง: {e} ***")