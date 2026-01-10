# Platform Integration Guide

**How to use your Soulfra Soul identity in games and applications**

Your Soul identity can be exported to multiple platforms. This guide shows you how to use the downloaded files in each supported platform.

---

## 🎮 Roblox Integration

### What You Get
A Lua ModuleScript (`.lua` file) containing:
- Your identity (username, user ID)
- Your essence (interests, expertise, values)
- Your stats (level, XP, karma)
- Deterministic color scheme (from username hash)
- Chat rules for moderation
- Sync configuration

### How to Use

#### Step 1: Download Your Soul Module
1. Visit your platform picker: `http://localhost:5001/soul/YOUR_USERNAME/platforms`
2. Click "Download Module" under Roblox
3. Save the `.lua` file (e.g., `soul_tester_soul.lua`)

#### Step 2: Add to Roblox Studio
1. Open Roblox Studio
2. In Explorer, navigate to `ServerScriptService`
3. Right-click → Insert Object → ModuleScript
4. Rename it to your username (e.g., `SoulTester`)
5. Copy the contents of your downloaded `.lua` file
6. Paste into the ModuleScript

#### Step 3: Use in Your Game
```lua
-- In any server script
local Soul = require(game.ServerScriptService.SoulTester)

-- Access identity
print("Welcome, " .. Soul:GetDisplayName())
print("You are level " .. Soul:GetLevel())

-- Use color scheme
local char = player.Character
if char then
    char.Head.BrickColor = BrickColor.new(Soul.Appearance.ColorScheme.Primary)
end

-- Check chat messages
local isValid, errorMsg = Soul:CheckChatMessage(message)
if not isValid then
    print("Message blocked: " .. errorMsg)
    return
end

-- Access interests for game mechanics
for _, interest in ipairs(Soul.Essence.Interests) do
    print("Player is interested in: " .. interest)
    -- Example: Give bonus XP for related content
end
```

### Example Game Ideas
- **Tower Defense**: Each player's interests become unique tower types
- **RPG**: Expertise determines starting abilities
- **Racing**: Color scheme applied to vehicle
- **Social Hub**: Values displayed on profile

---

## ⛏️ Minecraft Integration

### What You Get
A JSON file (`.json`) containing:
- Standard Minecraft player data (position, health, hunger, XP)
- Custom NBT section with Soul data
- Inventory with Soul items:
  - Enchanted books representing interests
  - Tools representing expertise
  - Custom lore and enchantments

### How to Use

#### Step 1: Download Your Soul Data
1. Visit your platform picker
2. Click "Download Data" under Minecraft
3. Save the `.json` file (e.g., `soul_tester_soul.json`)

#### Step 2: Server Plugin Integration (Spigot/Paper)

Create a custom plugin that reads the Soul JSON:

```java
// SoulLoader.java
public class SoulLoader extends JavaPlugin {

    @EventHandler
    public void onPlayerJoin(PlayerJoinEvent event) {
        Player player = event.getPlayer();

        // Load Soul data from JSON
        File soulFile = new File(getDataFolder(), player.getName() + "_soul.json");
        if (soulFile.exists()) {
            JSONObject soulData = loadJSON(soulFile);
            JSONObject nbt = soulData.getJSONObject("SoulfraNBT");

            // Apply Soul attributes
            applyHealth(player, soulData.getInt("Health"));
            applyLevel(player, soulData.getInt("XpLevel"));

            // Give Soul items
            JSONArray inventory = soulData.getJSONArray("Inventory");
            for (int i = 0; i < inventory.length(); i++) {
                ItemStack item = createItemFromNBT(inventory.getJSONObject(i));
                player.getInventory().addItem(item);
            }

            // Store essence data in player metadata
            JSONObject essence = nbt.getJSONObject("Essence");
            player.setMetadata("soul_interests",
                new FixedMetadataValue(this, essence.getJSONArray("Interests")));
        }
    }
}
```

#### Step 3: Use Soul Items

The generated inventory contains special items:

**Enchanted Books (Interests)**
- Name: "Soul Interest: coding"
- Lore: "This soul values coding"
- Custom NBT tag: `SoulData.Type = "Interest"`

