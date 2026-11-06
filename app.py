import re
import io
import pandas as pd
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Sifariş Analizatoru", layout="wide")

st.title("📦 Kuryer Sifarişləri - Gecikmə Analizatoru")
st.write("Sifariş mətnini aşağıdakı sahəyə yapışdırın və avtomatik Excel cədvəli yaradın.")

raw_text = st.text_area("Sifariş mətnini bura yapışdırın:", height=250, placeholder="Sifariş #59478\nBolmart Təzə bazar\n...")

def parse_time(time_str):
    """Mətndən saat:dəqiqə (HH:MM) vaxtını datetime obyekti kimi çıxarır"""
    if not time_str or time_str == "-":
        return None
    match = re.search(r'(\d{1,2}:\d{2})', time_str)
    if match:
        try:
            return datetime.strptime(match.group(1), "%H:%M")
        except ValueError:
            return None
    return None

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
        created_str = "-"
        delivered_str = "-"
        
        for i, line in enumerate(lines):
            if i == 1 and "Kurye" not in line and "Yaradılıb" not in line:
                store = line
                
            if "Yaradılıb" in line:
                m = re.search(r':\s*(.+)', line)
                if m: created_str = m.group(1).strip()
                
            if "Çatdırılıb" in line:
                m = re.search(r':\s*(.+)', line)
                if m: delivered_str = m.group(1).strip()
        
        # Vaxt fərqinin (dəqiqə ilə) hesablanması
        created_dt = parse_time(created_str)
        delivered_dt = parse_time(delivered_str)
        
        diff_minutes = ""
        status = "-"
        
        if created_dt and delivered_dt:
            if delivered_dt < created_dt:
                diff = (delivered_dt - created_dt).seconds // 60
            else:
                diff = int((delivered_dt - created_dt).total_seconds() // 60)
            
            diff_minutes = diff
            
            # Gecikmə qaydası: Təzə bazar > 60 dəq, Digərləri > 45 dəq
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
            "Yaradılıb": created_str,
            "Çatdırılıb": delivered_str,
            "Fərq": diff_minutes,
            "Status": status
        })
        
    df = pd.DataFrame(parsed_data)
    
    if not df.empty:
        # Mağazaların prioritet sıralaması
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

if st.button("Excel Faylı Yarad", type="primary"):
    if not raw_text.strip():
        st.warning("Zəhmət olmasa mətn daxil edin!")
    else:
        df = parse_orders(raw_text)
        
        if df.empty:
            st.error("Mətndə heç bir sifariş tapılmadı. Formatı yoxlayın.")
        else:
            st.success(f"Ümumi {len(df)} sifariş analiz edildi!")
            st.dataframe(df, use_container_width=True)
            
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
