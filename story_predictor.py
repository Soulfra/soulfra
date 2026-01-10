#!/usr/bin/env python3
"""
Story Predictor - AI predicts what happens next in real-time stories

Reverse WPM: Instead of measuring typing speed, we measure how unpredictable you are.
The more the AI fails to predict your story, the higher your score.

Usage:
    from story_predictor import StoryPredictor

    predictor = StoryPredictor()
    prediction = predictor.predict_next_segment(story_so_far)
    # User writes actual next segment
    score = predictor.score_prediction(prediction, actual_segment)
"""

import ollama
from datetime import datetime
from typing import Dict, List, Optional
import json
import re
from difflib import SequenceMatcher


class StoryPredictor:
    """
    AI predicts next story segment using multiple models
    """

    def __init__(self, models: List[str] = None):
        """
        Initialize with Ollama models

        Args:
            models: List of model names to use for predictions
        """
        if models is None:
            # Default to best narrative models
            self.models = [
                'mistral:latest',           # Great at creative writing
                'soulfra-model:latest',     # Authentic storytelling
                'deathtodata-model:latest'  # Plot twists and surprises
            ]
        else:
            self.models = models

        # Check which models are available
        try:
            available = ollama.list()
            available_names = [m['name'] for m in available.get('models', [])]
            self.models = [m for m in self.models if any(m.split(':')[0] in name for name in available_names)]

            if not self.models:
                print("⚠️  No target models available. Using first available model.")
                self.models = [available_names[0]] if available_names else []
        except Exception as e:
            print(f"⚠️  Could not list models: {e}")

    def predict_next_segment(
        self,
        story_so_far: str,
        genre: str = "general",
        length: str = "paragraph"  # 'sentence', 'paragraph', 'scene'
    ) -> Dict:
        """
        Predict what happens next in the story

        Args:
            story_so_far: The story text up to this point
            genre: Story genre (drama, thriller, comedy, etc.)
            length: How much to predict (sentence, paragraph, scene)

        Returns:
            {
                'predictions': [{'model': str, 'text': str, 'confidence': float}, ...],
                'consensus': str,  # Most likely prediction
                'confidence': float,  # 0-1 how confident AI is
                'timestamp': str
            }
        """
        if not self.models:
            return {
                'error': 'No models available',
                'predictions': [],
                'consensus': '',
                'confidence': 0.0,
                'timestamp': datetime.now().isoformat()
            }

        print(f"\n🔮 Predicting next {length} for {genre} story...")
        print(f"📖 Story so far ({len(story_so_far)} chars)")

        # Determine how much to predict
        length_instructions = {
            'sentence': 'one sentence (10-20 words)',
            'paragraph': 'one paragraph (50-100 words)',
            'scene': 'a complete scene (200-300 words)'
        }

        length_guide = length_instructions.get(length, length_instructions['paragraph'])

        # Build prompt for prediction
        system_prompt = f"""You are a master storyteller analyzing a {genre} story in progress.

Your task: Predict EXACTLY what happens next in the story.

Story so far:
{story_so_far}

Predict the next {length_guide} that the storyteller will write.
Be specific and creative. Think about:
- Character motivations and arcs
- Plot momentum and tension
- Genre conventions
- Narrative patterns
- Foreshadowing and setup

Output ONLY your prediction. No preamble, no explanation."""

        predictions = []

        # Get predictions from each model
        for model in self.models:
            try:
                print(f"🤖 Asking {model}...")

                response = ollama.chat(
                    model=model,
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': 'What happens next?'}
                    ]
                )

                prediction_text = response['message']['content'].strip()

                # Estimate confidence based on response length and specificity
                confidence = self._estimate_confidence(prediction_text, length)

                predictions.append({
                    'model': model,
                    'text': prediction_text,
                    'confidence': confidence,
                    'timestamp': datetime.now().isoformat()
                })

                print(f"✅ {model}: {prediction_text[:80]}..." if len(prediction_text) > 80 else f"✅ {model}: {prediction_text}")

            except Exception as e:
                print(f"❌ Error with {model}: {e}")
                continue

        if not predictions:
            return {
                'error': 'All models failed',
                'predictions': [],
                'consensus': '',
                'confidence': 0.0,
                'timestamp': datetime.now().isoformat()
            }

        # Find consensus prediction (model with highest confidence)
        best_prediction = max(predictions, key=lambda p: p['confidence'])

        # Calculate overall confidence (average of all models)
        avg_confidence = sum(p['confidence'] for p in predictions) / len(predictions)

        result = {
            'predictions': predictions,
            'consensus': best_prediction['text'],
            'consensus_model': best_prediction['model'],
            'confidence': avg_confidence,
            'timestamp': datetime.now().isoformat()
        }

        print(f"\n📊 Consensus prediction (confidence: {avg_confidence:.1%}):")
        print(f"   {result['consensus'][:150]}..." if len(result['consensus']) > 150 else f"   {result['consensus']}")

        return result

    def _estimate_confidence(self, prediction: str, expected_length: str) -> float:
        """
        Estimate AI's confidence in its prediction

        Args:
            prediction: The prediction text
            expected_length: Expected length (sentence, paragraph, scene)

        Returns:
            Confidence score 0-1
        """
        # Base confidence on length match
        word_count = len(prediction.split())

        target_ranges = {
            'sentence': (10, 20),
            'paragraph': (50, 100),
            'scene': (200, 300)
        }

        target_min, target_max = target_ranges.get(expected_length, (50, 100))

        # Confidence based on length appropriateness
        if target_min <= word_count <= target_max:
            length_score = 1.0
        elif word_count < target_min:
            length_score = word_count / target_min
        else:  # word_count > target_max
            length_score = target_max / word_count

        # Confidence based on specificity (presence of names, details, dialogue)
        specificity_score = 0.5  # Base

        # Check for specific details
        if re.search(r'"[^"]+"', prediction):  # Has dialogue
            specificity_score += 0.2
        if re.search(r'\b[A-Z][a-z]+\b', prediction):  # Has proper nouns
            specificity_score += 0.15
        if any(word in prediction.lower() for word in ['suddenly', 'then', 'next', 'after']):
            specificity_score += 0.15

        # Combine scores
        confidence = (length_score * 0.4) + (min(specificity_score, 1.0) * 0.6)

        return min(confidence, 1.0)

    def score_prediction(
        self,
        prediction: str,
        actual: str,
        method: str = "similarity"
    ) -> Dict:
        """
        Score how accurate the prediction was

        Args:
            prediction: What AI predicted
            actual: What actually happened
            method: Scoring method ('similarity', 'semantic', 'surprise')

        Returns:
            {
                'accuracy': float,  # 0-1 how accurate
                'unpredictability': float,  # 0-1 how unpredictable (inverse of accuracy)
                'surprise_factor': float,  # 0-1 how surprising actual was
                'method': str
            }
        """
        if method == "similarity":
            # Simple text similarity using SequenceMatcher
            similarity = SequenceMatcher(None, prediction.lower(), actual.lower()).ratio()

            return {
                'accuracy': similarity,
                'unpredictability': 1.0 - similarity,
                'surprise_factor': 1.0 - similarity,
                'method': 'similarity',
                'details': {
                    'predicted_length': len(prediction.split()),
                    'actual_length': len(actual.split()),
                    'text_similarity': similarity
                }
            }

        elif method == "semantic":
            # Use AI to judge semantic similarity
            return self._score_semantic(prediction, actual)

        elif method == "surprise":
            # Focus on narrative surprise elements
            return self._score_surprise(prediction, actual)

        else:
            raise ValueError(f"Unknown scoring method: {method}")

    def _score_semantic(self, prediction: str, actual: str) -> Dict:
        """
        Use AI to judge semantic similarity between prediction and actual
        """
        if not self.models:
            # Fall back to similarity
            return self.score_prediction(prediction, actual, method="similarity")

        prompt = f"""Compare these two story segments and rate their semantic similarity on a scale of 0-100.

Prediction: {prediction}

Actual: {actual}

Consider:
- Similar events happening?
- Same characters involved?
- Similar emotional tone?
- Same plot direction?

Output ONLY a number between 0-100. No explanation."""

        try:
            response = ollama.chat(
                model=self.models[0],
                messages=[{'role': 'user', 'content': prompt}]
            )

            # Extract number from response
            score_text = response['message']['content'].strip()
            score = float(re.search(r'\d+', score_text).group())
            accuracy = min(score / 100.0, 1.0)

            return {
                'accuracy': accuracy,
                'unpredictability': 1.0 - accuracy,
                'surprise_factor': 1.0 - accuracy,
                'method': 'semantic',
                'details': {
                    'semantic_score': score,
                    'ai_model': self.models[0]
                }
            }

        except Exception as e:
            print(f"⚠️  Semantic scoring failed: {e}")
            # Fall back to similarity
            return self.score_prediction(prediction, actual, method="similarity")

    def _score_surprise(self, prediction: str, actual: str) -> Dict:
        """
        Score based on narrative surprise elements
        """
        # Check for surprise elements in actual vs prediction
        surprise_keywords = [
            'suddenly', 'unexpectedly', 'shock', 'surprise', 'twist',
            'but', 'however', 'instead', 'never', 'impossible'
        ]

        actual_lower = actual.lower()
        prediction_lower = prediction.lower()

        # Count surprise keywords
        actual_surprises = sum(1 for kw in surprise_keywords if kw in actual_lower)
        predicted_surprises = sum(1 for kw in surprise_keywords if kw in prediction_lower)

        # If actual has more surprises, it's more unpredictable
        surprise_ratio = actual_surprises / max(predicted_surprises + 1, 1)
        surprise_factor = min(surprise_ratio, 1.0)

        # Also check text similarity
        similarity = SequenceMatcher(None, prediction_lower, actual_lower).ratio()

        # Combine: low similarity + high surprise = high unpredictability
        unpredictability = (1.0 - similarity) * 0.6 + surprise_factor * 0.4

        return {
            'accuracy': 1.0 - unpredictability,
            'unpredictability': unpredictability,
            'surprise_factor': surprise_factor,
            'method': 'surprise',
            'details': {
                'actual_surprises': actual_surprises,
                'predicted_surprises': predicted_surprises,
                'text_similarity': similarity
            }
        }

    def calculate_reverse_wpm(
        self,
        story_segments: List[Dict],
        time_elapsed: float
    ) -> Dict:
        """
        Calculate "Reverse WPM" - Unpredictability Per Minute

        Args:
            story_segments: List of {prediction, actual, score} dicts
            time_elapsed: Total time in seconds

        Returns:
            {
                'reverse_wpm': float,  # Unpredictability score per minute
                'total_unpredictability': float,
                'avg_unpredictability': float,
                'segments': int
            }
        """
        if not story_segments:
            return {
                'reverse_wpm': 0.0,
                'total_unpredictability': 0.0,
                'avg_unpredictability': 0.0,
                'segments': 0
            }

        # Sum all unpredictability scores
        total_unpredictability = sum(
            seg.get('score', {}).get('unpredictability', 0)
            for seg in story_segments
        )

        # Average unpredictability
        avg_unpredictability = total_unpredictability / len(story_segments)

        # Unpredictability per minute
        minutes = time_elapsed / 60.0
        reverse_wpm = total_unpredictability / max(minutes, 0.1)  # Avoid division by zero

        return {
            'reverse_wpm': reverse_wpm,
            'total_unpredictability': total_unpredictability,
            'avg_unpredictability': avg_unpredictability,
            'segments': len(story_segments),
            'time_minutes': minutes
        }


