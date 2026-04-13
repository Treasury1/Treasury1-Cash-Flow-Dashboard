import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(page_title="Finance Dashboard ASDP", layout="wide")

# Styling Custom (Mirip dengan versi React)
st.markdown("""
    <style>
    .main { background-color: #F8F9FB; }
    .stMetric { background-color: white; padding: 20px; border-radius: 15px; border: 1px solid #f0f0f0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# Fungsi Ambil Data
@st.cache_data(ttl=60) # Cache selama 1 menit (Auto-refresh)
def load_data():
    import requests
    import io
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    # 1. Ambil Data Inflow (Sheet: april, Cell: L482)
    inflow_url = "https://docs.google.com/spreadsheets/d/1ongKEVtqOlKQpgbZzkuAH740zHEaRp4T/export?format=csv&sheet=april"
    
    inflow_res = requests.get(inflow_url, headers=headers)
    if inflow_res.status_code != 200:
        raise Exception(f"Inflow Sheet Error: {inflow_res.status_code}. Pastikan 'Publish to the Web' sudah aktif.")
    
    df_inflow = pd.read_csv(io.StringIO(inflow_res.text))
    
    # L482 -> Kolom L (index 11), Baris 482 (index 481)
    try:
        total_inflow = df_inflow.iloc[480, 11] 
        if isinstance(total_inflow, str):
            total_inflow = float(total_inflow.replace(',', '').replace('$', ''))
    except:
        total_inflow = 0

    # 2. Ambil Data Outflow (Sheet: Summary Cash Outflow)
    outflow_url = "https://docs.google.com/spreadsheets/d/1CwkwjqbLAm8btPHuV0NNYOogp_Ltc83k/export?format=csv&gid=1507358761"
    
    outflow_res = requests.get(outflow_url, headers=headers)
    if outflow_res.status_code != 200:
        raise Exception(f"Outflow Sheet Error: {outflow_res.status_code}. Pastikan 'Publish to the Web' sudah aktif.")
    
    df_outflow = pd.read_csv(io.StringIO(outflow_res.text))
    
    # Bersihkan nama kolom (menghapus spasi berlebih)
    df_outflow.columns = [c.strip() for c in df_outflow.columns]
    
    # Penjumlahan Kolom C sampai K (Index 2 sampai 10)
    # Kolom: PAYMENT AP, PETTYFUND REIMBURSE, PEMBAYARAN LAIN, PETTYFUND KASBON, ..., OPEX, CAPEX
    cols_to_sum = df_outflow.columns[2:11] 
    for col in cols_to_sum:
        df_outflow[col] = pd.to_numeric(df_outflow[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    df_outflow['Total_Row_Outflow'] = df_outflow[cols_to_sum].sum(axis=1)
    
    return total_inflow, df_outflow, cols_to_sum

# Load Data
try:
    total_inflow, df_outflow, categories = load_data()
    
    # Sidebar & Filter
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Logo_ASDP_Indonesia_Ferry.png/800px-Logo_ASDP_Indonesia_Ferry.png", width=150)
    st.sidebar.title("Filters")
    
    # Filter Bulan (Berdasarkan Kolom A)
    all_months = ["All"] + sorted(df_outflow.iloc[:, 0].dropna().unique().tolist())
    selected_month = st.sidebar.selectbox("Select Month", all_months)
    
    # Filter Data
    if selected_month != "All":
        filtered_df = df_outflow[df_outflow.iloc[:, 0] == selected_month]
    else:
        filtered_df = df_outflow

    # Header
    st.title("🚢 FINANCE STATUS DASHBOARD")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Row 1: Stats Cards
    total_outflow = filtered_df['Total_Row_Outflow'].sum()
    balance = total_inflow - total_outflow

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Inflow", f"IDR {total_inflow:,.0f}")
    col2.metric("Total Outflow (C-K)", f"IDR {total_outflow:,.0f}")
    col3.metric("Monthly Balance", f"IDR {balance:,.0f}")

    st.divider()

    # Row 2: Charts
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Cash Outflow by Category")
        # Agregasi per kategori untuk chart
        cat_data = []
        for cat in categories:
            cat_data.append({"Category": cat, "Amount": filtered_df[cat].sum()})
        df_cat = pd.DataFrame(cat_data)
        
        fig = px.bar(df_cat, x="Category", y="Amount", color="Category", 
                     text_auto='.2s', title="Distribution of Expenses")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Inflow vs Outflow")
        fig_pie = go.Figure(data=[go.Pie(labels=['Inflow', 'Outflow'], 
                                         values=[total_inflow, total_outflow],
                                         hole=.3,
                                         marker_colors=['#1d4ed8', '#bfdbfe'])])
        st.plotly_chart(fig_pie, use_container_width=True)

    # Row 3: Data Table
    st.subheader("Detailed Transaction Log")
    st.dataframe(filtered_df.iloc[:, [0, 1] + list(range(2, 11)) + [-1]], use_container_width=True)

except Exception as e:
    st.error(f"Gagal memuat data dari Spreadsheet. Pastikan link dapat diakses. Error: {e}")
    st.info("Tips: Pastikan Spreadsheet diatur ke 'Anyone with the link can view'.")
