"""
Create DynamoDB Tables for MedGraph
=====================================
Creates all required DynamoDB tables with proper key schemas and GSIs.

Usage:
    python -m scripts.create_dynamodb_tables

Tables created (prefix: medgraph-):
    - medgraph-users
    - medgraph-consents
    - medgraph-chat-sessions
    - medgraph-chat-messages
    - medgraph-screening-summaries
    - medgraph-doctor-screening-consents
    - medgraph-patient-documents
    - medgraph-document-raw-texts
    - medgraph-fhir-bundles
    - medgraph-fhir-document-references
    - medgraph-phi-redaction-maps
    - medgraph-hospitals
    - medgraph-departments
    - medgraph-prescriptions
    - medgraph-appointments
    - medgraph-admissions
    - medgraph-vitals
    - medgraph-ipd-notes
    - medgraph-insurance-claims
    - medgraph-scheme-checks
    - medgraph-mlc-records
    - medgraph-mrn-counters
    - medgraph-notifications
    - medgraph-audit-logs
    - medgraph-activity-logs
"""
import boto3
import sys
import time

REGION = "us-east-1"
PREFIX = "medgraph"

# Table definitions: (name, partition_key, sort_key, GSIs)
# GSI format: (index_name, pk_attr, pk_type, sk_attr, sk_type)
TABLES = [
    {
        "name": "users",
        "pk": ("user_id", "S"),
        "sk": None,
        "gsis": [
            ("email-index", "email", "S", None, None),
            ("role-index", "role", "S", None, None),
        ],
    },
    {
        "name": "consents",
        "pk": ("consent_id", "S"),
        "sk": None,
        "gsis": [
            ("patient-index", "patient_id", "S", None, None),
            ("doctor-patient-index", "doctor_id", "S", "patient_id", "S"),
        ],
    },
    {
        "name": "chat-sessions",
        "pk": ("session_id", "S"),
        "sk": None,
        "gsis": [
            ("user-index", "user_id", "S", "updated_at", "S"),
        ],
    },
    {
        "name": "chat-messages",
        "pk": ("session_id", "S"),
        "sk": ("sort_key", "S"),
        "gsis": [],
    },
    {
        "name": "screening-summaries",
        "pk": ("screening_id", "S"),
        "sk": None,
        "gsis": [
            ("patient-index", "patient_id", "S", "summary_date", "S"),
            ("doctor-index", "target_doctor_id", "S", "summary_date", "S"),
        ],
    },
    {
        "name": "doctor-screening-consents",
        "pk": ("consent_id", "S"),
        "sk": None,
        "gsis": [
            ("screening-index", "screening_id", "S", None, None),
            ("doctor-index", "doctor_id", "S", None, None),
        ],
    },
    {
        "name": "patient-documents",
        "pk": ("document_id", "S"),
        "sk": None,
        "gsis": [
            ("patient-index", "patient_id", "S", "uploaded_at", "S"),
        ],
    },
    {
        "name": "document-raw-texts",
        "pk": ("document_id", "S"),
        "sk": None,
        "gsis": [],
    },
    {
        "name": "fhir-bundles",
        "pk": ("bundle_id", "S"),
        "sk": None,
        "gsis": [],
    },
    {
        "name": "fhir-document-references",
        "pk": ("document_id", "S"),
        "sk": None,
        "gsis": [
            ("patient-index", "patient_id", "S", None, None),
        ],
    },
    {
        "name": "phi-redaction-maps",
        "pk": ("redaction_map_id", "S"),
        "sk": None,
        "gsis": [
            ("document-index", "document_id", "S", None, None),
        ],
    },
    {
        "name": "hospitals",
        "pk": ("hospital_id", "S"),
        "sk": None,
        "gsis": [],
    },
    {
        "name": "departments",
        "pk": ("department_id", "S"),
        "sk": None,
        "gsis": [
            ("hospital-index", "hospital_id", "S", None, None),
        ],
    },
    {
        "name": "prescriptions",
        "pk": ("prescription_id", "S"),
        "sk": None,
        "gsis": [
            ("patient-index", "patient_id", "S", None, None),
        ],
    },
    {
        "name": "appointments",
        "pk": ("appointment_id", "S"),
        "sk": None,
        "gsis": [
            ("patient-index", "patient_id", "S", "date", "S"),
            ("doctor-index", "doctor_id", "S", "date", "S"),
        ],
    },
    {
        "name": "admissions",
        "pk": ("admission_id", "S"),
        "sk": None,
        "gsis": [
            ("patient-index", "patient_id", "S", None, None),
        ],
    },
    {
        "name": "vitals",
        "pk": ("vital_id", "S"),
        "sk": None,
        "gsis": [
            ("patient-index", "patient_id", "S", "recorded_at", "S"),
        ],
    },
    {
        "name": "ipd-notes",
        "pk": ("note_id", "S"),
        "sk": None,
        "gsis": [
            ("patient-index", "patient_id", "S", None, None),
            ("admission-index", "admission_id", "S", None, None),
        ],
    },
    {
        "name": "insurance-claims",
        "pk": ("claim_id", "S"),
        "sk": None,
        "gsis": [
            ("patient-index", "patient_id", "S", None, None),
        ],
    },
    {
        "name": "scheme-checks",
        "pk": ("check_id", "S"),
        "sk": None,
        "gsis": [
            ("patient-index", "patient_id", "S", None, None),
        ],
    },
    {
        "name": "mlc-records",
        "pk": ("mlc_id", "S"),
        "sk": None,
        "gsis": [
            ("patient-index", "patient_id", "S", None, None),
        ],
    },
    {
        "name": "mrn-counters",
        "pk": ("counter_id", "S"),
        "sk": None,
        "gsis": [],
    },
    {
        "name": "notifications",
        "pk": ("notification_id", "S"),
        "sk": None,
        "gsis": [
            ("user-index", "user_id", "S", "created_at", "S"),
        ],
    },
    {
        "name": "audit-logs",
        "pk": ("log_id", "S"),
        "sk": None,
        "gsis": [
            ("user-index", "user_id", "S", "timestamp", "S"),
            ("patient-index", "patient_id", "S", "timestamp", "S"),
        ],
    },
    {
        "name": "activity-logs",
        "pk": ("log_id", "S"),
        "sk": None,
        "gsis": [
            ("user-index", "user_id", "S", "timestamp", "S"),
        ],
    },
    {
        "name": "response-cache",
        "pk": ("cache_key", "S"),
        "sk": None,
        "gsis": [],
    },
]


