from google.cloud import bigquery
from datetime import datetime
import uuid
import pandas as pd

# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

PROJECT_ID = "project-b8fc8724-8adc-4499-9a4"

SOURCE_TABLE = f"{PROJECT_ID}.raw.orders"
ERROR_TABLE = f"{PROJECT_ID}.dq.dq_errors"
RUN_TABLE = f"{PROJECT_ID}.dq.dq_runs"

FILE_NAME = "orders_bad.csv"

# Generate unique run ID
RUN_ID = str(uuid.uuid4())

# Create BigQuery client
client = bigquery.Client(project=PROJECT_ID)


# --------------------------------------------------
# 2. READ DATA FROM BIGQUERY
# --------------------------------------------------

print("Reading data from BigQuery...")

query = f"""
SELECT *
FROM `{SOURCE_TABLE}`
"""

df = client.query(query).to_dataframe()

print(f"Total records found: {len(df)}")


# --------------------------------------------------
# 3. DATA QUALITY ERROR LIST
# --------------------------------------------------

errors = []


# --------------------------------------------------
# 4. CHECK NULL CUSTOMER_ID
# --------------------------------------------------

print("Checking NULL CUSTOMER_ID...")

null_customer = df[df["customer_id"].isna()]

for _, row in null_customer.iterrows():

    errors.append({
        "run_id": RUN_ID,
        "file_name": FILE_NAME,
        "order_id": int(row["order_id"]),
        "error_type": "NULL CUSTOMER ID",
        "error_message": "CUSTOMER_ID is NULL",
        "root_cause": "Customer ID was not provided in the source file",
        "solution": "Provide a valid CUSTOMER_ID and reload the record",
        "detected_at": datetime.utcnow()
    })


# --------------------------------------------------
# 5. CHECK NEGATIVE AMOUNT
# --------------------------------------------------

print("Checking negative amounts...")

negative_amount = df[df["amount"] < 0]

for _, row in negative_amount.iterrows():

    errors.append({
        "run_id": RUN_ID,
        "file_name": FILE_NAME,
        "order_id": int(row["order_id"]),
        "error_type": "NEGATIVE AMOUNT",
        "error_message": "AMOUNT is negative",
        "root_cause": "Transaction amount contains a negative value",
        "solution": "Correct the transaction amount and reload the record",
        "detected_at": datetime.utcnow()
    })


# --------------------------------------------------
# 6. CHECK INVALID EMAIL
# --------------------------------------------------

print("Checking invalid emails...")

invalid_email = df[
    ~df["email"].astype(str).str.contains("@", na=False)
]

for _, row in invalid_email.iterrows():

    errors.append({
        "run_id": RUN_ID,
        "file_name": FILE_NAME,
        "order_id": int(row["order_id"]),
        "error_type": "INVALID EMAIL",
        "error_message": "Invalid email format",
        "root_cause": "Email does not contain a valid @ symbol",
        "solution": "Provide a valid email address",
        "detected_at": datetime.utcnow()
    })


# --------------------------------------------------
# 7. CHECK DUPLICATE ORDER_ID
# --------------------------------------------------

print("Checking duplicate ORDER_ID...")

duplicates = df[
    df.duplicated(
        subset=["order_id"],
        keep=False
    )
]

for _, row in duplicates.iterrows():

    errors.append({
        "run_id": RUN_ID,
        "file_name": FILE_NAME,
        "order_id": int(row["order_id"]),
        "error_type": "DUPLICATE ORDER ID",
        "error_message": "ORDER_ID appears more than once",
        "root_cause": "Duplicate transaction exists in the source file",
        "solution": "Remove the duplicate record or provide a unique ORDER_ID",
        "detected_at": datetime.utcnow()
    })


# --------------------------------------------------
# 8. CHECK FUTURE ORDER DATE
# --------------------------------------------------

print("Checking future order dates...")

today = datetime.utcnow().date()

future_dates = df[
    df["order_date"] > today
]

for _, row in future_dates.iterrows():

    errors.append({
        "run_id": RUN_ID,
        "file_name": FILE_NAME,
        "order_id": int(row["order_id"]),
        "error_type": "FUTURE ORDER DATE",
        "error_message": "ORDER_DATE is in the future",
        "root_cause": "Source data contains a future transaction date",
        "solution": "Correct the ORDER_DATE and reload the record",
        "detected_at": datetime.utcnow()
    })


# --------------------------------------------------
# 9. DISPLAY RESULTS
# --------------------------------------------------

print("\n===================================")
print("DATA QUALITY RESULTS")
print("===================================")

print(f"Run ID: {RUN_ID}")
print(f"Total Records: {len(df)}")
print(f"Total Errors: {len(errors)}")


# --------------------------------------------------
# 10. WRITE ERRORS TO BIGQUERY
# --------------------------------------------------

if errors:

    error_df = pd.DataFrame(errors)

    print("\nWriting errors to BigQuery...")

    job = client.load_table_from_dataframe(
        error_df,
        ERROR_TABLE
    )

    job.result()

    print("Errors successfully written to dq_errors table.")

else:

    print("\nNo data quality errors found.")


# --------------------------------------------------
# 11. DETERMINE STATUS
# --------------------------------------------------

if errors:
    status = "FAILED"
else:
    status = "PASSED"


# --------------------------------------------------
# 12. WRITE RUN SUMMARY
# --------------------------------------------------

run_data = pd.DataFrame([{
    "run_id": RUN_ID,
    "file_name": FILE_NAME,
    "total_records": len(df),
    "failed_records": len(errors),
    "status": status,
    "run_time": datetime.utcnow()
}])

print("Writing run summary...")

job = client.load_table_from_dataframe(
    run_data,
    RUN_TABLE
)

job.result()


# --------------------------------------------------
# 13. FINAL RESULT
# --------------------------------------------------

print("\n===================================")
print("FINAL RESULT")
print("===================================")

print(f"STATUS          : {status}")
print(f"TOTAL RECORDS   : {len(df)}")
print(f"TOTAL ERRORS    : {len(errors)}")
print("===================================")