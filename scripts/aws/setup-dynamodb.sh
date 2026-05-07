#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# MedGraph AI — DynamoDB Table Setup
# ═══════════════════════════════════════════════════════════════════════════════
# Creates all DynamoDB tables required by the application.
# Uses on-demand (PAY_PER_REQUEST) billing — no capacity planning needed.
#
# Tables:
#   1. medgraph-users           — User accounts (PK: user_id, GSI: email)
#   2. medgraph-consents        — Consent records (PK: consent_id, GSIs: doctor+patient)
#   3. medgraph-chat-sessions   — Chat sessions (PK: session_id, GSI: user_id)
#   4. medgraph-chat-messages   — Chat messages (PK: session_id, SK: timestamp#message_id)
#   5. medgraph-audit-logs      — PHI access audit (PK: patient_id, SK: timestamp#event_id)
#   6. medgraph-screening       — Screening summaries (PK: screening_id, GSIs: stage, doctor)
#   7. medgraph-fhir-bundles    — FHIR bundles (PK: bundle_id)
#   8. medgraph-hospitals       — Hospital registry (PK: hospital_id)
#   9. medgraph-counters        — Atomic counters for MRN (PK: counter_id)
#  10. medgraph-cache           — Response cache (PK: cache_key, TTL enabled)
#
# Run: bash scripts/aws/setup-dynamodb.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -e

AWS_CMD="aws"
REGION="${AWS_REGION:-us-east-1}"
TABLE_PREFIX="medgraph"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   MedGraph AI — DynamoDB Table Setup                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Region: $REGION"
echo "Table prefix: $TABLE_PREFIX"
echo ""

# Helper: create table only if it doesn't exist
create_table_if_not_exists() {
    local TABLE_NAME=$1
    shift
    
    if $AWS_CMD dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" >/dev/null 2>&1; then
        echo "  ⏭  $TABLE_NAME already exists — skipping"
    else
        echo "  ⏳ Creating $TABLE_NAME..."
        $AWS_CMD dynamodb create-table --region "$REGION" "$@" >/dev/null
        echo "  ✓  $TABLE_NAME created"
    fi
}

# ══════════════════════════════════════════════════════════════════════════════
# TABLE 1: medgraph-users
# PK: user_id
# GSI: email-index (email → user_id) for login lookup
# GSI: role-index (role → user_id) for admin listing
# ══════════════════════════════════════════════════════════════════════════════
echo "[1/10] Users table..."
create_table_if_not_exists "${TABLE_PREFIX}-users" \
    --table-name "${TABLE_PREFIX}-users" \
    --attribute-definitions \
        AttributeName=user_id,AttributeType=S \
        AttributeName=email,AttributeType=S \
        AttributeName=role,AttributeType=S \
    --key-schema \
        AttributeName=user_id,KeyType=HASH \
    --global-secondary-indexes \
        "[
            {
                \"IndexName\": \"email-index\",
                \"KeySchema\": [{\"AttributeName\":\"email\",\"KeyType\":\"HASH\"}],
                \"Projection\": {\"ProjectionType\":\"ALL\"}
            },
            {
                \"IndexName\": \"role-index\",
                \"KeySchema\": [{\"AttributeName\":\"role\",\"KeyType\":\"HASH\"}],
                \"Projection\": {\"ProjectionType\":\"ALL\"}
            }
        ]" \
    --billing-mode PAY_PER_REQUEST

