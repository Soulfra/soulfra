# Voice Q&A Profile Builder

## What We Built

Instead of typing a README, users build profiles by **answering questions out loud**.

---

## The Flow

### 1. Anonymous Entry
**URL**: `https://192.168.1.87:5002/build-profile-voice.html`

No login required to start. Just open the page and begin.

### 2. Voice Q&A Session
- **12 curated questions** across 5 categories:
  - Technical (3 questions)
  - Reasoning (3 questions)
  - Infrastructure (3 questions)
  - Goals (3 questions)
  - Collaboration (2 questions)

- **Tap to record** → speak your answer → tap to stop
- **Skip questions** you don't want to answer
- **Real-time progress** indicator (Question 3/12)

### 3. AI Analysis (Behind the Scenes)
Each voice answer goes through:

```
Voice → Whisper (transcription) → Ollama (analysis)
```

**What Ollama extracts**:
- **Skills detected** - Technical terms, languages, frameworks mentioned
- **Reasoning quality** - Score 1-10 + label (basic/good/advanced)
  - Do they explain WHY, not just WHAT?
  - Do they consider trade-offs?
  - Do they show depth of understanding?
- **Infrastructure knowledge** - Score 1-10 + label (beginner/intermediate/expert)
  - Deployment processes
  - Database choices
  - Cloud vs local vs self-hosted
- **People mentioned** - Teammates, mentors (for collaboration graph)
- **Projects mentioned** - Things they've built
- **Goals mentioned** - What they want to build next

### 4. Completion Screen
After answering all questions (or skipping to the end), user sees:

- **Skills detected** (as tags)
- **Reasoning quality score** (e.g., "8/10 - Advanced reasoning")
- **Infrastructure knowledge** (e.g., "7/10 - Intermediate")

### 5. Claim Profile
Two options:

**Option A: GitHub OAuth**
- Click "🔗 Claim with GitHub"
- Redirects to GitHub login
- Creates profile at `/{github_username}`
- Auto-generates README from Q&A answers

**Option B: Phone Verification**
- Click "📱 Claim with Phone"
- Redirects to existing phone claim system
- Links Q&A session to phone number

Until claimed, the profile is **anonymous** - stored in database but not public.

---

## Database Tables Created

### `voice_qa_sessions`
```sql
CREATE TABLE voice_qa_sessions (
    id INTEGER PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    total_questions INTEGER DEFAULT 0,
    answered_questions INTEGER DEFAULT 0,
    claimed_by_user_id INTEGER,
    claimed_at TIMESTAMP
)
```

### `voice_qa_answers`
```sql
CREATE TABLE voice_qa_answers (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    question_text TEXT NOT NULL,
    category TEXT NOT NULL,
    recording_id INTEGER REFERENCES simple_voice_recordings(id),
    transcript TEXT,
    created_at TIMESTAMP
)
```

### `voice_qa_analysis`
```sql
CREATE TABLE voice_qa_analysis (
    id INTEGER PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    skills_detected TEXT,  -- JSON array
    reasoning_score INTEGER,  -- 1-10
    reasoning_quality TEXT,  -- "basic", "good", "advanced"
    infra_score INTEGER,  -- 1-10
    infra_quality TEXT,  -- "beginner", "intermediate", "expert"
    collaboration_mentions TEXT,  -- JSON array
    projects_mentioned TEXT,  -- JSON array
    goals_mentioned TEXT,  -- JSON array
    analysis_completed_at TIMESTAMP
)
```

---

## API Endpoints

### `POST /api/voice-qa/answer`
**Purpose**: Receive voice answer, transcribe, analyze

**Request**:
```
FormData:
  - audio (file): WebM audio blob
  - session_id (str): Unique session ID
  - question_id (str): Question identifier
  - question_text (str): The question asked
  - category (str): Question category
```

**What happens**:
1. Save audio to `voice-archive/recordings/qa_{session_id}_{question_id}.webm`
2. Store in `simple_voice_recordings` table
3. Transcribe with Whisper
4. Store in `voice_qa_answers` table
5. Update session answer count

**Response**:
```json
{
  "success": true,
  "recording_id": 123,
  "transcript": "I built a voice memo app...",
  "message": "Answer saved"
}
```

### `GET /api/voice-qa/results/<session_id>`
**Purpose**: Get AI analysis results for completed session

**Response**:
```json
{
  "success": true,
  "session_id": "qa_1234567890",
  "skills": ["Python", "Flask", "Whisper", "Ollama"],
  "reasoning_score": 8,
  "reasoning_quality": "advanced",
  "infra_score": 7,
  "infra_quality": "intermediate",
  "collaboration_mentions": ["Alice", "Bob"],
  "projects": ["Voice memo app", "Profile builder"],
  "goals": ["Build AI assistant", "Learn Rust"]
}
```

**If analysis not done yet**, triggers `run_qa_analysis()` and returns results.

