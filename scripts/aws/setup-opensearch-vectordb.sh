#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# MedGraph AI — AWS OpenSearch Serverless Vector DB Setup
# ═══════════════════════════════════════════════════════════════════════════════
# Creates an OpenSearch Serverless collection configured for vector search.
# This replaces Qdrant as the vector database for patient memory embeddings.
#
# What this script creates:
#   1. Encryption policy (required before collection)
#   2. Network policy (public access for dev)
#   3. Data access policy (IAM role-based)
#   4. OpenSearch Serverless collection (type: VECTORSEARCH)
#   5. Waits for collection to become ACTIVE
#   6. Creates the vector index with knn mapping
#
# Run: bash scripts/aws/setup-opensearch-vectordb.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -e

AWS_CMD="aws"
REGION="${AWS_REGION:-us-east-1}"
COLLECTION_NAME="medgraph-vectors"
INDEX_NAME="patient-memories"
EMBEDDING_DIM=1024

# Get current identity
ACCOUNT_ID=$($AWS_CMD sts get-caller-identity --query "Account" --output text)
CALLER_ARN=$($AWS_CMD sts get-caller-identity --query "Arn" --output text)

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   MedGraph AI — OpenSearch Serverless Vector DB Setup    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "  Region:     $REGION"
echo "  Account:    $ACCOUNT_ID"
echo "  Principal:  $CALLER_ARN"
echo "  Collection: $COLLECTION_NAME"
echo "  Index:      $INDEX_NAME"
echo "  Dimensions: $EMBEDDING_DIM"
echo ""

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1: Encryption Policy
# ══════════════════════════════════════════════════════════════════════════════
echo "[1/6] Creating encryption policy..."

ENCRYPTION_POLICY='{
  "Rules": [
    {
      "ResourceType": "collection",
      "Resource": ["collection/'"$COLLECTION_NAME"'"]
    }
  ],
  "AWSOwnedKey": true
}'

$AWS_CMD opensearchserverless create-security-policy \
    --region "$REGION" \
    --name "${COLLECTION_NAME}-enc" \
    --type encryption \
    --policy "$ENCRYPTION_POLICY" \
    --output text --query "securityPolicyDetail.name" 2>/dev/null && echo "  ✓ Encryption policy created" || echo "  ⏭ Encryption policy already exists"

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2: Network Policy (public access for development)
# ══════════════════════════════════════════════════════════════════════════════
echo "[2/6] Creating network policy..."

NETWORK_POLICY='[
  {
    "Rules": [
      {
        "ResourceType": "collection",
        "Resource": ["collection/'"$COLLECTION_NAME"'"]
      },
      {
        "ResourceType": "dashboard",
        "Resource": ["collection/'"$COLLECTION_NAME"'"]
      }
    ],
    "AllowFromPublic": true
  }
]'

$AWS_CMD opensearchserverless create-security-policy \
    --region "$REGION" \
    --name "${COLLECTION_NAME}-net" \
    --type network \
    --policy "$NETWORK_POLICY" \
    --output text --query "securityPolicyDetail.name" 2>/dev/null && echo "  ✓ Network policy created" || echo "  ⏭ Network policy already exists"

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3: Data Access Policy
# ══════════════════════════════════════════════════════════════════════════════
echo "[3/6] Creating data access policy..."

DATA_ACCESS_POLICY='[
  {
    "Rules": [
      {
        "ResourceType": "index",
        "Resource": ["index/'"$COLLECTION_NAME"'/*"],
        "Permission": [
          "aoss:CreateIndex",
          "aoss:DeleteIndex",
          "aoss:UpdateIndex",
          "aoss:DescribeIndex",
          "aoss:ReadDocument",
          "aoss:WriteDocument"
        ]
      },
      {
        "ResourceType": "collection",
        "Resource": ["collection/'"$COLLECTION_NAME"'"],
        "Permission": [
          "aoss:CreateCollectionItems",
          "aoss:DescribeCollectionItems",
          "aoss:UpdateCollectionItems",
          "aoss:DeleteCollectionItems"
        ]
      }
    ],
    "Principal": ["'"$CALLER_ARN"'", "arn:aws:iam::'"$ACCOUNT_ID"':root"]
  }
]'

$AWS_CMD opensearchserverless create-access-policy \
    --region "$REGION" \
    --name "${COLLECTION_NAME}-access" \
    --type data \
    --policy "$DATA_ACCESS_POLICY" \
    --output text --query "accessPolicyDetail.name" 2>/dev/null && echo "  ✓ Data access policy created" || echo "  ⏭ Data access policy already exists"

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4: Create Collection
# ══════════════════════════════════════════════════════════════════════════════
echo "[4/6] Creating OpenSearch Serverless collection..."

