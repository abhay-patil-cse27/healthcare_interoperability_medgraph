#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# MedGraph AI — Step 2: Configure AWS Credentials
# ═══════════════════════════════════════════════════════════════════════════════
# Run: bash scripts/aws/02-configure-aws-credentials.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -e

echo "============================================"
echo "  MedGraph AI — AWS Credentials Setup"
echo "============================================"

# Verify AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI is not installed. Run 01-install-aws-cli.sh first."
    exit 1
fi

echo ""
echo "Current AWS identity:"
aws sts get-caller-identity 2>/dev/null || {
    echo ""
    echo "No credentials configured. Running 'aws configure'..."
    echo "Use region: us-east-1 (required for Bedrock Claude Sonnet)"
    echo ""
    aws configure
}

echo ""
echo "Verifying credentials..."
aws sts get-caller-identity
echo ""
echo "✓ AWS credentials configured successfully."
echo ""
echo "Current region:"
aws configure get region
echo ""
