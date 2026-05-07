#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# MedGraph AI — Step 1: Install AWS CLI v2 (Windows)
# ═══════════════════════════════════════════════════════════════════════════════
# Run this in PowerShell as Administrator if AWS CLI is not installed.
# After installation, restart your terminal and run: aws --version
# ═══════════════════════════════════════════════════════════════════════════════

echo "============================================"
echo "  MedGraph AI — AWS CLI Installation"
echo "============================================"
echo ""
echo "For Windows, download and run the MSI installer:"
echo "  https://awscli.amazonaws.com/AWSCLIV2.msi"
echo ""
echo "Or via winget (Windows Package Manager):"
echo "  winget install Amazon.AWSCLI"
echo ""
echo "After installation, restart your terminal and verify:"
echo "  aws --version"
echo ""
echo "Then configure your credentials:"
echo "  aws configure"
echo ""
echo "You will need:"
echo "  - AWS Access Key ID"
echo "  - AWS Secret Access Key"
echo "  - Default region (us-east-1 recommended for Bedrock)"
echo "  - Default output format (json)"
echo ""
echo "============================================"
