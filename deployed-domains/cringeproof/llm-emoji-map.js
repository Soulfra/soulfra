/**
 * Emoji → LLM Instruction Mapping
 *
 * Maps visual emojis to LLM reasoning operations.
 * UI shows clean text, backend uses this to determine LLM pipeline.
 *
 * Each emoji represents a specific LLM instruction/reasoning pattern.
 */

const EMOJI_LLM_MAP = {
  // === Audio Processing ===
  '🎤': {
    operation: 'TRANSCRIBE_AUDIO',
    llm: 'whisper',
    instruction: 'Convert audio waveform to text transcript',
    input: 'audio/webm',
    output: 'string (transcript)',
    reasoning: 'speech-to-text'
  },

  '🎙️': {
    operation: 'CAPTURE_VOICE',
    llm: 'browser_mediarecorder',
    instruction: 'Record audio from microphone',
    input: 'microphone stream',
    output: 'audio/webm blob',
    reasoning: 'input-capture'
  },

  // === Cognitive Processing ===
  '🧠': {
    operation: 'EXTRACT_INSIGHTS',
    llm: 'ollama:llama2',
    instruction: 'Analyze transcript and extract key ideas, action items, themes',
    input: 'string (transcript)',
    output: 'structured JSON {ideas, actions, themes}',
    reasoning: 'natural-language-understanding'
  },

  '💡': {
    operation: 'IDEATE',
    llm: 'ollama:llama2',
    instruction: 'Generate creative variations, expansions, related concepts',
    input: 'string (seed idea)',
    output: 'array of related ideas',
    reasoning: 'creative-expansion'
  },

  // === Validation & Filtering ===
  '🚫': {
    operation: 'FILTER_CRINGE',
    llm: 'ollama:llama2',
    instruction: 'Validate authenticity, detect performative language, filter cringe',
    input: 'string (text)',
    output: 'boolean (is_authentic) + confidence score',
    reasoning: 'content-validation'
  },

  '🔒': {
    operation: 'ENCRYPT_CONTENT',
    llm: 'crypto_api',
    instruction: 'Encrypt sensitive content, rotate keys',
    input: 'string (plaintext)',
    output: 'string (ciphertext)',
    reasoning: 'security-operation'
  },

  // === Storage & Archival ===
  '📡': {
    operation: 'ARCHIVE_PERMANENT',
    llm: 'storage_engine',
    instruction: 'Store to permanent archive, generate content hash',
    input: 'any data',
    output: 'string (content_hash)',
    reasoning: 'persistence'
  },

  '📸': {
    operation: 'CAPTURE_CONTEXT',
    llm: 'vision_api',
    instruction: 'Extract text/context from screenshot',
    input: 'image/png',
    output: 'string (extracted_text)',
    reasoning: 'visual-processing'
  },

  // === Organization ===
  '🎯': {
    operation: 'PRIORITIZE',
    llm: 'ollama:llama2',
    instruction: 'Rank ideas by urgency, impact, feasibility',
    input: 'array of ideas',
    output: 'sorted array + priority scores',
    reasoning: 'decision-making'
  }
};

/**
 * Get LLM pipeline for a sequence of emojis
 *
 * Example: "🎤 → 🧠 → 🚫 → 📡"
 * Returns: [TRANSCRIBE_AUDIO, EXTRACT_INSIGHTS, FILTER_CRINGE, ARCHIVE_PERMANENT]
 */
function getEmojiPipeline(emojiSequence) {
  return emojiSequence
    .split('→')
    .map(e => e.trim())
    .map(emoji => EMOJI_LLM_MAP[emoji])
    .filter(Boolean);
}

/**
 * Get clean text label for emoji (for UI)
 */
function emojiToText(emoji) {
  const textMap = {
    '🎤': 'Record',
    '🎙️': 'Capture',
    '🧠': 'Extract',
    '💡': 'Ideas',
    '🚫': 'Filter',
    '🔒': 'Privacy',
    '📡': 'Archive',
    '📸': 'Screenshot',
    '🎯': 'Prioritize'
  };
  return textMap[emoji] || emoji;
}

/**
 * Build LLM wordmap from processing pipeline
 * Shows which LLM operations were used
 */
function buildLLMWordmap(voiceMemos) {
  const llmOps = {};

  voiceMemos.forEach(memo => {
    // Each memo went through: 🎤 → 🧠 → 🚫 → 📡
    const pipeline = ['🎤', '🧠', '🚫', '📡'];

    pipeline.forEach(emoji => {
      const op = EMOJI_LLM_MAP[emoji];
      if (op) {
        llmOps[op.operation] = (llmOps[op.operation] || 0) + 1;
      }
    });
  });

  return llmOps;
}

// Export for use in browser
if (typeof window !== 'undefined') {
  window.EMOJI_LLM_MAP = EMOJI_LLM_MAP;
  window.getEmojiPipeline = getEmojiPipeline;
  window.emojiToText = emojiToText;
  window.buildLLMWordmap = buildLLMWordmap;
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    EMOJI_LLM_MAP,
    getEmojiPipeline,
    emojiToText,
    buildLLMWordmap
  };
}
