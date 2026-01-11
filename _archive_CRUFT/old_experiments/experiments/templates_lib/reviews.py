#!/usr/bin/env python3
"""
Review Templates - Peer Review & Feedback Code Generation

Generates templates for:
- Review form generators
- Analysis report templates
- Comparison templates (self vs peer assessment)
- Recommendation emails
- Review question builders

Part of the peer review system where friends provide feedback on
game results and AI analyzes the quality and insights.
"""

from typing import Optional, List


# ==============================================================================
# CATEGORY CONSTANT
# ==============================================================================

CATEGORY = 'reviews'


# ==============================================================================
# GENERATOR FUNCTIONS
# ==============================================================================

def generate_review_form(
    game_type: str,
    questions_count: int = 7
) -> str:
    """
    Generate HTML review form template

    Args:
        game_type: Type of game (e.g., 'cringeproof', 'color_challenge')
        questions_count: Number of review questions

    Returns:
        HTML form template as string
    """
    # Use .format() instead of f-string to avoid brace escaping issues
    template = '''<!-- Review Form for {game_type} -->
<form id="review-form" method="POST" class="review-form">
    <input type="hidden" name="share_code" value="{{{{ share_code }}}}">

    <!-- Game Results Display -->
    <div class="game-results-card">
        <h2>Their {game_type} Results</h2>
        <div class="results-content">
            {{{{ game_results|safe }}}}
        </div>
    </div>

    <!-- Review Questions -->
    <div class="review-questions">
        {{% for question in review_questions %}}
        <div class="question-card">
            <label class="question-label">
                <span class="question-number">{{{{ loop.index }}}}</span>
                {{{{ question.question_text }}}}
            </label>

            {{% if question.question_type == 'rating' %}}
                <div class="rating-input">
                    {{% for i in range(1, 6) %}}
                    <label class="rating-option">
                        <input type="radio"
                               name="question_{{{{ question.id }}}}"
                               value="{{{{ i }}}}"
                               required>
                        <span class="rating-label">{{{{ i }}}}</span>
                    </label>
                    {{% endfor %}}
                    <div class="rating-labels">
                        <span>Not at all</span>
                        <span>Extremely</span>
                    </div>
                </div>

            {{% elif question.question_type == 'text' %}}
                <textarea name="question_{{{{ question.id }}}}"
                          class="text-input"
                          rows="4"
                          placeholder="Share your thoughts..."
                          {{% if question.is_required %}}required{{% endif %}}></textarea>

            {{% elif question.question_type == 'multiple_choice' %}}
                <div class="multiple-choice">
                    {{% set options = question.metadata.options %}}
                    {{% for option in options %}}
                    <label class="choice-option">
                        <input type="radio"
                               name="question_{{{{ question.id }}}}"
                               value="{{{{ option }}}}"
                               {{% if question.is_required %}}required{{% endif %}}>
                        <span>{{{{ option }}}}</span>
                    </label>
                    {{% endfor %}}
                </div>
            {{% endif %}}
        </div>
        {{% endfor %}}
    </div>

    <!-- Overall Rating -->
    <div class="overall-rating-card">
        <h3>Overall Rating</h3>
        <div class="star-rating">
            {{% for i in range(1, 6) %}}
            <label class="star-label">
                <input type="radio" name="overall_rating" value="{{{{ i }}}}" required>
                <span class="star">★</span>
            </label>
            {{% endfor %}}
        </div>
    </div>

    <!-- Anonymous Option -->
    <div class="anonymous-option">
        <label>
            <input type="checkbox" name="is_anonymous">
            Submit this review anonymously
        </label>
    </div>

    <!-- Submit Button -->
    <button type="submit" class="submit-btn">
        Submit Review
    </button>
</form>

<style>
.review-form {{
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}}

.game-results-card,
.question-card,
.overall-rating-card {{
    background: white;
    border-radius: 12px;
    padding: 30px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}}

.question-label {{
    display: block;
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 15px;
    color: #333;
}}

.question-number {{
    display: inline-block;
    width: 30px;
    height: 30px;
    background: var(--theme-primary, #667eea);
    color: white;
    border-radius: 50%;
    text-align: center;
    line-height: 30px;
    margin-right: 10px;
    font-size: 14px;
}}

.rating-input {{
    display: flex;
    gap: 10px;
    margin-bottom: 10px;
}}

.rating-option input {{
    display: none;
}}

.rating-option input:checked + .rating-label {{
    background: var(--theme-primary, #667eea);
    color: white;
}}

.rating-label {{
    display: inline-block;
    width: 50px;
    height: 50px;
    border: 2px solid #ddd;
    border-radius: 8px;
    text-align: center;
    line-height: 50px;
    cursor: pointer;
    transition: all 0.2s;
}}

.rating-label:hover {{
    border-color: var(--theme-primary, #667eea);
}}

.rating-labels {{
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #999;
}}

.text-input {{
    width: 100%;
    padding: 12px;
    border: 2px solid #ddd;
    border-radius: 8px;
    font-family: system-ui, sans-serif;
    font-size: 15px;
    resize: vertical;
}}

.text-input:focus {{
    outline: none;
    border-color: var(--theme-primary, #667eea);
}}

.multiple-choice {{
    display: flex;
    flex-direction: column;
    gap: 10px;
}}

.choice-option {{
    display: flex;
    align-items: center;
    padding: 12px;
    border: 2px solid #ddd;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
}}

.choice-option:hover {{
    border-color: var(--theme-primary, #667eea);
    background: #f8f9fa;
}}

.choice-option input {{
    margin-right: 10px;
}}

.star-rating {{
    display: flex;
    gap: 10px;
    justify-content: center;
}}

.star-label input {{
    display: none;
}}

.star {{
    font-size: 48px;
    color: #ddd;
    cursor: pointer;
    transition: all 0.2s;
}}

.star-label input:checked ~ .star,
.star-label:hover .star {{
    color: #FFD700;
}}

.anonymous-option {{
    text-align: center;
    margin: 20px 0;
}}

.submit-btn {{
    width: 100%;
    padding: 16px;
    background: var(--theme-primary, #667eea);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 18px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}}

.submit-btn:hover {{
    background: var(--theme-secondary, #764ba2);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}}
</style>

<script>
// Star rating interaction
document.querySelectorAll('.star-rating').forEach(container => {{
    const stars = container.querySelectorAll('.star-label');
    stars.forEach((star, index) => {{
        star.addEventListener('mouseenter', () => {{
            stars.forEach((s, i) => {{
                if (i <= index) {{
                    s.querySelector('.star').style.color = '#FFD700';
                }} else {{
                    s.querySelector('.star').style.color = '#ddd';
                }}
            }});
        }});
    }});

    container.addEventListener('mouseleave', () => {{
        const checked = container.querySelector('input:checked');
        if (checked) {{
            const checkedIndex = Array.from(stars).indexOf(checked.closest('.star-label'));
            stars.forEach((s, i) => {{
                if (i <= checkedIndex) {{
                    s.querySelector('.star').style.color = '#FFD700';
                }} else {{
                    s.querySelector('.star').style.color = '#ddd';
                }}
            }});
        }}
    }});
}});
</script>
'''
    return template.format(game_type=game_type)


