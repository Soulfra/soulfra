#!/bin/bash
#
# Start Multi-Port Ollama for Content Tumbler
#
# This script starts 4 Ollama instances on different ports for the tumbler system.
# Each port runs with different temperature settings for varied content generation.
#
# Usage:
#   ./start_tumbler_ollama.sh           # Start all 4 ports
#   ./start_tumbler_ollama.sh stop      # Stop all Ollama instances
#   ./start_tumbler_ollama.sh status    # Check status of all ports
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Port configuration
PORTS=(11434 11435 11436 11437)
NAMES=("Technical" "Creative" "Precise" "Experimental")
MODELS=("llama3" "mistral" "codellama" "llama3")

# =============================================================================
# FUNCTIONS
# =============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_port() {
    local port=$1
    if curl -s "http://localhost:$port/api/tags" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# =============================================================================
# START OLLAMA INSTANCES
# =============================================================================

start_ollama() {
    print_header "Starting Multi-Port Ollama for Tumbler System"

    for i in "${!PORTS[@]}"; do
        port=${PORTS[$i]}
        name=${NAMES[$i]}
        model=${MODELS[$i]}

        echo -e "${BLUE}Port $port${NC} - ${name} (${model})"

        # Check if already running
        if check_port "$port"; then
            print_warning "Already running on port $port"
            continue
        fi

        # Start Ollama on this port
        print_info "Starting Ollama on port $port..."

        if [ "$port" == "11434" ]; then
            # Default port - start normally
            ollama serve > "/tmp/ollama-$port.log" 2>&1 &
        else
            # Other ports - specify host
            OLLAMA_HOST="0.0.0.0:$port" ollama serve > "/tmp/ollama-$port.log" 2>&1 &
        fi

        # Wait a moment for it to start
        sleep 2

        # Verify it started
        if check_port "$port"; then
            print_success "Started on port $port"
        else
            print_error "Failed to start on port $port"
            print_info "Check logs: tail -f /tmp/ollama-$port.log"
        fi
    done

    echo ""
    print_header "Loading Models"

    for i in "${!PORTS[@]}"; do
        port=${PORTS[$i]}
        name=${NAMES[$i]}
        model=${MODELS[$i]}

        echo -e "${BLUE}Port $port${NC} - Loading ${model}..."

        # Check if model already loaded
        if OLLAMA_HOST="http://localhost:$port" ollama list | grep -q "$model"; then
            print_success "Model $model already loaded on port $port"
        else
            print_info "Pulling $model on port $port..."
            OLLAMA_HOST="http://localhost:$port" ollama pull "$model"
            print_success "Loaded $model on port $port"
        fi
    done

    echo ""
    print_success "Multi-port Ollama tumbler is ready!"
    print_info "Test it: python3 multi_port_ollama.py"
}

# =============================================================================
# STOP OLLAMA INSTANCES
# =============================================================================

stop_ollama() {
    print_header "Stopping All Ollama Instances"

    # Kill all Ollama processes
    pkill -9 ollama 2>/dev/null || true

    sleep 2

    # Verify they're stopped
    if pgrep ollama > /dev/null; then
        print_warning "Some Ollama processes still running"
        print_info "Force kill with: pkill -9 ollama"
    else
        print_success "All Ollama instances stopped"
    fi

    # Clean up log files
    rm -f /tmp/ollama-*.log
    print_info "Cleaned up log files"
}

# =============================================================================
# CHECK STATUS
# =============================================================================

check_status() {
    print_header "Ollama Multi-Port Status"

    for i in "${!PORTS[@]}"; do
        port=${PORTS[$i]}
        name=${NAMES[$i]}
        model=${MODELS[$i]}

        echo -e "${BLUE}Port $port${NC} - ${name} (${model})"

        if check_port "$port"; then
            # Get loaded models
            models=$(curl -s "http://localhost:$port/api/tags" | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
            print_success "Running - Models: $models"
        else
            print_error "Not running"
            print_info "Start with: ./start_tumbler_ollama.sh"
        fi

        echo ""
    done

    # Count running instances
    running_count=0
    for port in "${PORTS[@]}"; do
        if check_port "$port"; then
            ((running_count++))
        fi
    done

    echo ""
    if [ "$running_count" -eq 4 ]; then
        print_success "All 4 Ollama ports running - Full tumbler ready! 🎰"
    elif [ "$running_count" -eq 0 ]; then
        print_warning "No Ollama instances running"
        print_info "Start with: ./start_tumbler_ollama.sh"
    else
        print_warning "Only $running_count/4 ports running"
        print_info "Restart all: ./start_tumbler_ollama.sh stop && ./start_tumbler_ollama.sh"
    fi
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    case "${1:-start}" in
        start)
            start_ollama
            check_status
            ;;
        stop)
            stop_ollama
            ;;
        status)
            check_status
            ;;
        restart)
            stop_ollama
            sleep 2
            start_ollama
            check_status
            ;;
        *)
            echo "Usage: $0 {start|stop|status|restart}"
            echo ""
            echo "Commands:"
            echo "  start   - Start all 4 Ollama ports for tumbler"
            echo "  stop    - Stop all Ollama instances"
            echo "  status  - Check status of all ports"
            echo "  restart - Stop and restart all ports"
            exit 1
            ;;
    esac
}

main "$@"
