import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta
import plotly.express as px

# --- App configuration ---
st.set_page_config(page_title="Hotel Financial Reporting Dashboard", layout="wide")
st.title("💼 Hotel Financial Reporting Dashboard")

# --- Custom CSS for Card Borders ---
st.markdown("""
<style>
    /* Target the st.metric component directly */
    div[data-testid="stMetric"] {
        background-color: #f0f2f6; /* Light background for the cards */
        border: 1px solid black; /* Black border */
        border-radius: 5px; /* Slightly rounded corners */
        padding: 15px; /* Padding inside the border for content */
        margin-bottom: 15px; /* Space below each metric card */
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1); /* Subtle shadow for depth */
        text-align: center; /* Center the content within the card */
    }
    /* Adjust the main label of the metric */
    div[data-testid="stMetricLabel"] p {
        font-size: 1.1em; /* Slightly larger font for label */
        font-weight: bold;
        color: #333;
    }
    /* Adjust the value of the metric */
    div[data-testid="stMetricValue"] {
        font-size: 1.8em; /* Larger font for the value */
        font-weight: bolder;
        color: #007bff; /* A color to make the value stand out */
    }
    /* Hide the delta icon if not needed, or style it */
    div[data-testid="stMetricDelta"] svg {
        display: none;
    }
</style>
""", unsafe_allow_html=True)


# --- Configuration for Profit Margin (ASSUMPTION) ---
# Assuming total cost of goods is 70% to 75% of revenue,
# profit margin will be 25% to 30% of revenue.
ASSUMED_PROFIT_MARGIN_PERCENTAGE = 0.25 # 25% profit margin (reflecting 75% cost)

# --- MySQL connection details ---
# IMPORTANT: Replace these with your actual MySQL credentials
DB_HOST = "localhost"
DB_USER = "Mokereri"
DB_PASSWORD = "Kay@2030"
DB_NAME = "hotel_app_db"

