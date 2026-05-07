#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# MedGraph AI — Step 4: Create IAM Policy for Bedrock Access
# ═══════════════════════════════════════════════════════════════════════════════
# Creates a minimal IAM policy granting Bedrock invoke permissions.
# Attach this to your IAM user/role if not already permitted.
#
# Run: bash scripts/aws/04-setup-iam-policy.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -e

REGION="${AWS_REGION:-us-east-1}"
POLICY_NAME="MedGraphAI-BedrockAccess"
ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)

echo "============================================"
echo "  MedGraph AI — IAM Policy Setup"
echo "============================================"
echo ""
echo "Account: $ACCOUNT_ID"
echo "Region:  $REGION"
echo "Policy:  $POLICY_NAME"
echo ""

# Check if policy already exists
EXISTING=$(aws iam list-policies --scope Local --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text 2>/dev/null)

if [ -n "$EXISTING" ]; then
    echo "Policy already exists: $EXISTING"
    echo "Skipping creation."
    exit 0
fi

# Create the policy document
POLICY_DOC='{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "BedrockInvoke",
            "Effect": "Allow",
            "Action": [
                "bedrock:ListFoundationModels",
                "bedrock:GetFoundationModel",
                "bedrock-runtime:InvokeModel",
                "bedrock-runtime:InvokeModelWithResponseStream",
                "bedrock-runtime:Converse",
                "bedrock-runtime:ConverseStream"
            ],
            "Resource": "*"
        }
    ]
}'

echo "Creating IAM policy..."
POLICY_ARN=$(aws iam create-policy \
    --policy-name "$POLICY_NAME" \
    --policy-document "$POLICY_DOC" \
    --description "MedGraph AI - Bedrock model invocation permissions" \
    --query "Policy.Arn" \
    --output text)

echo ""
echo "✓ Policy created: $POLICY_ARN"
echo ""
echo "To attach to your current user:"
echo "  aws iam attach-user-policy --user-name <YOUR_USERNAME> --policy-arn $POLICY_ARN"
echo ""
echo "To attach to a role:"
echo "  aws iam attach-role-policy --role-name <YOUR_ROLE> --policy-arn $POLICY_ARN"
echo ""