**Tools (Expertise)**
- Diamond Pickaxe for "python" expertise
- Compass for "web" expertise
- Painting for "art" expertise
- Note Block for "music" expertise

### Example Server Ideas
- **Skills Plugin**: Interests grant passive XP bonuses
- **Quest System**: Generate quests based on Soul values
- **Economy**: Expertise affects shop prices
- **Permissions**: Grant roles based on Soul reputation

---

## 🎯 Unity / Unreal Integration

### What You Get
A JSON asset bundle containing:
- Character configuration
- Stat modifiers
- Visual appearance data
- Skill tree information

### How to Use in Unity

#### Step 1: Download Asset Bundle
1. Visit platform picker
2. Click "Download Asset" under Unity/Unreal
3. Save the `.json` file

#### Step 2: Create Importer Script

```csharp
// SoulImporter.cs
using UnityEngine;
using System.IO;

public class SoulImporter : MonoBehaviour
{
    [System.Serializable]
    public class SoulAsset {
        public CharacterData character;
        public StatData stats;
        public AppearanceData appearance;
    }

    public SoulAsset LoadSoul(string username) {
        string path = Path.Combine(Application.dataPath,
                                   "SoulAssets",
                                   username + "_soul.json");

        if (File.Exists(path)) {
            string json = File.ReadAllText(path);
            return JsonUtility.FromJson<SoulAsset>(json);
        }

        return null;
    }

    public void ApplyToCharacter(SoulAsset soul, GameObject character) {
        // Apply color scheme
        var renderer = character.GetComponent<Renderer>();
        renderer.material.color = HexToColor(soul.appearance.primaryColor);

        // Apply stats
        var stats = character.GetComponent<CharacterStats>();
        stats.maxHealth = soul.stats.health;
        stats.strength = soul.stats.strength;
        stats.intelligence = soul.stats.intelligence;

        // Grant abilities based on expertise
        var skills = character.GetComponent<SkillSystem>();
        foreach (string expertise in soul.character.expertise) {
            skills.UnlockSkill(expertise);
        }
    }
}
```

#### Step 3: Use in Game

```csharp
// PlayerController.cs
void Start() {
    SoulImporter importer = GetComponent<SoulImporter>();
    SoulAsset soul = importer.LoadSoul(playerUsername);

    if (soul != null) {
        importer.ApplyToCharacter(soul, gameObject);
        Debug.Log("Loaded Soul for " + soul.character.username);
    }
}
```

### Example Game Ideas
- **Character Creator**: Pre-configure character based on Soul
- **Skill Trees**: Unlock abilities matching expertise
- **Procedural Levels**: Generate content based on interests
- **Multiplayer**: Display Soul stats on player cards

---

## 🎙️ Voice AI / Chat Bot Integration

### What You Get
A JSON persona configuration containing:
- Personality traits
- Knowledge domains (from interests)
- Communication style
- Behavioral rules

### How to Use

#### Step 1: Download Persona Config
1. Visit platform picker
2. Click "Download Config" under Voice/AI (when available)
3. Save the `.json` file

#### Step 2: Load into AI System

**Example with OpenAI API:**

```python
import json
import openai

# Load Soul persona
with open('soul_tester_persona.json') as f:
    soul_persona = json.load(f)

# Build system prompt from Soul data
system_prompt = f"""You are {soul_persona['identity']['username']}.

Personality:
{chr(10).join('- ' + v for v in soul_persona['personality']['values'])}

Knowledge domains:
{chr(10).join('- ' + i for i in soul_persona['knowledge_domains'])}

Communication style: {soul_persona['style']}

Respond in character based on this persona.
"""

# Use in chat
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Tell me about yourself"}
    ]
)
```

**Example with Local LLM (Ollama):**

```python
import requests

def chat_as_soul(soul_persona, message):
    system_context = f"""
    You are an AI assistant with the following persona:

    Name: {soul_persona['identity']['username']}
    Expertise: {', '.join(soul_persona['knowledge_domains']['expertise'])}
    Values: {', '.join(soul_persona['personality']['values'])}
    """

    response = requests.post('http://localhost:11434/api/generate', json={
        'model': 'llama2',
        'prompt': f"{system_context}\n\nUser: {message}\nAssistant:",
        'stream': False
    })

    return response.json()['response']
```

