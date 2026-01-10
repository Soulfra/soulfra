# How Friends Can Add Their Code

**You asked:** "how do my friends' codes work/get used somehow with the logins or soulfra?"

**Answer:** Here are 4 ways friends can contribute code to your Soulfra app.

---

## Method 1: Git Branches (Recommended for Beginners)

**Best for:** Friends who know basic git

### Setup (One Time)

1. **Push your code to GitHub:**
   ```bash
   cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple

   # Initialize git if not already
   git init
   git add .
   git commit -m "Initial commit"

   # Create repo on GitHub, then:
   git remote add origin https://github.com/YOUR_USERNAME/soulfra-simple.git
   git push -u origin main
   ```

2. **Add friend as collaborator:**
   - Go to: `https://github.com/YOUR_USERNAME/soulfra-simple/settings/access`
   - Click "Add people"
   - Enter friend's GitHub username
   - They get email invite

### Friend Workflow

**Friend clones repo:**
```bash
git clone https://github.com/YOUR_USERNAME/soulfra-simple.git
cd soulfra-simple
```

**Friend creates branch for their feature:**
```bash
git checkout -b friend-calculator-feature
```

**Friend adds their route:**

Create `friend_calculator.py`:
```python
from flask import Blueprint, jsonify, request

calculator_bp = Blueprint('calculator', __name__)

@calculator_bp.route('/calc/add')
def add_numbers():
    a = request.args.get('a', type=int)
    b = request.args.get('b', type=int)
    return jsonify({'result': a + b})

@calculator_bp.route('/calc/multiply')
def multiply_numbers():
    a = request.args.get('a', type=int)
    b = request.args.get('b', type=int)
    return jsonify({'result': a * b})
```

**Friend registers their blueprint in app.py:**

```python
# At the top of app.py, add:
from friend_calculator import calculator_bp
app.register_blueprint(calculator_bp)
```

**Friend commits and pushes:**
```bash
git add friend_calculator.py app.py
git commit -m "Added calculator routes"
git push origin friend-calculator-feature
```

**Friend creates pull request:**
- Go to GitHub repo
- Click "Pull requests" → "New pull request"
- Select `friend-calculator-feature` branch
- Click "Create pull request"
- Write description: "Added calculator routes for math operations"

**You review and merge:**
- Go to pull request
- Review code
- Click "Merge pull request"
- Pull changes on your laptop:
  ```bash
  git pull origin main
  ```
- Restart Flask:
  ```bash
  pkill -f "python3 app.py"
  python3 app.py
  ```

**Now everyone can use:**
```
http://192.168.1.87:5001/calc/add?a=5&b=3
# Returns: {"result": 8}
```

### Pros
- ✅ Code review before merging
- ✅ Version history
- ✅ Easy to revert if broken
- ✅ Industry standard workflow

### Cons
- ❌ Requires git knowledge
- ❌ Requires GitHub account
- ❌ Friend needs to wait for you to merge

---

## Method 2: Live Plugin System (Instant)

**Best for:** Friends who want to test code immediately

### Setup (One Time)

**Create plugins folder:**
```bash
mkdir -p /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/plugins
```

**Update app.py to auto-load plugins:**

Add this at the end of app.py:
```python
# Auto-load plugins
import os
from importlib import import_module

plugins_dir = 'plugins'
if os.path.exists(plugins_dir):
    for filename in os.listdir(plugins_dir):
        if filename.endswith('.py') and not filename.startswith('_'):
            module_name = filename[:-3]  # Remove .py
            try:
                module = import_module(f'plugins.{module_name}')
                if hasattr(module, 'register'):
                    module.register(app)
                    print(f"✅ Loaded plugin: {module_name}")
            except Exception as e:
                print(f"❌ Failed to load plugin {module_name}: {e}")
```

### Friend Workflow

**Friend creates plugin file:**

`plugins/jane_todo.py`:
```python
from flask import Blueprint, jsonify, request

jane_bp = Blueprint('jane', __name__, url_prefix='/jane')

# In-memory storage (replace with database later)
todos = []

@jane_bp.route('/todos')
def list_todos():
    return jsonify(todos)

@jane_bp.route('/todo/add', methods=['POST'])
def add_todo():
    todo = request.json.get('todo')
    todos.append(todo)
    return jsonify({'success': True, 'todos': todos})

def register(app):
    """This function is called by plugin loader"""
    app.register_blueprint(jane_bp)
```

**Friend saves file:**
```bash
# Via Slack, email, or direct file share
# You save it to: plugins/jane_todo.py
```

**Restart Flask:**
```bash
pkill -f "python3 app.py"
python3 app.py
```

**Friend's routes are now live:**
```bash
# Test it
curl -X POST http://192.168.1.87:5001/jane/todo/add \
  -H "Content-Type: application/json" \
  -d '{"todo": "Build something cool"}'

curl http://192.168.1.87:5001/jane/todos
```

