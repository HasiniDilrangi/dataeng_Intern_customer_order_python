import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler

# custom CSS for streamlit
st.markdown(
    """
    <style>
    h1 {
        color: #3D3DF2;  
    }
    h3 {
        color: #11A1EF;  
    }
    .stSidebar {
        background-color: #071657;  
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Main Dashboard
st.title("Customer Orders Dashboard")

# Database connection
def create_connection():
    try:
        user = 'root'
        password = ''
        host = 'localhost'
        port = '3306'
        database = 'datatest'
        engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}')

        with engine.connect() as connection:
            st.success("Connected to the MySql database successfully!!!")
        return engine
    except SQLAlchemyError as e:
        st.error(f"Error connecting to the database: {e}")
        return None

engine = create_connection()

# Sidebar Filters
st.sidebar.header("Filter Options")
date_range = st.sidebar.date_input("Select date range", [pd.to_datetime('2023-01-01'), pd.to_datetime('2023-12-31')])
total_amount_filter = st.sidebar.slider("Minimum Total Amount Spent", 0, 10000, 1000)
num_orders_filter = st.sidebar.slider("Minimum Number of Orders", 1, 20, 5)


# Fetching data from the DB
def fetch_data():
    if engine is not None:
        customers = pd.read_sql("SELECT * FROM customers", engine)
        orders = pd.read_sql("SELECT * FROM orders", engine)

        # Ensure 'order_date' is datetime
        orders['order_date'] = pd.to_datetime(orders['order_date'])

        # Merge customers and orders on customer_id
        data = pd.merge(orders, customers, on='customer_id')

        # Filter data based on the sidebar inputs
        filtered_data = data[
            (data['order_date'] >= pd.to_datetime(date_range[0])) &
            (data['order_date'] <= pd.to_datetime(date_range[1])) &
            (data['total_amount'] >= total_amount_filter)
            ]

        # Filter by no of orders
        order_counts = filtered_data['customer_id'].value_counts()
        valid_customers = order_counts[order_counts >= num_orders_filter].index  # Change to >=
        filtered_data = filtered_data[filtered_data['customer_id'].isin(valid_customers)]

        return filtered_data
    return pd.DataFrame()

# Get filtered data
filtered_orders = fetch_data()

# Display filtered data
if not filtered_orders.empty:
    st.dataframe(filtered_orders)

    # Summary metrics
    total_revenue = filtered_orders['total_amount'].sum()
    unique_customers = filtered_orders['customer_id'].nunique()
    total_orders = filtered_orders.shape[0]

    st.subheader("Summary Metrics")
    st.write(f"Total Revenue - ${total_revenue}")
    st.write(f"Number of Unique Customers - {unique_customers}")
    st.write(f"Total Number of Orders - {total_orders}")

    # Bar chart of top 10 customers by total revenue
    st.write("### Bar Chart")
    top_customers = filtered_orders.groupby('customer_name')['total_amount'].sum().nlargest(10)
    st.bar_chart(top_customers)

    # Line chart of total revenue over time
    st.write("### Line Chart")
    revenue_over_time = filtered_orders.set_index('order_date').resample('M')['total_amount'].sum()
    st.line_chart(revenue_over_time)


    # Machine Learning Model
    def prepare_ml_data(filtered_orders, min_orders=1):
        customer_summary = filtered_orders.groupby('customer_id').agg(
            total_orders=('order_date', 'count'),
            total_revenue=('total_amount', 'sum')
        ).reset_index()
        customer_summary['repeat_purchaser'] = customer_summary['total_orders'].apply(
            lambda x: 1 if x > min_orders else 0)


        st.write(customer_summary[['customer_id', 'total_orders', 'repeat_purchaser']])
        st.write(f"Unique classes in repeat_purchaser: {customer_summary['repeat_purchaser'].unique()}")

        return customer_summary


    # Train Machine Learning Model
    def train_model(customer_summary):
        if len(customer_summary) < 5:
            st.warning("Not enough data to train the model.")
            return None

        # Check for class balance
        if customer_summary['repeat_purchaser'].nunique() < 2:
            st.warning("The target variable does not have enough classes for training.")
            return None

        # Feature selection for the model
        X = customer_summary[['total_orders', 'total_revenue']]
        y = customer_summary['repeat_purchaser']

        # Split data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

        # Normalize features
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        # Initialize and train the logistic regression model
        model = LogisticRegression()

        try:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            # Display results in Streamlit
            st.write("### Machine Learning Model - Repeat Purchaser Prediction")
            st.write(f"Model Accuracy - {accuracy * 100:.3f}%")
            st.write("### Classification Report")
            st.text(classification_report(y_test, y_pred))

            return model
        except Exception as e:
            st.error(f"An error occurred during model training -  {e}")
            return None


    # Prepare data and train the ML model
    customer_summary = prepare_ml_data(filtered_orders)
    if not customer_summary.empty:
        train_model(customer_summary)

else:
    st.warning("No data available for the selected filters.")
