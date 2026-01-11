# 🧪 Soulfra Testing Guide

**Quick Start:** Login and explore what's working RIGHT NOW

---

## 🚀 Start the Server

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
python3 app.py
```

Server starts at: `http://localhost:5001`

---

## 🔑 Test Accounts

### Admin Account
- **Username:** `admin`
- **Email:** `admin@soulfra.local`
- **Password:** Check database or reset if needed

### Soul Tester Account
- **Username:** `soul_tester`
- **Email:** `soul_tester@soulfra.local`
- **Password:** Check database or reset if needed

### Create Your Own Test Account

```bash
python3 -c "
from db_helpers import create_user
user_id = create_user('yourname', 'you@example.com', 'yourpassword')
print(f'✅ Created user ID: {user_id}')
"
```

---

## ✅ What You Can Test NOW

### 1. Login System

**URL:** `http://localhost:5001/login`

**Test:**
1. Enter username + password
2. Click "Login"
3. Should redirect to homepage

**What to check:**
- Session persists (you stay logged in)
- Can logout
- Invalid credentials rejected

---

### 2. Games Gallery

**URL:** `http://localhost:5001/games`

**Test:**
1. View available games
2. See "2+2 Math Game" (playable!)
3. See "Chess" and "D&D Campaign" (coming soon)

**What to check:**
- Games list displays
- Icons and descriptions visible
- "Play Now" vs "Coming Soon" status

---

### 3. 2+2 Math Game (FULLY WORKING!)

**URL:** `http://localhost:5001/games/play/2plus2`

**Test:**
1. Start game
2. Answer "What is 2 + 2?"
3. Submit answer (try 4, then try wrong answer like 5)
4. See AI verdict

**What to check:**
- Game creates session in database
- AI judges your answer using Ollama (if running)
- Correct answer = success
- Wrong answer = failure
- Game action logged to `game_actions` table

---

### 4. Membership System

**Check in Database:**

```bash
sqlite3 soulfra.db "SELECT user_id, tier, status FROM memberships;"
```

**Test:**
1. View your membership tier (should be 'free')
2. Check inventory limit (10 items for free tier)
3. Check trade limit (1 trade/day for free tier)

**Simulate upgrade to Premium:**

```bash
python3 -c "
from stripe_membership import simulate_upgrade
simulate_upgrade(1, 'premium')  # Upgrade user ID 1
"
```

---

### 5. Character Age & Attributes

**Check your character:**

```bash
sqlite3 soulfra.db "SELECT id, username, character_age, total_years_aged FROM users;"
```

**Calculate aging:**

```bash
python3 aging_curves.py
```

**What to check:**
- All users start at age 20
- Attributes calculated based on age
- Aging curves visualized (agility, wisdom, etc.)

---

### 6. Quests System

**View available quests:**

```bash
sqlite3 soulfra.db "SELECT quest_slug, name, difficulty, aging_years, rewards FROM quests WHERE active = 1;"
```

**Quests available:**
1. **Welcome to Adventure** (Easy, ages +2 years)
2. **Goblin Caves** (Medium, ages +5 years)
3. **Dragon Slayer** (Legendary, ages +10 years)
4. **Lost Temple** (Hard, ages +7 years)

**Note:** Quest UI not built yet - can see in database only

---

### 7. Items System

**View all items:**

```bash
sqlite3 soulfra.db "SELECT name, rarity, item_type, stats FROM items;"
```

**Items available:**
- Weapons: Wooden Sword, Steel Sword, Dragon Slayer
- Armor: Leather Armor, Plate Armor
- Potions: Health Potion, Mana Potion
- Scrolls: Fireball Scroll, Teleport Scroll
- Materials: Dragon Scale, Iron Ore
- Quest Items: Ancient Key

**Note:** Item economy works, trading UI not built yet

---

### 8. QR Code System

**Generate QR code:**

```bash
python3 -c "
from brand_qr_generator import generate_brand_qr
generate_brand_qr('deathtodata')
print('✅ QR code saved: deathtodata-qr.bmp')
"
```

**Test:**
1. Open QR code: `open deathtodata-qr.bmp`
2. Scan with phone camera
3. Opens: `http://192.168.1.123:5001/brand/deathtodata`
4. Can signup from phone

---

## 🔍 Database Exploration

### View All Tables

```bash
sqlite3 soulfra.db ".tables"
```

### Check System Stats

```bash
sqlite3 soulfra.db "
SELECT
  (SELECT COUNT(*) FROM users) as users,
  (SELECT COUNT(*) FROM brands) as brands,
  (SELECT COUNT(*) FROM quests) as quests,
  (SELECT COUNT(*) FROM items) as items,
  (SELECT COUNT(*) FROM memberships) as memberships,
  (SELECT COUNT(*) FROM inventory) as inventory_items;
"
```

