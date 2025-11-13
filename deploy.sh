#!/bin/bash

# Quick Deploy Script for GitHub
# This script helps you push to GitHub in one command

echo "======================================"
echo "X Agent Team - GitHub Deployment"
echo "======================================"
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
    echo "✅ Git initialized"
else
    echo "✅ Git already initialized"
fi

# Check if .env is in gitignore
if ! grep -q ".env" .gitignore 2>/dev/null; then
    echo "⚠️  WARNING: .env might not be in .gitignore!"
    echo "Please ensure .env is listed in .gitignore before continuing."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Add all files
echo ""
echo "Adding files to git..."
git add .
echo "✅ Files added"

# Commit
echo ""
read -p "Enter commit message (or press Enter for default): " commit_msg
if [ -z "$commit_msg" ]; then
    commit_msg="Update X Agent Team orchestrator"
fi

git commit -m "$commit_msg"
echo "✅ Committed: $commit_msg"

# Check if remote exists
if ! git remote | grep -q origin; then
    echo ""
    echo "No remote repository configured."
    read -p "Enter your GitHub repository URL (https://github.com/username/repo.git): " repo_url

    if [ -z "$repo_url" ]; then
        echo "❌ No repository URL provided. Exiting."
        exit 1
    fi

    git remote add origin "$repo_url"
    echo "✅ Remote added: $repo_url"
fi

# Push to GitHub
echo ""
echo "Pushing to GitHub..."
git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✅ Successfully pushed to GitHub!"
    echo "======================================"
    echo ""
    echo "Next steps:"
    echo "1. Go to https://dashboard.render.com"
    echo "2. Click 'New +' → 'Blueprint'"
    echo "3. Select your repository"
    echo "4. Add environment variables (API keys)"
    echo "5. Deploy!"
    echo ""
    echo "📖 Full guide: RENDER_DEPLOYMENT.md"
else
    echo ""
    echo "❌ Push failed. Please check the error above."
    echo ""
    echo "Common fixes:"
    echo "- Ensure you have access to the repository"
    echo "- Check your GitHub credentials"
    echo "- Verify the repository URL is correct"
fi
