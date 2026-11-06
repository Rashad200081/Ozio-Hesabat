import re
import io
import pandas as pd
import streamlit as st
from datetime import datetime

# Səhifə konfiqurasiyası
st.set_page_config(page_title="Sifariş Analizatoru", layout="wide")

# Arxa fon rəngi, mətn daxiletmə sahələri və "Başla" düyməsinin stili üçün CSS
custom_style = """
<style>
/* Bütün arxa fon Ozio brend rəngi */
[data-testid="stAppViewContainer"] {
    background-color: #e82562;
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
    gap: 25px;
    margin-bottom: 25px;
}

.courier-img {
    height: 100px;
    object-fit: contain;
}

.courier-right {
    transform: scaleX(-1);
}

/* Ozio Loqosu (80px) */
.ozio-logo-badge {
    background-color: #ffffff;
    color: #e82562;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 80px;
    font-weight: 900;
    padding: 6px 45px;
    border-radius: 18px;
    letter-spacing: 1px;
    box-shadow: 0px 6px 25px rgba(0, 0, 0, 0.3);
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
    box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.25) !important;
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
