import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
from requests import get, post
import datetime as dt
import time
import warnings
warnings.filterwarnings('ignore')
import matplotlib
matplotlib.use('Agg')

st.set_page_config(
    page_title="Blockchain Gas Fees Analysis",
    page_icon="📊",
    layout="wide"
)

# Pandas display settings
dim = 500
pd.set_option('display.max_rows', dim)
pd.set_option('display.max_columns', dim)
pd.set_option('display.width', dim)
pd.set_option('display.float_format', lambda x: '%.6f' % x)
break_section_str, break_str = '#' * 100, '=' * 100
delim = ' | '

@st.cache_data  # Cache the function to improve performance

def query_dune(query_id):
    # ==================================================================================================================
    # Def Dune Functions
    # ==================================================================================================================
    def make_api_url(query_id):
        """
        We shall use this function to generate a URL to call the API.
        """
        BASE_URL = 'https://api.dune.com/api/v1/query/'
        url = BASE_URL + query_id + "/results"

        return url

    def get_query_results(execution_id):
        """
        Takes in an execution ID.
        Fetches the results returned from the query using the API
        Returns the results response object
        """

        url = make_api_url("execution", "results", execution_id)
        response = get(url, headers=HEADER, verify=False)

        return response


    # ==================================================================================================================
    API_KEY = "Wq7rm5AaPh8rkmes6Ce2aOGOHeKHMaQA"
    url = make_api_url(query_id)
    headers = {"X-DUNE-API-KEY": API_KEY}
    response = requests.request("GET", url, headers=headers, verify=False)
    df = pd.json_normalize(response.json())
    df = pd.json_normalize(df['result.rows'])
    df = df.transpose()
    df_dune = pd.json_normalize(df[0])

    print(break_str)
    print('Executing DUNE query: {}'.format(query_id))
    print(break_str)


    is_complete = False
    while is_complete == False:
        query_status = response.json()['state']
        if query_status == 'QUERY_STATE_COMPLETED':
            print('> Status: {}'.format(query_status))
            print('> Execution ID: {}'.format(response.json()['execution_id']))
            print('> Query ID: {}'.format(response.json()['query_id']))
            query_runtime = pd.to_datetime(response.json()['execution_ended_at']) - pd.to_datetime(
                response.json()['execution_started_at'])
            print('> Runtime: {}'.format(query_runtime))
            print('Writing to DataFrame...')
            is_complete = True
        else:
            print('> Status: {}'.format(query_status))
            print('> Execution ID: {}'.format(response.json()['execution_id']))
            print('Query [{}] Executing...'.format(query_id))
            time.sleep(10)
            query_call_ct += 1
            if query_call_ct >= 10:
                cancel_query_execution(response.json()['execution_id'])
                print('ERROR: Query run-time limit exceeded (>= {} Seconds). Query cancelled...'.format(
                    query_call_ct * 10))
                print('> Status: QUERY_CANCELLED')
                print('> Execution ID: {}'.format(response.json()['execution_id']))
                print('Query: {}'.format(query_id))
                is_complete = True

    try:
        df = pd.DataFrame(response.json()['result']['rows'])
        df['VALUATION_DATE_UTC'] = pd.to_datetime(dt.datetime.utcnow())
    except Exception as e:
        print('ERROR: Query failed.')
        print(response.json())
        print(e)
        df = pd.DataFrame()

    return df_dune

query_id = '4667263'

df = query_dune(query_id)


def main():
    # Add title
    st.title("📊 Blockchain Tx Fee Comparison")

    # Query Dune
    query_id = '4667263'
    df = query_dune(query_id)

    if df.empty:
        st.error("No data available. Please check your Dune query.")
        return

    # Process data
    df['month'] = pd.to_datetime(df['month'])

    # Sidebar filters
    st.sidebar.header("📅 Filter Data")

    # Date filter
    min_date = df['month'].min()
    max_date = df['month'].max()
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date(),
    )

    # Category filter
    categories = sorted(df['category'].unique())
    selected_categories = st.sidebar.multiselect(
        "Select Blockchain Categories",
        options=categories,
        default=categories
    )

    # Filter data
    mask = (df['month'].dt.date >= date_range[0]) & (df['month'].dt.date <= date_range[1])
    filtered_df = df[mask]
    filtered_df = filtered_df[filtered_df['category'].isin(selected_categories)]

    # Create chart
    try:

        # Define custom colors for each blockchain
        color_map = {
            'ETH': '#716b94',  # Ethereum blue
            'AVAX': '#E84142',  # Polygon purple
            'BTC': '#F7931A',  # Arbitrum blue
            'BNB': '#F3BA2F',  # Optimism red
            'TRX': '#FF0013',  # Avalanche red
            'SOL': '#14F195'  # Binance yellow
        }

        fig = px.bar(
            filtered_df,
            x='month',
            y='gas_fees',
            color='category',
            title='Monthly Gas Fees by Blockchain',
            color_discrete_map=color_map,  # Add custom colors
            labels={
                'month': 'Month',
                'gas_fees': 'Gas Fees',
                'category': 'Blockchain'
            }
        )

        fig.update_layout(
            barmode='stack',
            xaxis_tickformat='%Y-%m',
            yaxis_title='Gas Fees',
            legend_title='Blockchain',
            height=600
        )

        # Display chart
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating visualization: {str(e)}")

    # Summary stats and data table
    try:
        # Get total gas fees for each blockchain
        blockchain_totals = filtered_df.groupby('category')['gas_fees'].sum().sort_values(
            ascending=False)  # Changed to gas_fees

        # Create a column for each blockchain (up to the top 3 by total fees)
        cols = st.columns(min(3, len(blockchain_totals)))

        # Display metrics for each blockchain
        for idx, (blockchain, total) in enumerate(blockchain_totals.items()):
            if idx < 3:  # Show only top 3 to fit in columns
                with cols[idx]:
                    st.metric(
                        f"{blockchain} Total Fees",
                        f"${total:,.0f}"
                    )

        # Data table
        st.subheader("🔍 Monthly Gas Fees by Blockchain")

        # Pivot the dataframe to show categories as columns
        pivoted_df = filtered_df.pivot(
            index='month',
            columns='category',
            values='gas_fees'  # Changed from tx_fees to gas_fees
        )

        # Sort the index by date
        pivoted_df = pivoted_df.sort_index(ascending=False)

        # Add a Total column
        pivoted_df['Total'] = pivoted_df.sum(axis=1)

        # Format and display the table
        st.dataframe(
            pivoted_df.style
            .format('${:,.0f}')
            .set_properties(**{
                'text-align': 'right',
                'font-family': 'monospace'
            })
            .set_table_styles([
                {'selector': 'th', 'props': [('min-width', '100px'), ('max-width', '200px')]},
                {'selector': 'td', 'props': [('min-width', '100px'), ('max-width', '200px')]},
                {'selector': 'th.col_heading', 'props': [('text-align', 'center')]},
                {'selector': 'th.row_heading', 'props': [('text-align', 'left')]},
                {'selector': '', 'props': [('width', '100%')]}
            ]),
            width=1200,  # Overall table width
            height=600  # Overall table height
        )

    except Exception as e:
        st.error(f"Error displaying statistics: {str(e)}")


if __name__ == '__main__':
    main()