import re
import io
import pandas as pd
import streamlit as st
from datetime import datetime

# Səhifə konfiqurasiyası
st.set_page_config(page_title="Sifariş Analizatoru", layout="wide")

# Ozio brend dizaynı və CSS tənzimləmələri
custom_style = """
<style>
[data-testid="stAppViewContainer"] {
    background-color:#e82562;
    color: #ffffff;
}
[data-testid="stAppViewContainer"] > .main {
    padding-top: 45px;
}
[data-testid="stHeader"] {
    background-color: rgba(0,0,0,0);
}
.ozio-logo-container {
    text-align: center;
    margin-bottom: 80px;
}
.ozio-logo-badge {
    display: inline-block;
    background-color: #e82562;
    color: #ffffff;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 100px;
    font-weight: 800;
    padding: 8px 30px;
    border-radius: 12px;
    letter-spacing: 1px;
    box-shadow: 0px 4px 15px rgba(232, 37, 98, 0.4);
}
.ozio-logo-badge span {
    font-size: 45px;
    vertical-align: super;
}
</style>
"""
st.markdown(custom_style, unsafe_allow_html=True)

# Yuxarı mərkəzdə Ozio brend loqosu
st.markdown('<div class="ozio-logo-container"><div class="ozio-logo-badge">ozio<span>+</span></div></div>', unsafe_allow_html=True)

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
            if "Ləğv" in line or "ləğv" in line.lower():
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

if st.button("Başla", type="primary"):
    color white
    if not raw_text.strip():
        st.warning("Zəhmət olmasa mətn daxil edin!")
    else:
        df = parse_orders(raw_text)
        
        if df.empty:
            st.error("Mətndə heç bir sifariş tapılmadı. Formatı yoxlayın.")
        else:
            st.success(f"Ümumi {len(df)} sifariş analiz edildi!")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Excel formatında Tab ilə ayrılmış mətn (Copy-Paste üçün)
            tsv_data = df.to_csv(sep='\t', index=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_area("📋 Excel üçün Kopyalayın (Hamısını seçib Ctrl+C edin):", value=tsv_data, height=150)
            
            with col2:
                output = io.BytesIO()
                wb = pd.ExcelWriter(output, engine='openpyxl')
                df.to_excel(wb, index=False, sheet_name='Sheet1')
                wb.close()
                processed_data = output.getvalue()
                
                st.download_button(
                    label="📥 Fayl olaraq Endir (.xlsx)",
                    data=processed_data,
                    file_name="sifaris_hesabati.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