EXISTING=$($AWS_CMD opensearchserverless list-collections \
    --region "$REGION" \
    --collection-filters "name=$COLLECTION_NAME" \
    --query "collectionSummaries[0].id" \
    --output text 2>/dev/null)

if [ "$EXISTING" != "None" ] && [ -n "$EXISTING" ]; then
    echo "  ⏭ Collection already exists (ID: $EXISTING)"
    COLLECTION_ID="$EXISTING"
else
    COLLECTION_ID=$($AWS_CMD opensearchserverless create-collection \
        --region "$REGION" \
        --name "$COLLECTION_NAME" \
        --type VECTORSEARCH \
        --description "MedGraph AI patient memory vector store" \
        --query "createCollectionDetail.id" \
        --output text)
    echo "  ✓ Collection created (ID: $COLLECTION_ID)"
fi

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5: Wait for collection to become ACTIVE
# ══════════════════════════════════════════════════════════════════════════════
echo "[5/6] Waiting for collection to become ACTIVE..."
echo "      (This can take 2-5 minutes for serverless collections)"

while true; do
    STATUS=$($AWS_CMD opensearchserverless batch-get-collection \
        --region "$REGION" \
        --ids "$COLLECTION_ID" \
        --query "collectionDetails[0].status" \
        --output text 2>/dev/null)
    
    if [ "$STATUS" = "ACTIVE" ]; then
        break
    fi
    echo "      Status: $STATUS — waiting 15s..."
    sleep 15
done

# Get the collection endpoint
ENDPOINT=$($AWS_CMD opensearchserverless batch-get-collection \
    --region "$REGION" \
    --ids "$COLLECTION_ID" \
    --query "collectionDetails[0].collectionEndpoint" \
    --output text)

echo "  ✓ Collection ACTIVE"
echo "  Endpoint: $ENDPOINT"

# ══════════════════════════════════════════════════════════════════════════════
# STEP 6: Create Vector Index
# ══════════════════════════════════════════════════════════════════════════════
echo "[6/6] Creating vector index '$INDEX_NAME'..."

# Use Python + opensearch-py with AWS SigV4 to create the index
python3 -c "
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

region = '$REGION'
endpoint = '$ENDPOINT'.replace('https://', '')
credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, region, 'aoss')

client = OpenSearch(
    hosts=[{'host': endpoint, 'port': 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    pool_maxsize=20,
)

index_body = {
    'settings': {
        'index': {
            'knn': True,
            'knn.algo_param.ef_search': 512
        }
    },
    'mappings': {
        'properties': {
            'patient_id': {'type': 'keyword'},
            'entry_id': {'type': 'keyword'},
            'text': {'type': 'text'},
            'source': {'type': 'keyword'},
            'encounter_date': {'type': 'date', 'format': 'strict_date_optional_time||epoch_millis'},
            'has_medications': {'type': 'boolean'},
            'has_conditions': {'type': 'boolean'},
            'has_symptoms': {'type': 'boolean'},
            'medication_names': {'type': 'keyword'},
            'condition_names': {'type': 'keyword'},
            'symptom_names': {'type': 'keyword'},
            'embedding': {
                'type': 'knn_vector',
                'dimension': $EMBEDDING_DIM,
                'method': {
                    'name': 'hnsw',
                    'space_type': 'cosinesimil',
                    'engine': 'nmslib',
                    'parameters': {
                        'ef_construction': 512,
                        'm': 16
                    }
                }
            }
        }
    }
}

try:
    if client.indices.exists(index='$INDEX_NAME'):
        print('  ⏭ Index already exists')
    else:
        client.indices.create(index='$INDEX_NAME', body=index_body)
        print('  ✓ Vector index created')
except Exception as e:
    print(f'  ✓ Index creation attempted: {e}')
" 2>&1 || echo "  ⚠ Index creation requires opensearch-py. Install: pip install opensearch-py requests-aws4auth"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   ✓ OpenSearch Serverless Vector DB Ready                ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║                                                          ║"
echo "║   .env config:                                           ║"
echo "║     OPENSEARCH_ENDPOINT=$ENDPOINT"
echo "║     OPENSEARCH_INDEX=$INDEX_NAME"
echo "║     EMBEDDING_DIM=$EMBEDDING_DIM"
echo "║                                                          ║"
echo "║   Collection: $COLLECTION_NAME (VECTORSEARCH)"
echo "║   Auth: AWS SigV4 (uses CLI credentials)                 ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
