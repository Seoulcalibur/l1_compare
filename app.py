import streamlit as st
import pandas as pd
import plotly.express as px
import warnings

warnings.filterwarnings('ignore')

# Import data.py
import data

# Transaction Fees
def create_transaction_fees_chart_stack(df):
    """Bar chart of transaction fees by blockchain"""
    df_copy = df.copy()
    # Define custom colors for each blockchain
    color_map = {
        'ETH': '#716b94',
        'AVAX': '#E84142',  
        'BTC': '#F7931A',  
        'BNB': '#F3BA2F',  
        'TRX': '#FF0013',  
        'SOL': '#14F195'  
    }
    fig = px.bar(
        df_copy,
        x='month',
        y='gas_fees',
        color='category',
        title='Monthly Transaction Fees by Blockchain',
        color_discrete_map=color_map,  # Add custom colors
        labels={
            'month': 'Month',
            'gas_fees': 'Transaction Fees',
            'category': 'Blockchain'
        }
    )
    
    # Tool Tip Formatting
    fig.update_traces(
        hovertemplate='<b>Blockchain</b>: %{customdata}<br>' +
                      '<b>Month</b>: %{x|%b %Y}<br>' +
                      '<b>Transaction Fees</b>: $%{y:,.0f}<extra></extra>',
        customdata=df_copy['category']
    )
    
    fig.update_layout(
        barmode='stack',
        xaxis_tickformat='%Y-%m',
        yaxis_title='Transaction Fees',
        legend_title='Blockchain',
        height=600
    )
    
    return fig

def create_transaction_fees_chart_relative(df):
    """100% stacked bar chart of transaction fees by blockchain"""
    # Define custom colors for each blockchain
    color_map = {
        'ETH': '#716b94', 
        'AVAX': '#E84142', 
        'BTC': '#F7931A',  
        'BNB': '#F3BA2F',  
        'TRX': '#FF0013',  
        'SOL': '#14F195' 
    }
    
    df_copy = df.copy()
    
    # Group by month and calculate the total gas fees for each month
    monthly_totals = df_copy.groupby('month')['gas_fees'].sum().reset_index()
    monthly_totals.rename(columns={'gas_fees': 'total_fees'}, inplace=True)
    
    # Merge the monthly totals back with the original dataframe
    df_pct = pd.merge(df_copy, monthly_totals, on='month')
    
    # Calculate the percentage of each blockchain's transaction fees relative to the total
    df_pct['percentage'] = (df_pct['gas_fees'] / df_pct['total_fees']) * 100
    
    fig = px.bar(
        df_pct,
        x='month',
        y='percentage',
        color='category',
        title='Monthly Gas Fees by Blockchain (Percentage)',
        color_discrete_map=color_map,  # Add custom colors
        labels={
            'month': 'Month',
            'percentage': 'Percentage of Gas Fees',
            'category': 'Blockchain'
        }
    )

    fig.update_traces(
    hovertemplate='<b>Blockchain</b>: %{customdata}<br>' +
                   '<b>Month</b>: %{x|%b %Y}<br>' +
                   '<b>Percentage of Gas Fees</b>: %{y:.2f}%<extra></extra>',
    customdata=df_pct['category']
    )

    # Tool Tip Formatting
    fig.update_layout(
        barmode='stack', 
        xaxis_tickformat='%Y-%m',
        yaxis_title='Percentage of Gas Fees',
        yaxis=dict(ticksuffix='%'), 
        legend_title='Blockchain',
        height=600
    )
    
    return fig