def generate_analysis_display(
    include_recommendations: bool = True,
    include_comparisons: bool = True
) -> str:
    """
    Generate HTML template for AI analysis results display

    Args:
        include_recommendations: Include recommendations section
        include_comparisons: Include self vs peer comparison

    Returns:
        HTML template as string
    """
    return '''<!-- AI Analysis Results Display -->
<div class="analysis-dashboard">
    <!-- Header -->
    <div class="analysis-header">
        <h1>🧠 AI Analysis Results</h1>
        <p class="subtitle">Neural networks analyzed {{ review_count }} peer review{{ 's' if review_count != 1 else '' }}</p>
    </div>

    <!-- Key Metrics -->
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-icon">⭐</div>
            <div class="metric-value">{{ overall_rating }}/5</div>
            <div class="metric-label">Overall Rating</div>
        </div>

        <div class="metric-card">
            <div class="metric-icon">🎯</div>
            <div class="metric-value">{{ helpfulness_score }}%</div>
            <div class="metric-label">Review Quality</div>
        </div>

        <div class="metric-card">
            <div class="metric-icon">🤖</div>
            <div class="metric-value">{{ classifications_count }}</div>
            <div class="metric-label">AI Classifications</div>
        </div>

        <div class="metric-card">
            <div class="metric-icon">💡</div>
            <div class="metric-value">{{ recommendations_count }}</div>
            <div class="metric-label">Recommendations</div>
        </div>
    </div>

    <!-- Neural Network Classifications -->
    <div class="classifications-section">
        <h2>Neural Network Analysis</h2>
        {% for classification in classifications %}
        <div class="classification-card">
            <div class="classification-header">
                <span class="network-name">{{ classification.network_name }}</span>
                <span class="confidence-badge" data-confidence="{{ classification.confidence }}">
                    {{ (classification.confidence * 100)|round|int }}% confident
                </span>
            </div>
            <div class="classification-result">
                <span class="label-badge {{ classification.label }}">
                    {{ classification.label }}
                </span>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: {{ (classification.confidence * 100)|round }}%"></div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

''' + ('''
    <!-- Recommendations -->
    <div class="recommendations-section">
        <h2>📊 Key Insights & Recommendations</h2>
        {% for recommendation in recommendations %}
        <div class="recommendation-card">
            <div class="recommendation-icon">
                {% if 'excellent' in recommendation.lower() or 'great' in recommendation.lower() %}
                    ✅
                {% elif 'consider' in recommendation.lower() or 'improve' in recommendation.lower() %}
                    ⚠️
                {% else %}
                    💡
                {% endif %}
            </div>
            <div class="recommendation-text">{{ recommendation }}</div>
        </div>
        {% endfor %}
    </div>
''' if include_recommendations else '') + ('''
    <!-- Self vs Peer Comparison -->
    <div class="comparison-section">
        <h2>🔍 Self-Assessment vs Peer Feedback</h2>
        <div class="comparison-grid">
            {% for dimension in comparison_dimensions %}
            <div class="comparison-item">
                <div class="dimension-name">{{ dimension.name }}</div>
                <div class="comparison-bars">
                    <div class="self-bar">
                        <span class="bar-label">You</span>
                        <div class="bar-container">
                            <div class="bar-fill self" style="width: {{ dimension.self_score * 20 }}%"></div>
                        </div>
                        <span class="bar-value">{{ dimension.self_score }}/5</span>
                    </div>
                    <div class="peer-bar">
                        <span class="bar-label">Peer</span>
                        <div class="bar-container">
                            <div class="bar-fill peer" style="width: {{ dimension.peer_score * 20 }}%"></div>
                        </div>
                        <span class="bar-value">{{ dimension.peer_score }}/5</span>
                    </div>
                </div>
                {% if dimension.gap %}
                <div class="gap-indicator {{ 'positive' if dimension.gap > 0 else 'negative' }}">
                    {{ '+' if dimension.gap > 0 else '' }}{{ dimension.gap }} point gap
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </div>
''' if include_comparisons else '') + '''
</div>

<style>
.analysis-dashboard {
    max-width: 1200px;
    margin: 0 auto;
    padding: 40px 20px;
}

.analysis-header {
    text-align: center;
    margin-bottom: 40px;
}

.analysis-header h1 {
    font-size: 36px;
    margin-bottom: 10px;
    color: #333;
}

.subtitle {
    font-size: 16px;
    color: #666;
}

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 40px;
}

.metric-card {
    background: white;
    border-radius: 12px;
    padding: 30px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.metric-icon {
    font-size: 48px;
    margin-bottom: 15px;
}

.metric-value {
    font-size: 36px;
    font-weight: 700;
    color: var(--theme-primary, #667eea);
    margin-bottom: 10px;
}

.metric-label {
    font-size: 14px;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.classifications-section,
.recommendations-section,
.comparison-section {
    background: white;
    border-radius: 12px;
    padding: 30px;
    margin-bottom: 30px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.classification-card {
    border: 2px solid #f0f0f0;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 15px;
}

.classification-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.network-name {
    font-weight: 600;
    color: #333;
}

.confidence-badge {
    background: #f0f0f0;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 13px;
    color: #666;
}

.confidence-badge[data-confidence^="0.9"],
.confidence-badge[data-confidence^="1"] {
    background: #d4edda;
    color: #155724;
}

.label-badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 10px;
}

.label-badge.technical { background: #e3f2fd; color: #1976d2; }
.label-badge.validated { background: #e8f5e9; color: #388e3c; }
.label-badge.privacy-focused { background: #fff3e0; color: #f57c00; }
.label-badge.approved { background: #f3e5f5; color: #7b1fa2; }

.confidence-bar {
    width: 100%;
    height: 8px;
    background: #f0f0f0;
    border-radius: 4px;
    overflow: hidden;
}

.confidence-fill {
    height: 100%;
    background: var(--theme-primary, #667eea);
    transition: width 0.3s ease;
}

.recommendation-card {
    display: flex;
    align-items: flex-start;
    gap: 15px;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 8px;
    margin-bottom: 10px;
}

.recommendation-icon {
    font-size: 24px;
    flex-shrink: 0;
}

.recommendation-text {
    flex: 1;
    line-height: 1.6;
    color: #333;
}

.comparison-grid {
    display: grid;
    gap: 20px;
}

.comparison-item {
    border: 2px solid #f0f0f0;
    border-radius: 8px;
    padding: 20px;
}

.dimension-name {
    font-weight: 600;
    margin-bottom: 15px;
    color: #333;
}

.comparison-bars {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.self-bar, .peer-bar {
    display: grid;
    grid-template-columns: 60px 1fr 60px;
    align-items: center;
    gap: 10px;
}

.bar-label {
    font-size: 13px;
    color: #666;
}

.bar-container {
    height: 24px;
    background: #f0f0f0;
    border-radius: 12px;
    overflow: hidden;
}

.bar-fill {
    height: 100%;
    transition: width 0.3s ease;
}

.bar-fill.self {
    background: #9b59b6;
}

.bar-fill.peer {
    background: var(--theme-primary, #667eea);
}

.bar-value {
    font-size: 13px;
    font-weight: 600;
    color: #333;
}

.gap-indicator {
    margin-top: 10px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    display: inline-block;
}

.gap-indicator.positive {
    background: #d4edda;
    color: #155724;
}

.gap-indicator.negative {
    background: #f8d7da;
    color: #721c24;
}
</style>
'''