# Function to load data from database
@st.cache_data(ttl=60) # Cache data for 60 seconds
def load_data():
    """Loads data from MySQL database tables (users, orders, order_items)."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        if not conn.is_connected():
            st.error("Failed to connect to the database. Please check your MySQL server and credentials.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        # Fetch users
        users_df = pd.read_sql("SELECT * FROM users", conn)

        # Fetch orders and items, then join them in pandas for 'sales' view
        orders_df = pd.read_sql("SELECT * FROM orders", conn)
        order_items_df = pd.read_sql("SELECT * FROM order_items", conn)

        # Merge order items with orders to get a 'sales-like' view
        if not orders_df.empty and not order_items_df.empty:
            sales_data_df = pd.merge(
                order_items_df,
                orders_df[['order_id', 'order_date', 'user_email', 'total_amount', 'status']],
                on='order_id',
                how='left'
            )
            # Calculate total_price per item (already available as price_per_item * quantity)
            sales_data_df['item_total_price'] = sales_data_df['price_per_item'] * sales_data_df['quantity']
        else:
            sales_data_df = pd.DataFrame(columns=[
                'order_id', 'meal_id', 'meal_name', 'quantity', 'price_per_item',
                'order_date', 'user_email', 'total_amount', 'status', 'item_total_price'
            ])
        
        conn.close() # Close connection after fetching data
        return users_df, sales_data_df, orders_df
    except mysql.connector.Error as err:
        st.error(f"Error connecting to database or fetching data: {err}. Please ensure your MySQL server is running and credentials are correct.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Load data
users_df, sales_data_df, orders_df = load_data()

# Check if data was loaded successfully
if users_df.empty and sales_data_df.empty and orders_df.empty:
    st.warning("No data loaded from the database. Please ensure your MySQL server is running and tables exist.")
    st.stop() # Stop the execution if no data

# Convert 'order_date' to datetime for sales_data_df and orders_df
sales_data_df['order_date'] = pd.to_datetime(sales_data_df['order_date'])
orders_df['order_date'] = pd.to_datetime(orders_df['order_date'])


# --- Sidebar Filters ---
st.sidebar.header("Dashboard Filters")

# Time granularity filter
filter_type = st.sidebar.selectbox(
    "Select time granularity for trends",
    options=["hour", "day", "week", "month", "year"],
    index=1 # Default to day for better initial view
)

st.sidebar.markdown("---")
st.sidebar.subheader("Product and Customer Filters")

# Product filter
# Get unique product names from sales_data_df, add 'All', and sort
all_products = ['All'] + sorted(sales_data_df['meal_name'].unique().tolist())
selected_product = st.sidebar.selectbox("Filter by Product", options=all_products)

# Customer filter
# Get unique customer emails from orders_df, add 'All', and sort
all_customers = ['All'] + sorted(orders_df['user_email'].unique().tolist())
selected_customer = st.sidebar.selectbox("Filter by Customer Email", options=all_customers)


# --- Apply Filters to DataFrames ---
# Create copies to avoid modifying the original loaded dataframes
filtered_sales_data_df = sales_data_df.copy()
filtered_orders_df = orders_df.copy()

if selected_product != 'All':
    # Filter sales data by selected product
    filtered_sales_data_df = filtered_sales_data_df[filtered_sales_data_df['meal_name'] == selected_product]
    # Filter orders data to include only orders that contain the selected product
    filtered_orders_df = filtered_orders_df[filtered_orders_df['order_id'].isin(filtered_sales_data_df['order_id'])]

if selected_customer != 'All':
    # Filter orders data by selected customer
    filtered_orders_df = filtered_orders_df[filtered_orders_df['user_email'] == selected_customer]
    # Filter sales data to include only items from the selected customer's orders
    filtered_sales_data_df = filtered_sales_data_df[filtered_sales_data_df['order_id'].isin(filtered_orders_df['order_id'])]

# --- Top Metrics (using filtered data) ---
st.subheader("Key Metrics")

# Calculate metrics using the filtered dataframes
total_revenue = filtered_orders_df['total_amount'].sum() if not filtered_orders_df.empty else 0
total_orders = filtered_orders_df.shape[0] if not filtered_orders_df.empty else 0
# Count unique customers from the filtered orders
total_customers = filtered_orders_df['user_email'].nunique() if not filtered_orders_df.empty else 0
# Find the top product based on quantity from filtered sales data
top_product = filtered_sales_data_df.groupby('meal_name')['quantity'].sum().idxmax() if not filtered_sales_data_df.empty else "N/A"

total_profit = total_revenue * ASSUMED_PROFIT_MARGIN_PERCENTAGE # Calculate total profit
profit_margin_percentage = (total_profit / total_revenue * 100) if total_revenue != 0 else 0 # Calculate profit margin %

# Display metrics in a 3x2 grid
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Revenue", f"Ksh {total_revenue:,.1f}")
with col2:
    st.metric("Total Orders", total_orders)
with col3:
    st.metric("Unique Customers", total_customers)

col4, col5, col6 = st.columns(3)
with col4:
    st.metric("Top-Selling Product", top_product)
with col5:
    st.metric("Total Profit", f"Ksh {total_profit:,.1f}")
with col6:
    st.metric("Profit Margin", f"{profit_margin_percentage:,.1f}%")


## 📈 Sales Trends Over Time (using filtered data)
st.subheader("Sales Trends Over Time")
if not filtered_orders_df.empty:
    # Group data based on selected time granularity
    if filter_type == "hour":
        orders_trend = filtered_orders_df.groupby(filtered_orders_df['order_date'].dt.to_period("H")).sum(numeric_only=True)['total_amount']
    elif filter_type == "day":
        orders_trend = filtered_orders_df.groupby(filtered_orders_df['order_date'].dt.to_period("D")).sum(numeric_only=True)['total_amount']
    elif filter_type == "week":
        orders_trend = filtered_orders_df.groupby(filtered_orders_df['order_date'].dt.to_period("W")).sum(numeric_only=True)['total_amount']
    elif filter_type == "month":
        orders_trend = filtered_orders_df.groupby(filtered_orders_df['order_date'].dt.to_period("M")).sum(numeric_only=True)['total_amount']
    elif filter_type == "year":
        orders_trend = filtered_orders_df.groupby(filtered_orders_df['order_date'].dt.to_period("Y")).sum(numeric_only=True)['total_amount']
    else: # Default to day if something unexpected happens
        orders_trend = filtered_orders_df.groupby(filtered_orders_df['order_date'].dt.to_period("D")).sum(numeric_only=True)['total_amount']

    orders_trend.index = orders_trend.index.astype(str) # Convert PeriodIndex to string for plotting
    fig4 = px.line(x=orders_trend.index, y=orders_trend.values, labels={'x':f'{filter_type.capitalize()} of Order', 'y':'Total Revenue (Ksh)'}, title=f"Total Revenue per {filter_type.capitalize()}")
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.info("No order data available for sales trends with the current filters.")

## ⏳ Sales Performance: This Week vs. Last Week (using filtered data)
st.subheader("Sales Performance: This Week vs. Last Week")
if not filtered_orders_df.empty:
    # Get current date and calculate start of this week and last week
    today = datetime.now()
    # Assuming week starts on Monday (weekday() returns 0 for Monday)
    this_week_start = today - timedelta(days=today.weekday())
    last_week_start = this_week_start - timedelta(weeks=1)

    # Filter data for this week and last week
    this_week_orders = filtered_orders_df[
        (filtered_orders_df['order_date'] >= this_week_start) &
        (filtered_orders_df['order_date'] < today + timedelta(days=1)) # Include today
    ]
    last_week_orders = filtered_orders_df[
        (filtered_orders_df['order_date'] >= last_week_start) &
        (filtered_orders_df['order_date'] < this_week_start)
    ]

    # Group by day of the week for comparison
    # Create a full date range to ensure all days are present, even if no sales
    all_dates = pd.date_range(start=last_week_start, end=today + timedelta(days=1), freq='D')
    daily_sales_this_week = this_week_orders.groupby(this_week_orders['order_date'].dt.date)['total_amount'].sum().reindex(all_dates.date, fill_value=0)
    daily_sales_last_week = last_week_orders.groupby(last_week_orders['order_date'].dt.date)['total_amount'].sum().reindex(all_dates.date, fill_value=0)

    # For plotting, align dates to weekdays (e.g., Monday, Tuesday)
    plot_df = pd.DataFrame({
        'Date': daily_sales_this_week.index,
        'This Week': daily_sales_this_week.values,
        'Last Week': daily_sales_last_week.values
    })
    # Map dates to day names for better X-axis labels
    plot_df['Day'] = plot_df['Date'].apply(lambda x: pd.to_datetime(x).strftime('%A'))

    # Melt DataFrame for Plotly Express
    plot_melted_df = plot_df.melt(id_vars=['Date', 'Day'], var_name='Week', value_name='Revenue')

    fig_weekly_compare = px.line(
        plot_melted_df,
        x='Day',
        y='Revenue',
        color='Week',
        title='Daily Revenue: This Week vs. Last Week',
        markers=True,
        line_shape='linear',
        category_orders={"Day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
    )
    fig_weekly_compare.update_xaxes(title_text="Day of the Week")
    fig_weekly_compare.update_yaxes(title_text="Total Revenue (Ksh)")
    st.plotly_chart(fig_weekly_compare, use_container_width=True)

    # Display comparison metrics
    this_week_total = this_week_orders['total_amount'].sum()
    last_week_total = last_week_orders['total_amount'].sum()
    growth = ((this_week_total - last_week_total) / last_week_total * 100) if last_week_total != 0 else (100 if this_week_total > 0 else 0)

    col_w1, col_w2, col_w3 = st.columns(3)
    col_w1.metric("Revenue This Week", f"Ksh {this_week_total:,.2f}")
    col_w2.metric("Revenue Last Week", f"Ksh {last_week_total:,.2f}")
    col_w3.metric("Week-over-Week Growth", f"{growth:,.2f}%")

else:
    st.info("Not enough order data to compare this week vs. last week sales with the current filters.")

## 🔁 Repeat Customers (using filtered data)
st.subheader("Regular Customers")
if not filtered_orders_df.empty:
    customer_order_counts = filtered_orders_df.groupby('user_email')['order_id'].nunique().reset_index()
    customer_order_counts.columns = ['user_email', 'order_count']

    repeat_customers = customer_order_counts[customer_order_counts['order_count'] > 1]

    if not repeat_customers.empty:
        st.subheader("Customers with Multiple Orders")
        # Merge with users_df to potentially get more user info if needed
        repeat_customers_details = pd.merge(
            repeat_customers,
            users_df[['email']],
            left_on='user_email',
            right_on='email',
            how='left'
        ).drop(columns=['email'])

        st.dataframe(repeat_customers_details.sort_values(by='order_count', ascending=False), use_container_width=True)

        st.markdown(f"**Total Repeat Customers:** {repeat_customers.shape[0]}")
    else:
        st.info("No repeat customers found with the current filters.")
else:
    st.info("No order data available to analyze repeat customers with the current filters.")

## 💸 Profitability Insights (using filtered data)
st.subheader("Profitability Insights")
if not filtered_orders_df.empty:
    # Profit margin breakdown by order status (example)
    profit_by_status = filtered_orders_df.groupby('status')['total_amount'].sum() * ASSUMED_PROFIT_MARGIN_PERCENTAGE
    if not profit_by_status.empty:
        fig_profit_status = px.pie(
            names=profit_by_status.index,
            values=profit_by_status.values,
            title="Assumed Profit by Order Status",
            hole=0.3
        )
        st.plotly_chart(fig_profit_status, use_container_width=True)
    else:
        st.info("No profit data available for breakdown by status with the current filters.")
else:
    st.info("No order data available to calculate profit insights with the current filters.")

## 💰 Revenue per Product (Treemap) (using filtered data)
st.subheader("Revenue per Product")
if not filtered_sales_data_df.empty:
    revenue_products = filtered_sales_data_df.groupby('meal_name')['item_total_price'].sum().sort_values(ascending=False).reset_index()
    if not revenue_products.empty:
        fig_treemap = px.treemap(
            revenue_products,
            path=[px.Constant("All Meals"), 'meal_name'], # Create a hierarchy for the treemap
            values='item_total_price',
            color='item_total_price',
            hover_data=['item_total_price'],
            title="Revenue per Product (Treemap)"
        )
        fig_treemap.update_layout(margin = dict(t=50, l=25, r=25, b=25)) # Adjust margins for better display
        st.plotly_chart(fig_treemap, use_container_width=True)
    else:
        st.info("No revenue data available for treemap visualization with the current filters.")
else:
    st.info("No sales data available for treemap visualization with the current filters.")


## ⬇️ Download Data (using filtered data)
st.subheader("Download Data")
if not filtered_sales_data_df.empty:
    csv = filtered_sales_data_df.to_csv(index=False)
    st.download_button("Download Filtered Data", csv, "filtered_order_items_data.csv", "text/csv")
else:
    st.info("No order items data available to download with the current filters.")

# --- Data Sync Options ---
# Initialize autosync state
if 'autosync_enabled' not in st.session_state:
    st.session_state.autosync_enabled = False
if 'last_sync_time' not in st.session_state:
    st.session_state.last_sync_time = datetime.now()

with st.sidebar:
    st.markdown("---")
    st.subheader("Data Sync Options")
    # Toggle for autosync
    st.session_state.autosync_enabled = st.checkbox("Enable Auto-Sync (Every Minute)", value=st.session_state.autosync_enabled)

    if st.button("🔄 Sync Data Now"):
        st.cache_data.clear() # Clear the cache to force data reload
        st.session_state.last_sync_time = datetime.now() # Update last sync time
        st.success("Data synced successfully! Dashboard will refresh.")
        st.rerun() # Use st.rerun() to immediately trigger a reload of data

    if st.session_state.autosync_enabled:
        st.info("Auto-sync is enabled. The dashboard will refresh every minute.")

        # Check if 1 minute has passed since last sync
        if (datetime.now() - st.session_state.last_sync_time).total_seconds() >= 60:
            st.cache_data.clear()
            st.session_state.last_sync_time = datetime.now()
            st.rerun()
