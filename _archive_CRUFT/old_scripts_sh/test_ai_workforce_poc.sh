#!/bin/bash
# AI Workforce POC - End-to-End Test
# Tests the full loop: Scrape → Generate → Approve → Publish

set -e  # Exit on error

echo "=============================================================================="
echo "🚀 AI WORKFORCE POC - END-TO-END TEST"
echo "=============================================================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Ollama is running
echo -e "${BLUE}Step 1: Checking Ollama...${NC}"
if curl -s http://192.168.1.87:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama is running${NC}"
else
    echo "❌ Ollama is not running at http://192.168.1.87:11434"
    echo "   Start it with: ollama serve"
    exit 1
fi
echo ""

# Step 2: Verify task exists
echo -e "${BLUE}Step 2: Checking pending task...${NC}"
TASK_COUNT=$(sqlite3 soulfra.db "SELECT COUNT(*) FROM ai_workforce_tasks WHERE status = 'pending';")
if [ "$TASK_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Found $TASK_COUNT pending task(s)${NC}"
    sqlite3 soulfra.db "SELECT id, assigned_to_persona, prompt FROM ai_workforce_tasks WHERE status = 'pending' LIMIT 1;"
else
    echo "❌ No pending tasks found"
    echo "   Create one with: sqlite3 soulfra.db \"INSERT INTO ai_workforce_tasks ...\""
    exit 1
fi
echo ""

# Step 3: Generate content with Ollama
echo -e "${BLUE}Step 3: Generating content with AI...${NC}"
echo "   (This may take 30-60 seconds)"
python3 auto_content_generator.py --execute
echo ""

# Step 4: Verify content was generated
echo -e "${BLUE}Step 4: Verifying content generation...${NC}"
COMPLETED_COUNT=$(sqlite3 soulfra.db "SELECT COUNT(*) FROM ai_workforce_tasks WHERE status = 'completed';")
if [ "$COMPLETED_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Content generated successfully${NC}"
    sqlite3 soulfra.db "SELECT output_title, LENGTH(output_content) as length FROM ai_workforce_tasks WHERE status = 'completed' ORDER BY completed_at DESC LIMIT 1;"
else
    echo "❌ Content generation failed"
    exit 1
fi
echo ""

# Step 5: Run CringeProof approval
echo -e "${BLUE}Step 5: Running CringeProof tribunal...${NC}"
python3 cringeproof_content_judge.py --approve
echo ""

# Step 6: Verify approval
echo -e "${BLUE}Step 6: Checking approval status...${NC}"
APPROVED_COUNT=$(sqlite3 soulfra.db "SELECT COUNT(*) FROM ai_workforce_tasks WHERE status = 'approved';")
if [ "$APPROVED_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Content approved by tribunal${NC}"
else
    echo "❌ Content was not approved"
    exit 1
fi
echo ""

# Step 7: Check if publish script exists
echo -e "${BLUE}Step 7: Looking for publish script...${NC}"
if [ -f "publish_to_github.py" ]; then
    echo -e "${GREEN}✅ publish_to_github.py found${NC}"

    # Ask if we should publish
    echo ""
    echo -e "${YELLOW}⚠️  Ready to publish to GitHub Pages${NC}"
    echo "   This will:"
    echo "   1. Insert approved content into posts table"
    echo "   2. Generate static HTML"
    echo "   3. Git commit and push to github-repos/soulfra/"
    echo ""
    read -p "Publish now? (y/n): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Insert into posts table
        echo -e "${BLUE}Inserting into posts table...${NC}"
        TASK_ID=1
        sqlite3 soulfra.db <<EOF
INSERT INTO posts (brand, title, content, status, published_at)
SELECT
    'soulfra',
    output_title,
    output_content,
    'published',
    CURRENT_TIMESTAMP
FROM ai_workforce_tasks
WHERE id = $TASK_ID AND status = 'approved';
EOF

        echo -e "${BLUE}Publishing to GitHub...${NC}"
        python3 publish_to_github.py --brand soulfra

        echo ""
        echo -e "${GREEN}✅ Published!${NC}"
        echo "   Visit: https://soulfra.github.io/blog/"
    else
        echo "Skipping publish"
    fi
else
    echo -e "${YELLOW}⚠️  publish_to_github.py not found - skipping publish step${NC}"
    echo "   Approved content is ready in ai_workforce_tasks table"
fi
echo ""

# Step 8: Show final status
echo "=============================================================================="
echo "📊 FINAL STATUS"
echo "=============================================================================="

echo ""
echo "Database Stats:"
sqlite3 soulfra.db <<EOF
SELECT
    '  Tasks Pending: ' || COUNT(*)
FROM ai_workforce_tasks WHERE status = 'pending'
UNION ALL
SELECT
    '  Tasks Completed: ' || COUNT(*)
FROM ai_workforce_tasks WHERE status = 'completed'
UNION ALL
SELECT
    '  Tasks Approved: ' || COUNT(*)
FROM ai_workforce_tasks WHERE status = 'approved';
EOF

echo ""
echo "Approval Votes:"
sqlite3 soulfra.db "SELECT '  ' || persona || ': ' || vote FROM content_approval_votes ORDER BY voted_at;"

echo ""
echo "Persona Credits:"
sqlite3 soulfra.db "SELECT '  ' || persona || ': ' || total_credits || ' credits' FROM ai_persona_stats ORDER BY total_credits DESC;"

echo ""
echo -e "${GREEN}✅ POC TEST COMPLETE${NC}"
echo ""
