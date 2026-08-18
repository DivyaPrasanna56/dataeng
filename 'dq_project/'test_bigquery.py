from google.cloud import bigquery

PROJECT_ID = "project-b8fc8724-8adc-4499-9a4"

client = bigquery.Client(project=PROJECT_ID)

query = """
SELECT *
FROM `project-b8fc8724-8adc-4499-9a4.raw.orders`
"""

df = client.query(query).to_dataframe()

print("Connection successful!")
print("Total records:", len(df))

print("\nData:")
print(df)
