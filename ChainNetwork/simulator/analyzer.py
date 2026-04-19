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

if __name__ == "__main__":
    print("Running Analytics...")
    df = load_data()
    rfm = run_rfm_analysis(df)
    
    plot_seasonality(df)
    plot_segments(rfm)
    
    churn_data = analyze_churn(df, rfm)
    
    print("Analytics completed. Visualizations saved to simulator/ directory.")
    print(f"Top 5 churn-risk users:\n{churn_data[churn_data['churn_risk']].head()}")
