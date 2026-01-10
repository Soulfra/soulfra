#!/usr/bin/env python3
"""
Prediction Tracker - Learning System for Voice Predictions

Tracks every prediction made, logs outcomes, calculates accuracy.
Turns the voice prediction system from "data fetcher" into "learning assistant".

Database Schema:
- predictions: Log every prediction made
- prediction_outcomes: Track actual results when they happen
- prediction_sources: Which APIs/sources were used
- model_performance: Aggregate accuracy stats per model

Usage:
    from prediction_tracker import log_prediction, log_outcome, get_accuracy

    # When making prediction:
    pred_id = log_prediction(
        text="Bitcoin will hit 100k by March",
        brand="deathtodata",
        models=["deathtodata-model", "mistral"],
        data_sources={"coinbase": 90052.96, "blockchair": 90098.00}
    )

    # When outcome is known:
    log_outcome(
        prediction_id=pred_id,
        actual_value=95000,
        notes="BTC peaked at 95k, missed by 5k"
    )

    # Check historical accuracy:
    accuracy = get_accuracy(model="deathtodata-model", topic="bitcoin")
    # Returns: 72%
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


DATABASE_PATH = Path(__file__).parent / 'soulfra.db'


# ==============================================================================
# DATABASE SCHEMA
# ==============================================================================

def init_prediction_tables():
    """
    Create prediction tracking tables if they don't exist
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Main voice predictions table (renamed to avoid conflict)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voice_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            brand TEXT,
            target_date TEXT,
            confidence INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            debate_file TEXT,
            device_id INTEGER,

            -- Timelock / Game mechanics
            unlock_date DATETIME,
            status TEXT DEFAULT 'locked',  -- locked, unlocked, verified, failed
            verification_block INTEGER,
            spot_check BOOLEAN DEFAULT 0,  -- Is this in the random sample?
            verified_at DATETIME,

            -- Metadata
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    ''')

    # Models used for this prediction
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prediction_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id INTEGER NOT NULL,
            model_name TEXT NOT NULL,
            response_text TEXT,
            response_confidence INTEGER,
            response_likelihood INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (prediction_id) REFERENCES voice_predictions(id)
        )
    ''')

    # Data sources used (which APIs, what values)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prediction_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id INTEGER NOT NULL,
            source_name TEXT NOT NULL,
            source_type TEXT,  -- 'api', 'blockchain', 'manual'
            data_value TEXT,   -- JSON blob of data
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (prediction_id) REFERENCES voice_predictions(id)
        )
    ''')

    # Actual outcomes when they happen
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prediction_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id INTEGER NOT NULL,
            actual_value REAL,
            actual_date DATETIME,
            variance REAL,  -- How far off was the prediction
            accuracy_score INTEGER,  -- 0-100 score
            notes TEXT,
            verified_by TEXT,  -- Which source verified this
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (prediction_id) REFERENCES voice_predictions(id)
        )
    ''')

    # Aggregate model performance stats
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            topic TEXT,
            brand TEXT,
            total_predictions INTEGER DEFAULT 0,
            correct_predictions INTEGER DEFAULT 0,
            accuracy_pct REAL DEFAULT 0.0,
            avg_variance REAL DEFAULT 0.0,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(model_name, topic, brand)
        )
    ''')

    # Verification blocks (game mechanic - group predictions)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verification_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_number INTEGER UNIQUE NOT NULL,
            unlock_date DATETIME NOT NULL,
            predictions_count INTEGER DEFAULT 0,
            spot_check_count INTEGER DEFAULT 0,
            verified_count INTEGER DEFAULT 0,
            accuracy_avg REAL DEFAULT 0.0,
            status TEXT DEFAULT 'pending',  -- pending, unlocked, completed
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            unlocked_at DATETIME,
            completed_at DATETIME
        )
    ''')

    # Player stats / achievements
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER UNIQUE,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            predictions_made INTEGER DEFAULT 0,
            predictions_verified INTEGER DEFAULT 0,
            accuracy_avg REAL DEFAULT 0.0,
            streak_days INTEGER DEFAULT 0,
            last_activity DATETIME,
            achievements TEXT,  -- JSON array of achievement IDs

            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    ''')

    # Create indexes for faster queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_voice_predictions_brand ON voice_predictions(brand)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_voice_predictions_timestamp ON voice_predictions(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_voice_predictions_status ON voice_predictions(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_voice_predictions_unlock_date ON voice_predictions(unlock_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_prediction_models_name ON prediction_models(model_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_performance_lookup ON model_performance(model_name, topic)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_verification_blocks_status ON verification_blocks(status)')

    conn.commit()
    conn.close()

    print("✅ Prediction tracking tables initialized")


# ==============================================================================
# LOGGING FUNCTIONS
# ==============================================================================

def log_prediction(
    text: str,
    brand: str = None,
    target_date: str = None,
    confidence: int = None,
    debate_file: str = None,
    device_id: int = None,
    models: List[str] = None,
    model_responses: List[Dict] = None,
    data_sources: Dict[str, Any] = None
) -> int:
    """
    Log a new prediction to the database

    Args:
        text: Prediction text
        brand: Brand slug (calriven, deathtodata, soulfra)
        target_date: When prediction should come true
        confidence: User's confidence 0-100
        debate_file: Path to generated debate markdown
        device_id: Device that made prediction
        models: List of model names used
        model_responses: Full model response dicts
        data_sources: Dict of {source_name: data_value}

    Returns:
        prediction_id
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Insert main prediction
    cursor.execute('''
        INSERT INTO voice_predictions (text, brand, target_date, confidence, debate_file, device_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (text, brand, target_date, confidence, debate_file, device_id))

    prediction_id = cursor.lastrowid

    # Log models used
    if models:
        for model in models:
            # Find corresponding response
            response_text = None
            response_conf = None
            response_like = None

            if model_responses:
                for resp in model_responses:
                    if resp.get('model') == model:
                        response_text = resp.get('response', '')[:1000]  # Limit size
                        # Try to extract confidence/likelihood from response
                        # (would need parsing logic here)
                        break

            cursor.execute('''
                INSERT INTO prediction_models (prediction_id, model_name, response_text, response_confidence, response_likelihood)
                VALUES (?, ?, ?, ?, ?)
            ''', (prediction_id, model, response_text, response_conf, response_like))

    # Log data sources
    if data_sources:
        for source_name, data_value in data_sources.items():
            cursor.execute('''
                INSERT INTO prediction_sources (prediction_id, source_name, source_type, data_value)
                VALUES (?, ?, ?, ?)
            ''', (prediction_id, source_name, 'api', json.dumps(data_value)))

    conn.commit()
    conn.close()

    print(f"💾 Logged prediction #{prediction_id} to database")
    return prediction_id


