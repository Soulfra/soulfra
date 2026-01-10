#!/usr/bin/env python3
"""
Reverse WPM - Unpredictability Scoring System

Traditional WPM (words per minute) measures typing speed.
Reverse WPM measures creative unpredictability - how often you surprise the AI.

Higher Reverse WPM = More unpredictable = Better storyteller = More reputation/rewards

Integrates with:
- story_predictor.py for AI predictions
- prediction_tracker.py for logging scores
- VIBE token economy for rewards
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass
import json


DATABASE_PATH = Path(__file__).parent / 'soulfra.db'


@dataclass
class UnpredictabilityScore:
    """Tracks a storyteller's unpredictability metrics"""
    storyteller_id: int
    reverse_wpm: float  # Unpredictability per minute
    total_segments: int
    successful_surprises: int  # Times AI was wrong
    avg_surprise_factor: float  # 0-1 how surprising
    streak: int  # Current streak of surprising AI
    best_streak: int
    level: int  # 1-100 based on total experience
    achievements: List[str]


class ReverseWPMTracker:
    """
    Tracks and calculates Reverse WPM scores for storytellers
    """

    def __init__(self):
        self.db = sqlite3.connect(DATABASE_PATH)
        self.init_tables()

        # Thresholds for "surprising" the AI
        self.surprise_threshold = 0.7  # 70% unpredictability = surprise
        self.streak_bonus_multiplier = 1.5  # 50% bonus for streaks

        # Level thresholds
        self.levels = self._calculate_level_thresholds()

        # Achievements
        self.achievements = {
            'first_surprise': 'Surprised the AI for the first time',
            'streak_3': 'Surprised AI 3 times in a row',
            'streak_5': 'Surprised AI 5 times in a row (Hot Streak!)',
            'streak_10': 'Surprised AI 10 times in a row (Unstoppable!)',
            'plot_twist_master': 'Average surprise factor > 80%',
            'speed_demon': 'Reverse WPM > 5.0',
            'literary_genius': 'Reverse WPM > 10.0',
            'unpredictable_legend': 'Reached level 50',
            'story_completed': 'Completed a full story session',
            'multi_genre_master': 'High scores in 3+ genres'
        }

    def init_tables(self):
        """Create reverse WPM tracking tables"""
        cursor = self.db.cursor()

        # Storyteller stats
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS storyteller_stats (
                storyteller_id INTEGER PRIMARY KEY,
                username TEXT,
                total_sessions INTEGER DEFAULT 0,
                total_segments INTEGER DEFAULT 0,
                total_surprises INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                best_streak INTEGER DEFAULT 0,
                avg_reverse_wpm REAL DEFAULT 0.0,
                best_reverse_wpm REAL DEFAULT 0.0,
                avg_surprise_factor REAL DEFAULT 0.0,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                achievements TEXT DEFAULT '[]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_story DATETIME
            )
        ''')

        # Session tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS story_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                storyteller_id INTEGER NOT NULL,
                title TEXT,
                genre TEXT,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ended_at DATETIME,
                segment_count INTEGER DEFAULT 0,
                surprise_count INTEGER DEFAULT 0,
                reverse_wpm REAL DEFAULT 0.0,
                avg_unpredictability REAL DEFAULT 0.0,
                status TEXT DEFAULT 'active',

                FOREIGN KEY (storyteller_id) REFERENCES storyteller_stats(storyteller_id)
            )
        ''')

        # Segment scores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS segment_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                segment_number INTEGER NOT NULL,
                prediction_text TEXT,
                actual_text TEXT,
                ai_confidence REAL,
                unpredictability_score REAL,
                surprise_factor REAL,
                method TEXT,
                surprised_ai BOOLEAN DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (session_id) REFERENCES story_sessions(id)
            )
        ''')

        # Genre leaderboards
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS genre_leaderboards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                storyteller_id INTEGER NOT NULL,
                genre TEXT NOT NULL,
                sessions_count INTEGER DEFAULT 0,
                best_reverse_wpm REAL DEFAULT 0.0,
                avg_reverse_wpm REAL DEFAULT 0.0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(storyteller_id, genre),
                FOREIGN KEY (storyteller_id) REFERENCES storyteller_stats(storyteller_id)
            )
        ''')

        # Achievement tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievement_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                storyteller_id INTEGER NOT NULL,
                achievement_key TEXT NOT NULL,
                achievement_name TEXT,
                earned_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (storyteller_id) REFERENCES storyteller_stats(storyteller_id)
            )
        ''')

        self.db.commit()
        print("✅ Reverse WPM tables initialized")

    def _calculate_level_thresholds(self) -> List[int]:
        """Calculate XP needed for each level (1-100)"""
        levels = []
        for level in range(1, 101):
            # Exponential curve: level 10 = 1000 XP, level 50 = 50000 XP
            xp_needed = int(100 * (level ** 1.5))
            levels.append(xp_needed)
        return levels

    def start_story_session(
        self,
        storyteller_id: int,
        username: str = None,
        title: str = None,
        genre: str = "general"
    ) -> int:
        """
        Start a new story session

        Args:
            storyteller_id: User/device ID
            username: Display name
            title: Story title
            genre: Story genre

        Returns:
            session_id
        """
        cursor = self.db.cursor()

        # Ensure storyteller exists
        cursor.execute('''
            INSERT OR IGNORE INTO storyteller_stats (storyteller_id, username)
            VALUES (?, ?)
        ''', (storyteller_id, username or f"Storyteller-{storyteller_id}"))

        # Create session
        cursor.execute('''
            INSERT INTO story_sessions (storyteller_id, title, genre)
            VALUES (?, ?, ?)
        ''', (storyteller_id, title, genre))

        session_id = cursor.lastrowid

        # Update storyteller stats
        cursor.execute('''
            UPDATE storyteller_stats
            SET total_sessions = total_sessions + 1,
                last_story = CURRENT_TIMESTAMP
            WHERE storyteller_id = ?
        ''', (storyteller_id,))

        self.db.commit()

        print(f"📖 Started story session #{session_id} for {username or storyteller_id}")
        print(f"   Genre: {genre}")
        if title:
            print(f"   Title: {title}")

        return session_id

    def score_segment(
        self,
        session_id: int,
        segment_number: int,
        prediction: Dict,
        actual_text: str,
        score: Dict
    ) -> Dict:
        """
        Score a story segment and update stats

        Args:
            session_id: Active session ID
            segment_number: Segment number (1, 2, 3...)
            prediction: Dict from story_predictor.predict_next_segment()
            actual_text: What storyteller actually wrote
            score: Dict from story_predictor.score_prediction()

        Returns:
            {
                'surprised_ai': bool,
                'unpredictability': float,
                'xp_earned': int,
                'achievements_unlocked': List[str],
                'new_streak': int
            }
        """
        cursor = self.db.cursor()

        # Get session info
        cursor.execute('SELECT storyteller_id FROM story_sessions WHERE id = ?', (session_id,))
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"Session {session_id} not found")

        storyteller_id = result[0]

        # Check if AI was surprised
        unpredictability = score.get('unpredictability', 0)
        surprise_factor = score.get('surprise_factor', 0)
        surprised_ai = unpredictability >= self.surprise_threshold

        # Log segment score
        cursor.execute('''
            INSERT INTO segment_scores (
                session_id, segment_number, prediction_text, actual_text,
                ai_confidence, unpredictability_score, surprise_factor,
                method, surprised_ai
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            segment_number,
            prediction.get('consensus', ''),
            actual_text,
            prediction.get('confidence', 0),
            unpredictability,
            surprise_factor,
            score.get('method', 'similarity'),
            int(surprised_ai)
        ))

        # Update session stats
        cursor.execute('''
            UPDATE story_sessions
            SET segment_count = segment_count + 1,
                surprise_count = surprise_count + ?
            WHERE id = ?
        ''', (int(surprised_ai), session_id))

        # Update storyteller stats
        cursor.execute('''
            UPDATE storyteller_stats
            SET total_segments = total_segments + 1,
                total_surprises = total_surprises + ?,
                current_streak = CASE
                    WHEN ? THEN current_streak + 1
                    ELSE 0
                END
            WHERE storyteller_id = ?
        ''', (int(surprised_ai), surprised_ai, storyteller_id))

        # Get updated streak
        cursor.execute('SELECT current_streak, best_streak FROM storyteller_stats WHERE storyteller_id = ?',
                      (storyteller_id,))
        current_streak, best_streak = cursor.fetchone()

        # Update best streak if needed
        if current_streak > best_streak:
            cursor.execute('''
                UPDATE storyteller_stats
                SET best_streak = ?
                WHERE storyteller_id = ?
            ''', (current_streak, storyteller_id))

        # Calculate XP earned
        base_xp = 10
        surprise_bonus = 50 if surprised_ai else 0
        streak_bonus = int(base_xp * self.streak_bonus_multiplier * (current_streak / 5)) if current_streak >= 3 else 0
        quality_bonus = int(unpredictability * 30)  # Up to 30 XP for max unpredictability

        xp_earned = base_xp + surprise_bonus + streak_bonus + quality_bonus

        # Award XP
        cursor.execute('''
            UPDATE storyteller_stats
            SET xp = xp + ?
            WHERE storyteller_id = ?
        ''', (xp_earned, storyteller_id))

        # Check for level up
        new_achievements = []
        cursor.execute('SELECT xp, level FROM storyteller_stats WHERE storyteller_id = ?', (storyteller_id,))
        total_xp, current_level = cursor.fetchone()

        new_level = self._calculate_level(total_xp)
        if new_level > current_level:
            cursor.execute('UPDATE storyteller_stats SET level = ? WHERE storyteller_id = ?',
                          (new_level, storyteller_id))
            print(f"🎉 Level UP! {current_level} → {new_level}")

        # Check for achievement unlocks
        new_achievements.extend(self._check_achievements(storyteller_id, current_streak, surprise_factor))

        self.db.commit()

        result = {
            'surprised_ai': surprised_ai,
            'unpredictability': unpredictability,
            'surprise_factor': surprise_factor,
            'xp_earned': xp_earned,
            'total_xp': total_xp + xp_earned,
            'level': new_level,
            'current_streak': current_streak,
            'achievements_unlocked': new_achievements
        }

        if surprised_ai:
            print(f"🎯 SURPRISED THE AI! (unpredictability: {unpredictability:.1%})")
            print(f"   +{xp_earned} XP (streak: {current_streak})")
        else:
            print(f"🤖 AI predicted correctly (unpredictability: {unpredictability:.1%})")
            print(f"   +{xp_earned} XP")

        return result

    def end_story_session(self, session_id: int) -> Dict:
        """
        End a story session and calculate final scores

        Args:
            session_id: Session to end

        Returns:
            {
                'reverse_wpm': float,
                'avg_unpredictability': float,
                'total_segments': int,
                'total_surprises': int,
                'session_time_minutes': float
            }
        """
        cursor = self.db.cursor()

        # Get session info
        cursor.execute('''
            SELECT storyteller_id, started_at, segment_count, surprise_count
            FROM story_sessions
            WHERE id = ?
        ''', (session_id,))

        result = cursor.fetchone()
        if not result:
            raise ValueError(f"Session {session_id} not found")

        storyteller_id, started_at, segment_count, surprise_count = result

        # Calculate session duration
        started_dt = datetime.fromisoformat(started_at)
        ended_dt = datetime.now()
        duration_seconds = (ended_dt - started_dt).total_seconds()
        duration_minutes = duration_seconds / 60.0

        # Get segment scores
        cursor.execute('''
            SELECT unpredictability_score, surprise_factor
            FROM segment_scores
            WHERE session_id = ?
        ''', (session_id,))

        scores = cursor.fetchall()

        if not scores:
            avg_unpredictability = 0.0
            reverse_wpm = 0.0
        else:
            avg_unpredictability = sum(s[0] for s in scores) / len(scores)
            # Reverse WPM = total unpredictability / minutes
            total_unpredictability = sum(s[0] for s in scores)
            reverse_wpm = total_unpredictability / max(duration_minutes, 0.1)

        # Update session
        cursor.execute('''
            UPDATE story_sessions
            SET ended_at = CURRENT_TIMESTAMP,
                reverse_wpm = ?,
                avg_unpredictability = ?,
                status = 'completed'
            WHERE id = ?
        ''', (reverse_wpm, avg_unpredictability, session_id))

        # Update storyteller averages
        cursor.execute('''
            SELECT AVG(reverse_wpm), MAX(reverse_wpm), AVG(avg_unpredictability)
            FROM story_sessions
            WHERE storyteller_id = ? AND status = 'completed'
        ''', (storyteller_id,))

        avg_rwpm, best_rwpm, avg_unpred = cursor.fetchone()

        cursor.execute('''
            UPDATE storyteller_stats
            SET avg_reverse_wpm = ?,
                best_reverse_wpm = ?,
                avg_surprise_factor = ?
            WHERE storyteller_id = ?
        ''', (avg_rwpm or 0, best_rwpm or 0, avg_unpred or 0, storyteller_id))

        # Update genre leaderboard
        cursor.execute('SELECT genre FROM story_sessions WHERE id = ?', (session_id,))
        genre = cursor.fetchone()[0]

        cursor.execute('''
            INSERT INTO genre_leaderboards (storyteller_id, genre, sessions_count, best_reverse_wpm, avg_reverse_wpm)
            VALUES (?, ?, 1, ?, ?)
            ON CONFLICT(storyteller_id, genre) DO UPDATE SET
                sessions_count = sessions_count + 1,
                best_reverse_wpm = MAX(best_reverse_wpm, ?),
                avg_reverse_wpm = ((avg_reverse_wpm * (sessions_count - 1)) + ?) / sessions_count,
                last_updated = CURRENT_TIMESTAMP
        ''', (storyteller_id, genre, reverse_wpm, reverse_wpm, reverse_wpm, reverse_wpm))

        # Check for completion achievement
        self._unlock_achievement(storyteller_id, 'story_completed', self.achievements['story_completed'])

        self.db.commit()

        print(f"\n📊 Story session completed!")
        print(f"   Reverse WPM: {reverse_wpm:.2f}")
        print(f"   Avg Unpredictability: {avg_unpredictability:.1%}")
        print(f"   Segments: {segment_count}")
        print(f"   Surprised AI: {surprise_count}/{segment_count}")
        print(f"   Duration: {duration_minutes:.1f} minutes")

        return {
            'reverse_wpm': reverse_wpm,
            'avg_unpredictability': avg_unpredictability,
            'total_segments': segment_count,
            'total_surprises': surprise_count,
            'session_time_minutes': duration_minutes
        }

    def _calculate_level(self, xp: int) -> int:
        """Calculate level from XP"""
        for level, threshold in enumerate(self.levels, start=1):
            if xp < threshold:
                return level
        return 100  # Max level

    def _check_achievements(self, storyteller_id: int, streak: int, surprise_factor: float) -> List[str]:
        """Check and unlock achievements"""
        new_achievements = []

        # Streak achievements
        if streak == 3:
            if self._unlock_achievement(storyteller_id, 'streak_3', self.achievements['streak_3']):
                new_achievements.append('streak_3')
        elif streak == 5:
            if self._unlock_achievement(storyteller_id, 'streak_5', self.achievements['streak_5']):
                new_achievements.append('streak_5')
        elif streak == 10:
            if self._unlock_achievement(storyteller_id, 'streak_10', self.achievements['streak_10']):
                new_achievements.append('streak_10')

        # Surprise factor achievement
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT AVG(surprise_factor)
            FROM segment_scores ss
            JOIN story_sessions s ON ss.session_id = s.id
            WHERE s.storyteller_id = ?
        ''', (storyteller_id,))

        avg_surprise = cursor.fetchone()[0] or 0
        if avg_surprise > 0.8:
            if self._unlock_achievement(storyteller_id, 'plot_twist_master', self.achievements['plot_twist_master']):
                new_achievements.append('plot_twist_master')

        return new_achievements

    def _unlock_achievement(self, storyteller_id: int, achievement_key: str, achievement_name: str) -> bool:
        """Unlock an achievement (returns True if newly unlocked)"""
        cursor = self.db.cursor()

        # Check if already unlocked
        cursor.execute('''
            SELECT id FROM achievement_log
            WHERE storyteller_id = ? AND achievement_key = ?
        ''', (storyteller_id, achievement_key))

        if cursor.fetchone():
            return False  # Already unlocked

        # Unlock it
        cursor.execute('''
            INSERT INTO achievement_log (storyteller_id, achievement_key, achievement_name)
            VALUES (?, ?, ?)
        ''', (storyteller_id, achievement_key, achievement_name))

        # Update storyteller's achievement list
        cursor.execute('SELECT achievements FROM storyteller_stats WHERE storyteller_id = ?', (storyteller_id,))
        achievements_json = cursor.fetchone()[0]
        achievements = json.loads(achievements_json)
        achievements.append(achievement_key)

        cursor.execute('''
            UPDATE storyteller_stats
            SET achievements = ?
            WHERE storyteller_id = ?
        ''', (json.dumps(achievements), storyteller_id))

        self.db.commit()

        print(f"🏆 ACHIEVEMENT UNLOCKED: {achievement_name}")
        return True

    def get_storyteller_stats(self, storyteller_id: int) -> Optional[UnpredictabilityScore]:
        """Get current stats for a storyteller"""
        cursor = self.db.cursor()

        cursor.execute('''
            SELECT
                storyteller_id, avg_reverse_wpm, total_segments, total_surprises,
                avg_surprise_factor, current_streak, best_streak, level, achievements
            FROM storyteller_stats
            WHERE storyteller_id = ?
        ''', (storyteller_id,))

        result = cursor.fetchone()
        if not result:
            return None

        achievements = json.loads(result[8])

        return UnpredictabilityScore(
            storyteller_id=result[0],
            reverse_wpm=result[1],
            total_segments=result[2],
            successful_surprises=result[3],
            avg_surprise_factor=result[4],
            streak=result[5],
            best_streak=result[6],
            level=result[7],
            achievements=achievements
        )

    def get_leaderboard(self, genre: str = None, limit: int = 10) -> List[Dict]:
        """Get top storytellers by Reverse WPM"""
        cursor = self.db.cursor()

        if genre:
            cursor.execute('''
                SELECT s.username, s.storyteller_id, g.best_reverse_wpm, g.avg_reverse_wpm,
                       s.level, s.total_surprises, g.sessions_count
                FROM genre_leaderboards g
                JOIN storyteller_stats s ON g.storyteller_id = s.storyteller_id
                WHERE g.genre = ?
                ORDER BY g.best_reverse_wpm DESC
                LIMIT ?
            ''', (genre, limit))
        else:
            cursor.execute('''
                SELECT username, storyteller_id, best_reverse_wpm, avg_reverse_wpm,
                       level, total_surprises, total_sessions
                FROM storyteller_stats
                ORDER BY best_reverse_wpm DESC
                LIMIT ?
            ''', (limit,))

        results = cursor.fetchall()

        return [
            {
                'rank': idx + 1,
                'username': row[0],
                'storyteller_id': row[1],
                'best_reverse_wpm': row[2],
                'avg_reverse_wpm': row[3],
                'level': row[4],
                'total_surprises': row[5],
                'total_sessions': row[6]
            }
            for idx, row in enumerate(results)
        ]


def main():
    """Demo reverse WPM tracker"""
    tracker = ReverseWPMTracker()

    print("=" * 60)
    print("🏆 REVERSE WPM TRACKER DEMO")
    print("=" * 60)

    # Start a session
    session_id = tracker.start_story_session(
        storyteller_id=1,
        username="CreativeWriter",
        title="The Mystery of the Vanishing Cat",
        genre="mystery"
    )

    # Simulate scoring some segments
    mock_predictions = [
        {'consensus': 'The cat was hiding under the bed.', 'confidence': 0.8},
        {'consensus': 'Sarah found the cat in the garden.', 'confidence': 0.7},
        {'consensus': 'The cat meowed loudly.', 'confidence': 0.6}
    ]

    mock_actuals = [
        'The cat had been kidnapped by the neighbor.',
        'Sarah discovered a secret tunnel behind the bookshelf.',
        'The cat spoke in perfect English, revealing it was an alien spy.'
    ]

    for i, (pred, actual) in enumerate(zip(mock_predictions, mock_actuals), start=1):
        # Mock score (high unpredictability)
        score = {
            'unpredictability': 0.85,
            'surprise_factor': 0.9,
            'method': 'surprise'
        }

        result = tracker.score_segment(session_id, i, pred, actual, score)
        print()

    # End session
    final = tracker.end_story_session(session_id)

    # Get stats
    stats = tracker.get_storyteller_stats(1)
    print(f"\n📈 Storyteller Stats:")
    print(f"   Level: {stats.level}")
    print(f"   Reverse WPM: {stats.reverse_wpm:.2f}")
    print(f"   Current Streak: {stats.streak}")
    print(f"   Achievements: {len(stats.achievements)}")

    # Show leaderboard
    print(f"\n🏆 LEADERBOARD (Mystery Genre):")
    print("=" * 60)
    leaderboard = tracker.get_leaderboard(genre="mystery")
    for entry in leaderboard:
        print(f"{entry['rank']}. {entry['username']} - {entry['best_reverse_wpm']:.2f} Reverse WPM (Level {entry['level']})")


if __name__ == '__main__':
    main()
