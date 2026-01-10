#!/usr/bin/env python3
"""
Physics-Based Scoring Algorithms - Pure Python

Apply physics and information theory concepts to game scoring.
No scipy, numpy, or external libraries - built from scratch.

Features:
- Momentum Analysis (velocity, acceleration of scores over time)
- Wave Analysis (frequency, amplitude, phase of patterns)
- Entropy Calculation (chaos/order in responses)
- Statistical Significance (is change meaningful?)
- Outlier Detection (which scores are unusual?)

Usage:
    from lib.physics import PhysicsScoring

    scorer = PhysicsScoring()
    analysis = scorer.analyze_score_history([65, 70, 73, 78, 82])
    print(f"Momentum: {analysis['momentum']}")  # Positive = improving
    print(f"Acceleration: {analysis['acceleration']}")  # Rate of change
"""

import math
from typing import List, Dict, Tuple, Any, Optional
from collections import Counter


# ==============================================================================
# MOMENTUM & DYNAMICS
# ==============================================================================

class MomentumAnalyzer:
    """
    Treat scores as physics objects with momentum

    Concepts:
    - Position = current score
    - Velocity = rate of change
    - Acceleration = change in velocity
    - Momentum = mass × velocity (mass = importance weight)
    """

    def calculate_velocity(self, scores: List[float]) -> float:
        """
        Calculate velocity (rate of change)

        velocity = (final_score - initial_score) / time_periods
        """
        if len(scores) < 2:
            return 0.0

        return (scores[-1] - scores[0]) / (len(scores) - 1)

    def calculate_acceleration(self, scores: List[float]) -> float:
        """
        Calculate acceleration (change in velocity)

        acceleration = (velocity_2 - velocity_1) / time
        """
        if len(scores) < 3:
            return 0.0

        # Split into two halves
        mid = len(scores) // 2
        first_half = scores[:mid + 1]
        second_half = scores[mid:]

        # Calculate velocity for each half
        v1 = self.calculate_velocity(first_half)
        v2 = self.calculate_velocity(second_half)

        # Acceleration = change in velocity
        return v2 - v1

    def calculate_momentum(self, scores: List[float], mass: float = 1.0) -> float:
        """
        Calculate momentum

        momentum = mass × velocity

        Args:
            scores: Score history
            mass: Weight/importance (default 1.0)
        """
        velocity = self.calculate_velocity(scores)
        return mass * velocity

    def predict_next_score(self, scores: List[float]) -> float:
        """
        Predict next score using linear extrapolation

        next_score = current_score + velocity
        """
        if not scores:
            return 0.0

        velocity = self.calculate_velocity(scores)
        return scores[-1] + velocity


# ==============================================================================
# WAVE ANALYSIS
# ==============================================================================

class WaveAnalyzer:
    """
    Analyze score patterns as waves

    Concepts:
    - Frequency = how often scores oscillate
    - Amplitude = range of scores (max - min)
    - Phase = timing of peaks/troughs
    - Period = time between peaks
    """

    def calculate_amplitude(self, scores: List[float]) -> float:
        """
        Calculate amplitude (range of scores)

        amplitude = (max - min) / 2
        """
        if not scores:
            return 0.0

        return (max(scores) - min(scores)) / 2

    def find_peaks_and_troughs(self, scores: List[float]) -> Dict[str, List[int]]:
        """
        Find peaks (local maxima) and troughs (local minima)

        Returns:
            Dict with 'peaks' and 'troughs' indices
        """
        if len(scores) < 3:
            return {'peaks': [], 'troughs': []}

        peaks = []
        troughs = []

        for i in range(1, len(scores) - 1):
            # Peak: value > neighbors
            if scores[i] > scores[i-1] and scores[i] > scores[i+1]:
                peaks.append(i)
            # Trough: value < neighbors
            elif scores[i] < scores[i-1] and scores[i] < scores[i+1]:
                troughs.append(i)

        return {'peaks': peaks, 'troughs': troughs}

    def calculate_period(self, scores: List[float]) -> Optional[float]:
        """
        Calculate period (average time between peaks)

        period = average distance between peaks
        """
        peaks = self.find_peaks_and_troughs(scores)['peaks']

        if len(peaks) < 2:
            return None

        # Calculate distances between consecutive peaks
        distances = [peaks[i+1] - peaks[i] for i in range(len(peaks) - 1)]

        return sum(distances) / len(distances)

    def detect_cycle(self, scores: List[float]) -> Dict[str, Any]:
        """
        Detect if scores follow a cyclical pattern

        Returns:
            Dict with cycle info (has_cycle, period, confidence)
        """
        period = self.calculate_period(scores)
        amplitude = self.calculate_amplitude(scores)

        # Cycle detected if:
        # 1. Period exists
        # 2. Amplitude is significant (> 10% of mean)
        has_cycle = False
        confidence = 0.0

        if period is not None and scores:
            mean_score = sum(scores) / len(scores)
            if amplitude > (mean_score * 0.1):
                has_cycle = True
                # Confidence based on amplitude and regularity
                confidence = min(1.0, amplitude / mean_score)

        return {
            'has_cycle': has_cycle,
            'period': period,
            'amplitude': amplitude,
            'confidence': confidence
        }


# ==============================================================================
# ENTROPY & INFORMATION THEORY
# ==============================================================================

class EntropyCalculator:
    """
    Calculate entropy (disorder/chaos) in responses

    Concepts:
    - Entropy = measure of unpredictability
    - High entropy = chaotic, inconsistent
    - Low entropy = ordered, predictable

    Formula: H = -Σ(p(x) * log2(p(x)))
    """

    def calculate_entropy(self, values: List[Any]) -> float:
        """
        Calculate Shannon entropy

        Args:
            values: List of any hashable values (numbers, strings, etc.)

        Returns:
            Entropy value (0 = perfectly ordered, high = chaotic)
        """
        if not values:
            return 0.0

        # Count frequencies
        counts = Counter(values)
        total = len(values)

        # Calculate probabilities
        probabilities = [count / total for count in counts.values()]

        # Calculate entropy: H = -Σ(p * log2(p))
        entropy = 0.0
        for p in probabilities:
            if p > 0:
                entropy -= p * math.log2(p)

        return entropy

    def normalize_entropy(self, entropy: float, num_unique_values: int) -> float:
        """
        Normalize entropy to 0-1 scale

        Max entropy = log2(num_unique_values)
        Normalized = actual_entropy / max_entropy
        """
        if num_unique_values <= 1:
            return 0.0

        max_entropy = math.log2(num_unique_values)
        return entropy / max_entropy if max_entropy > 0 else 0.0

    def consistency_score(self, values: List[Any]) -> float:
        """
        Calculate consistency (opposite of entropy)

        Returns:
            Score from 0-1 (1 = perfectly consistent, 0 = chaotic)
        """
        entropy = self.calculate_entropy(values)
        num_unique = len(set(values))
        normalized = self.normalize_entropy(entropy, num_unique)

        # Consistency = 1 - normalized_entropy
        return 1.0 - normalized


# ==============================================================================
# STATISTICAL ANALYSIS
# ==============================================================================

