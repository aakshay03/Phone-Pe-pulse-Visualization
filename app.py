# app.py - The Final, Advanced, and Multi-Chart Dashboard

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

year = st.sidebar.slider("Select Year", 2018, 2024, 2022)
quarter = st.sidebar.select_slider("Select Quarter", options=[1, 2, 3, 4], value=1)


# --- 6. MAIN DASHBOARD AREA ---
st.title("PhonePe Pulse Data Visualization and Analysis")
st.write("---")

# --- ANALYSIS DISPLAY LOGIC ---

# =======================================================================================================================
# Business Case 1: Geographical Insights (Transaction Map) - ENHANCED
# =======================================================================================================================
if analysis_choice == "Geographical Insights (Transaction Map)":
    st.subheader(f"Geographical Data for {year} - Q{quarter}")
    metric = st.sidebar.selectbox("Select Metric", ["Transaction Count", "Transaction Amount"])
    query = f"""
        SELECT state, SUM({metric.lower().replace(' ', '_')}) as metric_value
        FROM aggregated_transaction WHERE year = {year} AND quarter = {quarter} GROUP BY state;
    """
    df = fetch_data(query)
    if not df.empty:
        df['state_display'] = df['state'].str.replace('-', ' ').str.title()
        df.loc[df['state_display'] == 'Andaman & Nicobar Islands', 'state_display'] = 'Andaman & Nicobar'
        df.loc[df['state_display'] == 'Dadra & Nagar Haveli & Daman & Diu', 'state_display'] = 'Dadra and Nagar Haveli and Daman and Diu'
        geojson_url = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
        response = requests.get(geojson_url)
        geojson_data = response.json()
        fig = px.choropleth(df, geojson=geojson_data, featureidkey='properties.ST_NM', locations='state_display', color='metric_value',
                            color_continuous_scale='Viridis', hover_name='state_display', title=f"{metric} in {year} - Q{quarter}",
                            projection='mercator')
        fig.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig, use_container_width=True)
        st.write("---")
        st.subheader("Deeper Dive: Top Performers")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Top 10 States")
            df_top_states = df.nlargest(10, 'metric_value')
            fig_bar = px.bar(df_top_states, x='state_display', y='metric_value', title=f'Top 10 States by {metric}', color='metric_value')
            st.plotly_chart(fig_bar, use_container_width=True)
        with col2:
            st.markdown("#### Top 10 Districts by State")
            selected_state = st.selectbox("Select a State to View Districts", df['state'].unique())
            query_dist = f"""
                SELECT district_name, SUM(transaction_count) as Total_Transactions
                FROM map_transaction WHERE year = {year} AND quarter = {quarter} AND state = '{selected_state}'
                GROUP BY district_name ORDER BY Total_Transactions DESC LIMIT 10;
            """
            df_dist = fetch_data(query_dist)
            if not df_dist.empty:
                fig_dist = px.bar(df_dist, x='district_name', y='Total_Transactions', title=f'Top 10 Districts in {selected_state.replace("-", " ").title()}', color='Total_Transactions')
                st.plotly_chart(fig_dist, use_container_width=True)
            else:
                st.warning(f"No district data available for {selected_state.replace('-', ' ').title()}.")
    else:
        st.warning("No data available for the selected filters.")

