# Theme Builder Guide - Build Your Own Blog Theme

**Create professional, custom themes for your Soulfra blog without coding**

---

## What is the Theme Builder?

The Theme Builder lets you:

- **Choose from 5 pre-built themes** (light, dark, professional, creative, technical)
- **Customize colors, fonts, and layouts** with simple commands
- **Export/import themes** to share with others or backup
- **Apply themes instantly** with one command
- **Build from scratch** if you want complete control

**No CSS knowledge required!** (But you can add custom CSS if you want.)

---

## Quick Start (5 Minutes)

### 1. List Available Themes

```bash
python3 theme_builder.py list
```

**Output:**
```
Available Themes:

☀️ Minimal Light
   Name: minimal-light
   Description: Clean and minimal light theme
   Author: Soulfra

🌙 Minimal Dark
   Name: minimal-dark
   Description: Clean and minimal dark theme
   Author: Soulfra

💼 Professional
   Name: professional
   Description: Professional business theme with blue accents
   Author: Soulfra

🎨 Creative
   Name: creative
   Description: Colorful creative theme for artists and designers
   Author: Soulfra

💻 Technical
   Name: technical
   Description: Developer-focused theme with monospace fonts
   Author: Soulfra
```

### 2. Apply a Theme

```bash
python3 theme_builder.py apply minimal-dark
```

**Output:**
```
✓ Applied theme 'minimal-dark'
  CSS written to: static/css/theme.css
```

### 3. Restart Server (to see changes)

```bash
# Stop server (Ctrl+C)
# Start server
python3 app.py
```

### 4. Open Browser

```bash
open http://localhost:5001
```

**Done!** Your blog now has a dark theme.

---

## Pre-Built Themes

### Minimal Light (Default)

**Best for:** Clean, distraction-free blogs

**Colors:**
- Primary: Black (#000000)
- Accent: Blue (#0066cc)
- Background: White (#ffffff)

**Font:** Inter (modern sans-serif)

**Use case:** Personal blogs, writing-focused sites

---

### Minimal Dark

**Best for:** Night reading, developer blogs

**Colors:**
- Primary: White (#ffffff)
- Accent: Light Blue (#60a5fa)
- Background: Dark Gray (#1a202c)

**Font:** JetBrains Mono (monospace)

**Use case:** Tech blogs, late-night writing

---

### Professional

**Best for:** Business, corporate, portfolios

**Colors:**
- Primary: Navy Blue (#1e40af)
- Accent: Sky Blue (#0ea5e9)
- Background: White (#ffffff)

**Font:** Helvetica Neue (business standard)

**Use case:** Professional portfolios, company blogs

---

### Creative

**Best for:** Art, design, creative portfolios

**Colors:**
- Primary: Pink (#ec4899)
- Secondary: Purple (#8b5cf6)
- Accent: Orange (#f59e0b)
- Background: Warm Yellow (#fefce8)

**Font:** Comic Sans MS (playful)

**Use case:** Artists, designers, creative agencies

---

### Technical

**Best for:** Developer documentation, code-heavy blogs

**Colors:**
- Primary: Green (#22c55e)
- Accent: Lime (#84cc16)
- Background: Black (#0c0c0c)

**Font:** Fira Code (code font with ligatures)

**Use case:** Dev blogs, documentation, tutorials

---

## Customizing Themes

### Example: Create Your Own Theme

Let's create a custom theme called "my-brand" with your brand colors:

```bash
python3 theme_builder.py customize minimal-light my-brand
```

This creates a new theme based on "minimal-light". Now edit it:

```python
from theme_builder import ThemeBuilder

builder = ThemeBuilder()

# Customize your theme
builder.customize_theme(
    base_theme_name='minimal-light',
    new_theme_name='my-brand',
    customizations={
        'display_name': 'My Brand Theme',
        'description': 'Custom theme for my blog',
        'colors': {
            'primary': '#ff0066',       # Hot pink
            'accent': '#00ffcc',        # Cyan
            'bg_primary': '#ffffff',    # White
            'text_primary': '#1a1a1a'   # Almost black
        },
        'typography': {
            'font_family': '"Montserrat", sans-serif',
            'font_size_base': '18px'
        },
        'layout': {
            'max_width': '900px',       # Narrower content
            'border_radius': '12px'     # Rounder corners
        }
    }
)
```

**Apply it:**
```bash
python3 theme_builder.py apply my-brand
```

---

## Theme Configuration Reference

### Colors

All themes support these color variables:

```python
colors = {
    # Primary colors
    'primary': '#3b82f6',         # Main brand color
    'secondary': '#8b5cf6',       # Secondary brand color
    'accent': '#10b981',          # Accent/highlight color

    # Backgrounds
    'bg_primary': '#ffffff',      # Main background
    'bg_secondary': '#f3f4f6',    # Secondary background (cards, etc.)
    'bg_tertiary': '#e5e7eb',     # Tertiary background (hover, etc.)

    # Text
    'text_primary': '#111827',    # Main text color
    'text_secondary': '#6b7280',  # Secondary text (captions, etc.)
    'text_tertiary': '#9ca3af',   # Tertiary text (disabled, etc.)

    # Status colors
    'success': '#10b981',         # Green for success
    'warning': '#f59e0b',         # Orange for warnings
    'error': '#ef4444',           # Red for errors
    'info': '#3b82f6',            # Blue for info

    # Borders
    'border': '#e5e7eb',          # Default border color
    'border_focus': '#3b82f6'     # Border when focused
}
```

### Typography

```python
typography = {
    # Font families
    'font_family': '-apple-system, sans-serif',
    'font_family_mono': 'Monaco, monospace',

    # Font sizes
    'font_size_xs': '0.75rem',    # 12px
    'font_size_sm': '0.875rem',   # 14px
    'font_size_base': '1rem',     # 16px
    'font_size_lg': '1.125rem',   # 18px
    'font_size_xl': '1.25rem',    # 20px
    'font_size_2xl': '1.5rem',    # 24px
    'font_size_3xl': '1.875rem',  # 30px
    'font_size_4xl': '2.25rem',   # 36px

    # Line heights
    'line_height_tight': '1.25',
    'line_height_normal': '1.5',
    'line_height_relaxed': '1.75'
}
```

### Spacing

```python
spacing = {
    'xs': '0.25rem',   # 4px
    'sm': '0.5rem',    # 8px
    'md': '1rem',      # 16px
    'lg': '1.5rem',    # 24px
    'xl': '2rem',      # 32px
    'xxl': '3rem'      # 48px
}
```

### Layout

```python
layout = {
    'max_width': '1200px',        # Max content width
    'sidebar_width': '250px',     # Sidebar width
    'header_height': '60px',      # Header height
    'footer_height': '80px',      # Footer height
    'border_radius': '0.375rem',  # Corner roundness
    'border_width': '1px'         # Border thickness
}
```

---

## Export/Import Themes

### Export a Theme (to share or backup)

```bash
python3 theme_builder.py export my-brand > my-brand-theme.json
```

**Output (my-brand-theme.json):**
```json
{
  "name": "my-brand",
  "display_name": "My Brand Theme",
  "description": "Custom theme for my blog",
  "author": "Custom",
  "version": "1.0.0",
  "dark_mode": false,
  "colors": {
    "primary": "#ff0066",
    "accent": "#00ffcc",
    ...
  },
  "typography": { ... },
  "spacing": { ... },
  "layout": { ... }
}
```

### Import a Theme

```bash
cat my-brand-theme.json | python3 -c "
import sys, json
from theme_builder import ThemeBuilder

builder = ThemeBuilder()
theme_config = json.load(sys.stdin)
builder.import_theme(theme_config)
print('✓ Theme imported!')
"
```

---

## Advanced: Custom CSS

Every theme supports custom CSS for complete control.

**Example:**

```python
from theme_builder import ThemeBuilder

builder = ThemeBuilder()

custom_css = '''
/* Custom animations */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.post {
    animation: fadeIn 0.5s ease-in;
}

/* Custom button hover effect */
.btn-primary:hover {
    transform: scale(1.05);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 10px;
}

::-webkit-scrollbar-thumb {
    background: var(--color-primary);
    border-radius: 5px;
}
'''

builder.customize_theme(
    base_theme_name='minimal-dark',
    new_theme_name='animated-dark',
    customizations={
        'display_name': 'Animated Dark',
        'custom_css': custom_css
    }
)

builder.apply_theme('animated-dark')
```

---

## Using Themes in Code

### Python (Backend)

```python
from theme_builder import ThemeBuilder

# Initialize
builder = ThemeBuilder()

# Get available themes
themes = builder.list_themes()
for theme in themes:
    print(f"{theme['display_name']}: {theme['description']}")

# Apply theme programmatically
builder.apply_theme('minimal-dark', output_path='static/css/theme.css')

# Generate CSS string (without writing file)
theme = builder.get_theme('minimal-dark')
css = builder.generate_css(theme)
print(css)
```

### Flask Integration

```python
from flask import Flask, render_template
from theme_builder import ThemeBuilder

app = Flask(__name__)
builder = ThemeBuilder()

@app.route('/themes')
def list_themes():
    themes = builder.list_themes()
    return render_template('themes.html', themes=themes)

@app.route('/theme/apply/<theme_name>', methods=['POST'])
def apply_theme(theme_name):
    try:
        builder.apply_theme(theme_name)
        return {'success': True}
    except ValueError:
        return {'error': 'Theme not found'}, 404
```

---

## CLI Reference

### List Themes

```bash
python3 theme_builder.py list
```

### Apply Theme

```bash
python3 theme_builder.py apply <theme-name>
```

### Export Theme

```bash
python3 theme_builder.py export <theme-name>
```

### Customize Theme

```bash
python3 theme_builder.py customize <base-theme> <new-name>
```

---

## Troubleshooting

### Theme Not Applying

**Problem:** Changed theme but blog looks the same.

**Solution:**
1. Make sure you restarted the server after applying theme
2. Hard refresh browser: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
3. Check that `static/css/theme.css` was updated:
   ```bash
   ls -lh static/css/theme.css
   ```

### Colors Look Wrong

**Problem:** Colors don't match what you specified.

**Solution:**
1. Verify hex color format: `#rrggbb` (e.g., `#ff0066`, not `ff0066`)
2. Check theme was saved correctly:
   ```bash
   python3 -c "from theme_builder import ThemeBuilder; b = ThemeBuilder(); print(b.get_theme('my-theme').colors.primary)"
   ```
3. Re-apply theme:
   ```bash
   python3 theme_builder.py apply my-theme
   ```

### Font Not Loading

**Problem:** Custom font not displaying.

**Solution:**
1. Make sure font is web-safe or add web font import to custom CSS:
   ```css
   @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
   ```
2. Use font family fallbacks:
   ```python
   'font_family': '"Inter", -apple-system, BlinkMacSystemFont, sans-serif'
   ```

---

## Best Practices

### 1. Start with a Base Theme

Don't build from scratch. Always start with a pre-built theme and customize:

```bash
# Good
python3 theme_builder.py customize minimal-light my-theme

# Harder (not recommended for beginners)
# Building entire theme from scratch
```

### 2. Test in Both Light and Dark

Make sure your theme works in both modes:

```python
# Create light version
builder.customize_theme('minimal-light', 'my-theme-light', {...})

# Create dark version
builder.customize_theme('minimal-dark', 'my-theme-dark', {...})
```

### 3. Use CSS Variables

The theme system generates CSS variables like `var(--color-primary)`. Use these in custom CSS:

```css
/* Good - uses theme variable */
.my-button {
    background: var(--color-primary);
}

/* Bad - hardcoded color */
.my-button {
    background: #3b82f6;
}
```

### 4. Export and Backup

Always export your custom themes:

```bash
python3 theme_builder.py export my-theme > backups/my-theme-$(date +%Y%m%d).json
```

### 5. Version Control

Commit themes to git:

```bash
git add themes/my-theme.json
git commit -m "Add custom theme"
```

---

## Examples

### Example 1: Personal Blog

```python
builder.customize_theme(
    'minimal-light',
    'personal-blog',
    {
        'colors': {
            'primary': '#2563eb',      # Blue
            'accent': '#10b981',       # Green
            'bg_primary': '#ffffff'
        },
        'typography': {
            'font_family': '"Georgia", serif',  # Readable font
            'font_size_base': '18px',          # Larger text
            'line_height_normal': '1.7'        # More spacing
        },
        'layout': {
            'max_width': '700px'  # Narrow for readability
        }
    }
)
```

### Example 2: Tech Blog

```python
builder.customize_theme(
    'technical',
    'dev-blog',
    {
        'colors': {
            'primary': '#22c55e',      # Matrix green
            'bg_primary': '#0a0a0a',   # Almost black
        },
        'typography': {
            'font_family': '"Fira Code", monospace'
        }
    }
)
```

### Example 3: Creative Portfolio

```python
builder.customize_theme(
    'creative',
    'artist-portfolio',
    {
        'colors': {
            'primary': '#ec4899',       # Hot pink
            'secondary': '#8b5cf6',     # Purple
            'accent': '#f59e0b',        # Orange
            'bg_primary': '#fffbeb'     # Cream
        },
        'layout': {
            'max_width': '1600px',      # Wide for images
            'border_radius': '20px'     # Very round
        }
    }
)
```

---

## Next Steps

1. **Try all pre-built themes** to find your favorite
2. **Customize one** to match your brand
3. **Export it** for backup
4. **Share it** with the community!

---

## Related Documentation

- **ENCRYPTION_TIERS.md** - Security at each deployment tier
- **NETWORK_GUIDE.md** - Understanding the network stack
- **hello_world_blog.md** - Test your theme on the demo post
- **customer_onboarding.sh** - Set up blog with theme selection

---

## Support

**Need help?**
- GitHub: https://github.com/soulfra
- Docs: /@docs/THEME_BUILDER_GUIDE
- Issues: Report bugs on GitHub

**Built with Soulfra - Open Source Blog Platform** 🎨
