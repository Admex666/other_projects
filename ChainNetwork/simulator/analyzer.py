import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

def load_data():
    conn = sqlite3.connect('simulator/chainnetwork.db')
    
    # Load transactions
    df = pd.read_sql_query("""
        SELECT t.*, u.test_group, u.name as user_name, u.joined_at
        FROM transactions t
        JOIN users u ON t.user_id = u.id
    """, conn)
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    conn.close()
    return df

def run_rfm_analysis(df):
    now = df['timestamp'].max()
    
    rfm = df.groupby('user_id').agg({
        'timestamp': lambda x: (now - x.max()).days, # Recency
        'id': 'count', # Frequency
        'total_amount': 'sum' # Monetary
    })
    
    rfm.columns = ['recency', 'frequency', 'monetary']
    
    # Simple scoring (1-5)
    rfm['R_score'] = pd.qcut(rfm['recency'].rank(method='first'), 5, labels=[5, 4, 3, 2, 1])
    rfm['F_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
    rfm['M_score'] = pd.qcut(rfm['monetary'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
    
    rfm['RFM_Score'] = rfm['R_score'].astype(str) + rfm['F_score'].astype(str) + rfm['M_score'].astype(str)
    
    # Segment naming
    def segment_rfm(row):
        score = int(row['R_score']) + int(row['F_score']) + int(row['M_score'])
        if score >= 12: return 'Champion'
        if score >= 9: return 'Loyal'
        if score >= 6: return 'At Risk'
        return 'Lost'
    
    rfm['segment'] = rfm.apply(segment_rfm, axis=1)
    return rfm

def plot_seasonality(df):
    # Daily revenue
    daily_rev = df.set_index('timestamp').resample('D')['total_amount'].sum()
    
    plt.figure(figsize=(12, 6))
    plt.plot(daily_rev.index, daily_rev.values, label='Daily Revenue', color='#2ecc71')
    plt.title('Daily Revenue Trend (6 Months)')
    plt.xlabel('Date')
    plt.ylabel('Revenue (HUF)')
    plt.grid(True, alpha=0.3)
    plt.savefig('simulator/seasonality.png')
    plt.close()
    
    # Weekly patterns
    df['weekday'] = df['timestamp'].dt.day_name()
    order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly_rev = df.groupby('weekday')['total_amount'].mean().reindex(order)
    
    plt.figure(figsize=(10, 5))
    sns.barplot(x=weekly_rev.index, y=weekly_rev.values, palette='viridis')
    plt.title('Average Revenue by Weekday')
    plt.ylabel('Avg Revenue')
    plt.savefig('simulator/weekday_pattern.png')
    plt.close()

def plot_segments(rfm):
    seg_counts = rfm['segment'].value_counts()
    
    plt.figure(figsize=(8, 8))
    plt.pie(seg_counts, labels=seg_counts.index, autopct='%1.1f%%', startangle=140, colors=['#3498db', '#f1c40f', '#e67e22', '#e74c3c'])
    plt.title('Customer Segments (RFM)')
    plt.savefig('simulator/segments.png')
    plt.close()

def analyze_churn(df, rfm):
    # Calculate average time between visits for each user
    df = df.sort_values(['user_id', 'timestamp'])
    df['prev_visit'] = df.groupby('user_id')['timestamp'].shift(1)
    df['days_between'] = (df['timestamp'] - df['prev_visit']).dt.days
    
    avg_gap = df.groupby('user_id')['days_between'].mean()
    
    # A user is at churn risk if their recency > 2 * avg_gap
    churn_analysis = rfm.copy()
    churn_analysis['avg_gap'] = avg_gap
    churn_analysis['churn_risk'] = churn_analysis['recency'] > (2 * churn_analysis['avg_gap'])
    
    return churn_analysis

def get_market_basket(df):
    conn = sqlite3.connect('simulator/chainnetwork.db')
    # Get pairs of items bought together in the same transaction
    query = """
    SELECT ti1.menu_item_id as item_a, mi1.name as name_a, 
           ti2.menu_item_id as item_b, mi2.name as name_b, 
           COUNT(*) as frequency
    FROM transaction_items ti1
    JOIN transaction_items ti2 ON ti1.transaction_id = ti2.transaction_id AND ti1.menu_item_id < ti2.menu_item_id
    JOIN menu_items mi1 ON ti1.menu_item_id = mi1.id
    JOIN menu_items mi2 ON ti2.menu_item_id = mi2.id
    GROUP BY item_a, item_b
    ORDER BY frequency DESC
    LIMIT 15
    """
    basket = pd.read_sql_query(query, conn)
    conn.close()
    return basket

def get_user_journey(user_id):
    conn = sqlite3.connect('simulator/chainnetwork.db')
    # Combine transactions and interventions for a timeline
    query = f"""
    SELECT timestamp, 'Purchase' as type, total_amount as detail
    FROM transactions WHERE user_id = {user_id}
    UNION ALL
    SELECT i.timestamp, 'Intervention' as type, c.name as detail
    FROM interventions i 
    JOIN campaigns c ON i.campaign_id = c.id
    WHERE i.user_id = {user_id}
    ORDER BY timestamp ASC
    """
    journey = pd.read_sql_query(query, conn)
    conn.close()
    return journey

if __name__ == "__main__":
    print("Running Analytics...")
    df = load_data()
    rfm = run_rfm_analysis(df)
    
    plot_seasonality(df)
    plot_segments(rfm)
    
    churn_data = analyze_churn(df, rfm)
    basket = get_market_basket(df)
    
    print("Analytics completed. Market Basket top pairs:")
    print(basket.head())