# =======================================================================================================================
# Business Case 2: Decoding Transaction Dynamics - ENHANCED
# =======================================================================================================================
elif analysis_choice == "Decoding Transaction Dynamics":
    st.subheader(f"Transaction Categories Analysis for {year} - Q{quarter}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### By Transaction Volume (Count)")
        query_count = f"""
            SELECT transaction_name as Category, SUM(transaction_count) as Total_Transactions
            FROM aggregated_transaction WHERE year = {year} AND quarter = {quarter}
            GROUP BY transaction_name ORDER BY Total_Transactions DESC;
        """
        df_count = fetch_data(query_count)
        if not df_count.empty:
            fig_pie = px.pie(df_count, values='Total_Transactions', names='Category', title=f'Transaction Volume for {year}, Q{quarter}')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning("No data for volume analysis.")
    with col2:
        st.markdown("#### By Transaction Value (Amount)")
        query_amount = f"""
            SELECT transaction_name as Category, SUM(transaction_amount) as Total_Amount
            FROM aggregated_transaction WHERE year = {year} AND quarter = {quarter}
            GROUP BY transaction_name ORDER BY Total_Amount DESC;
        """
        df_amount = fetch_data(query_amount)
        if not df_amount.empty:
            fig_bar = px.bar(df_amount, x='Category', y='Total_Amount', title=f'Transaction Value for {year}, Q{quarter}', color='Total_Amount')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("No data for value analysis.")
    st.write("---")
    st.subheader(f"Trend Analysis for Top 5 Categories in {year}")
    query_trend = f"""
        SELECT quarter, transaction_name, SUM(transaction_count) as Total_Transactions
        FROM aggregated_transaction
        WHERE year = {year} AND transaction_name IN (
            SELECT transaction_name FROM (
                SELECT transaction_name, SUM(transaction_count)
                FROM aggregated_transaction WHERE year = {year} GROUP BY transaction_name
                ORDER BY SUM(transaction_count) DESC LIMIT 5
            ) as top_categories
        ) GROUP BY quarter, transaction_name ORDER BY quarter;
    """
    df_trend = fetch_data(query_trend)
    if not df_trend.empty:
        fig_line = px.line(df_trend, x='quarter', y='Total_Transactions', color='transaction_name',
                           title=f'Quarterly Transaction Trends for Top 5 Categories in {year}', markers=True)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("No data available for trend analysis.")

