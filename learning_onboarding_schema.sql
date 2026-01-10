-- Interactive Learning Onboarding Schema
-- Tracks user progress through calriven chapters and neural network building

-- User learning progress through chapters
CREATE TABLE IF NOT EXISTS user_learning_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    current_chapter INTEGER DEFAULT 1,
    chapters_completed TEXT DEFAULT '[]',  -- JSON array of completed chapter numbers
    context_profile TEXT DEFAULT '{}',     -- JSON: personality, learning style, interests
    neural_network_built INTEGER DEFAULT 0,  -- Has user built their first network?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- User's custom neural networks built during onboarding
CREATE TABLE IF NOT EXISTS user_neural_networks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    network_name TEXT NOT NULL,
    network_type TEXT DEFAULT 'feedforward',  -- feedforward, classifier, etc.
    architecture TEXT NOT NULL,  -- JSON: layers, neurons, activation functions
    weights TEXT,  -- JSON: trained weights (if trained)
    training_data TEXT,  -- JSON: what it was trained on
    accuracy REAL,  -- Training accuracy
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Interactive chat history per chapter (conversational learning)
CREATE TABLE IF NOT EXISTS chapter_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    chapter_number INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    model_used TEXT DEFAULT 'llama2',  -- Which LLM answered
    persona TEXT DEFAULT 'calriven',  -- calriven, deathtodata, auditor, soulfra
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Chapter completion events (for tracking progress)
CREATE TABLE IF NOT EXISTS chapter_completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    chapter_number INTEGER NOT NULL,
    time_spent_seconds INTEGER DEFAULT 0,
    interactions_count INTEGER DEFAULT 0,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, chapter_number)  -- One completion per chapter per user
);

-- Chapter quiz attempts (for tracking quiz submissions and scores)
CREATE TABLE IF NOT EXISTS chapter_quiz_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    chapter_number INTEGER NOT NULL,
    answers TEXT NOT NULL,  -- JSON: [{question_index: 0, selected_answer: 1}, ...]
    score REAL NOT NULL,  -- Percentage score (0-100)
    passed INTEGER DEFAULT 0,  -- 1 if score >= 70%, 0 otherwise
    attempt_number INTEGER DEFAULT 1,  -- Allow multiple attempts
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_learning_progress_user ON user_learning_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_neural_networks_user ON user_neural_networks(user_id);
CREATE INDEX IF NOT EXISTS idx_chapter_interactions_user_chapter ON chapter_interactions(user_id, chapter_number);
CREATE INDEX IF NOT EXISTS idx_chapter_completions_user ON chapter_completions(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user_chapter ON chapter_quiz_attempts(user_id, chapter_number);
