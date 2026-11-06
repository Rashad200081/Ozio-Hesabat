import re
import io
import pandas as pd
import streamlit as st
from datetime import datetime

# Səhifə konfiqurasiyası
st.set_page_config(page_title="Sifariş Analizatoru", layout="wide")

# Arxa fon rəngi, mətn daxiletmə və "Başla" düyməsinin xüsusi stili üçün CSS
custom_style = """
<style>
/* Bütün arxa fon Ozio loqosunun brend rəngi */
[data-testid="stAppViewContainer"] {
    background-color: #e82562;
    color: #ffffff;
}
[data-testid="stAppViewContainer"] > .main {
    padding-top: 30px;
}
[data-testid="stHeader"] {
    background-color: rgba(0,0,0,0);
}

/* Yuxarıdakı Ozio Loqosu (Ağ fonda brend yazısı) */
.ozio-logo-container {
    text-align: center;
    margin-bottom: 15px;
}
.ozio-logo-badge {
    display: inline-block;
    background-color: #ffffff;
    color: #e82562;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 40px;
    font-weight: 900;
    padding: 6px 35px;
    border-radius: 14px;
    letter-spacing: 1px;
    box-shadow: 0px 6px 20px rgba(0, 0, 0, 0.25);
}
.ozio-logo-badge span {
    font-size: 45px;
    vertical-align: super;
}

/* Titul və alt mətnlərin rəngi */
h1, p, label {
    color: #ffffff !important;
}

/* Mətn daxiletmə sahəsinin (Qeyd yerinin) ağ fonda olması */
textarea {
    background-color: #ffffff !important;
    color: #12121f !important;
    border: 2px solid rgba(255, 255, 255, 0.8) !important;
    border-radius: 12px !important;
    font-size: 15px !important;
}
textarea::placeholder {
