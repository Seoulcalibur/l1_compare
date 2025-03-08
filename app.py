import streamlit as st
import pandas as pd
import plotly.express as px
import warnings

warnings.filterwarnings('ignore')

# Import functions from data.py
import data

def create_transaction_fees_chart_stack(df):
    """Create a bar chart of transaction fees by blockchain"""
    # Create a copy of the dataframe to avoid modifying the original
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
    
    # Fix for tooltip format - using proper value formatting for transaction fees
    fig.update_traces(
        hovertemplate='<b>Blockchain</b>: %{customdata}<br>' +
                      '<b>Month</b>: %{x|%b %Y}<br>' +
                      '<b>Transaction Fees</b>: $%{y:,.2f}<extra></extra>',
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
    """Create a 100% stacked bar chart of gas fees by blockchain"""
    # Define custom colors for each blockchain
    color_map = {
        'ETH': '#716b94',  # Ethereum blue
        'AVAX': '#E84142',  # Polygon purple
        'BTC': '#F7931A',  # Arbitrum blue
        'BNB': '#F3BA2F',  # Optimism red
        'TRX': '#FF0013',  # Avalanche red
        'SOL': '#14F195'  # Binance yellow
    }
    
    # Create a copy of the dataframe to avoid modifying the original
    df_copy = df.copy()
    
    # Group by month and calculate the total gas fees for each month
    monthly_totals = df_copy.groupby('month')['gas_fees'].sum().reset_index()
    monthly_totals.rename(columns={'gas_fees': 'total_fees'}, inplace=True)
    
    # Merge the monthly totals back with the original dataframe
    df_pct = pd.merge(df_copy, monthly_totals, on='month')
    
    # Calculate the percentage of each blockchain's gas fees relative to the total
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
    
    fig.update_layout(
        barmode='stack',  # Use 'stack' for 100% chart
        xaxis_tickformat='%Y-%m',
        yaxis_title='Percentage of Gas Fees',
        yaxis=dict(ticksuffix='%'),  # Add % suffix to y-axis
        legend_title='Blockchain',
        height=600
    )
    
    return fig

def display_metrics_and_table(df):
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


# Function to generate sample data for testing
def get_sample_data():
    """Generate sample data when real data can't be accessed"""
    import datetime as dt
    import random

    data = []
    categories = ['ETH', 'BTC', 'BNB', 'SOL', 'AVAX', 'TRX']

    # Generate sample data for the last 12 months
    current_date = dt.datetime.now()

    for i in range(12):
        month = current_date - dt.timedelta(days=30 * i)
        for category in categories:
            # Random gas fees between 1000 and 10000
            gas_fee = random.randint(1000, 10000)
            data.append({
                'month': month.strftime('%Y-%m-%d'),
                'category': category,
                'gas_fees': gas_fee
            })

    return pd.DataFrame(data)


def main():
    # Set page config
    st.set_page_config(
        page_title="Blockchain Comparison Analysis",
        page_icon="📊",
        layout="wide"
    )

    # Add title
    st.title("📊 Blockchain Comparison Analysis2")

    # Create tabs
    tab_icons = {
        "L1 Transaction Fees": "⛽",
        "L1 Transactions Per Second": "⚡"
    }

    tabs = st.tabs([f"{tab_icons[tab]} {tab}" for tab in tab_icons.keys()])

    # Try to fetch data using the functions in data.py
    try:
        with st.spinner('Fetching data...'):
            # Check if these functions exist in your data.py module
            # and use the ones that match your actual implementation

            # Try different function names that might be in your data.py
            if hasattr(data, 'initialize_aws'):
                data.initialize_aws()
            # Try different ways to get the data
            if hasattr(data, 'fetch_tx_fee'):
                df = data.fetch_tx_fee()
            elif hasattr(data, 'fetch_json_data'):
                df = pd.DataFrame(data.fetch_json_data("dune_query_4667263.json"))
            else:
                st.warning("Could not find appropriate functions in data.py. Using sample data instead.")
                df = get_sample_data()

            if df is None or df.empty:
                st.warning("No data returned from data.py. Using sample data instead.")
                df = get_sample_data()
    except Exception as e:
        st.error(f"Error accessing data: {str(e)}")
        st.info("Using sample data for demonstration")
        df = get_sample_data()

    # Apply filters (common for both tabs)
    filtered_df = apply_filters(df)

    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
        return

    # Tab 1: L1 Transactions
    with tabs[0]:
        st.header("L1 Transaction Fees")

        try:
            # Create and display chart
            fig = create_transaction_fees_chart_stack(filtered_df)
            st.plotly_chart(fig, use_container_width=True, key="transaction_fee_stack")

            fig = create_transaction_fees_chart_relative(filtered_df)
            st.plotly_chart(fig, use_container_width=True, key="transaction_fee_relative")

            # Display metrics and table
            display_metrics_and_table(filtered_df)

        except Exception as e:
            st.error(f"Error in L1 Transactions tab: {str(e)}")

    # Tab 2: L1 Fees (same content as placeholder)
    with tabs[1]:
        st.header("L1 Gas Fees")

        try:
            # Create and display the same chart for now
            fig = create_transaction_fees_chart_relative(filtered_df)
            st.plotly_chart(fig, use_container_width=True, key="transaction_fee_relative")

            # Display metrics and table
            display_metrics_and_table(filtered_df)

        except Exception as e:
            st.error(f"Error in L1 Fees tab: {str(e)}")


if __name__ == '__main__':
    main()
