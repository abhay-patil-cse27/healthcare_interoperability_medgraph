#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# MedGraph AI — Bedrock LLM Setup & Validation
# ═══════════════════════════════════════════════════════════════════════════════
# This script validates your AWS CLI credentials and Bedrock model access.
# Bedrock is a fully managed API — no infrastructure to create.
# Your AWS CLI credentials are used directly by boto3 in the backend.
#
# Prerequisites:
#   - AWS CLI v2 installed and configured (aws configure)
#   - Bedrock model access enabled in AWS Console
#
# Run (from project root):
#   bash scripts/aws/setup-bedrock.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -e

AWS_CMD="aws"
REGION="us-east-1"
LLM_MODEL="us.anthropic.claude-sonnet-4-6"
EMBED_MODEL="amazon.titan-embed-text-v2:0"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   MedGraph AI — AWS Bedrock LLM Setup                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── Step 1: Verify AWS CLI ────────────────────────────────────────────────────
echo "[1/5] Checking AWS CLI..."
$AWS_CMD --version || { echo "ERROR: AWS CLI not found."; exit 1; }
echo ""

# ── Step 2: Verify credentials ───────────────────────────────────────────────
echo "[2/5] Verifying AWS credentials..."
IDENTITY=$($AWS_CMD sts get-caller-identity --output json)
echo "  Account: $(echo $IDENTITY | python -c "import sys,json; print(json.load(sys.stdin)['Account'])")"
echo "  ARN:     $(echo $IDENTITY | python -c "import sys,json; print(json.load(sys.stdin)['Arn'])")"
echo "  Region:  $REGION"
echo ""

# ── Step 3: Verify LLM model access ──────────────────────────────────────────
echo "[3/5] Testing LLM: $LLM_MODEL"
LLM_RESPONSE=$($AWS_CMD bedrock-runtime converse \
    --region "$REGION" \
    --model-id "$LLM_MODEL" \
    --messages "[{\"role\":\"user\",\"content\":[{\"text\":\"Reply with exactly one word: HEALTHY\"}]}]" \
    --inference-config "{\"maxTokens\":10,\"temperature\":0}" \
    --query "output.message.content[0].text" \
    --output text 2>&1) || {
    echo "  ✗ FAILED: $LLM_RESPONSE"
    echo ""
    echo "  FIX: Enable model access at:"
    echo "  https://console.aws.amazon.com/bedrock/home?region=$REGION#/modelaccess"
    exit 1
}
echo "  ✓ Response: $LLM_RESPONSE"
echo ""

# ── Step 4: Verify Embedding model access ────────────────────────────────────
echo "[4/5] Testing Embeddings: $EMBED_MODEL"
EMBED_BODY=$(echo -n '{"inputText":"health check","dimensions":1024,"normalize":true}' | base64)
EMBED_RESPONSE=$($AWS_CMD bedrock-runtime invoke-model \
    --region "$REGION" \
    --model-id "$EMBED_MODEL" \
    --content-type "application/json" \
    --accept "application/json" \
    --body "$EMBED_BODY" \
    /dev/stdout 2>/dev/null | python -c "import sys,json; d=json.load(sys.stdin); print(f'dim={len(d[\"embedding\"])}')" 2>&1) || {
    echo "  ✗ FAILED"
    exit 1
}
echo "  ✓ $EMBED_RESPONSE"
echo ""

# ── Step 5: Write .env values ─────────────────────────────────────────────────
echo "[5/5] Bedrock config for .env:"
echo ""
echo "  AWS_REGION=$REGION"
echo "  BEDROCK_MODEL_ID=$LLM_MODEL"
echo "  BEDROCK_EMBEDDING_MODEL_ID=$EMBED_MODEL"
echo "  EMBEDDING_DIM=1024"
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   ✓ Bedrock LLM fully operational                       ║"
echo "║                                                          ║"
echo "║   LLM:        Claude Sonnet 4.6 (us inference profile)   ║"
echo "║   Embeddings: Titan Text v2 (1024-dim)                   ║"
echo "║   Auth:       AWS CLI credentials (boto3 auto-detects)   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
