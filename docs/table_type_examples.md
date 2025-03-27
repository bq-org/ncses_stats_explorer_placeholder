# NCSES Table Type Examples

This document provides detailed examples of each table type used in the NCSES Statistics Explorer. Understanding these structures is essential for working with the transformed data.

## Table Types Overview

The NCSES Statistics Explorer classifies tables into five structural types:

1. **Row Hierarchical (RH)**: Tables with hierarchies in row headers
2. **Matrix Hierarchical (MH)**: Tables with hierarchies in both rows and columns
3. **Time Series (TS)**: Data tracked over multiple time periods
4. **Column Hierarchical (CH)**: Tables with hierarchies in column headers
5. **Simple Tabular (ST)**: Flat data without hierarchies

## Detailed Examples

### RH - Row Hierarchical

Row Hierarchical tables have a hierarchical structure in the row headers, where rows have parent-child relationships.

#### Original Format Example:

```
Department                     | Budget 2023 | Employees
------------------------------|------------|----------
Finance                       | $1,200,000 | 45
 -> Accounting                | $500,000   | 18
 -> Treasury                  | $400,000   | 15
 -> Financial Planning        | $300,000   | 12
Operations                    | $3,500,000 | 120
 -> Manufacturing             | $2,000,000 | 80
    -> Assembly               | $1,200,000 | 55
    -> Quality Control        | $800,000   | 25
 -> Logistics                 | $1,500,000 | 40
```

#### Transformed CSV Format:

```csv
table_id,row_id,department_full_path,department_level_1,department_level_2,department_level_3,hierarchy_depth,field_budget_2023,field_employees
ex001,r001,"Finance","Finance","","",1,1200000,45
ex001,r002,"Finance -> Accounting","Finance","Accounting","",2,500000,18
ex001,r003,"Finance -> Treasury","Finance","Treasury","",2,400000,15
ex001,r004,"Finance -> Financial Planning","Finance","Financial Planning","",2,300000,12
ex001,r005,"Operations","Operations","","",1,3500000,120
ex001,r006,"Operations -> Manufacturing","Operations","Manufacturing","",2,2000000,80
ex001,r007,"Operations -> Manufacturing -> Assembly","Operations","Manufacturing","Assembly",3,1200000,55
ex001,r008,"Operations -> Manufacturing -> Quality Control","Operations","Manufacturing","Quality Control",3,800000,25
ex001,r009,"Operations -> Logistics","Operations","Logistics","",2,1500000,40
```

#### Key Characteristics:
- Row headers have parent-child relationships (e.g., "Finance -> Accounting")
- Hierarchy depth is explicitly recorded
- Hierarchy levels are normalized into separate columns
- Original full path is preserved

#### Real-world Examples:
- Federal funding by agency and sub-agency
- Organizational structures
- Taxonomic classifications
- Survey results by demographic categories and subcategories

---

### MH - Matrix Hierarchical

Matrix Hierarchical tables have hierarchies in both rows and columns, creating a complex multi-dimensional structure.

#### Original Format Example:

```
                |      2023 Sales      |      2022 Sales      |
Region          | Q1    | Q2    | Total| Q1    | Q2    | Total|
----------------|-------|-------|------|-------|-------|------|
North America   | $120K | $150K | $270K| $100K | $120K | $220K|
 -> US          | $100K | $120K | $220K| $85K  | $100K | $185K|
 -> Canada      | $20K  | $30K  | $50K | $15K  | $20K  | $35K |
Europe          | $90K  | $110K | $200K| $80K  | $90K  | $170K|
 -> UK          | $40K  | $50K  | $90K | $35K  | $40K  | $75K |
 -> Germany     | $30K  | $35K  | $65K | $25K  | $30K  | $55K |
 -> France      | $20K  | $25K  | $45K | $20K  | $20K  | $40K |
```

#### Transformed CSV Format:

```csv
table_id,row_id,region_full_path,region_level_1,region_level_2,hierarchy_depth,year_period,year_level_1,year_level_2,period_hierarchy_depth,value
ex002,r001,"North America","North America","",1,"2023 Sales -> Q1","2023 Sales","Q1",2,120000
ex002,r002,"North America","North America","",1,"2023 Sales -> Q2","2023 Sales","Q2",2,150000
ex002,r003,"North America","North America","",1,"2023 Sales -> Total","2023 Sales","Total",2,270000
ex002,r004,"North America -> US","North America","US",2,"2023 Sales -> Q1","2023 Sales","Q1",2,100000
ex002,r005,"North America -> US","North America","US",2,"2023 Sales -> Q2","2023 Sales","Q2",2,120000
ex002,r006,"North America -> US","North America","US",2,"2023 Sales -> Total","2023 Sales","Total",2,220000
ex002,r007,"North America -> Canada","North America","Canada",2,"2023 Sales -> Q1","2023 Sales","Q1",2,20000
```

#### Key Characteristics:
- Both row and column headers have hierarchical structures
- The transformed format creates a normalized view of the matrix
- Each data point is associated with both row and column hierarchies
- All hierarchy information is preserved

#### Real-world Examples:
- Cross-tabulated survey results
- Multi-dimensional financial data
- Complex research studies with nested variables
- Comparative statistics across multiple dimensions

---

### TS - Time Series

Time Series tables track data over multiple time periods to show trends and changes over time.

#### Original Format Example:

```
Metric          | 2019   | 2020   | 2021   | 2022   | 2023   |
----------------|--------|--------|--------|--------|--------|
GDP Growth      | 2.3%   | -3.5%  | 5.7%   | 2.1%   | 1.9%   |
Unemployment    | 3.7%   | 8.1%   | 5.4%   | 3.9%   | 3.5%   |
Inflation Rate  | 1.8%   | 1.2%   | 4.7%   | 8.0%   | 4.1%   |
Interest Rate   | 2.25%  | 0.25%  | 0.25%  | 3.25%  | 5.50%  |
```

#### Transformed CSV Format:

```csv
table_id,row_id,metric,time_period,value,unit
ex003,r001,"GDP Growth","2019",2.3,"percentage"
ex003,r002,"GDP Growth","2020",-3.5,"percentage"
ex003,r003,"GDP Growth","2021",5.7,"percentage"
ex003,r004,"GDP Growth","2022",2.1,"percentage"
ex003,r005,"GDP Growth","2023",1.9,"percentage"
ex003,r006,"Unemployment","2019",3.7,"percentage"
ex003,r007,"Unemployment","2020",8.1,"percentage"
```

#### Key Characteristics:
- Time periods are explicitly identified in a dedicated column
- One record per time period and metric
- Long-form format that's ideal for time series analysis
- Units are standardized and consistently applied

#### Real-world Examples:
- Economic indicators over time
- Annual research funding trends
- Periodic survey results
- Longitudinal studies
- Historical statistics

---

### CH - Column Hierarchical

Column Hierarchical tables have hierarchical structures in column headers, often used for grouped measurements.

#### Original Format Example:

```
Employee ID | Name          |  Performance Metrics   |    Compensation     |
           |               | Targets | Achievement | Salary | Bonus | Total|
-----------|---------------|---------|------------|--------|-------|------|
101        | Alice Johnson | 95%     | 98%        | $85K   | $10K  | $95K |
102        | Bob Smith     | 90%     | 92%        | $75K   | $8K   | $83K |
103        | Carol Lee     | 95%     | 90%        | $90K   | $7K   | $97K |
104        | David Brown   | 85%     | 88%        | $70K   | $6K   | $76K |
```

#### Transformed CSV Format:

```csv
table_id,row_id,employee_id,name,category,category_level_1,category_level_2,hierarchy_depth,value,unit
ex004,r001,101,"Alice Johnson","Performance Metrics -> Targets","Performance Metrics","Targets",2,95,"percentage"
ex004,r002,101,"Alice Johnson","Performance Metrics -> Achievement","Performance Metrics","Achievement",2,98,"percentage"
ex004,r003,101,"Alice Johnson","Compensation -> Salary","Compensation","Salary",2,85000,"dollars"
ex004,r004,101,"Alice Johnson","Compensation -> Bonus","Compensation","Bonus",2,10000,"dollars"
ex004,r005,101,"Alice Johnson","Compensation -> Total","Compensation","Total",2,95000,"dollars"
ex004,r006,102,"Bob Smith","Performance Metrics -> Targets","Performance Metrics","Targets",2,90,"percentage"
```

#### Key Characteristics:
- Column headers have hierarchical structures
- Transformed format normalizes column hierarchies into category fields
- Each measurement is associated with its category hierarchy
- Units are preserved for each measurement type

#### Real-world Examples:
- Performance evaluations
- Educational assessment data
- Financial statements with grouped metrics
- Health statistics with nested measurement categories

---

### ST - Simple Tabular

Simple Tabular tables have a flat structure without hierarchies, using straightforward rows and columns.

#### Original Format Example:

```
Product ID | Product Name    | Category    | Price  | Stock | Rating |
-----------|----------------|-------------|--------|-------|--------|
P001       | Laptop Pro     | Electronics | $1,299 | 45    | 4.7    |
P002       | Office Chair   | Furniture   | $199   | 78    | 4.2    |
P003       | Wireless Mouse | Electronics | $49    | 120   | 4.5    |
P004       | Coffee Maker   | Appliances  | $89    | 34    | 4.8    |
P005       | Desk Lamp      | Lighting    | $39    | 67    | 4.3    |
```

#### Transformed CSV Format:

```csv
table_id,row_id,field_product_id,field_product_name,field_category,field_price,field_stock,field_rating
ex005,r001,"P001","Laptop Pro","Electronics",1299,45,4.7
ex005,r002,"P002","Office Chair","Furniture",199,78,4.2
ex005,r003,"P003","Wireless Mouse","Electronics",49,120,4.5
ex005,r004,"P004","Coffee Maker","Appliances",89,34,4.8
ex005,r005,"P005","Desk Lamp","Lighting",39,67,4.3
```

#### Key Characteristics:
- No hierarchical structures in rows or columns
- Straightforward transformation to CSV
- Field names are standardized with the "field_" prefix
- Data types are preserved (e.g., numeric values, text)

#### Real-world Examples:
- Product catalogs
- Simple survey responses
- Contact lists
- Event logs
- Basic inventory data

## Transformation Benefits

The NCSES Statistics Explorer's transformation process provides several key benefits:

1. **Standardization**: Consistent structure across different table types
2. **Machine-Readability**: CSV format that's easily processed by ML tools
3. **Hierarchical Preservation**: Complete retention of hierarchical relationships
4. **Semantic Enrichment**: ML Croissant metadata with data types and descriptions
5. **Flexibility**: Support for diverse visualization and analysis tools

## Conclusion

Understanding these table types and their transformations is crucial for effectively working with NCSES data. Each type has unique structural characteristics that impact how the data can be analyzed and visualized. The NCSES Statistics Explorer handles all these types seamlessly, providing standardized outputs that maintain the original semantic richness while being machine-readable.