### `GET /api/voice-qa/claim-github?session_id=<session_id>`
**Purpose**: Start GitHub OAuth flow to claim Q&A session

**What happens**:
1. Stores `session_id` in Flask session
2. Redirects to GitHub OAuth
3. On callback:
   - Creates user if doesn't exist
   - Generates README from Q&A answers
   - Creates profile in `user_profiles` table
   - Redirects to `/{github_username}`

---

## Question Bank

Located at: `voice-archive/_data/profile-questions.json`

**Sample questions**:

**Technical**:
- "What's something you built that you're proud of? Walk me through it."
- "Describe your development environment setup. What tools do you use daily?"
- "Tell me about a time you had to debug something really difficult."

**Reasoning**:
- "How do you decide if a solution is good or bad?"
- "Explain a technical trade-off you had to make recently."
- "When you encounter a new technology, how do you evaluate if it's worth learning?"

**Infrastructure**:
- "How do you think about infrastructure? Local first? Cloud? Self-hosted?"
- "Walk me through how you'd deploy something from your laptop to production."
- "What's your opinion on databases? SQL? NoSQL? Something else?"

**Goals**:
- "What do you want to build next?"
- "What skill are you actively trying to improve right now?"
- "If you had unlimited time and resources, what would you create?"

**Collaboration**:
- "Tell me about someone you loved working with. What made them great?"
- "When you're stuck, who do you ask for help? How do they help?"

---

## How README is Auto-Generated

The `generate_readme_from_answers()` function creates markdown:

```markdown
# About Me

{First technical answer - truncated to 200 chars}

## Skills

- Python
- Flask
- Whisper
- Ollama

## Projects

- Voice memo app
- Profile builder

## What I Want to Build

- Build AI assistant
- Learn Rust

---

*Profile built from voice Q&A on CringeProof*
```

---

## Frontend Features

### Mobile-First Design
- **Large tap targets** (120px record button)
- **Visual feedback** (pulse animation while recording)
- **Progress bar** with percentage fill
- **Auto-advance** to next question after saving
- **Skip button** for questions they don't want to answer

### Microphone Access
- Uses `navigator.mediaDevices.getUserMedia({ audio: true })`
- Records as WebM format (compatible with Whisper)
- Shows error if mic access denied

### Status Messages
- "Tap to record your answer"
- "Recording... Tap to stop"
- "Processing..."
- "✅ Answer saved"
- "❌ Failed to save. Try again?"

---

## Integration with Existing Systems

### With Whisper Transcription
- Reuses `simple_voice_recordings` table
- Same audio format (WebM)
- Same storage location (`voice-archive/recordings/`)

### With Collaboration Minesweeper
- People mentioned in Q&A → added to `collaboration_people` table
- Skills detected → feeds into skill confirmation system

### With README Profile System
- Auto-generates profile in `user_profiles` table
- Same slug system (`/{username}`)
- Same dashboard (`profile-dashboard.html`)

---

## Why This is Better Than Text Entry

**Traditional README profiles**:
- User has to format markdown ❌
- User has to think about structure ❌
- Imposter syndrome (blank page intimidating) ❌

**Voice Q&A profiles**:
- Just answer questions naturally ✅
- No markdown knowledge needed ✅
- Conversational, less intimidating ✅
- AI extracts structure automatically ✅
- Analysis reveals hidden skills ✅

---

## Testing Checklist

- [x] Question bank JSON loads correctly
- [x] Voice recording starts/stops
- [x] Audio uploads to backend
- [x] Whisper transcription works
- [x] Ollama analysis extracts skills
- [x] Progress bar updates
- [x] Skip button works
- [x] Completion screen shows results
- [x] GitHub OAuth claim flow works
- [x] Profile created at `/{username}`
- [ ] Test on mobile device (iOS Safari)
- [ ] Test with slow network
- [ ] Test with mic access denied
- [ ] Test skipping all questions

---

## URLs

**Local Testing**:
- Voice Q&A: `https://192.168.1.87:5002/build-profile-voice.html`
- Example profile: `https://192.168.1.87:5002/{username}`

**Public (via Cloudflared)**:
- Use existing tunnel URL
- Same endpoints work through tunnel

---

## Future Enhancements

1. **Audio Playback** - Let users review their answers before submitting
2. **Edit Transcript** - If Whisper gets it wrong, allow corrections
3. **Custom Questions** - Let admins add new questions via dashboard
4. **Multi-language** - Whisper supports 99 languages
5. **Voice Tone Analysis** - Detect confidence, enthusiasm from audio
6. **Anonymous Profiles** - Publish profile without GitHub claim (truly anonymous)
7. **Shareable Session** - Generate link to share your Q&A results before claiming

---

## System Status

✅ **All components implemented and loaded**:
- Voice Q&A tables initialized
- Flask blueprint registered
- Frontend interface built
- Ollama analysis pipeline ready
- GitHub OAuth claim flow working

**Next step**: Test on mobile device to ensure microphone access works on iOS Safari.
