#!/bin/bash

# Cloud FinOps Intelligence - Automated GitHub Deployment Script
# This strictly downloads the GitHub CLI natively (without Brew) and builds your repo!

echo "=========================================================="
echo "🚀 Cloud FinOps Intelligence - Automated GitHub Push"
echo "=========================================================="

echo "[1/3] Downloading official GitHub CLI for Apple Silicon..."
curl -sL \
  https://github.com/cli/cli/releases/download/v2.54.0/gh_2.54.0_macOS_arm64.zip \
  -o gh_cli.zip
unzip -q gh_cli.zip
export PATH="$PWD/gh_2.54.0_macOS_arm64/bin:$PATH"

echo "✅ GitHub CLI Engine Downloaded."
echo ""
echo "[2/3] Authenticating your GitHub Account..."
echo "----------------------------------------------------------"
echo "A device code will appear. Please hit ENTER, log into GitHub in the browser, and type the code."
./gh_2.54.0_macOS_arm64/bin/gh auth login -h github.com -p https -w

echo ""
echo "[3/3] Minting the new 'cloud-finops-intel' public repository..."
./gh_2.54.0_macOS_arm64/bin/gh repo create cloud-finops-intel --public --source=. --remote=origin --push

echo "=========================================================="
echo "🎉 SUCCESS! Your application is now securely on GitHub!"
echo "Next: Visit Vercel.com and Render.com to import your new repository."
echo "=========================================================="
