#!/bin/bash
# Create GitHub issues for code review refactoring initiative
# Usage: ./scripts/create_refactoring_issues.sh

set -e

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) not found"
    echo "Install: https://cli.github.com/"
    echo ""
    echo "Alternative: Copy issue templates from .github/ISSUE_TEMPLATE/ manually"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub"
    echo "Run: gh auth login"
    exit 1
fi

echo "🚀 Creating Code Review Refactoring Issues"
echo "==========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track created issue numbers
declare -A ISSUES

# Function to create issue from template
create_issue() {
    local template=$1
    local title=$2
    local labels=$3
    local body_file=$4

    echo -n "Creating: $title ... "

    # Extract body from template (skip YAML frontmatter)
    body=$(sed '1,/^---$/d' "$body_file" | sed '1,/^---$/d')

    # Create issue and capture number
    issue_url=$(gh issue create \
        --title "$title" \
        --label "$labels" \
        --body "$body" 2>&1)

    if [ $? -eq 0 ]; then
        # Extract issue number from URL
        issue_num=$(echo "$issue_url" | grep -oE '[0-9]+$')
        ISSUES["$template"]=$issue_num
        echo -e "${GREEN}✓ #$issue_num${NC}"
    else
        echo -e "${YELLOW}⚠ Failed${NC}"
        echo "  Error: $issue_url"
    fi
}

# Create master tracking issue first
echo "📋 Phase 0: Master Tracking Issue"
echo "-----------------------------------"
create_issue "master" \
    "[REFACTOR] Code Review Refactoring - Master Tracking Issue" \
    "epic,refactoring,documentation" \
    ".github/ISSUE_TEMPLATE/00-refactoring-overview.md"
echo ""

# Store master issue for reference
MASTER_ISSUE=${ISSUES["master"]}

# Phase 1: Critical Fixes
echo "🔴 Phase 1: Critical Fixes (HIGH Priority)"
echo "-------------------------------------------"

create_issue "pytest-config" \
    "[BUG] Fix pytest configuration contradiction in pyproject.toml" \
    "bug,priority: high,testing,phase-1" \
    ".github/ISSUE_TEMPLATE/01-fix-pytest-config.md"

create_issue "requirements" \
    "[REFACTOR] Consolidate 20+ requirements.txt files into pyproject.toml" \
    "refactoring,priority: high,dependencies,phase-1" \
    ".github/ISSUE_TEMPLATE/02-consolidate-requirements.md"

create_issue "todo-fixme" \
    "[TECH-DEBT] Remove or convert TODO/FIXME comments to GitHub issues" \
    "tech-debt,priority: high,ci-cd,phase-1" \
    ".github/ISSUE_TEMPLATE/03-todo-fixme-tracking.md"

create_issue "duplicate-detection" \
    "[CI] Add automated duplicate file detection to CI pipeline" \
    "ci-cd,priority: high,tooling,phase-1" \
    ".github/ISSUE_TEMPLATE/04-duplicate-file-detection.md"

echo ""

# Phase 2: Technical Debt
echo "🟡 Phase 2: Technical Debt Reduction (MEDIUM Priority)"
echo "-------------------------------------------------------"

create_issue "large-files" \
    "[REFACTOR] Break down large GUI files (3,933+ lines) into smaller modules" \
    "refactoring,priority: medium,code-quality,phase-2" \
    ".github/ISSUE_TEMPLATE/05-refactor-large-gui-files.md"

create_issue "constants" \
    "[REFACTOR] Consolidate 10 constants.py files into shared module" \
    "refactoring,priority: medium,code-quality,phase-2" \
    ".github/ISSUE_TEMPLATE/06-consolidate-constants.md"

echo ""

# Summary
echo "=========================================="
echo "✅ Issue Creation Complete!"
echo "=========================================="
echo ""
echo "Created Issues:"
for key in "${!ISSUES[@]}"; do
    echo "  #${ISSUES[$key]} - $key"
done
echo ""
echo "📋 Master Tracking Issue: #$MASTER_ISSUE"
echo ""
echo "Next steps:"
echo "1. Review created issues at: https://github.com/D-sorganization/Golf_Modeling_Suite/issues"
echo "2. Update master tracking issue #$MASTER_ISSUE with issue numbers"
echo "3. Assign issues to team members"
echo "4. Create project board for tracking progress"
echo ""
echo "To create project board:"
echo "  gh project create --title 'Code Review Refactoring' --body 'Systematic code quality improvements'"
echo ""
