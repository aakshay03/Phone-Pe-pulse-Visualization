# app.py - The Final Version with a Persistent Sidebar

# --- 1. IMPORTS ---
import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
import json
import requests

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="PhonePe Pulse Data Analysis",
    page_icon="🇮🇳",
    layout="wide"
)

# --- 3. CUSTOM STYLING ---
page_bg_color = """
<style>
[data-testid="stAppViewContainer"] {
    background-color: #E6F0FF; /* A light, professional blue */
}
[data-testid="stSidebar"] {
    background-color: #D1E3FF; /* A slightly darker blue for the sidebar */
}
</style>
"""
st.markdown(page_bg_color, unsafe_allow_html=True)


# --- 4. DATABASE CONNECTION FUNCTION ---
db_host = "127.0.0.1"
db_user = "root"
db_pass = "Akshay@200"
db_name = "phonepe_pulse"

@st.cache_data
def fetch_data(query):
    """Connects to the database and fetches data based on a SQL query."""
    try:
        con = mysql.connector.connect(host=db_host, user=db_user, password=db_pass, database=db_name)
        df = pd.read_sql(query, con)
        con.close()
        return df
    except mysql.connector.Error as err:
        st.error(f"Database Connection Error: {err}")
        return pd.DataFrame()

# --- 5. SIDEBAR CONTROLS ---
st.sidebar.header("Select Analysis Options")

# Main analysis choice
analysis_choice = st.sidebar.selectbox(
    "Choose a Business Case to Analyze",
    [
        "Geographical Insights (Transaction Map)",
        "Decoding Transaction Dynamics",
        "Insurance Penetration Analysis",
        "Top Performers: Transactions",
        "Top Performers: Users"
    ]
)

# Global filters for Year and Quarter that are always visible
year = st.sidebar.slider("Select Year", 2018, 2024, 2022)
quarter = st.sidebar.select_slider("Select Quarter", options=[1, 2, 3, 4], value=1)


# --- 6. MAIN DASHBOARD AREA ---
st.title("PhonePe Pulse Data Visualization and Analysis")
st.write("---")

# --- ANALYSIS DISPLAY LOGIC ---

# =======================================================================================================================
# Business Case 1: Geographical Insights (Transaction Map) (4)
# =======================================================================================================================
if analysis_choice == "Geographical Insights (Transaction Map)":
    st.subheader(f"Geographical Data for {year} - Q{quarter}")
    
    metric = st.sidebar.selectbox("Select Metric", ["Transaction Count", "Transaction Amount"])

    query = f"""
        SELECT state, SUM({metric.lower().replace(' ', '_')}) as metric_value
        FROM aggregated_transaction
        WHERE year = {year} AND quarter = {quarter}
        GROUP BY state;
    """
    df = fetch_data(query)

    if not df.empty:
        df['state'] = df['state'].str.replace('-', ' ').str.title()
        df['state'] = df['state'].str.replace('Dadra & Nagar Haveli & Daman & Diu', 'Dadra and Nagar Haveli and Daman and Diu')
        df.loc[df['state'] == 'Andaman & Nicobar Islands', 'state'] = 'Andaman & Nicobar'


        geojson_url = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
        response = requests.get(geojson_url)
        geojson_data = response.json()
        
        fig = px.choropleth(df, geojson=geojson_data, featureidkey='properties.ST_NM', locations='state', color='metric_value',
                            color_continuous_scale='Viridis', hover_name='state', title=f"{metric} in {year} - Q{quarter}",
                            projection='mercator')
        fig.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for the selected filters.")

# =======================================================================================================================
# Business Case 2: Decoding Transaction Dynamics (1)
# =======================================================================================================================
elif analysis_choice == "Decoding Transaction Dynamics":
    st.subheader(f"Transaction Categories Analysis for {year} - Q{quarter}")
    query = f"""
        SELECT transaction_name as Category, SUM(transaction_count) as Total_Transactions
        FROM aggregated_transaction
        WHERE year = {year} AND quarter = {quarter}
        GROUP BY transaction_name
        ORDER BY Total_Transactions DESC;
    """
    df = fetch_data(query)
    if not df.empty:
        fig = px.pie(df, values='Total_Transactions', names='Category', title=f'Transaction Categories for {year}, Q{quarter}')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for the selected filters.")


