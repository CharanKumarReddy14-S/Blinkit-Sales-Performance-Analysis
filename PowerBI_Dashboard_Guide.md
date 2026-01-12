# Blinkit Sales Performance Analytics - Power BI Dashboard Guide

## Dashboard Design: Executive Leadership View

This document outlines the structure for a CEO-level Power BI dashboard. The design prioritizes **actionability over aesthetics**—every visual must drive a business decision.

---

## Data Model Setup

### 1. Import Tables
Load the following CSVs into Power BI:
- `blinkit_master_data.csv` (Fact Table)
- `products.csv` (Dimension)
- `customers.csv` (Dimension)
- `orders.csv` (Fact/Dimension)
- `payments.csv` (Fact/Dimension)

### 2. Create Relationships
```
customers (customer_id) → orders (customer_id) [Many-to-One]
orders (order_id) → payments (order_id) [One-to-One]
orders (order_id) → blinkit_master_data (order_id) [One-to-One]
```

### 3. DAX Measures (Create in a new table: "_Measures")

```dax
// Revenue Metrics
Total Revenue = SUM(blinkit_master_data[revenue])
Total Profit = SUM(blinkit_master_data[profit])
Profit Margin % = DIVIDE([Total Profit], [Total Revenue], 0) * 100
Net Revenue = SUM(payments[final_amount])

// Order Metrics
Total Orders = COUNTROWS(blinkit_master_data)
Delivered Orders = CALCULATE([Total Orders], blinkit_master_data[order_status] = "Delivered")
Cancelled Orders = CALCULATE([Total Orders], blinkit_master_data[order_status] = "Cancelled")
Cancellation Rate % = DIVIDE([Cancelled Orders], [Total Orders], 0) * 100

// Delivery Metrics
Avg Delivery Time = AVERAGE(blinkit_master_data[delivery_time_minutes])
SLA Breach Rate % = DIVIDE(
    CALCULATE([Total Orders], blinkit_master_data[delivery_sla_breach] = 1),
    [Total Orders], 0
) * 100

// Customer Metrics
Repeat Customer Rate % = AVERAGE(blinkit_master_data[repeat_customer_flag]) * 100
Avg Order Value = DIVIDE([Total Revenue], [Total Orders], 0)

// Growth Metrics
Revenue MoM % = 
VAR CurrentRevenue = [Total Revenue]
VAR PreviousRevenue = CALCULATE([Total Revenue], DATEADD(blinkit_master_data[order_date], -1, MONTH))
RETURN DIVIDE(CurrentRevenue - PreviousRevenue, PreviousRevenue, 0) * 100

Order Growth MoM % = 
VAR CurrentOrders = [Total Orders]
VAR PreviousOrders = CALCULATE([Total Orders], DATEADD(blinkit_master_data[order_date], -1, MONTH))
RETURN DIVIDE(CurrentOrders - PreviousOrders, PreviousOrders, 0) * 100

// Discount Metrics
Avg Discount % = AVERAGE(blinkit_master_data[discount_pct])
Total Discount Given = SUM(payments[discount_amount])
```

---

## Page 1: Executive Overview (Main Dashboard)

### Layout: 3-Column Grid

#### Top Row: KPI Cards (4 cards)
1. **Total Revenue**
   - Measure: `[Total Revenue]`
   - Format: Currency (₹)
   - Trend: `[Revenue MoM %]` (green if positive, red if negative)

2. **Total Profit**
   - Measure: `[Total Profit]`
   - Format: Currency (₹)
   - Conditional: Red if margin < 10%

3. **Avg Delivery Time**
   - Measure: `[Avg Delivery Time]`
   - Format: "XX min"
   - Alert icon if > 30 min

4. **Order Growth %**
   - Measure: `[Order Growth MoM %]`
   - Format: Percentage
   - Trend arrow

#### Middle Row: Core Visualizations

**Left Column (40% width):**
- **Revenue & Profit Trend** (Line Chart)
  - X-axis: `order_date` (Month hierarchy)
  - Y-axis: `[Total Revenue]`, `[Total Profit]`
  - Dual axis
  - Add forecast for next 2 months

**Middle Column (30% width):**
- **City Performance Matrix** (Table)
  - Rows: `city`
  - Values: `[Total Revenue]`, `[Profit Margin %]`, `[SLA Breach Rate %]`
  - Conditional Formatting:
    - Profit Margin: Green (>20%), Yellow (10-20%), Red (<10%)
    - SLA Breach: Red (>30%), Yellow (20-30%), Green (<20%)
  - Sort by Revenue descending

**Right Column (30% width):**
- **Profit Margin by Category** (Clustered Bar Chart)
  - Y-axis: `category`
  - X-axis: `[Profit Margin %]`
  - Data labels ON
  - Sort descending

#### Bottom Row: Operational Insights

**Left:**
- **Discount Impact** (Scatter Chart)
  - X-axis: `discount_pct` (buckets: 0-5%, 5-10%, 10-15%, >15%)
  - Y-axis: `[Profit Margin %]`
  - Size: `[Total Orders]`
  - Tooltip: Show category breakdown

**Right:**
- **Peak Hours Heatmap** (Matrix)
  - Rows: `hour` (0-23)
  - Columns: `day_of_week` (Mon-Sun)
  - Values: `[Total Orders]`
  - Conditional: Color gradient (light to dark blue)

---

