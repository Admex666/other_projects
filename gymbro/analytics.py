import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def get_connection(db_path="gym_data.db"):
    return sqlite3.connect(db_path)

def get_dashboard_metrics():
    conn = get_connection()
    df_subs = pd.read_sql_query("SELECT s.*, p.price FROM Subscriptions s JOIN MembershipPlans p ON s.plan_id = p.plan_id", conn)
    total_revenue = df_subs['price'].sum()
    total_members = pd.read_sql_query("SELECT COUNT(*) as count FROM Members", conn)['count'][0]
    
    # 1. Inactivity (No active subscription currently)
    active_now = pd.read_sql_query("SELECT DISTINCT member_id FROM Subscriptions WHERE expiry_date >= DATE('now')", conn)
    active_count = len(active_now)
    inactivity_rate = (total_members - active_count) / total_members if total_members > 0 else 0
    
    # 2. MoM Churn (Members active last month who didn't renew in current month)
    # Period 1 (30 to 60 days ago)
    p1_active = pd.read_sql_query("""
        SELECT DISTINCT member_id FROM Subscriptions 
        WHERE purchase_date <= DATE('now', '-30 days') 
        AND expiry_date >= DATE('now', '-60 days')
    """, conn)
    
    # Period 2 (0 to 30 days ago)
    p2_active = pd.read_sql_query("""
        SELECT DISTINCT member_id FROM Subscriptions 
        WHERE purchase_date <= DATE('now') 
        AND expiry_date >= DATE('now', '-30 days')
    """, conn)
    
    p1_set = set(p1_active['member_id'])
    p2_set = set(p2_active['member_id'])
    
    churn_rate = 0
    if len(p1_set) > 0:
        renewed = p1_set.intersection(p2_set)
        churn_rate = (len(p1_set) - len(renewed)) / len(p1_set)
    
    conn.close()
    return {
        "Total Revenue": total_revenue,
        "Total Members": total_members,
        "Active Members": active_count,
        "Inactivity Rate": inactivity_rate,
        "Churn Rate": churn_rate
    }

def get_churn_risk_data():
    conn = get_connection()
    today = datetime.now()
    last_30 = (today - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    prev_30 = (today - timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")
    
    query = f"""
    SELECT 
        m.member_id,
        m.name as tag_neve,
        m.registration_date,
        COUNT(CASE WHEN v.check_in_time > '{last_30}' THEN 1 END) as visits_last_30,
        COUNT(CASE WHEN v.check_in_time <= '{last_30}' AND v.check_in_time > '{prev_30}' THEN 1 END) as visits_prev_30
    FROM Members m
    LEFT JOIN Visits v ON m.member_id = v.member_id
    GROUP BY m.member_id
    """
    df = pd.read_sql_query(query, conn)
    
    df['risk_score'] = 0.0
    df.loc[df['visits_prev_30'] > 0, 'risk_score'] = (df['visits_prev_30'] - df['visits_last_30']) / df['visits_prev_30']
    df['risk_score'] = df['risk_score'].clip(0, 1)
    
    high_risk = df[df['risk_score'] > 0.3].sort_values('risk_score', ascending=False)
    conn.close()
    return high_risk

def get_upsell_candidates():
    conn = get_connection()
    query = """
    SELECT 
        m.member_id,
        m.name as tag_neve,
        p.name as berlet_neve,
        COUNT(v.visit_id) as total_visits,
        COUNT(v.visit_id) / 4.0 as visits_per_week
    FROM Members m
    JOIN Subscriptions s ON m.member_id = s.member_id
    JOIN MembershipPlans p ON s.plan_id = p.plan_id
    JOIN Visits v ON s.subscription_id = v.subscription_id
    WHERE p.type = 'Occasional'
    GROUP BY m.member_id
    HAVING visits_per_week >= 1
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_winback_candidates():
    conn = get_connection()
    query = """
    SELECT 
        m.member_id,
        m.name as tag_neve,
        MAX(v.check_in_time) as last_visit,
        MAX(s.purchase_date) as last_purchase
    FROM Members m
    LEFT JOIN Visits v ON m.member_id = v.member_id
    LEFT JOIN Subscriptions s ON m.member_id = s.member_id
    GROUP BY m.member_id
    HAVING last_visit < DATE('now', '-14 days') OR (last_visit IS NULL AND m.registration_date < DATE('now', '-14 days'))
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