def log_outcome(
    prediction_id: int,
    actual_value: float = None,
    actual_date: str = None,
    notes: str = None,
    verified_by: str = None
) -> int:
    """
    Log the actual outcome of a prediction

    Args:
        prediction_id: ID of the original prediction
        actual_value: Actual value (e.g., BTC price was 95000)
        actual_date: When it happened
        notes: Human notes about what happened
        verified_by: Which source verified this (e.g., "Coinbase API")

    Returns:
        outcome_id
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Get original prediction to calculate variance
    cursor.execute('SELECT text FROM voice_predictions WHERE id = ?', (prediction_id,))
    prediction = cursor.fetchone()

    if not prediction:
        print(f"❌ Prediction {prediction_id} not found")
        conn.close()
        return None

    # Calculate variance (would need parsing logic to extract predicted value)
    variance = None
    accuracy_score = None

    # Insert outcome
    cursor.execute('''
        INSERT INTO prediction_outcomes (prediction_id, actual_value, actual_date, variance, accuracy_score, notes, verified_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (prediction_id, actual_value, actual_date, variance, accuracy_score, notes, verified_by))

    outcome_id = cursor.lastrowid

    # Update model performance stats
    update_model_performance(prediction_id, accuracy_score)

    conn.commit()
    conn.close()

    print(f"✅ Logged outcome for prediction #{prediction_id}")
    return outcome_id


def update_model_performance(prediction_id: int, accuracy_score: int = None):
    """
    Update aggregate model performance stats

    Args:
        prediction_id: ID of prediction
        accuracy_score: 0-100 accuracy score
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Get prediction details
    cursor.execute('''
        SELECT p.brand, pm.model_name
        FROM voice_predictions p
        JOIN prediction_models pm ON p.id = pm.prediction_id
        WHERE p.id = ?
    ''', (prediction_id,))

    results = cursor.fetchall()

    for brand, model_name in results:
        # Extract topic from prediction text (simple keyword matching)
        # In production would use NLP
        topic = "general"  # Placeholder

        # Update or create performance record
        cursor.execute('''
            INSERT INTO model_performance (model_name, topic, brand, total_predictions, correct_predictions, accuracy_pct)
            VALUES (?, ?, ?, 1, ?, ?)
            ON CONFLICT(model_name, topic, brand) DO UPDATE SET
                total_predictions = total_predictions + 1,
                correct_predictions = correct_predictions + ?,
                accuracy_pct = (CAST(correct_predictions AS REAL) / total_predictions) * 100,
                last_updated = CURRENT_TIMESTAMP
        ''', (
            model_name,
            topic,
            brand,
            1 if accuracy_score and accuracy_score >= 70 else 0,
            accuracy_score or 0,
            1 if accuracy_score and accuracy_score >= 70 else 0
        ))

    conn.commit()
    conn.close()


