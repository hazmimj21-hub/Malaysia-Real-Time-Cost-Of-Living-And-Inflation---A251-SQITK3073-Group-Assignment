import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ==================== DATA LOADING ====================
@st.cache_data
def load_data():
    url = "https://storage.dosm.gov.my/cpi/cpi_2d_state.csv"
    df = pd.read_csv(url)
    df['date'] = pd.to_datetime(df['date'])
    df = df[df['division'] == 'overall']
    df = df.sort_values(['state', 'date'])
    return df

df = load_data()

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="Malaysia Cost of Living Dashboard",
    page_icon="🇲🇾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.title("⚙️ Dashboard Controls")
    
    st.sidebar.header("Filters")

    state = st.sidebar.selectbox(
        "Select State",
        sorted(df['state'].unique())
    )

    start_date, end_date = st.sidebar.date_input(
        "Select Date Range",
        [df['date'].min(), df['date'].max()]
    )
    
    # Update Button
    if st.button("🔄 Update Dashboard", type="primary", use_container_width=True):
        st.rerun()


# ==================== MAIN DASHBOARD ====================
# Header
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown('<h1 class="dashboard-title">🇲🇾 Malaysia Cost of Living & Inflation Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="dashboard-subtitle">Real-time analytics and predictive insights for economic planning</p>', unsafe_allow_html=True)
with col2:
    st.metric("Last Updated", datetime.now().strftime("%d %b %Y"))

st.markdown("---")

# Calculate Inflation (YoY)

df['inflation_yoy'] = (
    df.groupby('state')['index']
    .pct_change(12) * 100
)

# Filter Data

state_data = df[
    (df['state'] == state) &
    (df['date'] >= pd.to_datetime(start_date)) &
    (df['date'] <= pd.to_datetime(end_date))
]

# Latest Inflation Metric

latest = state_data.dropna().iloc[-1]

st.metric(
    label=f"Latest Inflation Rate in {state} (YoY)",
    value=f"{latest['inflation_yoy']:.2f}%",
    delta=None
)

# CPI Trend Chart

st.subheader("CPI Trend Over Time")

fig1, ax1 = plt.subplots()
ax1.plot(state_data['date'], state_data['index'])
ax1.set_xlabel("Year")
ax1.set_ylabel("CPI Index")
ax1.set_title(f"CPI Trend in {state}")
st.pyplot(fig1)

# Inflation Trend Chart

st.subheader("Inflation Rate Trend (Year-on-Year %)")

fig2, ax2 = plt.subplots()
ax2.plot(state_data['date'], state_data['inflation_yoy'])
ax2.set_xlabel("Year")
ax2.set_ylabel("Inflation Rate (%)")
ax2.set_title(f"Inflation Rate in {state}")
st.pyplot(fig2)

# State Comparison

st.subheader("Latest Inflation Comparison Across States")

latest_state = (
    df.dropna()
      .sort_values('date')
      .groupby('state')
      .tail(1)
      .sort_values('inflation_yoy', ascending=False)
)

fig3, ax3 = plt.subplots()
ax3.barh(
    latest_state['state'],
    latest_state['inflation_yoy']
)
ax3.set_xlabel("Inflation Rate (%)")
ax3.set_title("Latest Inflation Rate by State")
st.pyplot(fig3)

# Data Table

with st.expander("View Data Table"):
    st.dataframe(state_data[['date', 'index', 'inflation_yoy']])

# ==================== FOOTER ====================
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns([2, 1, 1])

with footer_col1:
    st.markdown("""
    **SQITK 3073 Group Project**
    
    **Team Members:**
    - NUR FADHLIN NASRIN BINTI MOHD NAZRI (294330)
    - MUHAMMAD ALIEF HAZIQ BIN NOR ZARISH (306302)
    - MOHAMMAD HAZMI BIN MOHD JIM (306636)
    - IMAN HAFIZ BIN MUHAMMAD FAIZ (306827)
    - MUHAMAD NUR AZIM BIN AZMAN (307626)
    """)


with footer_col3:
    st.markdown(f"""
    **Last Updated:** {datetime.now().strftime("%d %B %Y, %H:%M")}  
    **Dashboard Version:** 1.0  
    **Next Update:** Automatic
    """)