def generate_comparison_report(output_format: str = 'html') -> str:
    """
    Generate self vs peer comparison report template

    Args:
        output_format: Output format ('html', 'markdown', 'json')

    Returns:
        Report template as string
    """
    if output_format == 'html':
        return '''<!-- Self vs Peer Comparison Report -->
<div class="comparison-report">
    <h1>Self-Awareness Gap Analysis</h1>

    <div class="executive-summary">
        <h2>Executive Summary</h2>
        <p>
            Based on comparing your self-assessment with peer feedback,
            we've identified {{ gap_count }} areas with significant differences
            in perception.
        </p>
    </div>

    <div class="gaps-grid">
        {% for gap in self_awareness_gaps %}
        <div class="gap-card {{ 'overestimate' if gap.direction == 'over' else 'underestimate' }}">
            <div class="gap-header">
                <h3>{{ gap.dimension }}</h3>
                <span class="gap-badge">{{ gap.difference }} point difference</span>
            </div>
            <div class="gap-scores">
                <div class="score-item">
                    <span class="label">Your Rating:</span>
                    <span class="value">{{ gap.self_score }}/5</span>
                </div>
                <div class="score-item">
                    <span class="label">Peer Rating:</span>
                    <span class="value">{{ gap.peer_score }}/5</span>
                </div>
            </div>
            <div class="gap-insight">
                {{ gap.insight }}
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="action-items">
        <h2>Recommended Actions</h2>
        <ul>
            {% for action in action_items %}
            <li>{{ action }}</li>
            {% endfor %}
        </ul>
    </div>
</div>
'''

    elif output_format == 'markdown':
        return '''# Self-Awareness Gap Analysis

## Executive Summary

Based on comparing your self-assessment with peer feedback, we've identified {{ gap_count }} areas with significant differences in perception.

## Gaps Identified

{% for gap in self_awareness_gaps %}
### {{ gap.dimension }}

- **Your Rating**: {{ gap.self_score }}/5
- **Peer Rating**: {{ gap.peer_score }}/5
- **Difference**: {{ gap.difference }} points ({{ 'overestimate' if gap.direction == 'over' else 'underestimate' }})

**Insight**: {{ gap.insight }}

{% endfor %}

## Recommended Actions

{% for action in action_items %}
- {{ action }}
{% endfor %}
'''

    else:
        return '''// Self-Awareness Gap Analysis (JSON)
{
  "summary": {
    "total_gaps": {{ gap_count }},
    "overestimates": {{ overestimate_count }},
    "underestimates": {{ underestimate_count }}
  },
  "gaps": [
    {% for gap in self_awareness_gaps %}
    {
      "dimension": "{{ gap.dimension }}",
      "self_score": {{ gap.self_score }},
      "peer_score": {{ gap.peer_score }},
      "difference": {{ gap.difference }},
      "direction": "{{ gap.direction }}",
      "insight": "{{ gap.insight }}"
    }{{ ',' if not loop.last else '' }}
    {% endfor %}
  ],
  "action_items": [
    {% for action in action_items %}
    "{{ action }}"{{ ',' if not loop.last else '' }}
    {% endfor %}
  ]
}
'''