# ==============================================================================
# QUERY FUNCTIONS
# ==============================================================================

def get_accuracy(model: str = None, topic: str = None, brand: str = None) -> float:
    """
    Get historical accuracy for a model/topic/brand

    Args:
        model: Model name (optional)
        topic: Topic (optional)
        brand: Brand slug (optional)

    Returns:
        Accuracy percentage (0-100)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    query = 'SELECT accuracy_pct FROM model_performance WHERE 1=1'
    params = []

    if model:
        query += ' AND model_name = ?'
        params.append(model)
    if topic:
        query += ' AND topic = ?'
        params.append(topic)
    if brand:
        query += ' AND brand = ?'
        params.append(brand)

    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    return 0.0


def get_prediction_history(limit: int = 100, brand: str = None) -> List[Dict]:
    """
    Get recent prediction history

    Args:
        limit: Max predictions to return
        brand: Filter by brand

    Returns:
        List of prediction dicts
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = '''
        SELECT
            p.*,
            GROUP_CONCAT(pm.model_name) as models,
            po.actual_value,
            po.accuracy_score
        FROM voice_predictions p
        LEFT JOIN prediction_models pm ON p.id = pm.prediction_id
        LEFT JOIN prediction_outcomes po ON p.id = po.prediction_id
        WHERE 1=1
    '''

    params = []
    if brand:
        query += ' AND p.brand = ?'
        params.append(brand)

    query += ' GROUP BY p.id ORDER BY p.timestamp DESC LIMIT ?'
    params.append(limit)

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    return [dict(row) for row in results]


# ==============================================================================
# CLI
# ==============================================================================

def main():
    """Initialize database or run queries"""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 prediction_tracker.py init       - Initialize database")
        print("  python3 prediction_tracker.py stats      - Show statistics")
        print("  python3 prediction_tracker.py history    - Show prediction history")
        return

    command = sys.argv[1]

    if command == 'init':
        init_prediction_tables()

    elif command == 'stats':
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        print("\n📊 PREDICTION STATISTICS")
        print("=" * 70)

        cursor.execute('SELECT COUNT(*) FROM voice_predictions')
        total = cursor.fetchone()[0]
        print(f"Total voice predictions: {total}")

        cursor.execute('SELECT COUNT(*) FROM prediction_outcomes')
        outcomes = cursor.fetchone()[0]
        print(f"Outcomes logged: {outcomes}")

        cursor.execute('SELECT model_name, topic, accuracy_pct FROM model_performance ORDER BY accuracy_pct DESC')
        performance = cursor.fetchall()

        if performance:
            print("\n🎯 Model Performance:")
            for model, topic, accuracy in performance:
                print(f"   {model} ({topic}): {accuracy:.1f}%")

        conn.close()

    elif command == 'history':
        history = get_prediction_history(limit=10)

        print("\n📜 RECENT PREDICTIONS")
        print("=" * 70)

        for pred in history:
            print(f"\n#{pred['id']} - {pred['timestamp']}")
            print(f"   {pred['text']}")
            print(f"   Brand: {pred['brand']} | Models: {pred['models']}")
            if pred.get('accuracy_score'):
                print(f"   Accuracy: {pred['accuracy_score']}%")


if __name__ == '__main__':
    main()