def display_metrics_and_table_transaction_fees(df):
    """Display metrics and data table for the gas fees"""
    try:
        # Get total gas fees for each blockchain
        blockchain_totals = df.groupby('category')['gas_fees'].sum().sort_values(ascending=False)

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
        st.subheader("🔍 Monthly Transaction Fees by Blockchain")

        # Pivot the dataframe to show categories as columns
        pivoted_df = df.pivot(
            index='month',
            columns='category',
            values='gas_fees'
        )

        # Sort the index by date
        pivoted_df = pivoted_df.sort_index(ascending=False)

        # Add a Total column
        pivoted_df['Total'] = pivoted_df.sum(axis=1)

        # Rename the index to have proper capitalization
        pivoted_df.index.name = 'Month'

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
                {'selector': 'th.col_heading', 'props': [('text-align', 'right')]}, 
                {'selector': 'th.row_heading', 'props': [('text-align', 'left')]},   
                {'selector': '', 'props': [('width', '100%')]}
            ]),
            width=1200,  # Overall table width
            height=600  # Overall table height
        )

    except Exception as e:
        st.error(f"Error displaying statistics: {str(e)}")

def apply_filters(df):
    """Apply user-selected filters to the dataframe"""
    # Process data
    if not pd.api.types.is_datetime64_any_dtype(df['month']):
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

    return filtered_df

## Transactions Per Seconds
def create_tps_chart(df):
    """Create a line chart of transactions per second by blockchain"""
    df_copy = df.copy()
    
    # Ensure date is in datetime format
    if not pd.api.types.is_datetime64_any_dtype(df_copy['block_date']):
        df_copy['block_date'] = pd.to_datetime(df_copy['block_date'])
    
    # Define custom colors for each blockchain
    color_map = {
        'solana': '#14F195',    # Bright green
        'tron': '#FF0013',      # Red
        'ethereum': '#716b94',  # Purple-blue
        'bitcoin': '#F7931A',   # Orange
        'base': '#0052FF',      # Blue
        'arbitrum': '#28A0F0',  # Light blue
        'optimism': '#FF0420',  # Bright red
        'ton': '#0098EA',       # Blue
        'linea': '#5F6FFF',     # Blue-purple
        'zksync': '#8E55FF',    # Purple
        'celo': '#FCFF52',      # Yellow
        'sei': '#FF00FF',       # Magenta
        'zkevm': '#6A00EA',     # Dark purple
        'scroll': '#FFA4E3',    # Pink
        'zora': '#A1723A'       # Brown
    }
    
    # Create line chart
    fig = px.line(
        df_copy,
        x='block_date',
        y='tps',
        color='blockchain',
        title='Transactions Per Second (TPS) by Blockchain',
        color_discrete_map=color_map,
        labels={
            'block_date': 'Date',
            'tps': 'Transactions Per Second',
            'blockchain': 'Blockchain'
        }
    )
    
    # Format tooltip
    fig.update_traces(
        hovertemplate='<b>%{customdata}</b><br>' +
                      '<b>Date</b>: %{x|%b %d, %Y}<br>' +
                      '<b>TPS</b>: %{y:,.1f}<extra></extra>',
        customdata=df_copy['blockchain']
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Transactions Per Second',
        legend_title='Blockchain',
        height=600,
        hovermode="closest"
    )
    
    return fig

def display_metrics_and_table_tps(df):
    """Display metrics and data table for TPS data"""
    try:
        # Get latest TPS for each blockchain
        latest_date = df['block_date'].max()
        latest_tps = df[df['block_date'] == latest_date].sort_values('tps', ascending=False)
        
        # Create a column for the top 3 blockchains by TPS
        st.subheader("Top Blockchains by TPS")
        cols = st.columns(min(3, len(latest_tps)))
        
        # Display metrics for top 3 blockchains
        for idx, (_, row) in enumerate(latest_tps.head(3).iterrows()):
            if idx < 3:  # Show only top 3
                with cols[idx]:
                    st.metric(
                        f"{row['blockchain'].title()}",
                        f"{row['tps']:,.1f} TPS"
                    )
        
        # Data table
        st.subheader("🔍 Transactions Per Second by Blockchain")
        
        # Pivot the dataframe to show blockchains as columns
        pivoted_df = df.pivot_table(
            index='block_date',
            columns='blockchain',
            values='tps',
            aggfunc='mean'  # In case there are multiple entries for same date/blockchain
        )
        
        # Sort the index by date (descending)
        pivoted_df = pivoted_df.sort_index(ascending=False)
        
        # Rename the index
        pivoted_df.index.name = 'Date'
        
        # Format and display the table
        st.dataframe(
            pivoted_df.style
            .format('{:,.1f}')
            .set_properties(**{
                'text-align': 'right',
                'font-family': 'monospace'
            })
            .set_table_styles([
                {'selector': 'th', 'props': [('min-width', '100px'), ('max-width', '200px')]},
                {'selector': 'td', 'props': [('min-width', '100px'), ('max-width', '200px')]},
                {'selector': 'th.col_heading', 'props': [('text-align', 'right')]},
                {'selector': 'th.row_heading', 'props': [('text-align', 'left')]},
                {'selector': '', 'props': [('width', '100%')]}
            ]),
            width=1200,  # Overall table width
            height=600  # Overall table height
        )
        
    except Exception as e:
        st.error(f"Error displaying TPS statistics: {str(e)}")