class StatisticalAnalyzer:
    """
    Statistical significance testing and outlier detection

    Concepts:
    - Mean, median, standard deviation
    - Z-scores for outlier detection
    - Variance analysis
    - Statistical significance
    """

    def calculate_mean(self, values: List[float]) -> float:
        """Calculate arithmetic mean (average)"""
        if not values:
            return 0.0
        return sum(values) / len(values)

    def calculate_median(self, values: List[float]) -> float:
        """Calculate median (middle value)"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        n = len(sorted_values)
        mid = n // 2

        if n % 2 == 0:
            # Even: average of two middle values
            return (sorted_values[mid - 1] + sorted_values[mid]) / 2
        else:
            # Odd: middle value
            return sorted_values[mid]

    def calculate_variance(self, values: List[float]) -> float:
        """
        Calculate variance

        variance = Σ(x - mean)² / n
        """
        if not values:
            return 0.0

        mean = self.calculate_mean(values)
        squared_diffs = [(x - mean) ** 2 for x in values]
        return sum(squared_diffs) / len(values)

    def calculate_std_dev(self, values: List[float]) -> float:
        """
        Calculate standard deviation

        std_dev = √variance
        """
        variance = self.calculate_variance(values)
        return math.sqrt(variance)

    def calculate_z_score(self, value: float, values: List[float]) -> float:
        """
        Calculate z-score (standard score)

        z = (x - mean) / std_dev

        Returns:
            Number of standard deviations from mean
        """
        mean = self.calculate_mean(values)
        std_dev = self.calculate_std_dev(values)

        if std_dev == 0:
            return 0.0

        return (value - mean) / std_dev

    def detect_outliers(self, values: List[float], threshold: float = 2.0) -> List[Tuple[int, float, float]]:
        """
        Detect outliers using z-score method

        Args:
            values: List of values to analyze
            threshold: Z-score threshold (default 2.0 = 95% confidence)

        Returns:
            List of (index, value, z_score) tuples for outliers
        """
        outliers = []

        for i, value in enumerate(values):
            z_score = self.calculate_z_score(value, values)
            if abs(z_score) > threshold:
                outliers.append((i, value, z_score))

        return outliers

    def is_significant_change(self, old_value: float, new_value: float,
                            historical_values: List[float], threshold: float = 1.5) -> bool:
        """
        Determine if change is statistically significant

        Args:
            old_value: Previous value
            new_value: Current value
            historical_values: Historical values for context
            threshold: Z-score threshold for significance

        Returns:
            True if change is significant
        """
        change = new_value - old_value

        # Calculate z-score of the change
        z_score = self.calculate_z_score(change, historical_values)

        return abs(z_score) > threshold

    def calculate_percentile(self, value: float, values: List[float]) -> float:
        """
        Calculate percentile rank

        Args:
            value: Value to rank
            values: List of values to compare against

        Returns:
            Percentile (0-100)
        """
        if not values:
            return 0.0

        count_below = sum(1 for v in values if v < value)
        return (count_below / len(values)) * 100


# ==============================================================================
# MAIN PHYSICS SCORING CLASS
# ==============================================================================

class PhysicsScoring:
    """
    Main class combining all physics-based scoring algorithms

    Usage:
        scorer = PhysicsScoring()
        analysis = scorer.analyze_score_history([65, 70, 73, 78, 82])
    """

    def __init__(self):
        self.momentum = MomentumAnalyzer()
        self.wave = WaveAnalyzer()
        self.entropy = EntropyCalculator()
        self.stats = StatisticalAnalyzer()

    def analyze_score_history(self, scores: List[float],
                             categories: Optional[Dict[str, List[float]]] = None) -> Dict[str, Any]:
        """
        Complete physics-based analysis of score history

        Args:
            scores: Overall score history (e.g., [65, 70, 73, 78, 82])
            categories: Optional dict of category scores over time

        Returns:
            Comprehensive analysis dictionary
        """
        if not scores:
            return {'error': 'No scores provided'}

        # Momentum analysis
        velocity = self.momentum.calculate_velocity(scores)
        acceleration = self.momentum.calculate_acceleration(scores)
        predicted = self.momentum.predict_next_score(scores)

        # Wave analysis
        amplitude = self.wave.calculate_amplitude(scores)
        peaks_troughs = self.wave.find_peaks_and_troughs(scores)
        cycle_info = self.wave.detect_cycle(scores)

        # Statistical analysis
        mean = self.stats.calculate_mean(scores)
        median = self.stats.calculate_median(scores)
        std_dev = self.stats.calculate_std_dev(scores)
        outliers = self.stats.detect_outliers(scores)

        # Entropy (consistency)
        # Bin scores into ranges for entropy calculation
        binned_scores = [round(s / 10) * 10 for s in scores]
        consistency = self.entropy.consistency_score(binned_scores)

        # Trend analysis
        trend = 'improving' if velocity > 0 else 'declining' if velocity < 0 else 'stable'
        trend_strength = abs(velocity)

        # Acceleration analysis
        if acceleration > 0.5:
            acceleration_status = 'accelerating'
        elif acceleration < -0.5:
            acceleration_status = 'decelerating'
        else:
            acceleration_status = 'steady'

        result = {
            # Overall metrics
            'current_score': scores[-1],
            'mean_score': round(mean, 2),
            'median_score': round(median, 2),

            # Momentum
            'velocity': round(velocity, 2),
            'acceleration': round(acceleration, 2),
            'predicted_next': round(predicted, 2),
            'trend': trend,
            'trend_strength': round(trend_strength, 2),
            'acceleration_status': acceleration_status,

            # Wave patterns
            'amplitude': round(amplitude, 2),
            'has_cycle': cycle_info['has_cycle'],
            'cycle_period': cycle_info['period'],
            'num_peaks': len(peaks_troughs['peaks']),
            'num_troughs': len(peaks_troughs['troughs']),

            # Statistical
            'std_dev': round(std_dev, 2),
            'consistency': round(consistency, 2),
            'outliers': outliers,

            # Raw data
            'score_history': scores,
            'num_sessions': len(scores)
        }

        # Category analysis (if provided)
        if categories:
            category_analysis = {}
            for cat_name, cat_scores in categories.items():
                if len(cat_scores) >= 2:
                    cat_velocity = self.momentum.calculate_velocity(cat_scores)
                    category_analysis[cat_name] = {
                        'current': cat_scores[-1],
                        'velocity': round(cat_velocity, 2),
                        'trend': 'improving' if cat_velocity > 0 else 'declining' if cat_velocity < 0 else 'stable'
                    }

            result['category_analysis'] = category_analysis

        return result

    def compare_users(self, scores1: List[float], scores2: List[float]) -> Dict[str, Any]:
        """
        Compare two users' score histories

        Args:
            scores1: First user's scores
            scores2: Second user's scores

        Returns:
            Comparison analysis
        """
        analysis1 = self.analyze_score_history(scores1)
        analysis2 = self.analyze_score_history(scores2)

        # Calculate similarity
        velocity_diff = abs(analysis1['velocity'] - analysis2['velocity'])
        mean_diff = abs(analysis1['mean_score'] - analysis2['mean_score'])

        # Users are similar if they have similar velocities (same journey)
        velocity_similarity = max(0, 1 - (velocity_diff / 10))
        score_similarity = max(0, 1 - (mean_diff / 100))

        overall_similarity = (velocity_similarity + score_similarity) / 2

        return {
            'user1': analysis1,
            'user2': analysis2,
            'similarity': round(overall_similarity, 2),
            'velocity_diff': round(velocity_diff, 2),
            'mean_diff': round(mean_diff, 2),
            'both_improving': analysis1['trend'] == 'improving' and analysis2['trend'] == 'improving',
            'both_declining': analysis1['trend'] == 'declining' and analysis2['trend'] == 'declining'
        }


if __name__ == '__main__':
    print("🔬 Physics-Based Scoring Algorithms")
    print("=" * 50)

    # Example: Improving student
    print("\n📈 Example: Improving Student")
    scores = [65, 70, 73, 78, 82]

    scorer = PhysicsScoring()
    analysis = scorer.analyze_score_history(scores)

    print(f"Scores: {scores}")
    print(f"Velocity: {analysis['velocity']:.2f} points/session ({analysis['trend']})")
    print(f"Acceleration: {analysis['acceleration']:.2f} ({analysis['acceleration_status']})")
    print(f"Predicted next: {analysis['predicted_next']:.2f}")
    print(f"Consistency: {analysis['consistency']:.2f} (0=chaotic, 1=consistent)")

    # Example: Declining student
    print("\n📉 Example: Declining Student")
    scores2 = [85, 80, 78, 73, 68]
    analysis2 = scorer.analyze_score_history(scores2)

    print(f"Scores: {scores2}")
    print(f"Velocity: {analysis2['velocity']:.2f} points/session ({analysis2['trend']})")
    print(f"Acceleration: {analysis2['acceleration']:.2f} ({analysis2['acceleration_status']})")
    print(f"Predicted next: {analysis2['predicted_next']:.2f}")

    # Example: Oscillating student
    print("\n🌊 Example: Oscillating Student")
    scores3 = [70, 85, 72, 87, 69, 88]
    analysis3 = scorer.analyze_score_history(scores3)

    print(f"Scores: {scores3}")
    print(f"Has cycle: {analysis3['has_cycle']}")
    print(f"Amplitude: {analysis3['amplitude']:.2f}")
    print(f"Peaks: {analysis3['num_peaks']}, Troughs: {analysis3['num_troughs']}")
    print(f"Consistency: {analysis3['consistency']:.2f}")

    print("\n✅ Import this module to use physics-based scoring!")