### View Game Actions (if you played 2+2)

```bash
sqlite3 soulfra.db "
SELECT
  ga.action_id,
  u.username,
  ga.action_type,
  ga.ai_verdict,
  ga.processed_at
FROM game_actions ga
JOIN users u ON ga.player_user_id = u.id
ORDER BY ga.processed_at DESC
LIMIT 5;
"
```

---

## ⚠️ What's NOT Working Yet

These exist in database but NO UI/routes:

1. **D&D Campaign Gameplay**
   - Database: quests, quest_progress tables ✅
   - Game logic: 60% done
   - UI template: ❌ Not created
   - Routes: ❌ Not added to app.py

2. **Trading System**
   - Database: trades, trade_limits tables ✅
   - Logic: trading_system.py ❌ Not created
   - UI template: ❌ Not created
   - Routes: ❌ Not added to app.py

3. **Membership Upgrade Page**
   - Stripe integration: ✅ Working
   - Checkout: ✅ Can create sessions
   - UI page: ❌ Not created
   - Route: ❌ Not added to app.py

4. **Character Sheet**
   - Database: character_age, aging curves ✅
   - Calculation: aging_curves.py ✅ Working
   - UI display: ❌ Not created

---

## 📊 Expected Test Results

### After Playing 2+2 Game:

```bash
sqlite3 soulfra.db "SELECT * FROM game_sessions WHERE game_type = '2plus2' ORDER BY created_at DESC LIMIT 1;"
```

Should show:
- session_name: "2+2 Math Quiz"
- game_type: "2plus2"
- creator_user_id: Your user ID
- status: "active" or "completed"

### After Simulating Membership Upgrade:

```bash
python3 stripe_membership.py
```

Should show:
- Tier upgraded to "premium"
- Inventory limit: Unlimited
- Trades/day: 10

### After Running Aging Curves:

```bash
python3 aging_curves.py
```

Should show:
- Aging curves table (agility, wisdom, etc. by age)
- Quest aging simulation (25 years → 35 years)
- Age milestones (peaks at different ages)

---

## 🐛 Troubleshooting

### Can't Login

```bash
# Reset admin password
python3 -c "
from db_helpers import create_user
import sqlite3
conn = sqlite3.connect('soulfra.db')
conn.execute('DELETE FROM users WHERE username = \"admin\"')
conn.commit()
create_user('admin', 'admin@soulfra.local', 'admin123')
print('✅ Admin password reset to: admin123')
"
```

### Ollama Not Running (2+2 Game)

Game will still work - it just falls back to rule-based logic instead of AI judging.

To start Ollama:
```bash
ollama serve
```

### Database Locked

```bash
# Close any open connections
pkill -f "sqlite3 soulfra.db"
```

### Port 5001 Already in Use

```bash
# Kill process on port 5001
lsof -ti:5001 | xargs kill -9
```

---

## ✅ Success Checklist

After testing, you should have confirmed:

- [ ] Can login with test account
- [ ] Games gallery displays
- [ ] 2+2 math game works end-to-end
- [ ] Game action logged to database
- [ ] Membership tier visible (free by default)
- [ ] Character age visible in database (20 years old)
- [ ] Quests exist in database (4 quests)
- [ ] Items exist in database (12 items)
- [ ] Aging curves calculate correctly
- [ ] QR code generates successfully

---

## 📝 Next Steps

After testing, you can:

1. **Build D&D Campaign** (~1.5 hours)
   - Complete quest gameplay
   - Create character sheet UI
   - Add game routes

2. **Build Trading System** (~30 min)
   - Create trading UI
   - Add trade routes
   - Test player-to-player trades

3. **Add Membership Pages** (~20 min)
   - Create upgrade UI
   - Add Stripe checkout route
   - Test payment flow

4. **Document Everything** (~30 min)
   - Create system overview
   - Visual architecture diagram
   - User guide

---

## 🎯 Test in Order:

1. **Start server** → `python3 app.py`
2. **Login** → `http://localhost:5001/login`
3. **View games** → `http://localhost:5001/games`
4. **Play 2+2** → Click "Play Now"
5. **Check database** → `sqlite3 soulfra.db "SELECT * FROM game_actions;"`
6. **Run aging test** → `python3 aging_curves.py`
7. **Test membership** → `python3 stripe_membership.py`

**Total test time:** ~20 minutes

---

**Generated:** 2025-12-25
**Platform:** Soulfra Simple (localhost:5001)
**Database:** soulfra.db (1.1MB, 76 tables)
**Status:** Core systems working, game UI in progress