def main():
    """Demo the story predictor"""
    predictor = StoryPredictor()

    # Example story
    story = """Sarah walked into the coffee shop on a rainy Tuesday morning.
She ordered her usual latte and sat by the window, watching droplets race down the glass."""

    print("=" * 60)
    print("📖 STORY PREDICTOR DEMO")
    print("=" * 60)

    # Get prediction
    result = predictor.predict_next_segment(story, genre="drama", length="paragraph")

    print("\n" + "=" * 60)
    print("🎯 AI PREDICTIONS:")
    print("=" * 60)
    for pred in result['predictions']:
        print(f"\n{pred['model']} (confidence: {pred['confidence']:.1%}):")
        print(f"{pred['text']}")

    # Simulate actual next segment
    actual = """A stranger sat down across from her without asking.
"I know what you did last summer," he said quietly, sliding a photograph across the table."""

    print("\n" + "=" * 60)
    print("✍️  ACTUAL NEXT SEGMENT:")
    print("=" * 60)
    print(actual)

    # Score the prediction
    score = predictor.score_prediction(result['consensus'], actual, method="surprise")

    print("\n" + "=" * 60)
    print("📊 PREDICTION SCORE:")
    print("=" * 60)
    print(f"Accuracy: {score['accuracy']:.1%}")
    print(f"Unpredictability: {score['unpredictability']:.1%}")
    print(f"Surprise Factor: {score['surprise_factor']:.1%}")
    print(f"Method: {score['method']}")

    # Calculate reverse WPM
    segments = [
        {'prediction': result['consensus'], 'actual': actual, 'score': score}
    ]
    reverse_wpm = predictor.calculate_reverse_wpm(segments, time_elapsed=120)  # 2 minutes

    print("\n" + "=" * 60)
    print("🏆 REVERSE WPM SCORE:")
    print("=" * 60)
    print(f"Reverse WPM: {reverse_wpm['reverse_wpm']:.2f}")
    print(f"Avg Unpredictability: {reverse_wpm['avg_unpredictability']:.1%}")
    print()
    print("💡 Higher Reverse WPM = More Unpredictable = Better Storyteller!")


if __name__ == '__main__':
    main()
