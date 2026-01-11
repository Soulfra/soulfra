#!/usr/bin/env python3
"""
Soulfra Schema Definitions - Single Source of Truth

Defines all data structures used across the platform.
Replaces hardcoded dicts with typed, validated structures.

Philosophy:
----------
Instead of passing dicts around like:
  {"sender": "user", "content": "hello", "timestamp": "..."}

We use typed dataclasses:
  Message(sender="user", content="hello", timestamp=datetime.now())

Benefits:
- Type safety
- Auto-completion in IDEs
- Clear documentation
- Validation at creation time
- No more KeyError surprises

Zero Dependencies: Uses Python stdlib dataclasses only.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum


# ==============================================================================
# MESSAGE SCHEMAS
# ==============================================================================

@dataclass
class Message:
    """Universal message structure for all chat/discussion systems"""
    sender: str  # 'user', 'ai', 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    message_type: str = 'chat'  # 'chat', 'command', 'system'
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        """Convert to dict for database storage"""
        return {
            'sender': self.sender,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'message_type': self.message_type,
            'metadata': self.metadata
        }

    @staticmethod
    def from_dict(data: dict) -> 'Message':
        """Create Message from dict"""
        return Message(
            sender=data['sender'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']) if isinstance(data['timestamp'], str) else data['timestamp'],
            message_type=data.get('message_type', 'chat'),
            metadata=data.get('metadata')
        )


@dataclass
class ConversationContext:
    """Context for an ongoing conversation"""
    session_id: Optional[int] = None
    post_id: Optional[int] = None
    post: Optional[Dict[str, Any]] = None
    user_id: Optional[int] = None
    url: str = '/'

    def to_dict(self) -> dict:
        return {
            'session_id': self.session_id,
            'post_id': self.post_id,
            'post': self.post,
            'user_id': self.user_id,
            'url': self.url
        }


# ==============================================================================
# AI MODEL SCHEMAS
# ==============================================================================

class ModelType(Enum):
    """Types of AI models available"""
    OLLAMA = 'ollama'
    NEURAL_NET = 'neural_net'
    VISION = 'vision'
    HYBRID = 'hybrid'


@dataclass
class AIModel:
    """Represents an AI model (Ollama, neural net, vision, etc.)"""
    name: str
    model_type: ModelType
    capabilities: List[str]  # e.g., ['chat', 'classify', 'analyze_image']
    tier_required: int = 0  # Minimum user tier to access
    description: str = ''
    endpoint: Optional[str] = None  # e.g., 'http://localhost:11434/api/generate'
    parameters: Dict[str, Any] = field(default_factory=dict)

    def can_access(self, user_tier: int) -> bool:
        """Check if user tier can access this model"""
        return user_tier >= self.tier_required

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'model_type': self.model_type.value,
            'capabilities': self.capabilities,
            'tier_required': self.tier_required,
            'description': self.description,
            'endpoint': self.endpoint,
            'parameters': self.parameters
        }


@dataclass
class AIQuery:
    """A query to an AI model"""
    prompt: str
    model_name: str
    user_tier: int = 0
    context: Optional[ConversationContext] = None
    capabilities_needed: List[str] = field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 300

    def to_dict(self) -> dict:
        return {
            'prompt': self.prompt,
            'model_name': self.model_name,
            'user_tier': self.user_tier,
            'context': self.context.to_dict() if self.context else None,
            'capabilities_needed': self.capabilities_needed,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }


@dataclass
class AIResponse:
    """Response from an AI model"""
    success: bool
    content: str
    model_name: str
    capabilities_used: List[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'success': self.success,
            'content': self.content,
            'model_name': self.model_name,
            'capabilities_used': self.capabilities_used,
            'metadata': self.metadata,
            'error': self.error
        }


# ==============================================================================
# USER TIER SCHEMAS
# ==============================================================================

class UserTier(Enum):
    """User permission tiers"""
    GUEST = 0       # Basic access: read posts, limited chat
    BASIC = 1       # Registered user: widget chat, basic commands
    NEURAL = 2      # Neural net access: classification, analysis
    VISION = 3      # Vision access: image/PDF analysis
    ADMIN = 4       # Full access: all AI models, platform admin

    def get_capabilities(self) -> List[str]:
        """Get capabilities for this tier"""
        tier_caps = {
            UserTier.GUEST: ['chat_basic'],
            UserTier.BASIC: ['chat_basic', 'research', 'qr_generate'],
            UserTier.NEURAL: ['chat_basic', 'research', 'qr_generate', 'neural_classify', 'neural_predict'],
            UserTier.VISION: ['chat_basic', 'research', 'qr_generate', 'neural_classify', 'neural_predict', 'vision_analyze', 'pdf_analyze'],
            UserTier.ADMIN: ['all']
        }
        return tier_caps.get(self, [])


@dataclass
class UserPermissions:
    """User permissions and tier information"""
    user_id: int
    tier: UserTier
    is_ai_persona: bool = False
    custom_capabilities: List[str] = field(default_factory=list)

    def has_capability(self, capability: str) -> bool:
        """Check if user has a specific capability"""
        tier_caps = self.tier.get_capabilities()
        if 'all' in tier_caps:
            return True
        return capability in tier_caps or capability in self.custom_capabilities

    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'tier': self.tier.value,
            'is_ai_persona': self.is_ai_persona,
            'custom_capabilities': self.custom_capabilities
        }


# ==============================================================================
# NEURAL NETWORK SCHEMAS
# ==============================================================================

@dataclass
class NeuralPrediction:
    """Result from a neural network classification"""
    model_name: str
    predicted_class: str
    confidence: float
    all_probabilities: Dict[str, float] = field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        return {
            'model_name': self.model_name,
            'predicted_class': self.predicted_class,
            'confidence': self.confidence,
            'all_probabilities': self.all_probabilities,
            'metadata': self.metadata
        }


@dataclass
class NeuralAnalysis:
    """Analysis of content using multiple neural networks"""
    content: str
    predictions: List[NeuralPrediction]
    primary_classification: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            'content': self.content[:100] + '...' if len(self.content) > 100 else self.content,
            'predictions': [p.to_dict() for p in self.predictions],
            'primary_classification': self.primary_classification,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat()
        }


# ==============================================================================
# VISION PROCESSING SCHEMAS
# ==============================================================================

@dataclass
class ImageAnalysis:
    """Result from image analysis"""
    image_path: str
    colors: List[tuple]  # [(r, g, b), ...]
    dominant_color: tuple
    patterns: List[str]  # Detected patterns
    text: Optional[str] = None  # OCR text if available
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'image_path': self.image_path,
            'colors': self.colors,
            'dominant_color': self.dominant_color,
            'patterns': self.patterns,
            'text': self.text,
            'metadata': self.metadata
        }


@dataclass
class PDFAnalysis:
    """Result from PDF analysis"""
    pdf_path: str
    pages: int
    text_content: str
    images: List[ImageAnalysis]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'pdf_path': self.pdf_path,
            'pages': self.pages,
            'text_content': self.text_content[:500] + '...' if len(self.text_content) > 500 else self.text_content,
            'images': [img.to_dict() for img in self.images],
            'metadata': self.metadata
        }


# ==============================================================================
# SELF-IMPROVEMENT SCHEMAS
# ==============================================================================

@dataclass
class CodeAnalysis:
    """Analysis of codebase by AI"""
    file_path: str
    issues: List[str]
    suggestions: List[str]
    quality_score: float  # 0-100
    complexity: str  # 'low', 'medium', 'high'
    neural_classification: Optional[NeuralPrediction] = None

    def to_dict(self) -> dict:
        return {
            'file_path': self.file_path,
            'issues': self.issues,
            'suggestions': self.suggestions,
            'quality_score': self.quality_score,
            'complexity': self.complexity,
            'neural_classification': self.neural_classification.to_dict() if self.neural_classification else None
        }


@dataclass
class PlatformHealth:
    """Overall platform health assessment"""
    timestamp: datetime = field(default_factory=datetime.now)
    total_files: int = 0
    broken_features: List[str] = field(default_factory=list)
    hardcoded_count: int = 0
    duplication_count: int = 0
    test_coverage: float = 0.0
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_files': self.total_files,
            'broken_features': self.broken_features,
            'hardcoded_count': self.hardcoded_count,
            'duplication_count': self.duplication_count,
            'test_coverage': self.test_coverage,
            'suggestions': self.suggestions
        }


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def validate_message(data: dict) -> bool:
    """Validate message structure"""
    required_fields = ['sender', 'content']
    return all(field in data for field in required_fields)


def validate_ai_query(data: dict) -> bool:
    """Validate AI query structure"""
    required_fields = ['prompt', 'model_name']
    return all(field in data for field in required_fields)


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == '__main__':
    print("🧪 Testing Schemas")
    print("=" * 70)

    # Test Message
    msg = Message(sender='user', content='Hello AI!')
    print(f"\n✅ Message: {msg.to_dict()}")

    # Test AIModel
    model = AIModel(
        name='llama2',
        model_type=ModelType.OLLAMA,
        capabilities=['chat', 'analyze'],
        tier_required=1
    )
    print(f"\n✅ AIModel: {model.to_dict()}")

    # Test UserPermissions
    perms = UserPermissions(user_id=1, tier=UserTier.NEURAL)
    print(f"\n✅ UserPermissions: {perms.to_dict()}")
    print(f"   Has 'neural_classify': {perms.has_capability('neural_classify')}")
    print(f"   Has 'vision_analyze': {perms.has_capability('vision_analyze')}")

    # Test NeuralPrediction
    pred = NeuralPrediction(
        model_name='calriven_classifier',
        predicted_class='technical',
        confidence=0.87,
        all_probabilities={'technical': 0.87, 'general': 0.13}
    )
    print(f"\n✅ NeuralPrediction: {pred.to_dict()}")

    print("\n" + "=" * 70)
    print("✅ All schemas working!")
