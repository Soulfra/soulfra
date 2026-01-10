#!/bin/bash
# Complete Voice System Proof-of-Concept Test
# Tests: Recording → Transcription → Live Show → Ollama → Voice Clone

set -e  # Exit on error

echo "🎤 =============================================="
echo "   COMPLETE VOICE SYSTEM TEST"
echo "   =============================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Database path
DB="soulfra.db"

# Test 1: Voice Recordings
echo -e "${BLUE}1️⃣  Testing Voice Recording System...${NC}"
recording_count=$(sqlite3 $DB "SELECT COUNT(*) FROM simple_voice_recordings;" 2>/dev/null || echo "0")
echo "   📊 Total recordings: $recording_count"

if [ "$recording_count" -gt 0 ]; then
    echo -e "   ${GREEN}✅ Voice recording system WORKING${NC}"

    # Show latest recording
    latest=$(sqlite3 $DB "SELECT id, filename, created_at FROM simple_voice_recordings ORDER BY id DESC LIMIT 1;" 2>/dev/null)
    echo "   📝 Latest: $latest"
else
    echo -e "   ${YELLOW}⚠️  No recordings yet. Record at: http://192.168.1.87:5001/voice${NC}"
fi

echo ""

# Test 2: Transcriptions
echo -e "${BLUE}2️⃣  Testing Whisper Transcription...${NC}"
transcription_count=$(sqlite3 $DB "SELECT COUNT(*) FROM simple_voice_recordings WHERE transcription IS NOT NULL;" 2>/dev/null || echo "0")
echo "   📊 Transcribed recordings: $transcription_count"

if [ "$transcription_count" -gt 0 ]; then
    echo -e "   ${GREEN}✅ Whisper transcription WORKING${NC}"

    # Show sample transcription
    sample=$(sqlite3 $DB "SELECT substr(transcription, 1, 80) FROM simple_voice_recordings WHERE transcription IS NOT NULL LIMIT 1;" 2>/dev/null)
    echo "   💬 Sample: $sample..."
else
    echo -e "   ${YELLOW}⚠️  No transcriptions yet. Whisper may need setup.${NC}"
fi

echo ""

# Test 3: Live Shows
echo -e "${BLUE}3️⃣  Testing Live Call-In Show System...${NC}"
show_count=$(sqlite3 $DB "SELECT COUNT(*) FROM live_shows;" 2>/dev/null || echo "0")
echo "   📊 Total shows: $show_count"

if [ "$show_count" -gt 0 ]; then
    echo -e "   ${GREEN}✅ Live show system WORKING${NC}"

    # Show latest show
    latest_show=$(sqlite3 $DB "SELECT id, title, status FROM live_shows ORDER BY id DESC LIMIT 1;" 2>/dev/null)
    echo "   📺 Latest show: $latest_show"

    # Check reactions
    reaction_count=$(sqlite3 $DB "SELECT COUNT(*) FROM show_reactions;" 2>/dev/null || echo "0")
    echo "   📞 Total reactions: $reaction_count"
else
    echo -e "   ${YELLOW}⚠️  No shows yet. Create one:${NC}"
    echo "      python3 live_call_in_show.py create \"Test Show\" --article-text \"Test\""
fi

echo ""

# Test 4: Ollama Connection
echo -e "${BLUE}4️⃣  Testing Ollama Service...${NC}"
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Ollama is running${NC}"

    # List models
    models=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; data = json.load(sys.stdin); print(', '.join([m['name'] for m in data.get('models', [])]))" 2>/dev/null || echo "unable to parse")
    echo "   🤖 Available models: $models"
else
    echo -e "   ${RED}❌ Ollama not running${NC}"
    echo "      Start it: ollama serve"
fi

echo ""

# Test 5: Flask Server
echo -e "${BLUE}5️⃣  Testing Flask Server...${NC}"
if curl -s http://localhost:5001/ >/dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Flask is running on port 5001${NC}"

    # Test Ollama connector endpoint
    if curl -s http://localhost:5001/api/ollama/stats >/dev/null 2>&1; then
        echo -e "   ${GREEN}✅ Ollama connector routes registered${NC}"
    fi

    # Test live show endpoint
    if curl -s http://localhost:5001/api/live-show/active >/dev/null 2>&1; then
        echo -e "   ${GREEN}✅ Live show routes registered${NC}"
    fi
else
    echo -e "   ${RED}❌ Flask not running${NC}"
    echo "      Start it: python3 app.py"
fi

echo ""

# Test 6: Voice Clone Setup (NEW)
echo -e "${BLUE}6️⃣  Testing Voice Clone System...${NC}"

# Check if Piper TTS is installed
if command -v piper &> /dev/null; then
    echo -e "   ${GREEN}✅ Piper TTS installed${NC}"
else
    echo -e "   ${YELLOW}⚠️  Piper TTS not installed${NC}"
    echo "      Install: pip install piper-tts"
fi

# Check for voice models
if [ -f "voice_models/matthew_voice.ckpt" ]; then
    echo -e "   ${GREEN}✅ Voice model trained${NC}"
else
    echo -e "   ${YELLOW}⚠️  Voice model not trained yet${NC}"
    echo "      Train: python3 voice_clone_trainer.py --train"
fi

# Check for training samples
sample_count=$(ls -1 voice_samples/*.wav 2>/dev/null | wc -l || echo "0")
echo "   📊 Voice samples: $sample_count"

if [ "$sample_count" -ge 10 ]; then
    echo -e "   ${GREEN}✅ Enough samples for training (need 10+)${NC}"
elif [ "$sample_count" -gt 0 ]; then
    echo -e "   ${YELLOW}⚠️  Need more samples (have $sample_count, need 10+)${NC}"
else
    echo -e "   ${YELLOW}⚠️  No voice samples yet${NC}"
    echo "      Record samples at: http://192.168.1.87:5001/voice"
fi

echo ""

# Summary
echo -e "${BLUE}📋 SUMMARY${NC}"
echo "   =================================="

total_tests=6
passing=0

[ "$recording_count" -gt 0 ] && ((passing++))
[ "$transcription_count" -gt 0 ] && ((passing++))
[ "$show_count" -gt 0 ] && ((passing++))
curl -s http://localhost:11434/api/tags >/dev/null 2>&1 && ((passing++))
curl -s http://localhost:5001/ >/dev/null 2>&1 && ((passing++))
[ "$sample_count" -ge 10 ] && ((passing++))

echo "   Tests passing: $passing / $total_tests"

if [ $passing -eq $total_tests ]; then
    echo -e "   ${GREEN}✅ ALL SYSTEMS OPERATIONAL!${NC}"
elif [ $passing -ge 4 ]; then
    echo -e "   ${YELLOW}⚠️  MOST SYSTEMS WORKING${NC}"
else
    echo -e "   ${RED}❌ MULTIPLE SYSTEMS NEED ATTENTION${NC}"
fi

echo ""
echo "   Next steps:"
if [ "$recording_count" -eq 0 ]; then
    echo "   1. Record voice: http://192.168.1.87:5001/voice"
fi
if [ "$show_count" -eq 0 ]; then
    echo "   2. Create show: python3 live_call_in_show.py create \"Test\" --article-text \"Test\""
fi
if [ "$sample_count" -lt 10 ]; then
    echo "   3. Record 10+ voice samples for cloning"
fi
if ! command -v piper &> /dev/null; then
    echo "   4. Install Piper TTS: pip install piper-tts"
fi
if [ ! -f "voice_models/matthew_voice.ckpt" ]; then
    echo "   5. Train voice model: python3 voice_clone_trainer.py --train"
fi

echo ""
echo "🎤 =============================================="
