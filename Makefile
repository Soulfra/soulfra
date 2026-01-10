# Soulfra Build System - Battlenet-style compilation
# Compile SQLite → JSON exports → Static assets

.PHONY: all build compile serve stats replays clean init

# Default target
all: build

# Initialize database and create tables
init:
	@echo "🔧 Initializing database tables..."
	@python3 -c "from database import init_db; init_db(); print('✅ Database initialized')"

# Build - Export all data to JSON
build: init
	@echo "🏗️  Building static exports from SQLite..."
	@mkdir -p build/exports
	@python3 scripts/export_data.py
	@echo "✅ Build complete: build/exports/"

# Compile - Bundle all assets (QR codes, avatars, metrics)
compile: build
	@echo "📦 Compiling assets..."
	@mkdir -p build/assets
	@python3 scripts/compile_assets.py
	@echo "✅ Compile complete: build/assets/"

# Replays - Generate .replay files from scan sessions
replays:
	@echo "🎮 Generating replay files..."
	@mkdir -p build/replays
	@python3 scripts/export_replays.py
	@echo "✅ Replays generated: build/replays/"

# Serve - Start Flask server with fresh build
serve: build
	@echo "🚀 Starting Flask server on https://192.168.1.87:5002..."
	@python3 cringeproof_api.py

# Stats - Show leaderboard and achievements
stats:
	@echo "📊 Current Stats:"
	@python3 scripts/show_stats.py

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf build/
	@echo "✅ Clean complete"

# Show help
help:
	@echo "Soulfra Makefile - Available targets:"
	@echo "  make init     - Initialize database tables"
	@echo "  make build    - Export SQLite → JSON"
	@echo "  make compile  - Bundle all assets"
	@echo "  make replays  - Generate .replay files"
	@echo "  make serve    - Start Flask server"
	@echo "  make stats    - Show leaderboard"
	@echo "  make clean    - Remove build artifacts"
