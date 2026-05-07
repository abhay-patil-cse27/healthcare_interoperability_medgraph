#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# MedGraph AI — Step 5: Verify Full Stack Connectivity
# ═══════════════════════════════════════════════════════════════════════════════
# Validates all external services are reachable:
#   - AWS Bedrock (LLM + Embeddings)
#   - MongoDB Atlas
#   - Neo4j Aura
#
# Run: bash scripts/aws/05-verify-full-stack.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -e

echo "============================================"
echo "  MedGraph AI — Full Stack Verification"
echo "============================================"
echo ""

# Load .env if present
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✓ Loaded .env"
else
    echo "WARNING: No .env file found. Using environment variables."
fi

REGION="${AWS_REGION:-us-east-1}"
PASS=0
FAIL=0

# ── 1. AWS Bedrock ────────────────────────────────────────────────────────────
echo ""
echo "--- [1/3] AWS Bedrock ---"
if aws bedrock-runtime converse \
    --region "$REGION" \
    --model-id "${BEDROCK_MODEL_ID:-us.anthropic.claude-sonnet-4-6}" \
    --messages '[{"role":"user","content":[{"text":"Reply: OK"}]}]' \
    --inference-config '{"maxTokens":5,"temperature":0}' \
    --output text --query "output.message.content[0].text" 2>/dev/null; then
    echo "✓ Bedrock LLM: PASS"
    PASS=$((PASS+1))
else
    echo "✗ Bedrock LLM: FAIL"
    FAIL=$((FAIL+1))
fi

# ── 2. MongoDB Atlas ──────────────────────────────────────────────────────────
echo ""
echo "--- [2/3] MongoDB Atlas ---"
if python -c "
from pymongo import MongoClient
import os
url = os.environ.get('MONGODB_URL', '')
if not url:
    print('MONGODB_URL not set')
    exit(1)
client = MongoClient(url, serverSelectionTimeoutMS=5000)
client.admin.command('ping')
print('✓ MongoDB Atlas: PASS')
" 2>/dev/null; then
    PASS=$((PASS+1))
else
    echo "✗ MongoDB Atlas: FAIL — Check MONGODB_URL in .env"
    FAIL=$((FAIL+1))
fi

# ── 3. Neo4j Aura ────────────────────────────────────────────────────────────
echo ""
echo "--- [3/3] Neo4j Aura ---"
if python -c "
from neo4j import GraphDatabase
import os
uri = os.environ.get('NEO4J_URI', '')
user = os.environ.get('NEO4J_USER', 'neo4j')
password = os.environ.get('NEO4J_PASSWORD', '')
if not uri or not password:
    print('NEO4J_URI or NEO4J_PASSWORD not set')
    exit(1)
driver = GraphDatabase.driver(uri, auth=(user, password))
with driver.session() as session:
    session.run('RETURN 1')
driver.close()
print('✓ Neo4j Aura: PASS')
" 2>/dev/null; then
    PASS=$((PASS+1))
else
    echo "✗ Neo4j Aura: FAIL — Check NEO4J_URI and NEO4J_PASSWORD in .env"
    FAIL=$((FAIL+1))
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "============================================"
echo "  Results: $PASS passed, $FAIL failed"
echo "============================================"

if [ $FAIL -eq 0 ]; then
    echo ""
    echo "  ✓ All services healthy. Ready to start backend."
    echo ""
    echo "  Start command:"
    echo "    python -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0"
    echo "    (run from backend/ directory)"
    echo ""
    exit 0
else
    echo ""
    echo "  ✗ Some services are unreachable. Fix the issues above."
    exit 1
fi
