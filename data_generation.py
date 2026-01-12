"""
Blinkit Sales Performance Analytics - Data Generation
Generates realistic synthetic dataset (50,000+ orders) with logical consistency
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

# Configuration
NUM_ORDERS = 50000
NUM_CUSTOMERS = 15000
NUM_PRODUCTS = 500
NUM_STORES = 50

# Define cities with different characteristics
CITIES = {
    'Mumbai': {'stores': 12, 'avg_delivery': 25, 'demand_multiplier': 1.4},
    'Delhi': {'stores': 10, 'avg_delivery': 28, 'demand_multiplier': 1.3},
    'Bangalore': {'stores': 10, 'avg_delivery': 22, 'demand_multiplier': 1.2},
    'Hyderabad': {'stores': 6, 'avg_delivery': 24, 'demand_multiplier': 1.0},
    'Chennai': {'stores': 5, 'avg_delivery': 26, 'demand_multiplier': 0.9},
    'Pune': {'stores': 4, 'avg_delivery': 23, 'demand_multiplier': 0.8},
    'Kolkata': {'stores': 3, 'avg_delivery': 30, 'demand_multiplier': 0.7}
}

# Product categories with realistic pricing
CATEGORIES = {
    'Fruits & Vegetables': {
        'subcategories': ['Fresh Fruits', 'Fresh Vegetables', 'Exotic Fruits'],
        'price_range': (20, 200),
        'margin_range': (0.15, 0.35)
    },
    'Dairy & Breakfast': {
        'subcategories': ['Milk', 'Bread & Pav', 'Eggs', 'Paneer & Tofu'],
        'price_range': (15, 150),
        'margin_range': (0.12, 0.25)
    },
    'Munchies': {
        'subcategories': ['Chips & Crisps', 'Namkeen', 'Biscuits', 'Chocolates'],
        'price_range': (10, 300),
        'margin_range': (0.20, 0.40)
    },
    'Cold Drinks & Juices': {
        'subcategories': ['Soft Drinks', 'Juices', 'Energy Drinks'],
        'price_range': (20, 150),
        'margin_range': (0.25, 0.45)
    },
    'Instant & Frozen': {
        'subcategories': ['Instant Noodles', 'Frozen Snacks', 'Ready to Cook'],
        'price_range': (30, 400),
        'margin_range': (0.18, 0.35)
    },
    'Tea Coffee & Beverages': {
        'subcategories': ['Tea', 'Coffee', 'Health Drinks'],
        'price_range': (40, 500),
        'margin_range': (0.22, 0.38)
    },
    'Bakery & Biscuits': {
        'subcategories': ['Cookies', 'Cakes', 'Rusks'],
        'price_range': (25, 350),
        'margin_range': (0.28, 0.42)
    },
    'Home & Office': {
        'subcategories': ['Cleaning', 'Detergents', 'Stationery'],
        'price_range': (50, 600),
        'margin_range': (0.15, 0.30)
    }
}

ACQUISITION_CHANNELS = ['Organic', 'Paid Social', 'Referral', 'App Store', 'Google Ads']
PAYMENT_MODES = ['UPI', 'Credit Card', 'Debit Card', 'Wallet', 'Cash on Delivery']

print("Generating Blinkit synthetic dataset...")

# Generate Products
products_data = []
product_id = 1

for category, details in CATEGORIES.items():
    products_per_cat = NUM_PRODUCTS // len(CATEGORIES)
    for _ in range(products_per_cat):
        subcategory = random.choice(details['subcategories'])
        selling_price = round(np.random.uniform(*details['price_range']), 2)
        margin = np.random.uniform(*details['margin_range'])
        cost_price = round(selling_price * (1 - margin), 2)
        
        products_data.append({
            'product_id': f'PRD{product_id:05d}',
            'product_name': f'{subcategory} Item {product_id}',
            'category': category,
            'sub_category': subcategory,
            'selling_price': selling_price,
            'cost_price': cost_price
        })
        product_id += 1

products_df = pd.DataFrame(products_data)

# Generate Customers
customers_data = []
city_list = list(CITIES.keys())

for i in range(1, NUM_CUSTOMERS + 1):
    city = np.random.choice(city_list, p=[0.25, 0.20, 0.18, 0.15, 0.10, 0.07, 0.05])
    
    customers_data.append({
        'customer_id': f'CUST{i:06d}',
        'city': city,
        'acquisition_channel': np.random.choice(ACQUISITION_CHANNELS, p=[0.35, 0.25, 0.20, 0.12, 0.08]),
        'repeat_customer_flag': np.random.choice([0, 1], p=[0.3, 0.7])
    })

customers_df = pd.DataFrame(customers_data)

# Generate Stores
stores_data = []
store_id = 1

for city, info in CITIES.items():
    for _ in range(info['stores']):
        stores_data.append({
            'store_id': f'STR{store_id:04d}',
            'city': city
        })
        store_id += 1

stores_df = pd.DataFrame(stores_data)

# Generate Orders
print("Generating orders with temporal patterns...")
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)
date_range = (end_date - start_date).days

orders_data = []
payments_data = []

for i in range(1, NUM_ORDERS + 1):
    # Temporal distribution - more recent orders
    days_offset = int(np.random.beta(2, 5) * date_range)
    order_date = start_date + timedelta(days=days_offset)
    
    # Peak hours: 7-10 AM, 6-10 PM
    hour_weights = [0.02]*6 + [0.08]*4 + [0.04]*8 + [0.08]*4 + [0.02]*2
    order_hour = np.random.choice(range(24), p=np.array(hour_weights)/sum(hour_weights))
    order_minute = np.random.randint(0, 60)
    order_time = f"{order_hour:02d}:{order_minute:02d}"
    
    # Select customer and derive city
    customer = customers_df.sample(1).iloc[0]
    customer_id = customer['customer_id']
    city = customer['city']
    
    # Select store from same city
    city_stores = stores_df[stores_df['city'] == city]
    store_id = city_stores.sample(1).iloc[0]['store_id']
    
    # Delivery time with city-specific patterns
    base_delivery = CITIES[city]['avg_delivery']
    # Peak hours = longer delivery
    peak_penalty = 8 if order_hour in list(range(7,11)) + list(range(18,23)) else 0
    delivery_time = int(np.random.normal(base_delivery + peak_penalty, 5))
    delivery_time = max(10, min(60, delivery_time))  # Cap between 10-60 mins
    
    # Order status (most delivered, some cancelled)
    order_status = np.random.choice(['Delivered', 'Cancelled', 'Returned'], p=[0.92, 0.06, 0.02])
    
    # Product selection (1-5 items per order)
    num_items = np.random.choice([1, 2, 3, 4, 5], p=[0.45, 0.30, 0.15, 0.07, 0.03])
    order_products = products_df.sample(num_items)
    
    order_value = order_products['selling_price'].sum()
    
    # Discount strategy
    if order_value < 200:
        discount_pct = np.random.uniform(0, 0.05)
    elif order_value < 500:
        discount_pct = np.random.uniform(0.05, 0.15)
    else:
        discount_pct = np.random.uniform(0.10, 0.25)
    
    discount_amount = round(order_value * discount_pct, 2)
    final_amount = round(order_value - discount_amount, 2)
    
    # Payment mode
    payment_mode = np.random.choice(PAYMENT_MODES, p=[0.55, 0.20, 0.12, 0.10, 0.03])
    
    orders_data.append({
        'order_id': f'ORD{i:07d}',
        'order_date': order_date.strftime('%Y-%m-%d'),
        'order_time': order_time,
        'customer_id': customer_id,
        'store_id': store_id,
        'city': city,
        'delivery_time_minutes': delivery_time,
        'order_status': order_status
    })
    
    payments_data.append({
        'order_id': f'ORD{i:07d}',
        'payment_mode': payment_mode,
        'discount_amount': discount_amount,
        'final_amount': final_amount if order_status == 'Delivered' else 0
    })

orders_df = pd.DataFrame(orders_data)
payments_df = pd.DataFrame(payments_data)

# Save all datasets
print("\nSaving datasets...")
products_df.to_csv('products.csv', index=False)
customers_df.to_csv('customers.csv', index=False)
orders_df.to_csv('orders.csv', index=False)
payments_df.to_csv('payments.csv', index=False)

print(f"\n✓ Generated {len(products_df)} products")
print(f"✓ Generated {len(customers_df)} customers")
print(f"✓ Generated {len(orders_df)} orders")
print(f"✓ Generated {len(payments_df)} payment records")

print("\nDataset Summary:")
print(f"Date Range: {orders_df['order_date'].min()} to {orders_df['order_date'].max()}")
print(f"Cities: {', '.join(CITIES.keys())}")
print(f"Categories: {len(CATEGORIES)}")
print("\nFiles saved:")
print("- products.csv")
print("- customers.csv")
print("- orders.csv")
print("- payments.csv")