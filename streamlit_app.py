import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Cash Flow Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a more polished look
st.markdown("""
    <style>
    .main {
        background-color: #f8fafc;
    }
    .stMetric {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #f1f5f9;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)

def format_idr(amount):
    return f"Rp {amount:,.0f}".replace(",", ".")

def main():
    st.title("💰 Cash Flow Dashboard")
    st.markdown("Monitor arus kas Anda dengan mudah melalui upload file Excel.")
    
    st.sidebar.header("Pengaturan & Upload")
    
    st.sidebar.subheader("📥 Inflow Data")
    inflow_file = st.sidebar.file_uploader("Upload Inflow (.xlsx)", type=["xlsx"], key="inflow")
    
    st.sidebar.subheader("📤 Outflow Data")
    outflow_file = st.sidebar.file_uploader("Upload Outflow (.xlsx)", type=["xlsx"], key="outflow")
    
    # Data Loading Logic
    dfs = []
    
    if inflow_file is not None:
        try:
            df_in = pd.read_excel(inflow_file)
            df_in['Type'] = 'Income'
            dfs.append(df_in)
        except Exception as e:
            st.error(f"Error reading Inflow file: {e}")

    if outflow_file is not None:
        try:
            df_out_raw = pd.read_excel(outflow_file)
            # Wide to Long transformation for Outflow
            # Columns: Month, Date, PAYMENT AP NON PR PO, PETTYFUND REIMBURSE, PEMBAYARAN LAIN-LAIN, PETTYFUND KASBON, PUK, OPEX, CAPEX
            outflow_cols = [
                'PAYMENT AP NON PR PO', 'PETTYFUND REIMBURSE', 'PEMBAYARAN LAIN-LAIN', 
                'PETTYFUND KASBON', 'PUK', 'OPEX', 'CAPEX'
            ]
            
            # Check if these columns exist
            existing_outflow_cols = [col for col in outflow_cols if col in df_out_raw.columns]
            
            if 'Date' in df_out_raw.columns and existing_outflow_cols:
                # Melt the dataframe
                df_out = df_out_raw.melt(
                    id_vars=['Date'], 
                    value_vars=existing_outflow_cols,
                    var_name='Category', 
                    value_name='Amount'
                )
                # Remove rows with NaN or 0 amount
                df_out = df_out[df_out['Amount'] > 0].dropna(subset=['Amount'])
                df_out['Type'] = 'Expense'
                df_out['Description'] = 'Outflow Transaction'
                dfs.append(df_out)
            else:
                st.error("File Outflow harus memiliki kolom 'Date' dan minimal satu kolom kategori (OPEX, CAPEX, dll).")
        except Exception as e:
            st.error(f"Error reading Outflow file: {e}")

    if not dfs:
        st.info("💡 Silakan upload file Inflow atau Outflow di sidebar. Menampilkan data contoh saat ini.")
        data = {
            'Date': ['2024-04-01', '2024-04-05', '2024-04-10', '2024-04-15', '2024-04-20', '2024-04-22', '2024-04-25', '2024-04-28'],
            'Category': ['Salary', 'PAYMENT AP NON PR PO', 'OPEX', 'Freelance', 'CAPEX', 'PETTYFUND REIMBURSE', 'PUK', 'PETTYFUND KASBON'],
            'Description': ['Gaji Bulanan', 'Vendor Payment', 'Biaya Operasional', 'Proyek Sampingan', 'Pembelian Aset', 'Reimburse Kantor', 'Kesejahteraan Karyawan', 'Kasbon'],
            'Amount': [15000000, 4500000, 2000000, 3500000, 5000000, 300000, 1200000, 500000],
            'Type': ['Income', 'Expense', 'Expense', 'Income', 'Expense', 'Expense', 'Expense', 'Expense']
        }
        df = pd.DataFrame(data)
    else:
        df = pd.concat(dfs, ignore_index=True)
        # Basic validation
        required_cols = ['Date', 'Category', 'Description', 'Amount']
        if not all(col in df.columns for col in required_cols):
            st.error(f"File Excel harus memiliki kolom minimal: {', '.join(required_cols)}")
            return

    # Data Processing
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    # Drop rows where Date could not be parsed
    df = df.dropna(subset=['Date'])
    df = df.sort_values('Date', ascending=False)
    
    # Month Filter in Sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filter Data")
    df['MonthYear'] = df['Date'].dt.strftime('%B %Y')
    months = ["All"] + sorted(df['MonthYear'].unique().tolist(), key=lambda x: datetime.strptime(x, '%B %Y'))
    selected_month = st.sidebar.selectbox("Pilih Bulan", months)

    # Apply Filter
    filtered_df = df.copy()
    if selected_month != "All":
        filtered_df = df[df['MonthYear'] == selected_month]

    total_income = filtered_df[filtered_df['Type'].str.lower() == 'income']['Amount'].sum()
    total_expense = filtered_df[filtered_df['Type'].str.lower() == 'expense']['Amount'].sum()
    net_cashflow = total_income - total_expense

    # Filtered Cash Outflow
    outflow_categories = [
        'PAYMENT AP NON PR PO', 'PETTYFUND REIMBURSE', 'PEMBAYARAN LAIN-LAIN', 
        'PETTYFUND KASBON', 'PUK', 'OPEX', 'CAPEX'
    ]
    cash_outflow_filtered = filtered_df[
        (filtered_df['Type'].str.lower() == 'expense') & 
        (filtered_df['Category'].str.upper().isin(outflow_categories))
    ]['Amount'].sum()

    # Summary Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Inflow", format_idr(total_income), delta=None)
    with col2:
        st.metric("Total Outflow", format_idr(total_expense), delta_color="inverse")
    with col3:
        st.metric("Cash Outflow (Filtered)", format_idr(cash_outflow_filtered), delta_color="inverse")
    with col4:
        st.metric("Saldo Bersih", format_idr(net_cashflow), delta=None)

    st.markdown("---")

    # Charts
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("📈 Tren Arus Kas")
        # Group by date for trend
        trend_df = filtered_df.groupby(['Date', 'Type'])['Amount'].sum().reset_index()
        fig_trend = px.area(trend_df, x='Date', y='Amount', color='Type',
                           color_discrete_map={'Income': '#10b981', 'Expense': '#ef4444'},
                           line_shape='spline', template='plotly_white')
        fig_trend.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_trend, use_container_width=True)

    with chart_col2:
        st.subheader("🍕 Outflow by Category")
        expense_df = filtered_df[filtered_df['Type'].str.lower() == 'expense']
        if not expense_df.empty:
            fig_pie = px.pie(expense_df, values='Amount', names='Category',
                            hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.write("Belum ada data pengeluaran untuk ditampilkan.")

    # Transaction Table
    st.subheader("📑 Daftar Transaksi Terbaru")
    st.dataframe(filtered_df.sort_values('Date', ascending=False), use_container_width=True)

    # Download processed data
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Data sebagai CSV",
        data=csv,
        file_name='cashflow_data.csv',
        mime='text/csv',
    )

if __name__ == "__main__":
    main()