def apply_filters_tps(df):
    """Apply user-selected filters to the TPS dataframe"""
    # Process data
    if not pd.api.types.is_datetime64_any_dtype(df['block_date']):
        df['block_date'] = pd.to_datetime(df['block_date'])
    
    # Sidebar filters (we'll reuse the existing sidebar section)
    # Date filter
    min_date = df['block_date'].min()
    max_date = df['block_date'].max()
    
    # Get existing date range if it exists, otherwise set new one
    if 'date_range' in st.session_state:
        date_range = st.session_state.date_range
    else:
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date(),
            key="tps_date_range"
        )
    
    # Category filter for blockchains
    blockchains = sorted(df['blockchain'].unique())
    
    # Get existing selected categories if they exist, otherwise set new ones
    if 'selected_blockchains' in st.session_state:
        selected_blockchains = st.session_state.selected_blockchains
    else:
        selected_blockchains = st.sidebar.multiselect(
            "Select Blockchains",
            options=blockchains,
            default=blockchains,
            key="tps_blockchains"
        )
    
    # Filter data
    mask = (df['block_date'].dt.date >= date_range[0]) & (df['block_date'].dt.date <= date_range[1])
    filtered_df = df[mask]
    filtered_df = filtered_df[filtered_df['blockchain'].isin(selected_blockchains)]
    
    return filtered_df

def fetch_tps_data(json_file=None):
    """
    Fetch TPS data from specified JSON file
    
    Args:
        json_file (str, optional): JSON file to use
        
    Returns:
        pandas.DataFrame: DataFrame with block_date, blockchain, and tps columns
    """
    if s3_client is None:
        logger.error("AWS not initialized. Call initialize_aws() first.")
        return None
    
    try:
        # Use specified file
        if json_file is None:
            logger.error("No JSON file name provided for TPS data")
            return None
            
        data = fetch_json_data(json_file)
        if data:
            df = pd.DataFrame(data)
            if all(col in df.columns for col in ['block_date', 'blockchain', 'tps']):
                return df[['block_date', 'blockchain', 'tps']]
            else:
                missing_cols = [col for col in ['block_date', 'blockchain', 'tps'] if col not in df.columns]
                logger.error(f"Missing columns in TPS data from {json_file}: {missing_cols}")
                return None
        return None
    except Exception as e:
        logger.error(f"Error processing TPS data from {json_file}: {e}")

# Function to generate sample data for testing - ONLY FOR TESTING
# def get_sample_data():
#     """Generate sample data when real data can't be accessed"""
#     import datetime as dt
#     import random

#     data = []
#     categories = ['ETH', 'BTC', 'BNB', 'SOL', 'AVAX', 'TRX']

#     # Generate sample data for the last 12 months
#     current_date = dt.datetime.now()

#     for i in range(12):
#         month = current_date - dt.timedelta(days=30 * i)
#         for category in categories:
#             # Random gas fees between 1000 and 10000
#             gas_fee = random.randint(1000, 10000)
#             data.append({
#                 'month': month.strftime('%Y-%m-%d'),
#                 'category': category,
#                 'gas_fees': gas_fee
#             })