# =======================================================================================================================
# Business Case 3: Insurance Penetration Analysis (3)
# =======================================================================================================================
elif analysis_choice == "Insurance Penetration Analysis":
    st.subheader(f"Insurance Transactions for {year} - Q{quarter}")
    query = f"""
        SELECT state, SUM(insurance_count) as Total_Policies, SUM(insurance_amount) as Total_Premium
        FROM aggregated_insurance
        WHERE year = {year} AND quarter = {quarter}
        GROUP BY state
        ORDER BY Total_Policies DESC;
    """
    df = fetch_data(query)
    if not df.empty:
        fig = px.bar(df, x='state', y='Total_Policies', title=f'Insurance Policies Sold for {year}, Q{quarter}', color='Total_Policies')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for the selected filters.")

# =======================================================================================================================
# Business Case 4 (7) & 5 (8): Top Performers (Transactions & Users) 
# =======================================================================================================================
elif analysis_choice in ["Top Performers: Transactions", "Top Performers: Users"]:
    
    st.subheader(f"Top 10 Performers for {year} - Q{quarter}")

    if analysis_choice == "Top Performers: Transactions":
        st.markdown("#### Analyzing: Transactions")
        col1, col2 = st.columns(2)
        with col1:
            query_dist = f"""
                SELECT entity_name as District, SUM(transaction_amount) as Total_Amount
                FROM top_transaction WHERE year = {year} AND quarter = {quarter} AND entity_type = 'district'
                GROUP BY entity_name ORDER BY Total_Amount DESC LIMIT 10;
            """
            df_dist = fetch_data(query_dist)
            fig_dist = px.pie(df_dist, values='Total_Amount', names='District', title='Top 10 Districts by Transaction Amount')
            st.plotly_chart(fig_dist, use_container_width=True)
        
        with col2:
            query_pin = f"""
                SELECT entity_name as Pincode, SUM(transaction_amount) as Total_Amount
                FROM top_transaction WHERE year = {year} AND quarter = {quarter} AND entity_type = 'pincode'
                GROUP BY entity_name ORDER BY Total_Amount DESC LIMIT 10;
            """
            df_pin = fetch_data(query_pin)
            fig_pin = px.pie(df_pin, values='Total_Amount', names='Pincode', title='Top 10 Pincodes by Transaction Amount')
            st.plotly_chart(fig_pin, use_container_width=True)

    elif analysis_choice == "Top Performers: Users":
        st.markdown("#### Analyzing: Users")
        col1, col2 = st.columns(2)
        with col1:
            query_dist = f"""
                SELECT entity_name as District, SUM(registered_users) as Total_Users
                FROM top_user WHERE year = {year} AND quarter = {quarter} AND entity_type = 'district'
                GROUP BY entity_name ORDER BY Total_Users DESC LIMIT 10;
            """
            df_dist = fetch_data(query_dist)
            fig_dist = px.bar(df_dist, x='District', y='Total_Users', title='Top 10 Districts by Registered Users', color='Total_Users')
            st.plotly_chart(fig_dist, use_container_width=True)

        with col2:
            query_pin = f"""
                SELECT entity_name as Pincode, SUM(registered_users) as Total_Users
                FROM top_user WHERE year = {year} AND quarter = {quarter} AND entity_type = 'pincode'
                GROUP BY entity_name ORDER BY Total_Users DESC LIMIT 10;
            """
            df_pin = fetch_data(query_pin)
            fig_pin = px.bar(df_pin, x='Pincode', y='Total_Users', title='Top 10 Pincodes by Registered Users', color='Total_Users')
            st.plotly_chart(fig_pin, use_container_width=True)