### Example Applications
- **Chatbots**: Each user gets a personalized AI assistant
- **NPCs**: Game characters with unique personalities
- **Content Moderation**: AI trained on user's values
- **Tutoring**: AI focused on user's knowledge gaps

---

## 🌐 Web Integration

### What You Get
A complete web profile page at `/@YOUR_USERNAME`

### Features
- Personal homepage
- Blog posts
- QR codes for sharing
- Soul statistics

### How to Embed

#### Iframe Embed
```html
<iframe
    src="http://localhost:5001/@soul_tester"
    width="100%"
    height="600px"
    frameborder="0">
</iframe>
```

#### API Integration
```javascript
// Fetch Soul data via API
fetch('http://localhost:5001/api/soul/soul_tester')
    .then(res => res.json())
    .then(soul => {
        console.log('Interests:', soul.essence.interests);
        console.log('Level:', soul.expression.level);

        // Use data in your app
        displayUserCard(soul);
    });
```

---

## 🔄 Sync and Updates

All platforms support auto-sync to keep your Soul data current.

### Roblox Sync
```lua
-- Auto-sync every 60 seconds
while true do
    wait(Soul.Sync.Interval)
    Soul:SyncWithServer()
end
```

### Minecraft Sync
```java
// Schedule sync task
Bukkit.getScheduler().runTaskTimerAsynchronously(this, () -> {
    // Fetch updated Soul data from API
    JSONObject updated = fetchSoulFromAPI(player.getName());
    updatePlayerData(player, updated);
}, 0L, 60 * 20L); // Every 60 seconds
```

### Unity Sync
```csharp
IEnumerator SyncSoul() {
    while (true) {
        yield return new WaitForSeconds(60);

        string url = $"http://localhost:5001/api/soul/{username}";
        using (UnityWebRequest req = UnityWebRequest.Get(url)) {
            yield return req.SendWebRequest();

            if (req.result == UnityWebRequest.Result.Success) {
                SoulAsset updated = JsonUtility.FromJson<SoulAsset>(req.downloadHandler.text);
                ApplyToCharacter(updated, gameObject);
            }
        }
    }
}
```

---

## 📦 Testing Your Integration

1. **Create test user:**
   ```bash
   python3 create_test_soul_user.py
   ```

2. **Download platform files:**
   - Visit `http://localhost:5001/soul/soul_tester/platforms`
   - Download file for your platform

3. **Verify file format:**
   ```bash
   python3 test_soul_platform_e2e.py
   ```

4. **Integrate into your project:**
   - Follow platform-specific steps above
   - Test with sample user data
   - Verify sync works correctly

---

## 🎮 Game Template Registry (Coming Soon)

A "Steam-like" marketplace of game templates that work with Soul data:

- **Template Browser**: Browse games by platform
- **One-Click Import**: Download template + your Soul in one bundle
- **Compatibility Check**: See which templates work with your Soul
- **Community Templates**: Upload your own Soul-compatible games

---

## 🐛 Troubleshooting

### "File not downloading"
- Check that server is running on port 5001
- Verify user exists: `http://localhost:5001/souls`
- Check browser console for errors

### "Invalid JSON/Lua format"
- Run test suite: `python3 test_soul_platform_e2e.py`
- Check `platform_outputs/` directory for generated files
- Verify Soul Pack compiles: `python3 -c "from soul_model import Soul; Soul(USER_ID).compile_pack()"`

### "Empty inventory in Minecraft"
- User needs posts/comments to generate Soul items
- Interests become enchanted books
- Expertise becomes tools
- Create content then re-download

### "Sync not working"
- Check API endpoint is accessible
- Verify server is running
- Check firewall settings
- Look for CORS issues in browser console

---

## 💡 Need Help?

- **Documentation**: See `README.md` and `HOW_IT_ACTUALLY_WORKS.md`
- **Test Scripts**: Run `create_test_soul_user.py` and `test_soul_platform_e2e.py`
- **Example Code**: Check platform connector source in `platform_connectors/`
- **API Docs**: Visit `http://localhost:5001/api/docs` (if available)

---

**Built with ❤️ by the Soulfra team**