### Pros
- ✅ No git required
- ✅ Instant deployment (just restart Flask)
- ✅ Isolated code (doesn't affect main app)
- ✅ Easy to disable (just delete plugin file)

### Cons
- ❌ No version control
- ❌ Can break if plugin has errors
- ❌ All plugins share same database

---

## Method 3: Direct Database Access (Read-Only)

**Best for:** Friends who want to build frontend apps using your data

### Setup (One Time)

**Create API endpoint to expose database:**

Add to app.py:
```python
@app.route('/api/public/professionals')
def public_professionals():
    """Read-only access to professional directory"""
    db = get_db()
    pros = db.execute('''
        SELECT id, business_name, category, city, state
        FROM professionals
        ORDER BY created_at DESC
        LIMIT 100
    ''').fetchall()

    return jsonify([dict(p) for p in pros])

@app.route('/api/public/messages/<int:user_id>')
def public_messages(user_id):
    """Read-only access to user's messages"""
    db = get_db()

    # Check if user is authenticated
    if not session.get('user_id') == user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    messages = db.execute('''
        SELECT * FROM messages
        WHERE to_user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,)).fetchall()

    return jsonify([dict(m) for m in messages])
```

### Friend Workflow

**Friend builds their own frontend:**

Create `friend_app.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Friend's Professional Viewer</title>
</head>
<body>
    <h1>Professionals</h1>
    <div id="professionals"></div>

    <script>
        async function loadProfessionals() {
            const response = await fetch('http://192.168.1.87:5001/api/public/professionals');
            const professionals = await response.json();

            const html = professionals.map(p => `
                <div>
                    <h3>${p.business_name}</h3>
                    <p>${p.category} - ${p.city}, ${p.state}</p>
                </div>
            `).join('');

            document.getElementById('professionals').innerHTML = html;
        }

        loadProfessionals();
    </script>
</body>
</html>
```

**Friend opens in browser:**
```
file:///path/to/friend_app.html
```

Their frontend fetches data from your Flask API!

### Pros
- ✅ Friend doesn't need Python knowledge
- ✅ Can use any language (React, Vue, vanilla JS)
- ✅ Read-only (safe, can't break database)
- ✅ Friend can host their own UI

### Cons
- ❌ Read-only (can't write data)
- ❌ Needs CORS enabled
- ❌ Limited to exposed endpoints

---

## Method 4: Shared Development Server (Advanced)

**Best for:** Roommates, hackathon teams, real-time collaboration

### Setup (Requires SSH or Screen Sharing)

**Option A: SSH Access**

1. **Enable Remote Login on your Mac:**
   - System Preferences → Sharing
   - Enable "Remote Login"
   - Add friend's username

2. **Create account for friend:**
   ```bash
   sudo dscl . -create /Users/friend
   sudo dscl . -create /Users/friend UserShell /bin/bash
   sudo dscl . -create /Users/friend RealName "Friend Name"
   sudo dscl . -passwd /Users/friend friend_password
   ```

3. **Friend connects:**
   ```bash
   ssh friend@192.168.1.87
   ```

4. **Friend edits code:**
   ```bash
   cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
   nano app.py  # or vim, or code
   ```

**Option B: VS Code Live Share**

1. **Install VS Code Live Share:**
   - Open VS Code
   - Install "Live Share" extension

2. **Start live session:**
   - Click "Live Share" in status bar
   - Click "Start collaboration session"
   - Copy link

3. **Share link with friend:**
   - Friend opens link in VS Code
   - Friend can edit files in real-time
   - Both see changes instantly

**Option C: tmux Shared Session**

1. **Install tmux:**
   ```bash
   brew install tmux
   ```

2. **Start shared session:**
   ```bash
   tmux new-session -s soulfra
   ```

3. **Friend connects (via SSH):**
   ```bash
   ssh friend@192.168.1.87
   tmux attach-session -t soulfra
   ```

4. **Both edit same terminal:**
   - Both see same screen
   - Both can type
   - Instant collaboration

### Pros
- ✅ Real-time editing
- ✅ Instant testing
- ✅ Great for pair programming
- ✅ No git complexity

### Cons
- ❌ Requires trust (friend has full file access)
- ❌ Can overwrite each other's changes
- ❌ Security risk if not careful

---

## How Soulfra Login Works for Friends

**All 4 methods use the SAME authentication system:**

### Friend Creates Account

1. **Friend visits:** `http://192.168.1.87:5001/signup/professional`
2. **Redirected to login:** `/login`
3. **Friend clicks:** "Create Soulfra Account"
4. **Friend enters:** Email, password, name
5. **Account created in:** `soulfra_master_users` table (your database)
6. **JWT token issued:** Stored in cookie
7. **Friend is logged in:** Can access protected routes

### Cross-Domain Login

**Soulfra Master Auth = ONE login for ALL domains**

When friend logs in on `soulfra.com`, they're ALSO logged in on:
- `stpetepros.com`
- `cringeproof.com`
- All other configured domains

**How it works:**
```python
# JWT token stored in cookie
# Cookie domain: .soulfra.com (wildcard)
# Works across all subdomains

# Example token:
{
    "user_id": 42,
    "email": "friend@example.com",
    "master_user_id": 42,
    "exp": 1234567890  # Expiration
}
```

### Friend-Specific Features

**Friend can:**
- Create their own professional profile
- Send/receive messages via inbox
- Use voice recording
- Access all public routes
- Use their custom routes (if added via plugin)

**Friend CANNOT:**
- Access other users' private data
- Delete database
- Modify other users' accounts
- See encrypted data without key

---

## Database Permissions

**SQLite by default = NO user permissions**

Everyone who can access the database file can read/write everything.

### Option 1: Trust System (Default)

- All friends share same database
- No restrictions
- Honor system: "Don't delete others' data"

**Good for:** Small teams, trusted friends

### Option 2: Application-Level Permissions

**Add permission checks in routes:**

```python
@app.route('/professional/<int:id>/edit', methods=['POST'])
def edit_professional(id):
    # Check if user owns this profile
    db = get_db()
    pro = db.execute('SELECT user_id FROM professionals WHERE id = ?', (id,)).fetchone()

    if pro['user_id'] != session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 403

    # Allow edit
    db.execute('UPDATE professionals SET ...', (...))
    db.commit()
    return jsonify({'success': True})
```

**Good for:** Protecting sensitive data

### Option 3: Separate Databases Per User

**Create database for each friend:**

```python
def get_user_db(user_id):
    db_path = f'databases/user_{user_id}.db'
    return sqlite3.connect(db_path)

@app.route('/friend/data')
def friend_data():
    user_id = session.get('user_id')
    db = get_user_db(user_id)
    # Query friend's personal database
```

**Good for:** Complete isolation

---

## Quick Start for Friends

### Friend Wants to Add a Simple Route

**Send them this template:**

```python
# Save as: plugins/YOUR_NAME.py

from flask import Blueprint, jsonify, request

# Replace YOUR_NAME with your name
YOUR_NAME_bp = Blueprint('YOUR_NAME', __name__, url_prefix='/YOUR_NAME')

@YOUR_NAME_bp.route('/hello')
def hello():
    return "Hello from YOUR_NAME's code!"

@YOUR_NAME_bp.route('/data')
def my_data():
    # Your custom logic here
    return jsonify({
        'message': 'Your data',
        'value': 42
    })

def register(app):
    app.register_blueprint(YOUR_NAME_bp)
```

**Steps:**
1. Replace `YOUR_NAME` with your actual name
2. Save file as `plugins/yourname.py`
3. Restart Flask
4. Access: `http://192.168.1.87:5001/yourname/hello`

---

## Security Best Practices

### For You (Host)

- ✅ Review all code before merging
- ✅ Use git branches, not direct edits
- ✅ Backup database before friend tests
- ✅ Set up `.gitignore` to exclude secrets
- ✅ Use environment variables for API keys
- ❌ Don't share `domain_config/secrets.env`
- ❌ Don't give SSH access to untrusted friends

### For Friends

- ✅ Use pull requests, not force push
- ✅ Test locally before pushing
- ✅ Add comments to your code
- ✅ Ask before accessing database directly
- ❌ Don't commit secrets or API keys
- ❌ Don't delete other people's data
- ❌ Don't spam the database with test data

---

## Troubleshooting

### Friend's code causes crash

**Symptom:** Flask won't start, error on screen

**Fix:**
```bash
# Disable their plugin
mv plugins/friend_code.py plugins/friend_code.py.disabled

# Or remove from app.py if registered there
# Comment out:
# from friend_code import friend_bp
# app.register_blueprint(friend_bp)

# Restart
python3 app.py
```

### Friend can't login

**Symptom:** "Invalid credentials" or redirect loop

**Fix:**
```bash
# Check if user exists
sqlite3 soulfra.db "SELECT * FROM soulfra_master_users WHERE email = 'friend@example.com';"

# Reset password manually
sqlite3 soulfra.db "UPDATE soulfra_master_users SET password_hash = 'temp_hash' WHERE email = 'friend@example.com';"
```

### Friend's route conflicts with yours

**Symptom:** `/calc/add` returns wrong result

**Fix:**
```python
# Use URL prefix to avoid conflicts
friend_bp = Blueprint('friend', __name__, url_prefix='/friend')

# Now routes are:
# /friend/calc/add  (friend's code)
# /calc/add         (your code)
```

---

## Next Steps

**Choose collaboration method:**

| Method | Best For | Difficulty |
|--------|----------|-----------|
| Git Branches | Remote friends | Medium |
| Plugin System | Quick testing | Easy |
| API Access | Frontend devs | Easy |
| Shared Server | Roommates | Hard |

**Then:**
1. Set up chosen method (see sections above)
2. Invite friend to add their code
3. Test together
4. Deploy to more friends!

**Need help?**
- See `LOCAL_NETWORK_SETUP.md` for sharing your server
- See `SIMPLE_README.md` for project overview

---

**Your friends can now build features with you!** 🤝
