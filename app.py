import re
import io
import pandas as pd
import streamlit as st
from datetime import datetime

# Səhifə konfiqurasiyası
st.set_page_config(page_title="Sifariş Analizatoru", layout="wide")

# Arxa fon rəngi (Şəkildəki tünd çəhrayı / albalı-qırmızı / bordo qradiyent)
custom_style = """
<style>
/* Arxa fon üçün tünd çəhrayı-bordo dinamik qradiyent */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #8b0032 0%, #b80046 50%, #610022 100%);
    color: #ffffff;
}
[data-testid="stAppViewContainer"] > .main {
    padding-top: 20px;
}
[data-testid="stHeader"] {
    background-color: rgba(0,0,0,0);
}

/* Yuxarı Loqo və Kuryerlər konteyneri */
.header-container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 30px;
    margin-bottom: 25px;
}

.courier-img {
    height: 140px;
    object-fit: contain;
}

.courier-right {
    transform: scaleX(-1);
}

/* Ozio Loqosu (80px) */
.ozio-logo-badge {
    background-color: #ffffff;
    color: #b80046;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 80px;
    font-weight: 900;
    padding: 6px 45px;
    border-radius: 18px;
    letter-spacing: 1px;
    box-shadow: 0px 6px 25px rgba(0, 0, 0, 0.4);
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
    font-size:
