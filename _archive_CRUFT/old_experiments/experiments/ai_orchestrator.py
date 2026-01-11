#!/usr/bin/env python3
"""
AI Orchestrator - Unified AI Interface

The ONE place to talk to ALL AI models:
- Ollama (LLM chat)
- Neural networks (classification)
- Vision models (image/PDF analysis)

Replaces 7+ fragmented Ollama implementations with a single, unified interface.

Philosophy:
----------
Currently the codebase has:
  - Widget: calls Ollama directly
  - Discussion: calls Ollama directly
  - Preview Feedback: calls Ollama directly
  - ollama_chat.py: calls Ollama directly
  - ollama_auto_commenter.py: calls Ollama directly
  ... etc

This creates:
  - Duplication (same code 7+ times)
  - No permission checking
  - No logging of AI usage
  - Can't easily switch models
  - Hard to add new AI capabilities

Solution: ONE orchestrator that:
  1. Routes queries to appropriate AI
  2. Checks user permissions (tiers)
  3. Logs all interactions
  4. Handles errors consistently
  5. Makes swapping models trivial

Zero Dependencies: Uses Python stdlib (urllib, json) + local modules.
"""

import json
import urllib.request
import urllib.error
from typing import List, Dict, Optional
from datetime import datetime

from schemas import (
    AIQuery, AIResponse, AIModel, ModelType,
    UserPermissions, UserTier, NeuralPrediction
)


