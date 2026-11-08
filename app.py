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
    ws = wb.active
    ws.title = "Sifarişlər"

    headers = ["Mağaza", "Sifariş ID", "Yaradılıb", "Çatdırılıb", "Fərq", "Status"]
    ws.append(headers)

    header_fill = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    red_fill = PatternFill(start_color="F8CECC", end_color="F8CECC", fill_type="solid")
    normal_font = Font(name="Calibri", size=11)
    bold_font = Font(name="Calibri", size=11, bold=True)
    status_red_font = Font(name="Calibri", size=11, bold=True, color="C00000")

    current_store = None
    store_start_row = 2

    for row_idx, row_data in enumerate(df.to_dict('records'), start=2):
        store = row_data["Mağaza"]
        status = str(row_data["Status"])

        if current_store is not None and store != current_store:
            if store_start_row < row_idx - 1:
                ws.merge_cells(start_row=store_start_row, start_column=1, end_row=row_idx - 1, end_column=1)
            store_start_row = row_idx

        current_store = store

        ws.cell(row=row_idx, column=1, value=store)
        ws.cell(row=row_idx, column=2, value=row_data["Sifariş ID"])
        ws.cell(row=row_idx, column=3, value=row_data["Yaradılıb"])
        ws.cell(row=row_idx, column=4, value=row_data["Çatdırılıb"])
        ws.cell(row=row_idx, column=5, value=row_data["Fərq"])
        ws.cell(row=row_idx, column=6, value=status)

        for col_idx in range(1, 7):
            c = ws.cell(row=row_idx, column=col_idx)
            c.border = thin_border
            c.font = normal_font
            
            if col_idx in [2, 3, 4, 5, 6]:
                c.alignment = Alignment(horizontal="center", vertical="center")
            else:
                c.alignment = Alignment(horizontal="left", vertical="center")

            if status in ["Gecikmə", "Ləğv"]:
                if col_idx in [5, 6]:
                    c.fill = red_fill
                    c.font = status_red_font

    if current_store is not None and store_start_row < len(df) + 2:
        ws.merge_cells(start_row=store_start_row, start_column=1, end_row=len(df) + 1, end_column=1)

    for r in range(2, len(df) + 2):
        ws.cell(row=r, column=1).alignment = Alignment(horizontal="left", vertical="center")
        ws.cell(row=r, column=1).font = bold_font

    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val = str(cell.value or '')
            if len(val) > max_len:
                max_len = len(val)
        ws.column_dimensions[col_letter].width = max(max_len + 5, 12)

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()

if st.button("Başla", type="primary"):
    if not raw_text.strip():
        st.warning("Zəhmət olmasa mətn daxil edin!")
    else:
        df = parse_orders(raw_text)
        
        if df.empty:
            st.error("Mətndə heç bir sifariş tapılmadı. Formatı yoxlayın.")
        else:
            st.success(f"Ümumi {len(df)} sifariş analiz edildi!")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            tsv_data = df.to_csv(sep='\t', index=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_area("📋 Excel üçün Kopyalayın (Hamısını seçib Ctrl+C edin):", value=tsv_data, height=150)
            
            with col2:
                excel_bytes = generate_styled_excel(df)
                
                st.download_button(
                    label="📥 Fayl olaraq Endir (.xlsx)",
                    data=excel_bytes,
                    file_name="sifaris_hesabati.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
