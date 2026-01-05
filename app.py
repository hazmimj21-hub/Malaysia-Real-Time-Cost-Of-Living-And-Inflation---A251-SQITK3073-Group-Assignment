import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from datetime import datetime
import requests
from io import StringIO
import warnings
warnings.filterwarnings('ignore')

# Configure the page
st.set_page_config(
    page_title="Malaysia Cost of Living Dashboard",
    page_icon="🇲🇾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS for better loading experience
st.markdown("""
    <style>
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== DATA LOADING ====================
@st.cache_data(ttl=300)  # Cache data for 5 minutes
def load_data(force_refresh=False):
    if force_refresh:
        st.cache_data.clear()  # Clear cache if force refresh is True
        
    url = "https://storage.dosm.gov.my/cpi/cpi_2d_state.csv"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        df['date'] = pd.to_datetime(df['date'])
        df = df[df['division'] == 'overall']
        df = df.sort_values(['state', 'date'])
        
        # Calculate Inflation (YoY)
        df['inflation_yoy'] = df.groupby('state')['index'].pct_change(12) * 100
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

# Initialize session state
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
    st.session_state.df = load_data()

# Function to refresh data
def refresh_data():
    with st.spinner('Refreshing data...'):
        st.session_state.df = load_data(force_refresh=True)
        st.session_state.last_refresh = datetime.now()
        st.rerun()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.title("⚙️ Dashboard Controls")
    
    # Refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        refresh_data()
    
    st.caption(f"Last updated: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("Click the button above to refresh data")
    
    st.header("Filters")

    # Ensure df is loaded
    if st.session_state.df is not None:
        state = st.selectbox(
            "Select State",
            sorted(st.session_state.df['state'].unique())
        )

        start_date, end_date = st.date_input(
            "Select Date Range",
            [st.session_state.df['date'].min().to_pydatetime().date(), 
             st.session_state.df['date'].max().to_pydatetime().date()]
        )
    else:
        st.error("Failed to load data. Please try refreshing the page.")
        state = ""
        start_date = end_date = datetime.now().date()

# ==================== MAIN DASHBOARD ====================
# Show loading state
if st.session_state.df is None:
    st.warning("Loading data...")
    st.stop()

# Header
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown('<h1 class="dashboard-title">🇲🇾 Malaysia Cost of Living & Inflation Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="dashboard-subtitle">Real-time analytics and predictive insights for economic planning</p>', unsafe_allow_html=True)
with col2:
    # Show last updated time in a clean format
    st.metric(
        "Data last refreshed",
        st.session_state.last_refresh.strftime("%H:%M"),
        delta=None
    )

st.markdown("---")

# Filter Data with loading indicator
with st.spinner('Processing data...'):
    state_data = st.session_state.df[
        (st.session_state.df['state'] == state) &
        (st.session_state.df['date'] >= pd.to_datetime(start_date)) &
        (st.session_state.df['date'] <= pd.to_datetime(end_date))
    ]

# Get latest data point
if not state_data.empty:
    latest = state_data.dropna().iloc[-1]
else:
    st.warning("No data available for the selected filters.")
    st.stop()

# Latest Inflation Metric
col1, col2 = st.columns(2)
with col1:
    st.metric(
        label=f"Latest Inflation Rate in {state} (YoY)",
        value=f"{latest['inflation_yoy']:.2f}%",
        delta=None
    )
with col2:
    st.empty()  # Empty space for visual balance

# CPI Trend Chart
st.subheader("CPI Trend Over Time")
fig1 = px.line(
    state_data, 
    x='date', 
    y='index',
    title=f"CPI Trend in {state}",
    labels={'index': 'CPI Index', 'date': 'Date'},
    hover_data={'index': ':.2f', 'date': '%b %Y'}
)
fig1.update_traces(
    hovertemplate="<b>Date:</b> %{x|%d %b %Y}<br><b>CPI Index:</b> %{y:.2f}<extra></extra>"
)
st.plotly_chart(fig1, use_container_width=True)

# Inflation Trend Chart
st.subheader("Inflation Rate Trend (Year-on-Year %)")
fig2 = px.line(
    state_data, 
    x='date', 
    y='inflation_yoy',
    title=f"Inflation Rate in {state}",
    labels={'inflation_yoy': 'Inflation Rate (%)', 'date': 'Date'},
    hover_data={'inflation_yoy': ':.2f', 'date': '%b %Y'}
)
fig2.update_traces(
    hovertemplate="<b>Date:</b> %{x|%d %b %Y}<br><b>Inflation Rate:</b> %{y:.2f}%<extra></extra>"
)
st.plotly_chart(fig2, use_container_width=True)

# State Comparison
st.subheader("Latest Inflation Comparison Across States")

latest_state = (
    st.session_state.df.dropna()
      .sort_values('date')
      .groupby('state')
      .tail(1)
      .sort_values('inflation_yoy', ascending=True)  # Changed to ascending for better visualization
)

fig3 = px.bar(
    latest_state,
    x='inflation_yoy',
    y='state',
    orientation='h',
    title="Latest Inflation Rate by State",
    labels={'inflation_yoy': 'Inflation Rate (%)', 'state': 'State'},
    hover_data={'inflation_yoy': ':.2f'}
)

# Customize hover template
fig3.update_traces(
    hovertemplate="<b>%{y}</b><br>Inflation: %{x:.2f}%<extra></extra>",
    marker_color='skyblue'
)

# Adjust layout
fig3.update_layout(
    yaxis={'categoryorder': 'total ascending'},
    xaxis=dict(
        showgrid=True,
        gridwidth=1,
        gridcolor='LightGrey',
        showline=True,
        linewidth=1,
        linecolor='Grey'
    ),
    height=500
)

st.plotly_chart(fig3, use_container_width=True)

# Data Table
with st.expander("View Data Table"):
    st.dataframe(state_data[['date', 'index', 'inflation_yoy']].sort_values('date', ascending=False))

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
**SQITK 3073 Group Project**

**Team Members:**
- NUR FADHLIN NASRIN BINTI MOHD NAZRI (294330)
- MUHAMMAD ALIEF HAZIQ BIN NOR ZARISH (306302)
- MOHAMMAD HAZMI BIN MOHD JIM (306636)
- IMAN HAFIZ BIN MUHAMMAD FAIZ (306827)
- MUHAMAD NUR AZIM BIN AZMAN (307626)
""")