def generate_review_questions(game_type: str) -> str:
    """
    Generate SQL to create review questions for a game type

    Args:
        game_type: Type of game (e.g., 'color_challenge', 'catchphrase')

    Returns:
        SQL INSERT statements
    """
    return f'''-- Review Questions for {game_type}
-- Add these to your database migration

INSERT OR IGNORE INTO review_questions (game_type, question_text, question_type, order_index, is_required) VALUES
    ('{game_type}', 'How well did they understand the game concept?', 'rating', 1, 1),
    ('{game_type}', 'Rate the creativity of their responses', 'rating', 2, 1),
    ('{game_type}', 'What was their strongest answer?', 'text', 3, 1),
    ('{game_type}', 'What could they improve?', 'text', 4, 1),
    ('{game_type}', 'Compared to average players, they are...', 'multiple_choice', 5, 1),
    ('{game_type}', 'Would you recommend this person to others?', 'rating', 6, 1),
    ('{game_type}', 'Overall quality of responses', 'rating', 7, 1);

-- Update multiple choice options
UPDATE review_questions
SET metadata = json('{{"options": ["Well below average", "Below average", "Average", "Above average", "Exceptional"]}}')
WHERE game_type = '{game_type}' AND order_index = 5;

-- Verify insertion
SELECT COUNT(*) as question_count FROM review_questions WHERE game_type = '{game_type}';
'''


