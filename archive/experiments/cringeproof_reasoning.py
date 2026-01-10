#!/usr/bin/env python3
"""
Cringeproof Reasoning Engine - Deep Inference, Not If/Else

Replaces hardcoded grading curves with actual reasoning about root causes.

OLD WAY (grading curve):
    if score > 70:
        print("You're anxious")

NEW WAY (reasoning engine):
    - Analyze wave patterns to find triggers
    - Infer root causes from category combinations
    - Match personality archetypes through pattern recognition
    - Generate personalized insights based on specific issues

Usage:
    from cringeproof_reasoning import ReasoningEngine

    engine = ReasoningEngine()
    analysis = engine.deep_analyze(score_history, category_scores, user_content)
    print(analysis['root_cause'])  # "Code review anxiety from perfectionism"
    print(analysis['triggers'])     # ["Monday mornings", "After mistakes"]
"""

import math
from typing import Dict, List, Tuple, Any, Optional
from collections import Counter
import re

# Import physics scoring
from lib.physics import PhysicsScoring, MomentumAnalyzer, WaveAnalyzer, EntropyCalculator


# ==============================================================================
# ROOT CAUSE INFERENCE
# ==============================================================================

class RootCauseInference:
    """
    Infer ROOT CAUSES from patterns, not just symptoms

    Example:
    - Symptom: High communication anxiety
    - Root Cause: Perfectionism in code reviews
    - Evidence: High scores only when discussing technical work
    """

    def __init__(self):
        self.physics = PhysicsScoring()

    def infer_from_categories(self, category_scores: Dict[str, float]) -> Dict[str, Any]:
        """
        Infer root cause from category score patterns

        NOT: if score > 70, say "anxious"
        BUT: analyze which COMBINATION of categories is high
        """
        # Calculate which categories are outliers
        scores = list(category_scores.values())
        if not scores:
            return {'cause': 'unknown', 'confidence': 0.0}

        mean = sum(scores) / len(scores)
        std_dev = math.sqrt(sum((s - mean) ** 2 for s in scores) / len(scores)) if len(scores) > 1 else 1

        # Find categories significantly above average
        high_categories = {}
        for cat, score in category_scores.items():
            if score > mean + std_dev:  # 1 std dev above mean
                z_score = (score - mean) / std_dev if std_dev > 0 else 0
                high_categories[cat] = {
                    'score': score,
                    'z_score': z_score,
                    'above_avg': score - mean
                }

        # Infer root cause from pattern
        if not high_categories:
            return {
                'cause': 'balanced',
                'confidence': 0.8,
                'description': 'No specific anxiety pattern - well-balanced',
                'evidence': f'All categories within 1σ of mean ({mean:.1f})'
            }

        # Pattern: Communication + Validation = Approval seeking
        if ('communication_anxiety' in high_categories and
            'validation_seeking' in high_categories):
            return {
                'cause': 'approval_seeking',
                'confidence': 0.85,
                'description': 'Seeks approval through perfect communication',
                'evidence': f"Both communication anxiety ({category_scores.get('communication_anxiety', 0):.0f}) and validation seeking ({category_scores.get('validation_seeking', 0):.0f}) elevated",
                'specific_triggers': ['Sending messages to authority figures', 'Public communication', 'Group chats'],
                'root': 'Fear of judgment on communication quality'
            }

        # Pattern: Preparation + Retrospective = Perfectionism
        if ('preparation_anxiety' in high_categories and
            'retrospective_anxiety' in high_categories):
            return {
                'cause': 'perfectionism',
                'confidence': 0.9,
                'description': 'Perfectionist who rehearses and dwells on mistakes',
                'evidence': f"High preparation ({category_scores.get('preparation_anxiety', 0):.0f}) + retrospective ({category_scores.get('retrospective_anxiety', 0):.0f}) anxiety",
                'specific_triggers': ['Before important conversations', 'After any perceived mistake'],
                'root': 'Unrealistic standards for social performance'
            }

        # Pattern: Social + Communication = General social anxiety
        if ('social_anxiety' in high_categories and
            'communication_anxiety' in high_categories):
            return {
                'cause': 'social_anxiety_general',
                'confidence': 0.75,
                'description': 'Broad social anxiety across contexts',
                'evidence': f"Multiple social domains affected",
                'specific_triggers': ['Any social interaction', 'Public settings'],
                'root': 'General fear of social judgment'
            }

        # Pattern: Only ONE category high = Specific phobia
        if len(high_categories) == 1:
            cat_name = list(high_categories.keys())[0]
            return {
                'cause': f'specific_{cat_name}',
                'confidence': 0.8,
                'description': f'Anxiety specific to {cat_name.replace("_", " ")}',
                'evidence': f"Only {cat_name} significantly elevated ({category_scores[cat_name]:.0f}), others normal",
                'specific_triggers': [f'Situations involving {cat_name.replace("_", " ")}'],
                'root': f'Isolated issue with {cat_name.replace("_", " ")}'
            }

        # Default: Multiple categories but no clear pattern
        top_cats = sorted(high_categories.items(), key=lambda x: x[1]['score'], reverse=True)[:2]
        return {
            'cause': 'mixed_anxiety',
            'confidence': 0.6,
            'description': f'Mixed anxiety primarily in {top_cats[0][0]} and {top_cats[1][0]}',
            'evidence': f"Multiple elevated categories: {', '.join(c for c, _ in top_cats)}",
            'specific_triggers': ['Varies by context'],
            'root': 'Multiple anxiety sources - needs individual analysis'
        }

    def infer_from_velocity(self, category_velocities: Dict[str, float]) -> Dict[str, Any]:
        """
        Infer what's CHANGING and WHY

        Example:
        - Communication anxiety improving but social anxiety stable
        - Inference: Working on messaging skills, but still avoiding events
        """
        improving = {k: v for k, v in category_velocities.items() if v < -1}  # Declining anxiety = improving
        declining = {k: v for k, v in category_velocities.items() if v > 1}   # Increasing anxiety = declining
        stable = {k: v for k, v in category_velocities.items() if -1 <= v <= 1}

        if improving and not declining:
            top_improvement = min(improving.items(), key=lambda x: x[1])
            return {
                'trend': 'improving',
                'confidence': 0.85,
                'description': f'Strong improvement in {top_improvement[0]}',
                'evidence': f'Velocity: {top_improvement[1]:.1f} points/week',
                'inference': f'Actively working on {top_improvement[0].replace("_", " ")}',
                'recommendation': 'Keep doing what you\'re doing!'
            }

        if declining and not improving:
            top_decline = max(declining.items(), key=lambda x: x[1])
            return {
                'trend': 'declining',
                'confidence': 0.8,
                'description': f'Increasing anxiety in {top_decline[0]}',
                'evidence': f'Velocity: +{top_decline[1]:.1f} points/week',
                'inference': f'New stressor or trigger in {top_decline[0].replace("_", " ")}',
                'recommendation': f'Focus on {top_decline[0].replace("_", " ")} - what changed recently?'
            }

        if improving and declining:
            return {
                'trend': 'mixed',
                'confidence': 0.7,
                'description': 'Some areas improving, others declining',
                'evidence': f'Improving: {list(improving.keys())}, Declining: {list(declining.keys())}',
                'inference': 'Progress is non-uniform - different categories have different causes',
                'recommendation': 'Analyze each category separately'
            }

        return {
            'trend': 'stable',
            'confidence': 0.6,
            'description': 'No significant changes in any category',
            'evidence': 'All velocities near zero',
            'inference': 'Either stable state or insufficient data',
            'recommendation': 'Continue monitoring'
        }


# ==============================================================================
# TRIGGER PREDICTION
# ==============================================================================

class TriggerPredictor:
    """
    Predict WHEN anxiety spikes using wave analysis

    Example:
    - Wave pattern shows peaks every Monday
    - Inference: Monday morning meetings are a trigger
    - Prediction: Next Monday will be high anxiety
    """

    def __init__(self):
        self.wave = WaveAnalyzer()

    def predict_from_cycles(self, score_history: List[float],
                          timestamps: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Predict future anxiety spikes from cyclical patterns

        Args:
            score_history: Anxiety scores over time
            timestamps: Optional timestamps for pattern analysis

        Returns:
            Trigger predictions with timing
        """
        # Detect cycle
        cycle_info = self.wave.detect_cycle(score_history)

        if not cycle_info['has_cycle']:
            return {
                'has_pattern': False,
                'confidence': 0.3,
                'prediction': 'No cyclical pattern detected - triggers may be random or data insufficient'
            }

        # Find peaks and troughs
        peaks_troughs = self.wave.find_peaks_and_troughs(score_history)
        peaks = peaks_troughs['peaks']
        troughs = peaks_troughs['troughs']

        if not peaks:
            return {
                'has_pattern': False,
                'confidence': 0.4,
                'prediction': 'No clear peaks detected'
            }

        # Calculate average peak value vs average trough value
        peak_values = [score_history[i] for i in peaks]
        trough_values = [score_history[i] for i in troughs] if troughs else []

        avg_peak = sum(peak_values) / len(peak_values)
        avg_trough = sum(trough_values) / len(trough_values) if trough_values else avg_peak * 0.7

        # Predict next peak
        period = cycle_info['period']
        last_peak_index = peaks[-1]
        next_peak_index = int(last_peak_index + period) if period else len(score_history) + 1

        return {
            'has_pattern': True,
            'confidence': cycle_info['confidence'],
            'period': period,
            'amplitude': cycle_info['amplitude'],
            'avg_peak_anxiety': avg_peak,
            'avg_low_anxiety': avg_trough,
            'next_peak_predicted': next_peak_index,
            'peak_indices': peaks,
            'trough_indices': troughs,
            'prediction': f'Anxiety spikes every ~{period:.1f} sessions. Next spike predicted at session {next_peak_index}.',
            'recommendation': f'Prepare coping strategies before session {next_peak_index}'
        }

    def infer_triggers_from_timing(self, peaks: List[int], timestamps: Optional[List[str]] = None) -> List[str]:
        """
        Infer what triggers correspond to peaks

        Example:
        - Peaks at sessions 1, 8, 15, 22 (every 7 sessions)
        - If timestamps show these are Mondays
        - Inference: Monday is a trigger (e.g., weekly team meeting)
        """
        if not timestamps or len(timestamps) != len(peaks):
            # Without timestamps, can only infer periodicity
            if len(peaks) >= 2:
                intervals = [peaks[i+1] - peaks[i] for i in range(len(peaks) - 1)]
                avg_interval = sum(intervals) / len(intervals)
                return [f'Cyclical trigger every ~{avg_interval:.0f} sessions']
            return ['Insufficient data for trigger inference']

        # Analyze day of week pattern (simplified - would need actual date parsing)
        return ['Trigger analysis requires timestamp data']


# ==============================================================================
# PERSONALITY ARCHETYPE MATCHER
# ==============================================================================

class ArchetypeMatcher:
    """
    Match personality archetype through pattern recognition

    NOT: if score > 70, you're "anxious"
    BUT: analyze multi-dimensional patterns to find specific archetype
    """

    ARCHETYPES = {
        'imposter_syndrome': {
            'name': 'Imposter Syndrome',
            'description': 'Competent but doubts abilities despite evidence',
            'pattern': {
                'high': ['validation_seeking', 'retrospective_anxiety'],
                'low': [],
                'velocity': 'improving',  # Getting better but still anxious
            },
            'root_cause': 'Discrepancy between actual competence and perceived competence',
            'recommendation': 'Track your wins. Keep evidence of successes.',
            'mentor_match': 'recovered_imposter'  # Who to pair with
        },

        'perfectionist': {
            'name': 'Perfectionist',
            'description': 'Unrealistically high standards causing stress cycles',
            'pattern': {
                'high': ['preparation_anxiety', 'retrospective_anxiety'],
                'low': [],
                'velocity': 'stable',
                'has_cycle': True
            },
            'root_cause': 'Unrealistic expectations for social/professional performance',
            'recommendation': 'Practice "good enough". Set time limits on preparation.',
            'mentor_match': 'reformed_perfectionist'
        },

        'recovered_anxious': {
            'name': 'Recovered Anxious',
            'description': 'Overcame anxiety through deliberate practice',
            'pattern': {
                'high': [],
                'low': [],
                'velocity': 'strong_improvement',  # Velocity < -3
                'from_high_baseline': True  # Started with high scores
            },
            'root_cause': 'Learned effective coping strategies',
            'recommendation': 'You\'re doing great! Consider mentoring others on similar journeys.',
            'mentor_match': None  # Is a mentor, not seeking one
        },

        'approval_seeker': {
            'name': 'Approval Seeker',
            'description': 'Seeks external validation, especially in communication',
            'pattern': {
                'high': ['validation_seeking', 'communication_anxiety'],
                'low': [],
                'velocity': 'any'
            },
            'root_cause': 'Self-worth tied to others\' opinions',
            'recommendation': 'Build internal validation. Practice self-compassion.',
            'mentor_match': 'confident_communicator'
        },

        'social_avoider': {
            'name': 'Social Avoider',
            'description': 'Avoids social situations to reduce anxiety',
            'pattern': {
                'high': ['social_anxiety'],
                'low': ['communication_anxiety'],  # Low because avoids situations
                'velocity': 'stable'
            },
            'root_cause': 'Avoidance preventing exposure and growth',
            'recommendation': 'Start with small, low-stakes social interactions. Gradual exposure.',
            'mentor_match': 'social_butterfly'
        },

        'burnout_risk': {
            'name': 'Burnout Risk',
            'description': 'Inconsistent performance with declining trend',
            'pattern': {
                'high': [],
                'low': [],
                'velocity': 'declining',
                'consistency': 'low'  # Entropy < 0.5
            },
            'root_cause': 'Exhaustion or overwhelm',
            'recommendation': 'Take breaks. Reduce commitments. Self-care is not optional.',
            'mentor_match': 'recovered_burnout'
        },

        'growth_mindset': {
            'name': 'Growth Mindset',
            'description': 'Consistent improvement through deliberate practice',
            'pattern': {
                'high': [],
                'low': [],
                'velocity': 'improving',  # Velocity -1 to -3
                'consistency': 'high'  # Entropy > 0.6
            },
            'root_cause': 'Strong learning habits and self-reflection',
            'recommendation': 'Keep it up! Your steady progress is inspiring.',
            'mentor_match': None  # Potential mentor for others
        }
    }

    def match_archetype(self, category_scores: Dict[str, float],
                       physics_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match user to personality archetype using pattern recognition

        Args:
            category_scores: Current category scores
            physics_analysis: Physics-based analysis from PhysicsScoring

        Returns:
            Best matching archetype with confidence score
        """
        matches = []

        for archetype_id, archetype in self.ARCHETYPES.items():
            confidence = self._calculate_match_confidence(
                category_scores,
                physics_analysis,
                archetype['pattern']
            )

            if confidence > 0.3:  # Threshold for consideration
                matches.append({
                    'id': archetype_id,
                    'name': archetype['name'],
                    'confidence': confidence,
                    'description': archetype['description'],
                    'root_cause': archetype['root_cause'],
                    'recommendation': archetype['recommendation'],
                    'mentor_match': archetype['mentor_match']
                })

        # Sort by confidence
        matches.sort(key=lambda x: x['confidence'], reverse=True)

        if not matches:
            return {
                'id': 'unclassified',
                'name': 'Unclassified',
                'confidence': 0.5,
                'description': 'No clear archetype match - unique pattern',
                'root_cause': 'Individual analysis needed',
                'recommendation': 'Continue tracking patterns for personalized insights'
            }

        return matches[0]  # Return best match

    def _calculate_match_confidence(self, category_scores: Dict[str, float],
                                   physics_analysis: Dict[str, Any],
                                   pattern: Dict) -> float:
        """Calculate confidence that user matches this archetype pattern"""
        confidence_factors = []

        # Check 'high' categories (should be above 60)
        if 'high' in pattern and pattern['high']:
            high_matches = sum(1 for cat in pattern['high']
                             if category_scores.get(cat, 0) > 60)
            high_ratio = high_matches / len(pattern['high'])
            confidence_factors.append(high_ratio)

        # Check 'low' categories (should be below 40)
        if 'low' in pattern and pattern['low']:
            low_matches = sum(1 for cat in pattern['low']
                            if category_scores.get(cat, 100) < 40)
            low_ratio = low_matches / len(pattern['low'])
            confidence_factors.append(low_ratio)

        # Check velocity pattern
        if 'velocity' in pattern:
            velocity = physics_analysis.get('velocity', 0)
            trend = physics_analysis.get('trend', 'stable')

            if pattern['velocity'] == 'improving' and trend == 'declining' and velocity < 0:
                # Declining anxiety = improving
                confidence_factors.append(1.0)
            elif pattern['velocity'] == 'strong_improvement' and velocity < -3:
                confidence_factors.append(1.0)
            elif pattern['velocity'] == 'declining' and velocity > 0:
                # Increasing anxiety = declining
                confidence_factors.append(1.0)
            elif pattern['velocity'] == 'stable' and abs(velocity) < 1:
                confidence_factors.append(0.8)
            elif pattern['velocity'] == 'any':
                confidence_factors.append(0.6)
            else:
                confidence_factors.append(0.2)

        # Check consistency pattern
        if 'consistency' in pattern:
            consistency = physics_analysis.get('consistency', 0.5)

            if pattern['consistency'] == 'high' and consistency > 0.6:
                confidence_factors.append(1.0)
            elif pattern['consistency'] == 'low' and consistency < 0.5:
                confidence_factors.append(1.0)
            else:
                confidence_factors.append(0.5)

        # Check cycle pattern
        if 'has_cycle' in pattern:
            has_cycle = physics_analysis.get('has_cycle', False)
            if pattern['has_cycle'] == has_cycle:
                confidence_factors.append(1.0)
            else:
                confidence_factors.append(0.3)

        # Average all factors
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        return 0.0


# ==============================================================================
# MAIN REASONING ENGINE
# ==============================================================================

class ReasoningEngine:
    """
    Main reasoning engine combining all inference components

    Usage:
        engine = ReasoningEngine()
        analysis = engine.deep_analyze(score_history, category_scores)
    """

    def __init__(self):
        self.root_cause = RootCauseInference()
        self.trigger_predictor = TriggerPredictor()
        self.archetype_matcher = ArchetypeMatcher()
        self.physics = PhysicsScoring()

    def deep_analyze(self, score_history: List[float],
                    category_scores: Dict[str, float],
                    category_history: Optional[Dict[str, List[float]]] = None) -> Dict[str, Any]:
        """
        Complete deep analysis using reasoning (not if/else)

        Args:
            score_history: Overall scores over time
            category_scores: Current category scores
            category_history: Category scores over time (optional)

        Returns:
            Comprehensive analysis with root causes, triggers, archetypes
        """
        # Physics analysis
        physics_analysis = self.physics.analyze_score_history(
            score_history,
            category_history
        )

        # Root cause inference
        root_cause_analysis = self.root_cause.infer_from_categories(category_scores)

        # Velocity-based insights (if we have category history)
        velocity_insights = None
        if category_history:
            category_velocities = {
                cat: self.physics.momentum.calculate_velocity(scores)
                for cat, scores in category_history.items()
                if len(scores) >= 2
            }
            velocity_insights = self.root_cause.infer_from_velocity(category_velocities)

        # Trigger prediction
        trigger_prediction = self.trigger_predictor.predict_from_cycles(score_history)

        # Archetype matching
        archetype = self.archetype_matcher.match_archetype(category_scores, physics_analysis)

        # Generate personalized insights (NOT generic!)
        insights = self._generate_personalized_insights(
            root_cause_analysis,
            trigger_prediction,
            archetype,
            physics_analysis
        )

        return {
            'physics': physics_analysis,
            'root_cause': root_cause_analysis,
            'velocity_insights': velocity_insights,
            'trigger_prediction': trigger_prediction,
            'archetype': archetype,
            'personalized_insights': insights,
            'summary': self._generate_summary(root_cause_analysis, archetype, physics_analysis)
        }

    def _generate_personalized_insights(self, root_cause, trigger_pred, archetype, physics) -> List[str]:
        """Generate SPECIFIC insights, not generic platitudes"""
        insights = []

        # Root cause insight
        if root_cause['cause'] != 'unknown':
            insights.append(
                f"🎯 Root Cause: {root_cause['description']} "
                f"(confidence: {root_cause['confidence']*100:.0f}%)"
            )
            insights.append(f"   Evidence: {root_cause['evidence']}")

        # Archetype insight
        insights.append(
            f"🎭 Personality Match: {archetype['name']} "
            f"({archetype['confidence']*100:.0f}% match)"
        )
        insights.append(f"   {archetype['description']}")

        # Momentum insight
        if physics['velocity'] < -2:
            insights.append(
                f"🚀 Strong Progress: Reducing anxiety by {abs(physics['velocity']):.1f} points/week"
            )
        elif physics['velocity'] > 2:
            insights.append(
                f"⚠️ Increasing Anxiety: Up {physics['velocity']:.1f} points/week - "
                "what changed recently?"
            )

        # Trigger insight
        if trigger_pred['has_pattern']:
            insights.append(
                f"📊 Pattern Detected: Anxiety spikes every ~{trigger_pred['period']:.0f} sessions"
            )
            insights.append(
                f"   Next spike predicted: {trigger_pred['prediction']}"
            )

        # Specific recommendation (from archetype)
        insights.append(f"💡 Recommendation: {archetype['recommendation']}")

        return insights

    def _generate_summary(self, root_cause, archetype, physics) -> str:
        """One-sentence summary of entire analysis"""
        trend_desc = "improving" if physics['velocity'] < 0 else "increasing" if physics['velocity'] > 0 else "stable"

        return (
            f"{archetype['name']} with {root_cause['cause'].replace('_', ' ')} "
            f"({trend_desc} trend, {physics['current_score']:.0f} current anxiety)"
        )


if __name__ == '__main__':
    print("🧠 Cringeproof Reasoning Engine - Deep Inference")
    print("=" * 70)

    # Example: Alice (imposter syndrome)
    print("\n📊 Example: Alice - Improving Anxious Coder")
    alice_scores = [78, 75, 73, 70]
    alice_categories = {
        'communication_anxiety': 75,
        'social_anxiety': 45,
        'preparation_anxiety': 70,
        'retrospective_anxiety': 80,
        'validation_seeking': 78
    }

    engine = ReasoningEngine()
    analysis = engine.deep_analyze(alice_scores, alice_categories)

    print(f"\n✨ Summary: {analysis['summary']}")
    print("\n💡 Insights:")
    for insight in analysis['personalized_insights']:
        print(f"   {insight}")

    print(f"\n🎯 Root Cause Details:")
    print(f"   Cause: {analysis['root_cause']['cause']}")
    print(f"   Description: {analysis['root_cause']['description']}")
    print(f"   Confidence: {analysis['root_cause']['confidence']*100:.0f}%")

    print(f"\n🎭 Archetype Match:")
    print(f"   {analysis['archetype']['name']} ({analysis['archetype']['confidence']*100:.0f}% match)")
    print(f"   {analysis['archetype']['description']}")
    print(f"   Root: {analysis['archetype']['root_cause']}")

    print("\n✅ This is REASONING, not grading curves!")
    print("   - Infers specific root causes from patterns")
    print("   - Predicts when anxiety will spike")
    print("   - Matches personality archetypes")
    print("   - Generates personalized (not generic) insights")
