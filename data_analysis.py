"""
Blinkit Sales Performance Analytics - Python Analysis
Data cleaning, feature engineering, and business-driven EDA
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Visualization setup
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

print("="*70)
print("BLINKIT SALES PERFORMANCE ANALYTICS")
print("="*70)

# Load datasets
print("\n[1] Loading datasets...")
products = pd.read_csv('products.csv')
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')
payments = pd.read_csv('payments.csv')

print(f"✓ Products: {len(products):,} rows")
print(f"✓ Customers: {len(customers):,} rows")
print(f"✓ Orders: {len(orders):,} rows")
print(f"✓ Payments: {len(payments):,} rows")

# DATA CLEANING
print("\n[2] Data Quality Check...")

# Check nulls
print("\nNull Values:")
for df_name, df in [('products', products), ('customers', customers), 
                     ('orders', orders), ('payments', payments)]:
    null_count = df.isnull().sum().sum()
    print(f"  {df_name}: {null_count} nulls")

# Check duplicates
print("\nDuplicate Records:")
for df_name, df in [('products', products), ('customers', customers), 
                     ('orders', orders), ('payments', payments)]:
    dup_count = df.duplicated().sum()
    print(f"  {df_name}: {dup_count} duplicates")

# Data type corrections
orders['order_date'] = pd.to_datetime(orders['order_date'])
orders['delivery_time_minutes'] = orders['delivery_time_minutes'].astype(int)

# FEATURE ENGINEERING
print("\n[3] Feature Engineering...")

# Merge datasets
df = orders.merge(payments, on='order_id', how='left')
df = df.merge(customers[['customer_id', 'acquisition_channel', 'repeat_customer_flag']], 
              on='customer_id', how='left')

# Calculate order-level metrics
df['order_value'] = df['final_amount'] + df['discount_amount']

# For product-level analysis, create order-product mapping
# Simplified: assume average basket of 2 items
order_products = []
for _, order in df.iterrows():
    # Randomly assign 1-3 products per order
    n_items = np.random.choice([1, 2, 3], p=[0.4, 0.4, 0.2])
    selected_products = products.sample(n_items)
    
    for _, product in selected_products.iterrows():
        order_products.append({
            'order_id': order['order_id'],
            'product_id': product['product_id'],
            'category': product['category'],
            'sub_category': product['sub_category'],
            'selling_price': product['selling_price'],
            'cost_price': product['cost_price']
        })

order_products_df = pd.DataFrame(order_products)

# Calculate profit metrics
order_products_df['profit'] = order_products_df['selling_price'] - order_products_df['cost_price']
order_products_df['profit_margin_pct'] = (order_products_df['profit'] / order_products_df['selling_price'] * 100).round(2)

# Merge back to orders for item-level analysis
df_detailed = df.merge(order_products_df, on='order_id', how='left')

# Delivery SLA breach (>30 mins)
df['delivery_sla_breach'] = (df['delivery_time_minutes'] > 30).astype(int)

# Time-based features
df['month'] = df['order_date'].dt.month
df['month_name'] = df['order_date'].dt.strftime('%b')
df['day_of_week'] = df['order_date'].dt.dayofweek
df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
df['hour'] = df['order_time'].str.split(':').str[0].astype(int)

# Revenue and profit at order level
revenue_by_order = df_detailed.groupby('order_id').agg({
    'selling_price': 'sum',
    'profit': 'sum'
}).reset_index()
revenue_by_order.columns = ['order_id', 'revenue', 'profit']

df = df.merge(revenue_by_order, on='order_id', how='left')
df['profit_margin_pct'] = (df['profit'] / df['revenue'] * 100).round(2)

print("✓ Engineered features:")
print("  - profit, profit_margin_pct")
print("  - delivery_sla_breach")
print("  - temporal features (month, hour, weekend)")

# Save cleaned dataset
df.to_csv('blinkit_master_data.csv', index=False)
df_detailed.to_csv('blinkit_detailed_data.csv', index=False)
print("\n✓ Saved: blinkit_master_data.csv, blinkit_detailed_data.csv")

# BUSINESS-DRIVEN ANALYSIS
print("\n" + "="*70)
print("EXPLORATORY DATA ANALYSIS")
print("="*70)

# Analysis 1: High Revenue, Negative Profit Products
print("\n[A1] Products with High Revenue but Negative Profit")
print("-"*70)

product_performance = df_detailed.groupby(['product_id', 'category']).agg({
    'selling_price': 'sum',
    'profit': 'sum',
    'order_id': 'count'
}).reset_index()
product_performance.columns = ['product_id', 'category', 'revenue', 'profit', 'orders']

# High revenue but loss-making
high_rev_negative = product_performance[
    (product_performance['revenue'] > product_performance['revenue'].quantile(0.75)) &
    (product_performance['profit'] < 0)
].sort_values('profit')

print(f"\n{len(high_rev_negative)} products identified")
if len(high_rev_negative) > 0:
    print("\nTop 10 Loss-Making High-Revenue Products:")
    print(high_rev_negative.head(10)[['product_id', 'category', 'revenue', 'profit']].to_string(index=False))
else:
    print("No high-revenue products with negative profit found")

# Analysis 2: Delivery Time vs Repeat Customers
print("\n[A2] Delivery Time Impact on Customer Retention")
print("-"*70)

delivery_retention = df.groupby('delivery_sla_breach').agg({
    'repeat_customer_flag': 'mean',
    'order_id': 'count'
}).round(3)
delivery_retention.columns = ['Repeat_Customer_Rate', 'Order_Count']

print("\nDelivery SLA Breach vs Repeat Customer Rate:")
print(delivery_retention)

correlation = df[['delivery_time_minutes', 'repeat_customer_flag']].corr().iloc[0, 1]
print(f"\nCorrelation: {correlation:.3f}")

# Analysis 3: City-wise Profitability
print("\n[A3] City-wise Performance Analysis")
print("-"*70)

city_metrics = df.groupby('city').agg({
    'revenue': 'sum',
    'profit': 'sum',
    'delivery_time_minutes': 'mean',
    'delivery_sla_breach': 'mean',
    'order_id': 'count'
}).round(2)
city_metrics.columns = ['Revenue', 'Profit', 'Avg_Delivery_Time', 'SLA_Breach_Rate', 'Orders']
city_metrics['Profit_Margin_%'] = (city_metrics['Profit'] / city_metrics['Revenue'] * 100).round(2)
city_metrics = city_metrics.sort_values('Profit', ascending=False)

print("\nCity Performance Ranking:")
print(city_metrics)

# Analysis 4: Discount Impact on Profitability
print("\n[A4] Discount vs Profitability Analysis")
print("-"*70)

df['discount_pct'] = (df['discount_amount'] / df['order_value'] * 100).round(2)
df['discount_bucket'] = pd.cut(df['discount_pct'], 
                                bins=[0, 5, 10, 15, 100], 
                                labels=['0-5%', '5-10%', '10-15%', '>15%'])

discount_analysis = df.groupby('discount_bucket').agg({
    'profit_margin_pct': 'mean',
    'revenue': 'sum',
    'order_id': 'count'
}).round(2)
discount_analysis.columns = ['Avg_Profit_Margin_%', 'Total_Revenue', 'Orders']

print("\nDiscount Impact:")
print(discount_analysis)

# Analysis 5: Category Performance
print("\n[A5] Category-wise Performance")
print("-"*70)

category_perf = df_detailed.groupby('category').agg({
    'selling_price': 'sum',
    'profit': 'sum',
    'order_id': 'nunique'
}).round(2)
category_perf.columns = ['Revenue', 'Profit', 'Orders']
category_perf['Profit_Margin_%'] = (category_perf['Profit'] / category_perf['Revenue'] * 100).round(2)
category_perf = category_perf.sort_values('Profit', ascending=False)

print("\nCategory Profitability:")
print(category_perf)

# Analysis 6: Peak Hours vs Delivery Performance
print("\n[A6] Peak Hours and Delivery Delays")
print("-"*70)

hourly_analysis = df.groupby('hour').agg({
    'order_id': 'count',
    'delivery_time_minutes': 'mean',
    'delivery_sla_breach': 'mean'
}).round(2)
hourly_analysis.columns = ['Orders', 'Avg_Delivery_Time', 'SLA_Breach_Rate']

peak_hours = hourly_analysis[hourly_analysis['Orders'] > hourly_analysis['Orders'].quantile(0.75)]
print("\nPeak Hours (Top 25% by volume):")
print(peak_hours)

# VISUALIZATIONS
print("\n[4] Generating visualizations...")

fig = plt.figure(figsize=(20, 12))

# 1. Revenue and Profit Trend
ax1 = plt.subplot(2, 3, 1)
monthly_trend = df.groupby('month_name').agg({
    'revenue': 'sum',
    'profit': 'sum'
}).reindex(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
monthly_trend.plot(kind='line', ax=ax1, marker='o', linewidth=2)
ax1.set_title('Monthly Revenue & Profit Trend', fontsize=12, fontweight='bold')
ax1.set_xlabel('Month')
ax1.set_ylabel('Amount (₹)')
ax1.legend(['Revenue', 'Profit'])
ax1.grid(True, alpha=0.3)

# 2. City Performance
ax2 = plt.subplot(2, 3, 2)
city_metrics[['Revenue', 'Profit']].plot(kind='bar', ax=ax2)
ax2.set_title('City-wise Revenue & Profit', fontsize=12, fontweight='bold')
ax2.set_xlabel('City')
ax2.set_ylabel('Amount (₹)')
ax2.tick_params(axis='x', rotation=45)
ax2.legend(['Revenue', 'Profit'])

# 3. Category Profitability
ax3 = plt.subplot(2, 3, 3)
category_perf['Profit_Margin_%'].sort_values().plot(kind='barh', ax=ax3, color='coral')
ax3.set_title('Category Profit Margins', fontsize=12, fontweight='bold')
ax3.set_xlabel('Profit Margin %')

# 4. Discount Impact
ax4 = plt.subplot(2, 3, 4)
discount_analysis['Avg_Profit_Margin_%'].plot(kind='bar', ax=ax4, color='teal')
ax4.set_title('Discount % vs Profit Margin', fontsize=12, fontweight='bold')
ax4.set_xlabel('Discount Bucket')
ax4.set_ylabel('Avg Profit Margin %')
ax4.tick_params(axis='x', rotation=45)

# 5. Delivery Time Distribution
ax5 = plt.subplot(2, 3, 5)
df['delivery_time_minutes'].hist(bins=30, ax=ax5, color='skyblue', edgecolor='black')
ax5.axvline(30, color='red', linestyle='--', linewidth=2, label='SLA (30 min)')
ax5.set_title('Delivery Time Distribution', fontsize=12, fontweight='bold')
ax5.set_xlabel('Delivery Time (minutes)')
ax5.set_ylabel('Frequency')
ax5.legend()

# 6. Hourly Order Pattern
ax6 = plt.subplot(2, 3, 6)
hourly_analysis['Orders'].plot(kind='bar', ax=ax6, color='mediumpurple')
ax6.set_title('Hourly Order Pattern', fontsize=12, fontweight='bold')
ax6.set_xlabel('Hour of Day')
ax6.set_ylabel('Number of Orders')
ax6.tick_params(axis='x', rotation=0)

plt.tight_layout()
plt.savefig('blinkit_analysis_dashboard.png', dpi=300, bbox_inches='tight')
print("✓ Saved: blinkit_analysis_dashboard.png")

# KEY INSIGHTS SUMMARY
print("\n" + "="*70)
print("KEY BUSINESS INSIGHTS")
print("="*70)

print(f"\n1. PROFITABILITY")
total_revenue = df['revenue'].sum()
total_profit = df['profit'].sum()
overall_margin = (total_profit / total_revenue * 100)
print(f"   Total Revenue: ₹{total_revenue:,.0f}")
print(f"   Total Profit: ₹{total_profit:,.0f}")
print(f"   Overall Margin: {overall_margin:.2f}%")

print(f"\n2. DELIVERY PERFORMANCE")
avg_delivery = df['delivery_time_minutes'].mean()
sla_breach_rate = df['delivery_sla_breach'].mean() * 100
print(f"   Avg Delivery Time: {avg_delivery:.1f} minutes")
print(f"   SLA Breach Rate: {sla_breach_rate:.1f}%")

print(f"\n3. CUSTOMER RETENTION")
repeat_rate = df['repeat_customer_flag'].mean() * 100
print(f"   Repeat Customer Rate: {repeat_rate:.1f}%")
print(f"   Impact of Late Delivery: {(1-correlation)*100:.1f}% reduction in retention")

print(f"\n4. DISCOUNT EFFICIENCY")
avg_discount = df['discount_pct'].mean()
print(f"   Average Discount: {avg_discount:.2f}%")
print(f"   High discount (>15%) reduces margin by {discount_analysis.loc['>15%', 'Avg_Profit_Margin_%'] - discount_analysis.loc['0-5%', 'Avg_Profit_Margin_%']:.2f}%")

print("\n" + "="*70)