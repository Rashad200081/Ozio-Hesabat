import re
import io
import pandas as pd
import streamlit as st
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="Sifariş Analizatoru", layout="centered")

st.title("📦 Kuryer Sifarişləri - Excel Çevirici")
st.write("Sifariş mətnini aşağıdakı sahəyə yapışdırın və avtomatik olaraq Excel cədvəli yaradın.")

raw_text = st.text_area("Sifariş mətnini bura yapışdırın:", height=250, placeholder="Sifariş #59478\nMegastore Həzi Aslanov\n...")

def parse_orders(text):
    blocks = re.split(r'(?=Sifariş\s*#)', text)
    parsed_data = []
    
    for block in blocks:
        if not block.strip():
            continue
            
        order_match = re.search(r'Sifariş\s*#(\d+)', block)
        order_id = int(order_match.group(1)) if order_match else ""
        
        lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
        
        store = ""
        courier_id = ""
        courier_name = ""
        created = "-"
        courier_accept = "-"
        store_ready = "-"
        delivered = "-"
        amount = 0.0
        
        for i, line in enumerate(lines):
            if i == 1 and "Kurye" not in line and "Yaradılıb" not in line:
                store = line
                
            if "Kurye #" in line:
                c_match = re.search(r'Kurye\s*#(\d+)\s*[·•-]\s*(.+)', line)
                if c_match:
                    courier_id = int(c_match.group(1))
                    courier_name = c_match.group(2).strip()
            
            if "Yaradılıb" in line:
                m = re.search(r':\s*(.+)', line)
                if m: created = m.group(1).strip()
            if "Kurye qəbul" in line:
                m = re.search(r':\s*(.+)', line)
                if m: courier_accept = m.group(1).strip()
            if "Mağaza hazır" in line:
                m = re.search(r':\s*(.+)', line)
                if m: store_ready = m.group(1).strip()
            if "Çatdırılıb" in line:
                m = re.search(r':\s*(.+)', line)
                if m: delivered = m.group(1).strip()
                
            if "₼" in line:
                amt_match = re.search(r'([\d\.]+)', line)
                if amt_match:
                    amount = float(amt_match.group(1))
                    
        parsed_data.append({
            "Sifariş #": order_id,
            "Mağaza": store,
            "Kurye İD": courier_id,
            "Kurye Adı": courier_name,
            "Yaradılıb (Mağaza)": created,
            "Kurye Qəbul": courier_accept,
            "Mağaza Hazır": store_ready,
            "Çatdırılıb": delivered,
            "Məbləğ (₼)": amount
        })
        
    return pd.DataFrame(parsed_data)

if st.button("Excel Faylı Yarad", type="primary"):
    if not raw_text.strip():
        st.warning("Zəhmət olmasa mətn daxil edin!")
    else:
        df = parse_orders(raw_text)
        
        if df.empty:
            st.error("Mətndə heç bir sifariş tapılmadı. Formatı yoxlayın.")
        else:
            st.success(f"Ümumi {len(df)} sifariş tapıldı!")
            st.dataframe(df)
            
            output = io.BytesIO()
            wb = pd.ExcelWriter(output, engine='openpyxl')
            df.to_excel(wb, index=False, sheet_name='Sifariş Hesabatı')
            wb.close()
            processed_data = output.getvalue()
            
            st.download_button(
                label="📥 Excel Faylını Endir (.xlsx)",
                data=processed_data,
                file_name="sifaris_hesabati.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