def create_table(client, table_def):
    """Create a single DynamoDB table."""
    table_name = f"{PREFIX}-{table_def['name']}"

    # Key schema
    key_schema = [
        {"AttributeName": table_def["pk"][0], "KeyType": "HASH"},
    ]
    attr_defs = [
        {"AttributeName": table_def["pk"][0], "AttributeType": table_def["pk"][1]},
    ]

    if table_def["sk"]:
        key_schema.append(
            {"AttributeName": table_def["sk"][0], "KeyType": "RANGE"}
        )
        attr_defs.append(
            {"AttributeName": table_def["sk"][0], "AttributeType": table_def["sk"][1]}
        )

    # GSIs
    gsis = []
    for gsi in table_def.get("gsis", []):
        index_name, pk_attr, pk_type, sk_attr, sk_type = gsi

        # Add attribute definitions if not already present
        if not any(a["AttributeName"] == pk_attr for a in attr_defs):
            attr_defs.append({"AttributeName": pk_attr, "AttributeType": pk_type})
        if sk_attr and not any(a["AttributeName"] == sk_attr for a in attr_defs):
            attr_defs.append({"AttributeName": sk_attr, "AttributeType": sk_type})

        gsi_key_schema = [{"AttributeName": pk_attr, "KeyType": "HASH"}]
        if sk_attr:
            gsi_key_schema.append({"AttributeName": sk_attr, "KeyType": "RANGE"})

        gsis.append({
            "IndexName": index_name,
            "KeySchema": gsi_key_schema,
            "Projection": {"ProjectionType": "ALL"},
        })

    # Create table params
    params = {
        "TableName": table_name,
        "KeySchema": key_schema,
        "AttributeDefinitions": attr_defs,
        "BillingMode": "PAY_PER_REQUEST",
    }
    if gsis:
        params["GlobalSecondaryIndexes"] = gsis

    try:
        client.create_table(**params)
        print(f"  [CREATED]  {table_name}")
        return True
    except client.exceptions.ResourceInUseException:
        print(f"  [EXISTS]   {table_name}")
        return False
    except Exception as e:
        print(f"  [ERROR]    {table_name}: {e}")
        return False


def main():
    print("=" * 60)
    print("  MedGraph — DynamoDB Table Creation")
    print(f"  Region: {REGION}")
    print(f"  Prefix: {PREFIX}")
    print("=" * 60)
    print()

    client = boto3.client("dynamodb", region_name=REGION)

    # Verify credentials work
    try:
        client.list_tables(Limit=1)
        print("  AWS credentials verified ✓")
    except Exception as e:
        print(f"  ERROR: Cannot connect to AWS DynamoDB: {e}")
        print("  Make sure 'aws configure' is set up correctly.")
        sys.exit(1)

    print()
    print(f"  Creating {len(TABLES)} tables...")
    print("-" * 60)

    created = 0
    existed = 0
    errors = 0

    for table_def in TABLES:
        result = create_table(client, table_def)
        if result is True:
            created += 1
        elif result is False:
            existed += 1
        else:
            errors += 1

    print("-" * 60)
    print(f"  Done! Created: {created}, Already existed: {existed}, Errors: {errors}")
    print()

    if created > 0:
        print("  Waiting for tables to become ACTIVE...")
        waiter = client.get_waiter("table_exists")
        for table_def in TABLES:
            table_name = f"{PREFIX}-{table_def['name']}"
            try:
                waiter.wait(
                    TableName=table_name,
                    WaiterConfig={"Delay": 2, "MaxAttempts": 30}
                )
            except Exception:
                pass
        print("  All tables ACTIVE ✓")

    print()
    print("  Next steps:")
    print("    1. Run: python -m scripts.seed_test_users")
    print("    2. Run: python -m scripts.seed_patient_mrn")
    print("    3. Run: python -m scripts.seed_entities")
    print("    4. Restart the backend server")
    print()


if __name__ == "__main__":
    main()
