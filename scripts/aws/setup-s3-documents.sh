#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# MedGraph AI — S3 Bucket Setup for Patient Document Storage
# ═══════════════════════════════════════════════════════════════════════════════
# Creates an S3 bucket for storing patient-uploaded lab reports (PDFs).
#
# Architecture:
#   Patient uploads PDF → S3 (encrypted at rest, versioned)
#   → Text extracted (PyMuPDF)
#   → PHI redacted
#   → Redacted text → OpenSearch (vector) + Neo4j (graph)
#   → Original PDF stays in S3 (patient can view/download)
#
# Compliance:
#   - Server-side encryption (AES-256)
#   - Versioning enabled (audit trail)
#   - Lifecycle: move to Glacier after 365 days
#   - Block public access (all)
#   - CORS configured for frontend uploads
#
# Run: bash scripts/aws/setup-s3-documents.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -e

AWS_CMD="aws"
REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID=$($AWS_CMD sts get-caller-identity --query "Account" --output text)
BUCKET_NAME="medgraph-patient-documents-${ACCOUNT_ID}"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   MedGraph AI — S3 Patient Documents Setup               ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "  Region:  $REGION"
echo "  Bucket:  $BUCKET_NAME"
echo ""

# ── Step 1: Create bucket ─────────────────────────────────────────────────────
echo "[1/6] Creating S3 bucket..."
if $AWS_CMD s3api head-bucket --bucket "$BUCKET_NAME" --region "$REGION" 2>/dev/null; then
    echo "  ⏭ Bucket already exists"
else
    if [ "$REGION" = "us-east-1" ]; then
        $AWS_CMD s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$REGION" >/dev/null
    else
        $AWS_CMD s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$REGION" \
            --create-bucket-configuration LocationConstraint="$REGION" >/dev/null
    fi
    echo "  ✓ Bucket created"
fi

# ── Step 2: Block all public access ──────────────────────────────────────────
echo "[2/6] Blocking public access..."
$AWS_CMD s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" >/dev/null
echo "  ✓ Public access blocked"

# ── Step 3: Enable versioning ─────────────────────────────────────────────────
echo "[3/6] Enabling versioning..."
$AWS_CMD s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled >/dev/null
echo "  ✓ Versioning enabled"

# ── Step 4: Server-side encryption (AES-256) ──────────────────────────────────
echo "[4/6] Enabling server-side encryption..."
$AWS_CMD s3api put-bucket-encryption \
    --bucket "$BUCKET_NAME" \
    --server-side-encryption-configuration '{
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                },
                "BucketKeyEnabled": true
            }
        ]
    }' >/dev/null
echo "  ✓ AES-256 encryption enabled"

# ── Step 5: Lifecycle policy (Glacier after 365 days) ─────────────────────────
echo "[5/6] Setting lifecycle policy..."
$AWS_CMD s3api put-bucket-lifecycle-configuration \
    --bucket "$BUCKET_NAME" \
    --lifecycle-configuration '{
        "Rules": [
            {
                "ID": "ArchiveOldDocuments",
                "Status": "Enabled",
                "Filter": {"Prefix": "documents/"},
                "Transitions": [
                    {
                        "Days": 365,
                        "StorageClass": "GLACIER"
                    }
                ]
            }
        ]
    }' >/dev/null
echo "  ✓ Lifecycle: Glacier after 365 days"

# ── Step 6: CORS for frontend direct upload ───────────────────────────────────
echo "[6/6] Configuring CORS..."
$AWS_CMD s3api put-bucket-cors \
    --bucket "$BUCKET_NAME" \
    --cors-configuration '{
        "CORSRules": [
            {
                "AllowedHeaders": ["*"],
                "AllowedMethods": ["GET", "PUT", "POST"],
                "AllowedOrigins": ["http://localhost:5173", "http://localhost:3000", "https://*.medgraph.ai"],
                "ExposeHeaders": ["ETag"],
                "MaxAgeSeconds": 3600
            }
        ]
    }' >/dev/null
echo "  ✓ CORS configured"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   ✓ S3 Patient Documents Bucket Ready                    ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║                                                          ║"
echo "║   Bucket: $BUCKET_NAME"
echo "║                                                          ║"
echo "║   .env config:                                           ║"
echo "║     S3_DOCUMENTS_BUCKET=$BUCKET_NAME"
echo "║                                                          ║"
echo "║   Security:                                              ║"
echo "║     ✓ AES-256 encryption at rest                         ║"
echo "║     ✓ Versioning (audit trail)                           ║"
echo "║     ✓ Public access blocked                              ║"
echo "║     ✓ Glacier archival after 365 days                    ║"
echo "║     ✓ CORS for frontend uploads                          ║"
echo "║                                                          ║"
echo "║   Key structure:                                         ║"
echo "║     documents/{patient_id}/{document_id}.pdf             ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
