-- ============================================================================
-- BLINKIT SALES PERFORMANCE ANALYTICS - SQL QUERIES
-- Database: PostgreSQL/MySQL Compatible
-- ============================================================================

-- ----------------------------------------------------------------------------
-- TABLE CREATION & DATA LOADING
-- ----------------------------------------------------------------------------

-- Create Products Table
CREATE TABLE products (
    product_id VARCHAR(10) PRIMARY KEY,
    product_name VARCHAR(100),
    category VARCHAR(50),
    sub_category VARCHAR(50),
    selling_price DECIMAL(10,2),
    cost_price DECIMAL(10,2)
);

-- Create Customers Table
CREATE TABLE customers (
    customer_id VARCHAR(10) PRIMARY KEY,
    city VARCHAR(50),
    acquisition_channel VARCHAR(30),
    repeat_customer_flag INT
);

-- Create Orders Table
CREATE TABLE orders (
    order_id VARCHAR(12) PRIMARY KEY,
    order_date DATE,
    order_time TIME,
    customer_id VARCHAR(10),
    store_id VARCHAR(8),
    city VARCHAR(50),
    delivery_time_minutes INT,
    order_status VARCHAR(20),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Create Payments Table
CREATE TABLE payments (
    order_id VARCHAR(12) PRIMARY KEY,
    payment_mode VARCHAR(30),
    discount_amount DECIMAL(10,2),
    final_amount DECIMAL(10,2),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- Note: Load CSV files using database-specific import commands
-- PostgreSQL: \COPY table_name FROM 'file.csv' DELIMITER ',' CSV HEADER;
-- MySQL: LOAD DATA INFILE 'file.csv' INTO TABLE table_name FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' IGNORE 1 ROWS;

-- ----------------------------------------------------------------------------
-- QUERY 1: Month-over-Month Revenue & Profit Growth by City
-- ----------------------------------------------------------------------------

WITH monthly_city_metrics AS (
    SELECT 
        o.city,
        DATE_TRUNC('month', o.order_date) AS month,
        SUM(p.final_amount + p.discount_amount) AS revenue,
        SUM(p.final_amount) AS net_revenue,
        SUM(p.discount_amount) AS total_discount,
        COUNT(DISTINCT o.order_id) AS orders
    FROM orders o
    JOIN payments p ON o.order_id = p.order_id
    WHERE o.order_status = 'Delivered'
    GROUP BY o.city, DATE_TRUNC('month', o.order_date)
),
mom_growth AS (
    SELECT 
        city,
        month,
        revenue,
        net_revenue,
        total_discount,
        orders,
        LAG(revenue) OVER (PARTITION BY city ORDER BY month) AS prev_month_revenue,
        LAG(net_revenue) OVER (PARTITION BY city ORDER BY month) AS prev_month_net_revenue,
        LAG(orders) OVER (PARTITION BY city ORDER BY month) AS prev_month_orders
    FROM monthly_city_metrics
)
SELECT 
    city,
    TO_CHAR(month, 'YYYY-MM') AS month,
    revenue,
    net_revenue,
    orders,
    ROUND(((revenue - prev_month_revenue) / NULLIF(prev_month_revenue, 0) * 100), 2) AS revenue_growth_pct,
    ROUND(((net_revenue - prev_month_net_revenue) / NULLIF(prev_month_net_revenue, 0) * 100), 2) AS net_revenue_growth_pct,
    ROUND(((orders - prev_month_orders) / NULLIF(prev_month_orders::DECIMAL, 0) * 100), 2) AS order_growth_pct,
    ROUND((total_discount / revenue * 100), 2) AS discount_rate_pct
FROM mom_growth
WHERE prev_month_revenue IS NOT NULL
ORDER BY city, month;

-- ----------------------------------------------------------------------------
-- QUERY 2: Category-wise Discount Impact on Profitability
-- Note: Requires order_products junction table (created from detailed data)
-- ----------------------------------------------------------------------------

-- First create order_products table
CREATE TABLE order_products (
    order_id VARCHAR(12),
    product_id VARCHAR(10),
    quantity INT DEFAULT 1,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Analysis Query
WITH category_discount_buckets AS (
    SELECT 
        pr.category,
        CASE 
            WHEN (py.discount_amount / NULLIF(py.final_amount + py.discount_amount, 0) * 100) < 5 THEN '0-5%'
            WHEN (py.discount_amount / NULLIF(py.final_amount + py.discount_amount, 0) * 100) < 10 THEN '5-10%'
            WHEN (py.discount_amount / NULLIF(py.final_amount + py.discount_amount, 0) * 100) < 15 THEN '10-15%'
            ELSE '>15%'
        END AS discount_bucket,
        (pr.selling_price - pr.cost_price) AS profit,
        pr.selling_price AS revenue,
        py.discount_amount
    FROM order_products op
    JOIN products pr ON op.product_id = pr.product_id
    JOIN payments py ON op.order_id = py.order_id
    JOIN orders o ON op.order_id = o.order_id
    WHERE o.order_status = 'Delivered'
)
SELECT 
    category,
    discount_bucket,
    COUNT(*) AS orders,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(SUM(discount_amount), 2) AS total_discount,
    ROUND(AVG(profit / NULLIF(revenue, 0) * 100), 2) AS avg_profit_margin_pct,
    ROUND(SUM(profit) / NULLIF(SUM(revenue), 0) * 100, 2) AS overall_margin_pct
FROM category_discount_buckets
GROUP BY category, discount_bucket
ORDER BY category, discount_bucket;

-- ----------------------------------------------------------------------------
-- QUERY 3: Top 5 Loss-Making SKUs per City
-- ----------------------------------------------------------------------------

WITH product_city_performance AS (
    SELECT 
        o.city,
        pr.product_id,
        pr.product_name,
        pr.category,
        COUNT(DISTINCT o.order_id) AS orders,
        SUM(pr.selling_price) AS total_revenue,
        SUM(pr.cost_price) AS total_cost,
        SUM(pr.selling_price - pr.cost_price) AS total_profit,
        ROUND(AVG((pr.selling_price - pr.cost_price) / NULLIF(pr.selling_price, 0) * 100), 2) AS avg_margin_pct
    FROM orders o
    JOIN order_products op ON o.order_id = op.order_id
    JOIN products pr ON op.product_id = pr.product_id
    WHERE o.order_status = 'Delivered'
    GROUP BY o.city, pr.product_id, pr.product_name, pr.category
    HAVING SUM(pr.selling_price - pr.cost_price) < 0
),
ranked_products AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY city ORDER BY total_profit ASC) AS loss_rank
    FROM product_city_performance
)
SELECT 
    city,
    product_id,
    product_name,
    category,
    orders,
    total_revenue,
    total_profit,
    avg_margin_pct
FROM ranked_products
WHERE loss_rank <= 5
ORDER BY city, loss_rank;

-- ----------------------------------------------------------------------------
-- QUERY 4: Delivery Performance vs Customer Retention Analysis
-- ----------------------------------------------------------------------------

WITH customer_delivery_experience AS (
    SELECT 
        c.customer_id,
        c.city,
        c.repeat_customer_flag,
        AVG(o.delivery_time_minutes) AS avg_delivery_time,
        COUNT(o.order_id) AS total_orders,
        SUM(CASE WHEN o.delivery_time_minutes > 30 THEN 1 ELSE 0 END) AS sla_breaches,
        ROUND(SUM(CASE WHEN o.delivery_time_minutes > 30 THEN 1 ELSE 0 END)::DECIMAL / COUNT(o.order_id) * 100, 2) AS sla_breach_rate
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'Delivered'
    GROUP BY c.customer_id, c.city, c.repeat_customer_flag
)
SELECT 
    CASE 
        WHEN avg_delivery_time <= 20 THEN '0-20 min'
        WHEN avg_delivery_time <= 25 THEN '20-25 min'
        WHEN avg_delivery_time <= 30 THEN '25-30 min'
        ELSE '>30 min'
    END AS delivery_time_bucket,
    COUNT(customer_id) AS customers,
    ROUND(AVG(repeat_customer_flag) * 100, 2) AS repeat_customer_rate_pct,
    ROUND(AVG(total_orders), 2) AS avg_orders_per_customer,
    ROUND(AVG(sla_breach_rate), 2) AS avg_sla_breach_rate
FROM customer_delivery_experience
GROUP BY 
    CASE 
        WHEN avg_delivery_time <= 20 THEN '0-20 min'
        WHEN avg_delivery_time <= 25 THEN '20-25 min'
        WHEN avg_delivery_time <= 30 THEN '25-30 min'
        ELSE '>30 min'
    END
ORDER BY delivery_time_bucket;

-- ----------------------------------------------------------------------------
-- QUERY 5: Peak Hours Operational Analysis
-- ----------------------------------------------------------------------------

WITH hourly_operations AS (
    SELECT 
        EXTRACT(HOUR FROM o.order_time) AS hour,
        o.city,
        COUNT(o.order_id) AS orders,
        AVG(o.delivery_time_minutes) AS avg_delivery_time,
        ROUND(AVG(CASE WHEN o.delivery_time_minutes > 30 THEN 1 ELSE 0 END) * 100, 2) AS sla_breach_rate,
        SUM(p.final_amount + p.discount_amount) AS revenue
    FROM orders o
    JOIN payments p ON o.order_id = p.order_id
    WHERE o.order_status = 'Delivered'
    GROUP BY EXTRACT(HOUR FROM o.order_time), o.city
)
SELECT 
    hour,
    city,
    orders,
    ROUND(avg_delivery_time, 2) AS avg_delivery_time,
    sla_breach_rate,
    ROUND(revenue, 2) AS revenue,
    CASE 
        WHEN hour BETWEEN 7 AND 10 THEN 'Morning Peak'
        WHEN hour BETWEEN 18 AND 22 THEN 'Evening Peak'
        ELSE 'Off-Peak'
    END AS peak_classification
FROM hourly_operations
WHERE orders > (SELECT AVG(orders) FROM hourly_operations)
ORDER BY city, hour;

-- ----------------------------------------------------------------------------
-- QUERY 6: Customer Acquisition Channel ROI
-- ----------------------------------------------------------------------------

WITH channel_performance AS (
    SELECT 
        c.acquisition_channel,
        COUNT(DISTINCT c.customer_id) AS customers,
        COUNT(o.order_id) AS total_orders,
        ROUND(COUNT(o.order_id)::DECIMAL / COUNT(DISTINCT c.customer_id), 2) AS orders_per_customer,
        SUM(p.final_amount + p.discount_amount) AS gross_revenue,
        SUM(p.final_amount) AS net_revenue,
        SUM(p.discount_amount) AS total_discount,
        ROUND(AVG(c.repeat_customer_flag) * 100, 2) AS repeat_rate_pct
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN payments p ON o.order_id = p.order_id
    WHERE o.order_status = 'Delivered'
    GROUP BY c.acquisition_channel
)
SELECT 
    acquisition_channel,
    customers,
    total_orders,
    orders_per_customer,
    gross_revenue,
    net_revenue,
    total_discount,
    repeat_rate_pct,
    ROUND(net_revenue / customers, 2) AS revenue_per_customer,
    ROUND(total_discount / gross_revenue * 100, 2) AS discount_rate_pct
FROM channel_performance
ORDER BY net_revenue DESC;

-- ----------------------------------------------------------------------------
-- QUERY 7: Product Performance Segmentation (RFM-style)
-- ----------------------------------------------------------------------------

WITH product_metrics AS (
    SELECT 
        pr.product_id,
        pr.product_name,
        pr.category,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(pr.selling_price) AS revenue,
        SUM(pr.selling_price - pr.cost_price) AS profit,
        MAX(o.order_date) AS last_order_date,
        CURRENT_DATE - MAX(o.order_date) AS recency_days
    FROM products pr
    JOIN order_products op ON pr.product_id = op.product_id
    JOIN orders o ON op.order_id = o.order_id
    WHERE o.order_status = 'Delivered'
    GROUP BY pr.product_id, pr.product_name, pr.category
),
product_segments AS (
    SELECT 
        *,
        NTILE(4) OVER (ORDER BY recency_days ASC) AS recency_score,
        NTILE(4) OVER (ORDER BY frequency DESC) AS frequency_score,
        NTILE(4) OVER (ORDER BY profit DESC) AS profit_score
    FROM product_metrics
)
SELECT 
    product_id,
    product_name,
    category,
    frequency,
    revenue,
    profit,
    recency_days,
    CASE 
        WHEN recency_score >= 3 AND frequency_score >= 3 AND profit_score >= 3 THEN 'Champion'
        WHEN recency_score >= 3 AND frequency_score >= 2 THEN 'Loyal'
        WHEN profit_score >= 3 THEN 'High-Value'
        WHEN recency_days > 90 THEN 'Dormant'
        WHEN profit < 0 THEN 'Loss-Maker'
        ELSE 'Standard'
    END AS product_segment
FROM product_segments
ORDER BY profit DESC;

-- ----------------------------------------------------------------------------
-- QUERY 8: City Expansion Opportunity Analysis
-- ----------------------------------------------------------------------------

SELECT 
    o.city,
    COUNT(DISTINCT o.customer_id) AS active_customers,
    COUNT(DISTINCT o.store_id) AS stores,
    COUNT(o.order_id) AS total_orders,
    ROUND(COUNT(o.order_id)::DECIMAL / COUNT(DISTINCT o.store_id), 2) AS orders_per_store,
    ROUND(AVG(o.delivery_time_minutes), 2) AS avg_delivery_time,
    SUM(p.final_amount + p.discount_amount) AS revenue,
    SUM(p.discount_amount) AS total_discount,
    ROUND(AVG(CASE WHEN o.delivery_time_minutes > 30 THEN 1 ELSE 0 END) * 100, 2) AS sla_breach_rate,
    ROUND(SUM(p.final_amount + p.discount_amount) / COUNT(DISTINCT o.store_id), 2) AS revenue_per_store,
    CASE 
        WHEN AVG(o.delivery_time_minutes) > 28 THEN 'High Priority - Delivery Issues'
        WHEN COUNT(o.order_id)::DECIMAL / COUNT(DISTINCT o.store_id) > 1000 THEN 'High Priority - Capacity Constraint'
        WHEN SUM(p.final_amount + p.discount_amount) / COUNT(DISTINCT o.store_id) > 100000 THEN 'Expansion Opportunity'
        ELSE 'Monitor'
    END AS strategic_priority
FROM orders o
JOIN payments p ON o.order_id = p.order_id
WHERE o.order_status = 'Delivered'
GROUP BY o.city
ORDER BY revenue DESC;