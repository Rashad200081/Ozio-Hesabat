import re
import io
import pandas as pd
import streamlit as st
from datetime import datetime

# Səhifə konfiqurasiyası
st.set_page_config(page_title="Sifariş Analizatoru", layout="wide")

# Arxa fon rəngi (Şəkildəki orijinal tünd bordo-albalı çəhrayı dinamik qradiyent)
custom_style = """
<style>
/* Dəqiq fon rəngləri: tünd bordo (#2b0014) -> albalı-qırmızı (#8d003a) -> çəhrayı-bordo (#d8005f) */
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

/* Yuxarı Loqo konteyneri */
.header-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 25px;
}

/* Ozio Loqosu (80px) */
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

/* Titul və alt mətnlərin rəngi */
h1, p, label {
    color: #ffffff !important;
}

/* Mətn daxiletmə sahəsi (ağ fonda) */
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

/* "Başla" düyməsinin stili (Xana ağ, mətn TAM QARA) */
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

div.stButton > button:hover p {
    color: #000000 !important;
}
</style>
"""
st.markdown(custom_style, unsafe_allow_html=True)

# Yalnız mərkəzdə Ozio Loqosu
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
    blocks = re.split(r'(?=Sifariş\s*#)', text)
    parsed_data = []
    
    for block in blocks:
        if not block.strip():
            continue
            
        order_match = re.search(r'Sifariş\s*#(\d+)', block)
        order_id = f"#{order_match.group(1)}" if order_match else ""
        
        lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
