# 🚀 Automated Data Quality Monitoring and Intelligent Error Resolution using n8n and Google BigQuery

In this project, we build an **end-to-end automated Data Quality (DQ) pipeline** that accepts a CSV file through an n8n form, loads the data into Google BigQuery, validates the data using a Python Flask Data Quality API, identifies data-quality issues, and automatically sends an email notification containing the errors and recommended solutions.

This project demonstrates a practical data engineering use case where data-quality validation is automated instead of being performed manually.

---

## 🔥 What This Project Does

The pipeline automatically detects:

* ❌ NULL ORDER_ID
* ❌ NULL CUSTOMER_ID
* ❌ NEGATIVE AMOUNT
* ❌ INVALID EMAIL
* ❌ DUPLICATE ORDER_ID
* ❌ FUTURE ORDER_DATE

For every detected issue, the system provides:

* File name
* Total records
* Total errors
* Order ID
* Error type
* Recommended solution
* Unique Run ID

---

# 🏗️ Project Architecture

```text
CSV File
   ↓
n8n Form Trigger
   ↓
Extract From File
   ↓
Google BigQuery
   ↓
HTTP Request
   ↓
Python Flask DQ API
   ↓
Data Quality Validation
   ↓
IF Node
   ↓
Send Email
```

---

# 📁 Project Folder Structure

```text
D:\DQ_Project
│
├── requirements.txt
├── testbigquery.py
├── dqengine.py
├── dq_api.py
├── orders_bad.csv
└── orders_test2.csv
```

---

# 🐍 Python Requirements

```text
Flask==3.1.2
pandas==2.3.2
google-cloud-bigquery==3.36.0
db-dtypes==1.4.3
pyarrow==21.0.0
```

## ✅ Install Everything 

From CMD:

```cmd
cd /d D:\DQ_Project
```

Then:

```cmd
pip install -r requirements.txt
```

---

# ☁️ Google Cloud Configuration

### Project ID

```text
project-b8fc8724-8adc-4499-9a4
```

### Dataset

```text
raw
dq
```

---

# 🗄️ BigQuery Setup (UPDATED WITH DQ TABLES)

## ✅ 1. Raw Orders Table

```sql
CREATE SCHEMA IF NOT EXISTS `project-b8fc8724-8adc-4499-9a4.raw`;

CREATE OR REPLACE TABLE `project-b8fc8724-8adc-4499-9a4.raw.orders` (
  order_id INT64,
  customer_id STRING,
  email STRING,
  amount NUMERIC,
  order_date DATE
);
```

---

## ✅ 2. DQ Engine Table (NEW)

This table stores all detected data quality issues.

```sql
CREATE SCHEMA IF NOT EXISTS `project-b8fc8724-8adc-4499-9a4.dq`;

CREATE OR REPLACE TABLE `project-b8fc8724-8adc-4499-9a4.dq.dqengine` (
  run_id STRING,
  file_name STRING,
  order_id INT64,
  error_type STRING,
  error_description STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

---

## ✅ 3. DQ Run Summary Table (NEW)

This table stores overall execution summary of each run.

```sql
CREATE OR REPLACE TABLE `project-b8fc8724-8adc-4499-9a4.dq.dqrun` (
  run_id STRING,
  file_name STRING,
  total_records INT64,
  total_errors INT64,
  status STRING,
  run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);


```

---

## 📥 HOW TO LOAD CSV INTO BIGQUERY 

```cmd
bq load --source_format=CSV --skip_leading_rows=1 project-b8fc8724-8adc-4499-9a4:raw.orders orders_bad.csv
```

---

# 🔐 Google Cloud Authentication

```cmd
gcloud auth application-default login
```

---

# 🧪 Initial Testing

```cmd
cd /d D:\DQ_Project
python testbigquery.py
python dqengine.py
```

---

# 🐍 Start Flask API

```cmd
python dq_api.py
```

API:

```text
http://127.0.0.1:5000

```

---

# ✅ CURL COMMANDS 

After starting the Flask API, use the following commands to test the endpoints:

### 1️⃣ Check API is running

```cmd
curl http://127.0.0.1:5000/
```

---

### 2️⃣ Trigger Data Quality Run

```cmd
curl -X POST http://127.0.0.1:5000/run-dq
```

---

# 🔄 n8n Workflow

```text
Form Trigger
↓
Extract From File
↓
BigQuery Insert
↓
HTTP Request
↓
IF Node
↓
Send Email
```

---

# 🧩 n8n NODE JSON VALUES 

## ✅ HTTP Request Node (Body JSON)

```json
{
  "file_name": "{{ $('On form submission').item.binary.Upload_Orders_CSV.fileName }}"
}
```

---

## ✅ IF Node Condition

```json
{
  "conditions": {
    "string": [
      {
        "value1": "={{ $json.status }}",
        "operation": "equals",
        "value2": "FAILED"
      }
    ]
  }
}
```

---

## ✅ Send Email Node (HTML Body Expression)

```javascript
{{
`<h2>Data Quality Check Failed</h2>

<p><b>File Name:</b> ${$json.file_name}</p>
<p><b>Total Records:</b> ${$json.total_records}</p>
<p><b>Total Errors:</b> ${$json.total_errors}</p>

<h3>Error Details</h3>

${$json.errors.map((e, i) =>
`<p>
<b>${i + 1}. Order ID:</b> ${e.order_id}<br>
<b>Error:</b> ${e.error_type}<br>
<b>Solution:</b> ${e.solution}
</p>`
).join('')}

<hr>
<p><b>Run ID:</b> ${$json.run_id}</p>`
}}
```

---

# 🧠 Key Addition (Why dqengine & dqrun tables matter)

* `dqengine` → stores **row-level data quality errors**
* `dqrun` → stores **execution summary per file run**

This helps in:

* Audit tracking
* Historical DQ analysis
* Dashboard creation (Looker / Power BI)
* Monitoring pipeline health

---

# 🎯 Final Outcome

You now have a **production-style Data Quality system** with:

* Raw ingestion layer (BigQuery)
* Error tracking layer (dqengine)
* Execution tracking layer (dqrun)
* API-based validation engine
* Fully automated n8n workflow
* Email alert system