# ==============================================================================
# TEMPLATE DEFINITIONS
# ==============================================================================

TEMPLATES = {
    'review-form': {
        'description': 'HTML review form with rating scales, text inputs, and multiple choice',
        'generator': generate_review_form,
        'parameters': ['game_type', 'questions_count?'],
        'examples': [
            "generate_template('reviews', 'review-form', game_type='cringeproof')",
            "generate_template('reviews', 'review-form', game_type='color_challenge', questions_count=5)"
        ],
        'tags': ['html', 'form', 'review', 'peer-feedback', 'games']
    },

    'analysis-display': {
        'description': 'AI analysis results dashboard with neural network classifications',
        'generator': generate_analysis_display,
        'parameters': ['include_recommendations?', 'include_comparisons?'],
        'examples': [
            "generate_template('reviews', 'analysis-display')",
            "generate_template('reviews', 'analysis-display', include_recommendations=False)"
        ],
        'tags': ['html', 'dashboard', 'ai', 'analysis', 'neural-networks']
    },

    'comparison-report': {
        'description': 'Self vs peer comparison report template',
        'generator': generate_comparison_report,
        'parameters': ['output_format?'],
        'examples': [
            "generate_template('reviews', 'comparison-report')",
            "generate_template('reviews', 'comparison-report', output_format='markdown')"
        ],
        'tags': ['html', 'markdown', 'json', 'report', 'comparison', 'self-awareness']
    },

    'review-questions': {
        'description': 'SQL to create review questions for a game type',
        'generator': generate_review_questions,
        'parameters': ['game_type'],
        'examples': [
            "generate_template('reviews', 'review-questions', game_type='color_challenge')",
            "generate_template('reviews', 'review-questions', game_type='catchphrase')"
        ],
        'tags': ['sql', 'database', 'questions', 'games', 'setup']
    }
}


# ==============================================================================
# TEST CODE
# ==============================================================================

if __name__ == '__main__':
    print("📝 Review Templates\n")

    print("=" * 70)
    print("1. Review Form")
    print("=" * 70)
    form = generate_review_form('cringeproof', 7)
    print(f"Generated {len(form)} characters")
    print(form[:400] + "...\n")

    print("=" * 70)
    print("2. Analysis Display")
    print("=" * 70)
    analysis = generate_analysis_display(True, True)
    print(f"Generated {len(analysis)} characters")
    print(analysis[:400] + "...\n")

    print("=" * 70)
    print("3. Comparison Report (Markdown)")
    print("=" * 70)
    report = generate_comparison_report('markdown')
    print(report[:400] + "...\n")

    print("=" * 70)
    print("4. Review Questions SQL")
    print("=" * 70)
    sql = generate_review_questions('color_challenge')
    print(sql)

    print("\n✅ All review templates working!")
