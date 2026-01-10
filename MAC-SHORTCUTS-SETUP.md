# Mac Shortcuts Integration Guide

Automate your blog network with Mac Shortcuts app.

## Setup

1. Open **Shortcuts** app on your Mac
2. Create new shortcuts using the templates below
3. Assign keyboard shortcuts for quick access

## Available Shortcuts

### 1. Quick Blog Post

**What it does**: Create a blog post from anywhere on your Mac

**Setup**:
1. Create new Shortcut named "Quick Blog Post"
2. Add these actions:

```
1. Ask for Input
   Prompt: "Blog post title"

2. Ask for Input
   Prompt: "Blog post content"

3. Choose from List
   Items: soulfra.com, calriven.com, deathtodata.com, etc.
   Prompt: "Select domain"

4. Run Shell Script
   Shell: /bin/bash
   Pass Input: As Arguments
   Script:
   cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
   python3 shortcuts_integration.py quick-post \
     --title "$1" \
     --content "$2" \
     --domain "$3" \
     --username "your_username"

5. Show Notification
   Title: "Post Created!"
   Body: Result
```

**Keyboard Shortcut**: `⌘⌥B` (Command + Option + B for Blog)

---

### 2. Open Domain Editor

**What it does**: Open the domain manager for a specific domain

**Setup**:
1. Create new Shortcut named "Open Domain Editor"
2. Add these actions:

```
1. Choose from List
   Items: soulfra.com, calriven.com, deathtodata.com, etc.
   Prompt: "Select domain to edit"

2. Run Shell Script
   Shell: /bin/bash
   Script:
   cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
   python3 shortcuts_integration.py open-editor "$1"

3. Get Dictionary Value
   Key: url

4. Open URLs
   URL: Dictionary Value
```

**Keyboard Shortcut**: `⌘⌥D` (Command + Option + D for Domain)

---

### 3. Chat with Ollama

**What it does**: Quick chat with Ollama from anywhere

**Setup**:
1. Create new Shortcut named "Ollama Quick Chat"
2. Add these actions:

```
1. Ask for Input
   Prompt: "Ask Ollama"

2. Run Shell Script
   Shell: /bin/bash
   Script:
   cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
   python3 shortcuts_integration.py ollama-chat "$1"

3. Get Dictionary Value
   Key: response

4. Show Result
   Text: Dictionary Value
```

**Keyboard Shortcut**: `⌘⌥O` (Command + Option + O for Ollama)

---

### 4. View Recent Posts

**What it does**: See your recent blog posts

**Setup**:
1. Create new Shortcut named "Recent Posts"
2. Add these actions:

```
1. Run Shell Script
   Shell: /bin/bash
   Script:
   cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
   python3 shortcuts_integration.py recent-posts 20

2. Get Dictionary Value
   Key: posts

3. Choose from List
   Prompt: "Recent Posts"
   Items: Repeat with each post (title + domain)

4. Get Dictionary Value
   Key: url

5. Open URLs
   URL: Dictionary Value
```

**Keyboard Shortcut**: `⌘⌥R` (Command + Option + R for Recent)

---

### 5. Auto-Syndicate Posts

**What it does**: Syndicate recent posts across network

**Setup**:
1. Create new Shortcut named "Syndicate Posts"
2. Add these actions:

```
1. Run Shell Script
   Shell: /bin/bash
   Script:
   cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
   python3 automation_workflows.py auto-syndicate 24

2. Show Notification
   Title: "Syndication Complete"
   Body: Result
```

**Keyboard Shortcut**: `⌘⌥S` (Command + Option + S for Syndicate)

---

## Advanced: Automations

You can schedule shortcuts to run automatically:

### Daily Syndication

1. Open **Automations** tab in Shortcuts
2. Create new Automation
3. Trigger: **Time of Day** (e.g., 9:00 AM)
4. Action: Run Shortcut "Syndicate Posts"

### Weekly Summary Email

1. Create automation for **Time of Day** (e.g., Monday 10:00 AM)
2. Run Shell Script:
   ```bash
   cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
   python3 automation_workflows.py weekly-summary soulfra.com
   ```
3. Get Dictionary Value: summary
4. Send Email with summary

---

## Usage from Terminal

You can also use these directly from Terminal:

```bash
# Quick post
python3 shortcuts_integration.py quick-post \
  --title "My New Post" \
  --content "This is the content" \
  --domain "soulfra.com" \
  --username "your_username"

# List domains
python3 shortcuts_integration.py list-domains

# Recent posts
python3 shortcuts_integration.py recent-posts 10

# Chat with Ollama
python3 shortcuts_integration.py ollama-chat "Explain quantum computing"

# Open editor
python3 shortcuts_integration.py open-editor calriven.com
```

---

## Python Automation Workflows

Run automation tasks from Terminal or Shortcuts:

```bash
# Auto-syndicate posts from last 24 hours
python3 automation_workflows.py auto-syndicate 24

# Generate weekly summary (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY="your-key-here"
python3 automation_workflows.py weekly-summary soulfra.com

# Optimize post with AI
python3 automation_workflows.py optimize-post 123 improve_seo

# Bulk tag posts
python3 automation_workflows.py bulk-tag calriven.com "AI,Engineering,Tech"
```

---

## Integration with Alfred/Raycast

If you use Alfred or Raycast, you can create workflows that call these scripts:

### Alfred Workflow
1. Create new Workflow
2. Add Keyword trigger (e.g., "blog")
3. Run Script with argument
4. Show notification with result

### Raycast Script Command
1. Create new Script Command
2. Set to Python 3
3. Add script content from shortcuts_integration.py
4. Assign keyboard shortcut

---

## Troubleshooting

**"Command not found" error**:
- Ensure Python 3 is installed: `which python3`
- Use full path: `/usr/bin/python3` or `/opt/homebrew/bin/python3`

**"Module not found" error**:
- Make sure you're in the right directory
- Install dependencies: `pip3 install requests anthropic`

**Ollama not responding**:
- Check Ollama is running: `ollama list`
- Start Ollama: `ollama serve`

**Permission denied**:
- Make scripts executable: `chmod +x shortcuts_integration.py`

---

## Next Steps

1. Set up Claude API key for AI features:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.zshrc
   ```

2. Configure scheduled automations for:
   - Daily post syndication
   - Weekly summaries
   - Monthly analytics reports

3. Customize shortcuts for your workflow:
   - Add default domains
   - Pre-fill author username
   - Set post templates
