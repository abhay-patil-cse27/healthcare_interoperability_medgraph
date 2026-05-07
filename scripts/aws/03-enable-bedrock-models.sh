#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# MedGraph AI — Step 3: Enable Bedrock Model Access
# ═══════════════════════════════════════════════════════════════════════════════
# This script verifies that the required Bedrock models are accessible.
# NOTE: Model access must be enabled via the AWS Console (Bedrock > Model access).
#       This script validates access — it cannot grant it programmatically.
#
# Required models:
#   - anthropic.claude-3-sonnet-20240229-v1:0  (LLM)
#   - amazon.titan-embed-text-v2:0             (Embeddings)
#
# Run: bash scripts/aws/03-enable-bedrock-models.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -e

REGION="${AWS_REGION:-us-east-1}"
LLM_MODEL="us.anthropic.claude-sonnet-4-6"
EMBED_MODEL="amazon.titan-embed-text-v2:0"

echo "============================================"
echo "  MedGraph AI — Bedrock Model Access Check"
echo "============================================"
echo ""
echo "Region: $REGION"
echo "LLM Model: $LLM_MODEL"
echo "Embedding Model: $EMBED_MODEL"
echo ""

# Check if Bedrock is accessible
echo "--- Checking Bedrock service access ---"
aws bedrock list-foundation-models \
    --region "$REGION" \
    --query "modelSummaries[?modelId=='$LLM_MODEL'].{ModelId:modelId,Status:modelLifecycle.status}" \
    --output table 2>/dev/null || {
    echo "ERROR: Cannot access Bedrock. Check your IAM permissions."
    echo "Required IAM policy actions:"
    echo "  - bedrock:ListFoundationModels"
    echo "  - bedrock-runtime:InvokeModel"
    echo "  - bedrock-runtime:Converse"
    exit 1
}

echo ""
echo "--- Testing LLM invocation (Claude Sonnet) ---"
aws bedrock-runtime converse \
    --region "$REGION" \
    --model-id "$LLM_MODEL" \
    --messages '[{"role":"user","content":[{"text":"Reply with exactly: PONG"}]}]' \
    --inference-config '{"maxTokens":10,"temperature":0}' \
    --query "output.message.content[0].text" \
    --output text 2>/dev/null && echo "✓ Claude Sonnet accessible" || {
    echo ""
    echo "ERROR: Cannot invoke Claude Sonnet."
    echo ""
    echo "FIX: Go to AWS Console → Bedrock → Model access → Request access to:"
    echo "  - Anthropic Claude 3 Sonnet"
    echo "  - Amazon Titan Text Embeddings V2"
    echo ""
    echo "URL: https://console.aws.amazon.com/bedrock/home?region=$REGION#/modelaccess"
    exit 1
}

echo ""
echo "--- Testing Embedding model (Titan) ---"
aws bedrock-runtime invoke-model \
    --region "$REGION" \
    --model-id "$EMBED_MODEL" \
    --content-type "application/json" \
    --accept "application/json" \
    --body '{"inputText":"test","dimensions":1024,"normalize":true}' \
    --query "embedding[:3]" \
    /dev/stdout 2>/dev/null | head -c 100 && echo "" && echo "✓ Titan Embeddings accessible" || {
    echo ""
    echo "ERROR: Cannot invoke Titan Embeddings."
    echo "FIX: Enable Amazon Titan Text Embeddings V2 in Bedrock Model Access."
    exit 1
}

echo ""
echo "============================================"
echo "  ✓ All Bedrock models accessible!"
echo "============================================"
echo ""
echo "Models ready:"
echo "  LLM:        $LLM_MODEL"
echo "  Embeddings: $EMBED_MODEL"
echo ""
