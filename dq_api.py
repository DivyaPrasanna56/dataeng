from flask import Flask, jsonify, request
from google.cloud import bigquery
import pandas as pd
import uuid

app = Flask(__name__)

PROJECT_ID = "project-b8fc8724-8adc-4499-9a4"

SOURCE_TABLE = f"{PROJECT_ID}.raw.orders"

client = bigquery.Client(project=PROJECT_ID)


@app.route("/", methods=["GET"])
def home():
    return "DQ API is running"


@app.route("/run-dq", methods=["POST"])
def run_dq():

    try:
        print("DQ API request received")

        # Get filename from n8n
        data = request.get_json(silent=True) or {}

        file_name = data.get("file_name", "unknown.csv")

        # Create unique run ID
        run_id = str(uuid.uuid4())

        print(f"File: {file_name}")
        print(f"Run ID: {run_id}")

        # Read BigQuery
        query = f"""
        SELECT
            order_id,
            customer_id,
            email,
            amount,
            order_date
        FROM `{SOURCE_TABLE}`
        """

        print("Reading BigQuery...")

        df = client.query(query).to_dataframe()

        print(f"Records found: {len(df)}")

        errors = []

        # Safe ORDER_ID conversion
        def get_order_id(value):
            if pd.isna(value):
                return None
            return int(value)

        # NULL ORDER ID
        null_order_id = df[df["order_id"].isna()]

        for _, row in null_order_id.iterrows():
            errors.append({
                "order_id": None,
                "error_type": "NULL ORDER ID",
                "solution": "Provide a valid ORDER_ID"
            })

        # NULL CUSTOMER ID
        null_customer = df[df["customer_id"].isna()]

        for _, row in null_customer.iterrows():
            errors.append({
                "order_id": get_order_id(row["order_id"]),
                "error_type": "NULL CUSTOMER ID",
                "solution": "Provide a valid CUSTOMER_ID"
            })

        # NEGATIVE AMOUNT
        negative_amount = df[df["amount"] < 0]

        for _, row in negative_amount.iterrows():
            errors.append({
                "order_id": get_order_id(row["order_id"]),
                "error_type": "NEGATIVE AMOUNT",
                "solution": "Correct the transaction amount"
            })

        # INVALID EMAIL
        invalid_email = df[
            ~df["email"].astype(str).str.contains("@", na=False)
        ]

        for _, row in invalid_email.iterrows():
            errors.append({
                "order_id": get_order_id(row["order_id"]),
                "error_type": "INVALID EMAIL",
                "solution": "Provide a valid email address"
            })

        # DUPLICATE ORDER ID
        duplicates = df[
            df.duplicated(
                subset=["order_id"],
                keep=False
            )
            & df["order_id"].notna()
        ]

        for _, row in duplicates.iterrows():
            errors.append({
                "order_id": get_order_id(row["order_id"]),
                "error_type": "DUPLICATE ORDER ID",
                "solution": "Remove the duplicate ORDER_ID"
            })

        # FUTURE DATE
        df["order_date"] = pd.to_datetime(
            df["order_date"],
            errors="coerce"
        )

        today = pd.Timestamp.today().normalize()

        future_dates = df[
            df["order_date"] > today
        ]

        for _, row in future_dates.iterrows():
            errors.append({
                "order_id": get_order_id(row["order_id"]),
                "error_type": "FUTURE ORDER DATE",
                "solution": "Correct the ORDER_DATE"
            })

        # Final status
        status = "FAILED" if errors else "PASSED"

        print(f"DQ Status: {status}")
        print(f"Total errors: {len(errors)}")

        # Return result to n8n
        return jsonify({
            "status": status,
            "total_records": len(df),
            "total_errors": len(errors),
            "file_name": file_name,
            "errors": errors,
            "run_id": run_id
        })

    except Exception as e:

        print("ERROR:", str(e))

        return jsonify({
            "status": "ERROR",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )