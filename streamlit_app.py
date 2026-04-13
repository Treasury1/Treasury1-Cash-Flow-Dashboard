import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="CashFlow Pro Dashboard",
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
    st.title("💰 CashFlow Pro Dashboard")
    st.markdown("Monitor arus kas Anda dengan mudah melalui upload file Excel.")
    
    st.sidebar.header("Pengaturan & Upload")
    uploaded_file = st.sidebar.file_uploader("Upload file Excel (.xlsx)", type=["xlsx"])
    
    # Sample Data if no file is uploaded
    if uploaded_file is None:
        st.info("💡 Silakan upload file Excel di sidebar. Menampilkan data contoh saat ini.")
        data = {
            'Date': ['2024-03-01', '2024-03-05', '2024-03-10', '2024-03-15', '2024-03-20'],
            'Category': ['Salary', 'Rent', 'Food', 'Freelance', 'Transport'],
            'Description': ['Gaji Bulanan', 'Sewa Apartemen', 'Belanja Bulanan', 'Proyek Sampingan', 'Bensin'],
            'Amount': [15000000, 4500000, 1200000, 3500000, 800000],
            'Type': ['Income', 'Expense', 'Expense', 'Income', 'Expense']
        }
        df = pd.DataFrame(data)
    else:
        try:
            df = pd.read_excel(uploaded_file)
            # Basic validation
            required_cols = ['Date', 'Category', 'Description', 'Amount', 'Type']
            if not all(col in df.columns for col in required_cols):
                st.error(f"File Excel harus memiliki kolom: {', '.join(required_cols)}")
                return
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membaca file: {e}")
            return

    # Data Processing
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    
    total_income = df[df['Type'].str.lower() == 'income']['Amount'].sum()
    total_expense = df[df['Type'].str.lower() == 'expense']['Amount'].sum()
    net_cashflow = total_income - total_expense

    # Summary Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Pemasukan", format_idr(total_income), delta=None)
    with col2:
        st.metric("Total Pengeluaran", format_idr(total_expense), delta_color="inverse")
    with col3:
        st.metric("Saldo Bersih", format_idr(net_cashflow), delta=None)

    st.markdown("---")

    # Charts
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("📈 Tren Arus Kas")
        # Group by date for trend
        trend_df = df.groupby(['Date', 'Type'])['Amount'].sum().reset_index()
        fig_trend = px.area(trend_df, x='Date', y='Amount', color='Type',
                           color_discrete_map={'Income': '#10b981', 'Expense': '#ef4444'},
                           line_shape='spline', template='plotly_white')
        fig_trend.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_trend, use_container_width=True)

    with chart_col2:
        st.subheader("🍕 Distribusi Pengeluaran")
        expense_df = df[df['Type'].str.lower() == 'expense']
        if not expense_df.empty:
            fig_pie = px.pie(expense_df, values='Amount', names='Category',
                            hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.write("Belum ada data pengeluaran untuk ditampilkan.")

    # Transaction Table
    st.subheader("📑 Daftar Transaksi Terbaru")
    st.dataframe(df.sort_values('Date', ascending=False), use_container_width=True)

    # Download processed data
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Data sebagai CSV",
        data=csv,
        file_name='cashflow_data.csv',
        mime='text/csv',
    )

if __name__ == "__main__":
    main()
