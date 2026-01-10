-- Migration 009: Add ML Tables
-- From simple_ml.py
--
-- Machine learning with Python stdlib only - no dependencies

-- ML models table
CREATE TABLE IF NOT EXISTS ml_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_type TEXT NOT NULL,
    model_data TEXT NOT NULL,
    trained_on INTEGER,
    accuracy REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,
    input_data TEXT NOT NULL,
    prediction TEXT NOT NULL,
    confidence REAL,
    actual_result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES ml_models(id)
);