# ══════════════════════════════════════════════════════════════════════════════
# TABLE 2: medgraph-consents
# PK: consent_id
# GSI: patient-index (patient_id → consent records)
# GSI: doctor-patient-index (doctor_id + patient_id) for consent checks
# ══════════════════════════════════════════════════════════════════════════════
echo "[2/10] Consents table..."
create_table_if_not_exists "${TABLE_PREFIX}-consents" \
    --table-name "${TABLE_PREFIX}-consents" \
    --attribute-definitions \
        AttributeName=consent_id,AttributeType=S \
        AttributeName=patient_id,AttributeType=S \
        AttributeName=doctor_id,AttributeType=S \
    --key-schema \
        AttributeName=consent_id,KeyType=HASH \
    --global-secondary-indexes \
        "[
            {
                \"IndexName\": \"patient-index\",
                \"KeySchema\": [{\"AttributeName\":\"patient_id\",\"KeyType\":\"HASH\"}],
                \"Projection\": {\"ProjectionType\":\"ALL\"}
            },
            {
                \"IndexName\": \"doctor-patient-index\",
                \"KeySchema\": [
                    {\"AttributeName\":\"doctor_id\",\"KeyType\":\"HASH\"},
                    {\"AttributeName\":\"patient_id\",\"KeyType\":\"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\":\"ALL\"}
            }
        ]" \
    --billing-mode PAY_PER_REQUEST

# ══════════════════════════════════════════════════════════════════════════════
# TABLE 3: medgraph-chat-sessions
# PK: session_id
# GSI: user-index (user_id + updated_at) for listing sessions
# ══════════════════════════════════════════════════════════════════════════════
echo "[3/10] Chat sessions table..."
create_table_if_not_exists "${TABLE_PREFIX}-chat-sessions" \
    --table-name "${TABLE_PREFIX}-chat-sessions" \
    --attribute-definitions \
        AttributeName=session_id,AttributeType=S \
        AttributeName=user_id,AttributeType=S \
        AttributeName=updated_at,AttributeType=S \
    --key-schema \
        AttributeName=session_id,KeyType=HASH \
    --global-secondary-indexes \
        "[
            {
                \"IndexName\": \"user-index\",
                \"KeySchema\": [
                    {\"AttributeName\":\"user_id\",\"KeyType\":\"HASH\"},
                    {\"AttributeName\":\"updated_at\",\"KeyType\":\"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\":\"ALL\"}
            }
        ]" \
    --billing-mode PAY_PER_REQUEST

# ══════════════════════════════════════════════════════════════════════════════
# TABLE 4: medgraph-chat-messages
# PK: session_id, SK: timestamp#message_id (for chronological ordering)
# TTL on 'expires_at' field for auto-cleanup
# ══════════════════════════════════════════════════════════════════════════════
echo "[4/10] Chat messages table..."
create_table_if_not_exists "${TABLE_PREFIX}-chat-messages" \
    --table-name "${TABLE_PREFIX}-chat-messages" \
    --attribute-definitions \
        AttributeName=session_id,AttributeType=S \
        AttributeName=sort_key,AttributeType=S \
    --key-schema \
        AttributeName=session_id,KeyType=HASH \
        AttributeName=sort_key,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST

# Enable TTL on chat messages
$AWS_CMD dynamodb update-time-to-live \
    --table-name "${TABLE_PREFIX}-chat-messages" \
    --region "$REGION" \
    --time-to-live-specification "Enabled=true,AttributeName=expires_at" 2>/dev/null || true

# ══════════════════════════════════════════════════════════════════════════════
# TABLE 5: medgraph-audit-logs
# PK: patient_id, SK: timestamp#event_id (for chronological patient audit trail)
# GSI: accessor-index (accessor_id + timestamp) for "who accessed what"
# ══════════════════════════════════════════════════════════════════════════════
echo "[5/10] Audit logs table..."
create_table_if_not_exists "${TABLE_PREFIX}-audit-logs" \
    --table-name "${TABLE_PREFIX}-audit-logs" \
    --attribute-definitions \
        AttributeName=patient_id,AttributeType=S \
        AttributeName=sort_key,AttributeType=S \
        AttributeName=accessor_id,AttributeType=S \
    --key-schema \
        AttributeName=patient_id,KeyType=HASH \
        AttributeName=sort_key,KeyType=RANGE \
    --global-secondary-indexes \
        "[
            {
                \"IndexName\": \"accessor-index\",
                \"KeySchema\": [
                    {\"AttributeName\":\"accessor_id\",\"KeyType\":\"HASH\"},
                    {\"AttributeName\":\"sort_key\",\"KeyType\":\"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\":\"ALL\"}
            }
        ]" \
    --billing-mode PAY_PER_REQUEST

# ══════════════════════════════════════════════════════════════════════════════
# TABLE 6: medgraph-screening
# PK: screening_id
# GSI: stage-index (stage → screening_id) for HITL queue
# GSI: doctor-index (target_doctor_id + stage) for doctor inbox
# GSI: patient-index (patient_id) for patient history
# ══════════════════════════════════════════════════════════════════════════════
echo "[6/10] Screening table..."
create_table_if_not_exists "${TABLE_PREFIX}-screening" \
    --table-name "${TABLE_PREFIX}-screening" \
    --attribute-definitions \
        AttributeName=screening_id,AttributeType=S \
        AttributeName=stage,AttributeType=S \
        AttributeName=target_doctor_id,AttributeType=S \
        AttributeName=patient_id,AttributeType=S \
    --key-schema \
        AttributeName=screening_id,KeyType=HASH \
    --global-secondary-indexes \
        "[
            {
                \"IndexName\": \"stage-index\",
                \"KeySchema\": [{\"AttributeName\":\"stage\",\"KeyType\":\"HASH\"}],
                \"Projection\": {\"ProjectionType\":\"ALL\"}
            },
            {
                \"IndexName\": \"doctor-index\",
                \"KeySchema\": [
                    {\"AttributeName\":\"target_doctor_id\",\"KeyType\":\"HASH\"},
                    {\"AttributeName\":\"stage\",\"KeyType\":\"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\":\"ALL\"}
            },
            {
                \"IndexName\": \"patient-index\",
                \"KeySchema\": [{\"AttributeName\":\"patient_id\",\"KeyType\":\"HASH\"}],
                \"Projection\": {\"ProjectionType\":\"ALL\"}
            }
        ]" \
    --billing-mode PAY_PER_REQUEST

# ══════════════════════════════════════════════════════════════════════════════
# TABLE 7: medgraph-fhir-bundles
# PK: bundle_id
# ══════════════════════════════════════════════════════════════════════════════
echo "[7/10] FHIR bundles table..."
create_table_if_not_exists "${TABLE_PREFIX}-fhir-bundles" \
    --table-name "${TABLE_PREFIX}-fhir-bundles" \
    --attribute-definitions \
        AttributeName=bundle_id,AttributeType=S \
    --key-schema \
        AttributeName=bundle_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

# ══════════════════════════════════════════════════════════════════════════════
# TABLE 8: medgraph-hospitals
# PK: hospital_id
# ══════════════════════════════════════════════════════════════════════════════
echo "[8/10] Hospitals table..."
create_table_if_not_exists "${TABLE_PREFIX}-hospitals" \
    --table-name "${TABLE_PREFIX}-hospitals" \
    --attribute-definitions \
        AttributeName=hospital_id,AttributeType=S \
    --key-schema \
        AttributeName=hospital_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

# ══════════════════════════════════════════════════════════════════════════════
# TABLE 9: medgraph-counters
# PK: counter_id (e.g., "national-2026" for MRN sequences)
# Uses atomic ADD for incrementing
# ══════════════════════════════════════════════════════════════════════════════
echo "[9/10] Counters table..."
create_table_if_not_exists "${TABLE_PREFIX}-counters" \
    --table-name "${TABLE_PREFIX}-counters" \
    --attribute-definitions \
        AttributeName=counter_id,AttributeType=S \
    --key-schema \
        AttributeName=counter_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

# ══════════════════════════════════════════════════════════════════════════════
# TABLE 10: medgraph-cache
# PK: cache_key
# TTL on 'expires_at' for auto-eviction
# ══════════════════════════════════════════════════════════════════════════════
echo "[10/10] Cache table..."
create_table_if_not_exists "${TABLE_PREFIX}-cache" \
    --table-name "${TABLE_PREFIX}-cache" \
    --attribute-definitions \
        AttributeName=cache_key,AttributeType=S \
    --key-schema \
        AttributeName=cache_key,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

# Enable TTL on cache
$AWS_CMD dynamodb update-time-to-live \
    --table-name "${TABLE_PREFIX}-cache" \
    --region "$REGION" \
    --time-to-live-specification "Enabled=true,AttributeName=expires_at" 2>/dev/null || true

# ══════════════════════════════════════════════════════════════════════════════
# Wait for all tables to become ACTIVE
# ══════════════════════════════════════════════════════════════════════════════
echo ""
echo "Waiting for tables to become ACTIVE..."

TABLES=(
    "${TABLE_PREFIX}-users"
    "${TABLE_PREFIX}-consents"
    "${TABLE_PREFIX}-chat-sessions"
    "${TABLE_PREFIX}-chat-messages"
    "${TABLE_PREFIX}-audit-logs"
    "${TABLE_PREFIX}-screening"
    "${TABLE_PREFIX}-fhir-bundles"
    "${TABLE_PREFIX}-hospitals"
    "${TABLE_PREFIX}-counters"
    "${TABLE_PREFIX}-cache"
)

for TABLE in "${TABLES[@]}"; do
    $AWS_CMD dynamodb wait table-exists --table-name "$TABLE" --region "$REGION" 2>/dev/null
done

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   ✓ All 10 DynamoDB tables created successfully          ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║                                                          ║"
echo "║   .env config:                                           ║"
echo "║     AWS_REGION=$REGION                                   ║"
echo "║     DYNAMODB_TABLE_PREFIX=$TABLE_PREFIX                  ║"
echo "║                                                          ║"
echo "║   Billing: PAY_PER_REQUEST (on-demand)                   ║"
echo "║   TTL: Enabled on chat-messages + cache                  ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