## Page 2: Delivery Operations

### Layout: Focus on operational bottlenecks

#### Top KPIs (3 cards)
- SLA Breach Rate %
- Avg Delivery Time
- On-Time Delivery % (inverse of breach rate)

#### Main Visualizations

**Delivery Time Distribution** (Histogram)
- X-axis: `delivery_time_minutes` (bins: 0-15, 15-20, 20-25, 25-30, 30-40, 40+)
- Y-axis: Count of orders
- Reference line at 30 min (SLA)

**City Delivery Performance** (Map Visual)
- Location: `city`
- Size: `[Total Orders]`
- Color: `[SLA Breach Rate %]` (Red-Yellow-Green gradient)

**Delivery vs Retention** (Combo Chart)
- X-axis: `city`
- Column Y-axis: `[Avg Delivery Time]`
- Line Y-axis: `[Repeat Customer Rate %]`
- Shows correlation

**Hourly Delivery Trend** (Line Chart)
- X-axis: `hour`
- Y-axis: `[Avg Delivery Time]`
- Color: Peak vs Off-Peak classification

---

## Page 3: Profitability Deep-Dive

### Focus: Where are we bleeding money?

#### Top Row
- **Loss-Making Products** (Table - Top 20)
  - Columns: Product Name, Category, City, Total Orders, Revenue, Profit
  - Filter: Profit < 0
  - Sort by Profit ascending

#### Middle Row

**Left:**
- **Category Profitability** (Waterfall Chart)
  - Categories on X-axis
  - Profit contribution on Y-axis
  - Shows which categories add/subtract from total profit

**Right:**
- **Margin vs Volume** (Bubble Chart)
  - X-axis: `[Total Orders]`
  - Y-axis: `[Profit Margin %]`
  - Bubble size: `[Total Revenue]`
  - Color by Category

#### Bottom Row
- **Discount Efficiency** (Table)
  - Rows: `discount_bucket`
  - Values: Avg Profit Margin %, Total Revenue, Orders
  - Conditional: Highlight buckets with negative ROI

---

## Interactive Slicers (All Pages)

Position: Left sidebar (10% width)

1. **Date Range** (Between slicer)
   - Field: `order_date`
   - Default: Last 90 days

2. **City** (Dropdown multi-select)
   - Field: `city`
   - Default: All

3. **Category** (Dropdown multi-select)
   - Field: `category`
   - Default: All

4. **Order Status** (Checkbox)
   - Field: `order_status`
   - Default: Delivered only

5. **Payment Mode** (Checkbox)
   - Field: `payment_mode`

---

## Drill-Through Setup

### From Any Visual → Product Details
- Target Page: "Product Details" (create new page)
- Drill-through fields: `product_id`, `category`
- Shows: Historical sales, profit trend, price changes

### From City Performance → City Deep-Dive
- Target Page: "City Deep-Dive" (create new page)
- Drill-through fields: `city`
- Shows: Store-level breakdown, hourly patterns, customer demographics

---

## Bookmarks for Quick Views

Create bookmarks for:
1. **Profit Alert View**: Filters to cities/categories with <10% margin
2. **Delivery Crisis View**: Filters to cities with >30% SLA breach
3. **Top Performers**: Filters to top 3 cities and categories
4. **Discount Analysis**: Focuses on discount-heavy orders

---

## Color Scheme (Brand Consistency)

- **Primary**: #FF5733 (Blinkit Orange)
- **Success**: #28A745 (Green)
- **Warning**: #FFC107 (Yellow)
- **Danger**: #DC3545 (Red)
- **Neutral**: #6C757D (Gray)

Background: White or very light gray (#F8F9FA)

---

## Advanced Features

### 1. What-If Parameters
Create parameter: "Discount Reduction %"
- Min: 0%, Max: 50%, Step: 5%
- Calculate projected profit impact

### 2. Forecasting
- Enable forecast on Revenue Trend (3-month prediction)
- Confidence interval: 95%

### 3. Alerts
Set up email alerts (if Power BI Service):
- Alert when SLA Breach Rate > 35%
- Alert when Profit Margin < 8%
- Alert when Cancellation Rate > 10%

---

## Publishing & Sharing

1. Publish to Power BI Service
2. Create App workspace: "Blinkit Leadership"
3. Schedule refresh: Daily at 6 AM
4. Share with: CEO, COO, CFO, City Heads
5. Row-level security (optional): City Heads see only their city

---

## Testing Checklist

Before presenting:
- [ ] All measures calculate correctly
- [ ] Filters work across pages
- [ ] Drill-throughs function
- [ ] Bookmarks load properly
- [ ] Colors align with brand
- [ ] No blank visuals
- [ ] Mobile layout configured
- [ ] Performance is acceptable (<3s load time)

---

## Key Insights to Highlight in Presentation

When presenting this dashboard, emphasize:

1. **Profit Margin Crisis**: If overall margin is <12%, this is unsustainable
2. **Delivery Bottlenecks**: Cities with >30% SLA breach need immediate operational fixes
3. **Discount Trap**: Quantify how deep discounts (>15%) destroy margins
4. **Category Optimization**: Show which categories subsidize loss-makers
5. **Customer Retention**: Prove correlation between delivery speed and repeat rate

---

**Dashboard Objective**: Enable leadership to make data-driven decisions within 30 seconds of opening the report.

Every visual must answer: "What should we do differently tomorrow?"