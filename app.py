import re
import io
import pandas as pd
import streamlit as st
from datetime import datetime
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Səhifə konfiqurasiyası
st.set_page_config(page_title="Sifariş Analizatoru", layout="wide")

# Arxa fon rəngi (Şəkildəki orijinal tünd bordo-albalı çəhrayı dinamik qradiyent)
custom_style = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(145deg, #2a0013 0%, #70002d 45%, #b9004b 75%, #e60064 100%);
    background-attachment: fixed;
    color: #ffffff;
}
[data-testid="stAppViewContainer"] > .main {
    padding-top: 20px;
}
[data-testid="stHeader"] {
    background-color: rgba(0,0,0,0);
}

.header-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 25px;
}

.ozio-logo-badge {
    background-color: #ffffff;
    color: #d8005f;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 80px;
    font-weight: 900;
    padding: 6px 45px;
    border-radius: 18px;
    letter-spacing: 1px;
    box-shadow: 0px 8px 25px rgba(0, 0, 0, 0.4);
    display: inline-block;
}
.ozio-logo-badge span {
    font-size: 55px;
    vertical-align: super;
}

h1, p, label {
    color: #ffffff !important;
}

textarea {
    background-color: #ffffff !important;
    color: #12121f !important;
    border: 2px solid rgba(255, 255, 255, 0.8) !important;
    border-radius: 12px !important;
    font-size: 15px !important;
}
textarea::placeholder {
    color: #777777 !important;
}

div.stButton > button, 
div.stButton > button:link, 
div.stButton > button:visited {
    background-color: #ffffff !important;
    border: none !important;
    box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.3) !important;
    border-radius: 10px !important;
    padding: 12px 36px !important;
}

div.stButton > button p,
div.stButton > button div,
div.stButton > button span {
    color: #000000 !important;
    font-weight: 900 !important;
    font-size: 18px !important;
}

div.stButton > button:hover {
    background-color: #f0f0f0 !important;
    transform: scale(1.02);
}
</style>
"""
st.markdown(custom_style, unsafe_allow_html=True)

header_html = """
<div class="header-container">
    <div class="ozio-logo-badge">ozio<span>+</span></div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

st.title("📦 Ozio Sifarişləri - Hesabat Analizatoru")
st.write("Sifarişlərin mətnini aşağıdakı sahəyə yapışdırın və avtomatik Excel cədvəli yaradın.")

raw_text = st.text_area("Sifarişlərin məlumatlarını bura yapışdırın:", height=250, placeholder="Sifariş #59478\nBolmart Təzə bazar\n...")

def extract_time_str(time_str):
    if not time_str or time_str in ["-", "—"]:
        return "—"
    clean_str = str(time_str).replace('.', ':')
    match = re.search(r'(\d{1,2}:\d{2})', clean_str)
    if match:
        return match.group(1)
    return "—"

def parse_time_obj(time_clean):
    if not time_clean or time_clean == "—":
        return None
    try:
        return datetime.strptime(time_clean, "%H:%M")
    except ValueError:
        return None

def parse_orders(text):
    order_positions = [m.start() for m in re.finditer(r'Sifariş\s*#\d+', text)]
    if not order_positions:
        return pd.DataFrame()

    blocks = []
    for i in range(len(order_positions)):
        start = order_positions[i]
        end = order_positions[i+1] if i+1 < len(order_positions) else len(text)
        blocks.append(text[start:end])

    parsed_data = []
    
    for block in blocks:
        if not block.strip():
            continue
            
        order_match = re.search(r'Sifariş\s*#(\d+)', block)
        order_id = f"#{order_match.group(1)}" if order_match else ""
        
        lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
        
        store = ""
        created_raw = "—"
        accept_raw = "—"
        ready_raw = "—"
        delivered_raw = "—"
        is_cancelled = False
        
        for i, line in enumerate(lines):
            if i == 1 and "Kurye" not in line and "Yaradılıb" not in line:
                store = line
                
            if "Yaradılıb" in line:
                m = re.search(r':\s*(.+)', line)
                if m: created_raw = m.group(1).strip()
            if "Kurye qəbul" in line:
                m = re.search(r':\s*(.+)', line)
                if m: accept_raw = m.group(1).strip()
            if "Mağaza hazır" in line:
                m = re.search(r':\s*(.+)', line)
                if m: ready_raw = m.group(1).strip()
            if "Çatdırılıb" in line:
                m = re.search(r':\s*(.+)', line)
                if m: delivered_raw = m.group(1).strip()
            if "Ləğv" in line or "ləğv" in line.lower() or "cancell" in line.lower():
                is_cancelled = True

        created_clean = extract_time_str(created_raw)
        
        end_raw = "—"
        for candidate in [delivered_raw, ready_raw, accept_raw]:
            if candidate != "—":
                end_raw = candidate
                break
        
        end_clean = extract_time_str(end_raw)
        
        created_dt = parse_time_obj(created_clean)
        end_dt = parse_time_obj(end_clean)
        
        diff_minutes = "—"
        status = "Normal"
        
        if is_cancelled or delivered_raw == "—":
            status = "Ləğv"
            end_clean = "—"
        elif created_dt and end_dt:
            if end_dt < created_dt:
                diff = (end_dt - created_dt).seconds // 60
            else:
                diff = int((end_dt - created_dt).total_seconds() // 60)
            
            diff_minutes = diff
            
            store_lower = store.lower()
            if "təzə bazar" in store_lower or "teze bazar" in store_lower:
                if diff > 60:
                    status = "Gecikmə"
                else:
                    status = "Normal"
            else:
                if diff > 45:
                    status = "Gecikmə"
                else:
                    status = "Normal"

        parsed_data.append({
            "Mağaza": store,
            "Sifariş ID": order_id,
            "Yaradılıb": created_clean,
            "Çatdırılıb": end_clean,
            "Fərq": diff_minutes,
            "Status": status
        })
        
    df = pd.DataFrame(parsed_data)
    
    if not df.empty:
        def get_store_priority(store_name):
            name = str(store_name).lower()
            if "təzə bazar" in name or "teze bazar" in name:
                return 1
            elif "salamzadə" in name or "salamzade" in name:
                return 2
            elif "mir cəlal" in name or "mir celal" in name:
                return 3
            else:
                return 4

        df['Priority'] = df['Mağaza'].apply(get_store_priority)
        df = df.sort_values(by=['Priority', 'Mağaza']).drop(columns=['Priority'])
        
    return df

def generate_styled_excel(df):
    wb = openpyxl.Workbook()