# =======================================================================================================================
# Business Case 3: Insurance Penetration Analysis - ENHANCED
# =======================================================================================================================
elif analysis_choice == "Insurance Penetration Analysis":
    st.subheader(f"Insurance Penetration for {year} - Q{quarter}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"#### Top 10 States by Policies Sold")
        query_ins_state = f"""
            SELECT state, SUM(insurance_count) as Total_Policies
            FROM aggregated_insurance WHERE year = {year} AND quarter = {quarter}
            GROUP BY state ORDER BY Total_Policies DESC LIMIT 10;
        """
        df_ins_state = fetch_data(query_ins_state)
        if not df_ins_state.empty:
            df_ins_state['state'] = df_ins_state['state'].str.replace('-', ' ').str.title()
            fig_ins_state = px.bar(df_ins_state, x='state', y='Total_Policies', title=f'Top 10 States for {year}, Q{quarter}', color='Total_Policies')
            st.plotly_chart(fig_ins_state, use_container_width=True)
        else:
            st.warning("No data for state-wise insurance.")
    with col2:
        st.markdown("#### Overall Growth of Insurance Policies")
        query_ins_line = """
            SELECT year, SUM(insurance_count) as Total_Policies
            FROM aggregated_insurance GROUP BY year ORDER BY year;
        """
        df_ins_line = fetch_data(query_ins_line)
        if not df_ins_line.empty:
            fig_ins_line = px.line(df_ins_line, x='year', y='Total_Policies', title='Overall Growth of Insurance Policies Sold', markers=True)
            st.plotly_chart(fig_ins_line, use_container_width=True)
        else:
            st.warning("No data for insurance growth trend.")



# =======================================================================================================================
# Business Case 4: Top Performers: Transactions - CORRECTED
# =======================================================================================================================
elif analysis_choice == "Top Performers: Transactions":
    st.subheader(f"Top Performers by Transaction Value for {year} - Q{quarter}")
    
    state_query = "SELECT DISTINCT state FROM top_transaction ORDER BY state ASC;"
    states_df = fetch_data(state_query)
    if not states_df.empty:
        selected_state = st.sidebar.selectbox("Select a State to Analyze", options=states_df['state'].tolist())

        st.markdown(f"#### Analyzing Top Districts and Pincodes in **{selected_state.replace('-', ' ').title()}**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Top 10 Districts by Transaction Value")
            query_dist = f"""
                SELECT entity_name as District, SUM(transaction_amount) as Total_Amount
                FROM top_transaction 
                WHERE year = {year} AND quarter = {quarter} AND entity_type = 'district' AND state = '{selected_state}'
                GROUP BY entity_name ORDER BY Total_Amount DESC LIMIT 10;
            """
            df_dist = fetch_data(query_dist)
            if not df_dist.empty:
                # --- THIS IS THE CHANGE: Using Pie Chart ---
                fig_dist = px.pie(df_dist, values='Total_Amount', names='District', title='Top 10 Districts')
                st.plotly_chart(fig_dist, use_container_width=True)
            else:
                st.warning("No district data available for this state.")
        
        with col2:
            st.markdown("##### Top 10 Pincodes by Transaction Value")
            query_pin = f"""
                SELECT entity_name as Pincode, SUM(transaction_amount) as Total_Amount
                FROM top_transaction 
                WHERE year = {year} AND quarter = {quarter} AND entity_type = 'pincode' AND state = '{selected_state}'
                GROUP BY entity_name ORDER BY Total_Amount DESC LIMIT 10;
            """
            df_pin = fetch_data(query_pin)
            if not df_pin.empty:
                # --- THIS IS THE CHANGE: Using Pie Chart and ensuring Pincode is a string ---
                df_pin['Pincode'] = df_pin['Pincode'].astype(str)
                fig_pin = px.pie(df_pin, values='Total_Amount', names='Pincode', title='Top 10 Pincodes')
                st.plotly_chart(fig_pin, use_container_width=True)
            else:
                st.warning("No pincode data available for this state.")

# =======================================================================================================================
# Business Case 5: Top Performers: Users - CORRECTED
# =======================================================================================================================
elif analysis_choice == "Top Performers: Users":
    st.subheader(f"Top Performers by Registered Users for {year} - Q{quarter}")
    
    state_query = "SELECT DISTINCT state FROM top_user ORDER BY state ASC;"
    states_df = fetch_data(state_query)
    if not states_df.empty:
        selected_state = st.sidebar.selectbox("Select a State to Analyze", options=states_df['state'].tolist())

        st.markdown(f"#### Analyzing Top Districts and Pincodes in **{selected_state.replace('-', ' ').title()}**")
        
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Top 10 Districts by Registered Users")
            query_dist_users = f"""
                SELECT entity_name as District, SUM(registered_users) as Total_Users
                FROM top_user 
                WHERE year = {year} AND quarter = {quarter} AND entity_type = 'district' AND state = '{selected_state}'
                GROUP BY entity_name 
                ORDER BY Total_Users DESC LIMIT 10;
            """
            df_dist_users = fetch_data(query_dist_users)
            if not df_dist_users.empty:
                fig_dist = px.bar(df_dist_users, x='District', y='Total_Users', title='Top 10 Districts by Registered Users', color='Total_Users')
                st.plotly_chart(fig_dist, use_container_width=True)
            else:
                st.warning("No district data available for this state.")
                
        with col2:
            st.markdown("##### Top 10 Pincodes by Registered Users")
            query_pin_users = f"""
                SELECT entity_name as Pincode, SUM(registered_users) as Total_Users
                FROM top_user 
                WHERE year = {year} AND quarter = {quarter} AND entity_type = 'pincode' AND state = '{selected_state}'
                GROUP BY entity_name ORDER BY Total_Users DESC LIMIT 10;
            """
            df_pin_users = fetch_data(query_pin_users)
            if not df_pin_users.empty:
                # --- THIS IS THE FIX ---
                # Convert Pincode to a string to use it as a label for the bar chart.
                df_pin_users['Pincode'] = df_pin_users['Pincode'].astype(str)
                fig_pin_users = px.bar(df_pin_users, y='Pincode', x='Total_Users', orientation='h', title='Top 10 Pincodes')
                st.plotly_chart(fig_pin_users, use_container_width=True)
            else:
                st.warning("No pincode data available for this state.")