import streamlit as st
import pandas as pd
import plotly.express as px
import warnings
import data # Import functions from data.py
warnings.filterwarnings('ignore')

def create_tx_fees_chart(df, chart_type):
    """Gas Fee Chart"""
    # Custom color for each chain
    color_map = {
        'ETH': '#716b94',  
        'AVAX': '#E84142',  
        'BTC': '#F7931A',  
        'BNB': '#F3BA2F',  
        'TRX': '#FF0013',  
        'SOL': '#14F195' 
    }
    
    # Handle relative (percentage) chart type
    if chart_type == "relative":
        # Create a copy to avoid modifying original data
        plot_df = df.copy()
        
        # Calculate percentage for each group
        monthly_totals = plot_df.groupby('month')['gas_fees'].transform('sum')
        plot_df['percentage'] = plot_df['gas_fees'] / monthly_totals
        
        # Create chart with percentage data
        fig = px.bar(
            plot_df,
            x='month',
            y='percentage',  # Use calculated percentages
            color='category',
            title='Tx Fees by Blockchain (Percentage)',
            color_discrete_map=color_map,
            labels={'month': 'Month', 'percentage': 'Percentage', 'category': 'Blockchain'}
        )
        
        # Stack the bars
        fig.update_layout(
            barmode='stack',  # Use stack with normalized data
            xaxis_tickformat='%Y-%m',
            yaxis_title='Percentage (%)',
            legend_title='Blockchain',
            height=600
        )
        
        # Format y-axis as percentage
        fig.update_yaxes(tickformat=".0%")
    else:
        # Original absolute value chart
        fig = px.bar(
            df,
            x='month',
            y='gas_fees',
            color='category',
            title='Monthly Gas Fees by Blockchain',
            color_discrete_map=color_map,
            labels={'month': 'Month', 'gas_fees': 'Gas Fees', 'category': 'Blockchain'}
        )
        
        fig.update_layout(
            barmode='stack',
            xaxis_tickformat='%Y-%m',
            yaxis_title='Gas Fees',
            legend_title='Blockchain',
            height=600
        )
    
    return fig

def display_metrics_and_table(df):
    """Gas Fee Table & Metrics"""
    try:
        # total gas fees for each blockchain
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
        st.subheader("Monthly Gas Fees by Blockchain")
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

        # Change the index name from "month" to "Month"
        pivoted_df.index.name = "Month"

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
        page_title="Cross-chain Analysis",
        page_icon="📊",
        layout="wide"
    )

    # Add title
    st.title("📊 Cross-chain Analysis")

    # Create tabs
    tab_icons = {
        "Transaction Fees": "⛽️",
        "Transaction Count": "📈"
    }

    tabs = st.tabs([f"{tab_icons[tab]} {tab}" for tab in tab_icons.keys()])

    # Try to fetch data using the functions in data.py
    try:
        with st.spinner('Fetching data...'):
            # Check if these functions exist in your data.py module
            # and use the ones that match your actual implementation
            if hasattr(data, 'initialize_aws'):
            # Pass your AWS credentials directly
                data.initialize_aws(
                    access_key='AWS_ACCESS_KEY',
                    secret_key='AWS_SECRET_KEY',
                    bucket='seoulcalibur',  # Your bucket name
                    validator_file='DUNE_QUERY_4667263.json'  # File name for Transaction Fees
                )

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

    # Tab 1: Transaction Fees
    with tabs[0]:
        st.header("Transaction Fees")

        try:
            # Create and display chart
            fig = create_tx_fees_chart(filtered_df, "stack")
            st.plotly_chart(fig, use_container_width=True, key="tx_fees_stack")

            # Add Percentage Chart
            fig = create_tx_fees_chart(filtered_df, "relative")
            st.plotly_chart(fig, use_container_width=True, key="tx_fees_relative")

            # Display metrics and table
            display_metrics_and_table(filtered_df)

        except Exception as e:
            st.error(f"Error in L1 Transactions tab: {str(e)}")

    # Tab 2: Transaction Counts
    with tabs[1]:
        st.header("Transaction Counts")

        try:
            # Create and display the same chart for now
            fig = create_tx_fees_chart(filtered_df, "relative")
            st.plotly_chart(fig, use_container_width=True, key="counts_chart")

            # Display metrics and table
            display_metrics_and_table(filtered_df)

        except Exception as e:
            st.error(f"Error in L1 Fees tab: {str(e)}")
    


if __name__ == '__main__':
    main()