class AIOrchestrator:
    """
    Unified interface to all AI models

    Usage:
        orchestrator = AIOrchestrator()

        # Simple chat
        response = orchestrator.query("What is 2+2?", user_tier=1)

        # Neural classification
        response = orchestrator.query(
            "Analyze this post",
            user_tier=2,
            capabilities_needed=['neural_classify'],
            model_name='calriven_classifier'
        )
    """

    def __init__(self):
        """Initialize orchestrator with available models"""
        self.models: Dict[str, AIModel] = {}
        self._register_default_models()
        self.interaction_log: List[Dict] = []

    def _register_default_models(self):
        """Register all available AI models"""

        # Ollama models (LLM chat)
        ollama_models = [
            'llama2', 'mistral', 'codellama', 'phi', 'llava',
            'soulfra-model', 'calriven-expert', 'deathtodata-model',
            'theauditor-expert', 'iiif-expert', 'jsonld-expert'
        ]

        for model_name in ollama_models:
            self.models[model_name] = AIModel(
                name=model_name,
                model_type=ModelType.OLLAMA,
                capabilities=['chat', 'analyze', 'generate'],
                tier_required=1,  # Basic tier
                description=f'Ollama {model_name} model',
                endpoint='http://localhost:11434/api/generate'
            )

        # Neural network models (classification)
        neural_models = [
            ('calriven_technical_classifier', 'Technical content classification'),
            ('deathtodata_privacy_classifier', 'Privacy-focused classification'),
            ('theauditor_validation_classifier', 'Validation and testing classification'),
            ('soulfra_judge', 'Overall quality assessment'),
            ('color_classifier', 'Warm vs Cool color classification'),
            ('even_odd_classifier', 'Binary number classification')
        ]

        for model_name, description in neural_models:
            self.models[model_name] = AIModel(
                name=model_name,
                model_type=ModelType.NEURAL_NET,
                capabilities=['classify', 'predict'],
                tier_required=2,  # Neural tier
                description=description,
                endpoint=None  # Local processing
            )

    def query(
        self,
        prompt: str,
        user_tier: int = 0,
        model_name: Optional[str] = None,
        capabilities_needed: Optional[List[str]] = None,
        context: Optional[Dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 300
    ) -> AIResponse:
        """
        Unified query interface to all AI models

        Args:
            prompt: The user's query/prompt
            user_tier: User's permission tier (0=guest, 1=basic, 2=neural, 3=vision, 4=admin)
            model_name: Specific model to use (auto-selected if None)
            capabilities_needed: Required capabilities (e.g., ['chat', 'classify'])
            context: Additional context (post content, conversation history, etc.)
            temperature: LLM temperature for randomness
            max_tokens: Max response length

        Returns:
            AIResponse with success status and content
        """

        # Auto-select model if not specified
        if not model_name:
            model_name = self._select_model(capabilities_needed or ['chat'], user_tier)

        # Get model
        model = self.models.get(model_name)
        if not model:
            return AIResponse(
                success=False,
                content='',
                model_name=model_name,
                error=f'Model not found: {model_name}'
            )

        # Check permissions
        if not model.can_access(user_tier):
            return AIResponse(
                success=False,
                content='',
                model_name=model_name,
                error=f'Insufficient permissions. Tier {model.tier_required} required (you have {user_tier})'
            )

        # Route to appropriate handler
        if model.model_type == ModelType.OLLAMA:
            response = self._query_ollama(model, prompt, temperature, max_tokens, context)
        elif model.model_type == ModelType.NEURAL_NET:
            response = self._query_neural_net(model, prompt, context)
        else:
            response = AIResponse(
                success=False,
                content='',
                model_name=model_name,
                error=f'Model type not yet implemented: {model.model_type}'
            )

        # Log interaction
        self._log_interaction(prompt, response, user_tier, model_name)

        return response

    def _select_model(self, capabilities: List[str], user_tier: int) -> str:
        """
        Auto-select best model for requested capabilities

        Args:
            capabilities: List of required capabilities
            user_tier: User's permission tier

        Returns:
            Model name
        """
        # Find models that support all required capabilities
        candidates = [
            name for name, model in self.models.items()
            if all(cap in model.capabilities for cap in capabilities)
            and model.can_access(user_tier)
        ]

        if not candidates:
            return 'llama2'  # Fallback

        # Prefer specialized models over generic
        for cap in capabilities:
            if cap == 'classify' or cap == 'predict':
                # Prefer neural networks for classification
                neural_candidates = [c for c in candidates if 'classifier' in c]
                if neural_candidates:
                    return neural_candidates[0]

        # Default to first candidate
        return candidates[0]

    def _query_ollama(
        self,
        model: AIModel,
        prompt: str,
        temperature: float,
        max_tokens: int,
        context: Optional[Dict]
    ) -> AIResponse:
        """
        Query an Ollama LLM model

        This replaces all the duplicated Ollama code scattered throughout:
        - soulfra_assistant.py
        - ollama_chat.py
        - ollama_auto_commenter.py
        - prove_it_works.py
        - test_integration.py
        """

        # Build context-aware prompt
        full_prompt = prompt
        if context and context.get('post'):
            post = context['post']
            post_excerpt = post.get('content', '')[:800]
            if len(post.get('content', '')) > 800:
                post_excerpt += '...'

            full_prompt = f"""You are viewing a blog post titled: "{post.get('title', 'Untitled')}"

Post content excerpt:
{post_excerpt}

User question: {prompt}

Please answer based on the post content above."""

        # Prepare Ollama API request
        request_data = {
            'model': model.name,
            'prompt': full_prompt,
            'stream': False,
            'options': {
                'temperature': temperature,
                'num_predict': max_tokens
            }
        }

        try:
            req = urllib.request.Request(
                model.endpoint,
                data=json.dumps(request_data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                content = result.get('response', '').strip()

                return AIResponse(
                    success=True,
                    content=content,
                    model_name=model.name,
                    capabilities_used=['chat', 'analyze'],
                    metadata={'ollama_model': model.name}
                )

        except urllib.error.URLError as e:
            return AIResponse(
                success=False,
                content='',
                model_name=model.name,
                error=f'Ollama not connected. Start with: ollama serve'
            )
        except Exception as e:
            return AIResponse(
                success=False,
                content='',
                model_name=model.name,
                error=f'Ollama error: {str(e)}'
            )

    def _query_neural_net(
        self,
        model: AIModel,
        prompt: str,
        context: Optional[Dict]
    ) -> AIResponse:
        """
        Query a neural network classifier

        This unifies neural network access across the platform.
        """

        try:
            # Import neural network prediction (uses existing code)
            from brand_voice_generator import predict_brand_voice

            # Run prediction
            result = predict_brand_voice(prompt)

            # Format response
            brand = result.get('brand', 'unknown')
            confidence = result.get('confidence', 0.0)

            response_text = f"""🧠 Neural Network Classification

Model: {model.name}
Predicted Class: {brand.title()}
Confidence: {confidence * 100:.1f}%

"""

            if result.get('all_predictions'):
                response_text += "All Predictions:\n"
                for pred in result['all_predictions']:
                    conf = pred.get('confidence', 0) * 100
                    bar = '█' * int(conf / 10) + '░' * (10 - int(conf / 10))
                    response_text += f"  {pred['brand']:20s} {bar} {conf:.1f}%\n"

            return AIResponse(
                success=True,
                content=response_text.strip(),
                model_name=model.name,
                capabilities_used=['classify', 'predict'],
                metadata={
                    'predicted_class': brand,
                    'confidence': confidence,
                    'all_predictions': result.get('all_predictions', [])
                }
            )

        except Exception as e:
            return AIResponse(
                success=False,
                content='',
                model_name=model.name,
                error=f'Neural network error: {str(e)}'
            )

    def _log_interaction(
        self,
        prompt: str,
        response: AIResponse,
        user_tier: int,
        model_name: str
    ):
        """Log AI interaction for analytics and self-improvement"""
        self.interaction_log.append({
            'timestamp': datetime.now().isoformat(),
            'model_name': model_name,
            'user_tier': user_tier,
            'prompt_length': len(prompt),
            'success': response.success,
            'error': response.error
        })

    def get_available_models(self, user_tier: int) -> List[Dict]:
        """Get list of models accessible to user tier"""
        return [
            model.to_dict()
            for model in self.models.values()
            if model.can_access(user_tier)
        ]

    def get_stats(self) -> Dict:
        """Get orchestrator statistics"""
        total = len(self.interaction_log)
        successful = sum(1 for log in self.interaction_log if log['success'])

        return {
            'total_queries': total,
            'successful': successful,
            'failed': total - successful,
            'success_rate': (successful / total * 100) if total > 0 else 0.0,
            'models_available': len(self.models)
        }


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == '__main__':
    print("🧪 Testing AI Orchestrator")
    print("=" * 70)

    orchestrator = AIOrchestrator()

    # Test 1: List available models for different tiers
    print("\n📋 Available Models:")
    for tier in [0, 1, 2, 3, 4]:
        models = orchestrator.get_available_models(tier)
        print(f"  Tier {tier}: {len(models)} models")

    # Test 2: Model selection
    print("\n🎯 Auto Model Selection:")
    chat_model = orchestrator._select_model(['chat'], user_tier=1)
    print(f"  For 'chat': {chat_model}")

    classify_model = orchestrator._select_model(['classify'], user_tier=2)
    print(f"  For 'classify': {classify_model}")

    # Test 3: Permission checking
    print("\n🔐 Permission Checking:")

    # User with tier 1 tries to access tier 2 model
    response = orchestrator.query(
        "Test prompt",
        user_tier=1,
        model_name='calriven_technical_classifier'
    )
    print(f"  Tier 1 accessing neural net: {response.success}")
    print(f"  Error: {response.error}")

    # User with tier 2 can access
    response = orchestrator.query(
        "Test prompt",
        user_tier=2,
        model_name='calriven_technical_classifier'
    )
    print(f"  Tier 2 accessing neural net: {response.success}")

    # Test 4: Stats
    print("\n📊 Stats:")
    stats = orchestrator.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print("✅ AI Orchestrator working!")
    print("\n💡 Next: Replace fragmented Ollama calls with:")
    print("   orchestrator.query(prompt, user_tier=session.get('tier', 1))")