#     return pd.DataFrame(data)


def main():
    # Set page config
    st.set_page_config(
        page_title="Blockchain Comparison Analysis",
        page_icon="📊",
        layout="wide"
    )

    # Add title
    st.title("📊 Blockchain Comparison Analysis")

    # Create tabs
    tab_icons = {
        "L1 Transaction Fees": "⛽",
        "L1 Transactions Per Second": "⚡"
    }

    tabs = st.tabs([f"{tab_icons[tab]} {tab}" for tab in tab_icons.keys()])

    # Fetch data using the functions in data.py
    try:
        with st.spinner('Fetching data...'):
            # Initialize AWS
            if hasattr(data, 'initialize_aws'):
                data.initialize_aws()
                
            # Fetch transaction fee data
            if hasattr(data, 'fetch_tx_fee'):
                df_tx_fee = data.fetch_tx_fee("DUNE_QUERY_4667263.json")
            elif hasattr(data, 'fetch_json_data'):
                df_tx_fee = pd.DataFrame(data.fetch_json_data("DUNE_QUERY_4667263.json"))
            else:
                st.warning("Could not find appropriate functions in data.py for transaction fees.")
                df_tx_fee = None
                ## df_tx_fee = get_sample_data() -- ONLY FOR TESTING

            # Fetch TPS data
            if hasattr(data, 'fetch_tps_data'):
                df_tps = data.fetch_tps_data("DUNE_QUERY_4660344.json")  # Use your actual query ID
            elif hasattr(data, 'fetch_json_data'):
                df_tps = pd.DataFrame(data.fetch_json_data("DUNE_QUERY_4660344.json"))
            else:
                st.warning("Could not find appropriate functions in data.py for TPS data.")
                df_tps = None
                
            # Check if data was returned
            if df_tx_fee is None or df_tx_fee.empty:
                st.warning("No transaction fee data returned.")
                
            if df_tps is None or df_tps.empty:
                st.warning("No TPS data returned.")
    
    except Exception as e:
        st.error(f"Error accessing data: {str(e)}")
        st.info("Using sample data for demonstration")
        ##df = get_sample_data()

    # Apply filters (common for both tabs)
    filtered_df_tx_fee = apply_filters(df_tx_fee)

    if filtered_df_tx_fee.empty:
        st.warning("No data available for the selected filters.")
        return

    # Tab 1: L1 Transaction Fees
    with tabs[0]:
        st.header("⛽ L1 Transaction Fees")

        try:
            # Create container with custom padding
            chart_container = st.container()

            with chart_container:
            # Create and display chart
                fig = create_transaction_fees_chart_stack(filtered_df_tx_fee)
                st.plotly_chart(fig, use_container_width=True, key="transaction_fee_stack")
                
                # Add compact spacing between charts
                st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

                fig = create_transaction_fees_chart_relative(filtered_df_tx_fee)
                st.plotly_chart(fig, use_container_width=True, key="transaction_fee_relative")

                # Display metrics and table
                display_metrics_and_table_transaction_fees(filtered_df_tx_fee)

        except Exception as e:
            st.error(f"Error in L1 Transactions tab: {str(e)}")

    # Tab 2: L1 Fees (same content as placeholder)
    with tabs[1]:
        st.header("⚡ L1 Transactions Per Second")

        try:
            if df_tps is not None and not df_tps.empty:
                # Apply filters
                filtered_df_tps = apply_filters_tps(df_tps)
                
                if not filtered_df_tps.empty:
                    # Create and display chart
                    fig = create_tps_chart(filtered_df_tps)
                    st.plotly_chart(fig, use_container_width=True, key="tps_chart")

                    # Display metrics and table
                    display_metrics_and_table_tps(filtered_df_tps)
                else:
                    st.warning("No TPS data available for the selected filters.")
            else:
                st.warning("No TPS data available to display.")
        except Exception as e:
            st.error(f"Error in L1 Transactions Per Second tab: {str(e)}")

if __name__ == '__main__':
    main()
