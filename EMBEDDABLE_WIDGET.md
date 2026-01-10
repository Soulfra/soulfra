# Embeddable Widget Guide

**How to embed Soulfra's AI chat widget on WordPress, static sites, or any web page**

---

## Quick Embed (Copy-Paste)

Add this to any HTML page:

```html
<!-- Soulfra Chat Widget -->
<div id="soulfra-widget-container"></div>
<script src="https://your-domain.com/static/widget-embed.js"></script>
<script>
  SoulWidget.init({
    apiEndpoint: 'https://your-domain.com',
    position: 'bottom-right',
    primaryColor: '#667eea',
    welcomeMessage: 'Hey! Talk to me about anything.'
  });
</script>
```

**That's it.** The widget will appear in the bottom-right corner.

---

## WordPress Integration

### Method 1: Custom HTML Block (Easiest)

1. **Edit your page/post** in WordPress
2. **Add a Custom HTML block** (+ button → Custom HTML)
3. **Paste the embed code** (from Quick Embed above)
4. **Publish**

The widget will appear on that specific page.

### Method 2: Theme Footer (Site-Wide)

**For all pages:**

1. Go to **Appearance → Theme Editor**
2. Open **footer.php**
3. Add embed code **before `</body>`**
4. **Update File**

**⚠️ Caution:** This edits your theme directly. Use a child theme if possible.

### Method 3: Plugin (Recommended)

**Install "Insert Headers and Footers" plugin:**

1. **Plugins → Add New** → Search "Insert Headers and Footers"
2. **Install & Activate**
3. **Settings → Insert Headers and Footers**
4. **Paste embed code in "Footer" section**
5. **Save**

Widget will appear on all pages without editing theme files.

---

## Configuration Options

```javascript
SoulWidget.init({
  // Required
  apiEndpoint: 'https://your-domain.com',

  // Optional
  position: 'bottom-right',        // or 'bottom-left'
  primaryColor: '#667eea',         // Brand color
  buttonIcon: '💬',                // Chat bubble icon
  welcomeMessage: 'Hello!',        // First message
  placeholder: 'Type here...',     // Input placeholder

  // Advanced
  width: '400px',                  // Widget width
  height: '600px',                 // Widget height
  sessionDuration: 3600,           // Session timeout (seconds)
  enableNotifications: true,       // Browser notifications

  // Branding
  brandName: 'Soulfra',
  brandLogo: 'https://your-domain.com/logo.png',

  // Features
  enableFileUpload: true,
  enableVoiceInput: false,
  enableMarkdown: true
});
```

---

## Standalone Widget File

Create `static/widget-embed.js` on your Soulfra server:

```javascript
(function() {
  'use strict';

  const SoulWidget = {
    config: {},
    isOpen: false,
    sessionId: null,

    init: function(options) {
      this.config = Object.assign({
        apiEndpoint: window.location.origin,
        position: 'bottom-right',
        primaryColor: '#667eea',
        buttonIcon: '💬',
        welcomeMessage: 'Hi! How can I help?',
        placeholder: 'Type your message...',
        width: '400px',
        height: '600px',
        brandName: 'Soulfra'
      }, options);

      this.createWidget();
      this.attachEventListeners();
      this.generateSessionId();
    },

    generateSessionId: function() {
      this.sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    },

    createWidget: function() {
      const container = document.getElementById('soulfra-widget-container');
      if (!container) {
        console.error('Widget container not found');
        return;
      }

      // Chat button
      const button = document.createElement('div');
      button.id = 'soulfra-widget-button';
      button.className = 'soulfra-widget-button';
      button.innerHTML = this.config.buttonIcon;
      button.style.cssText = `
        position: fixed;
        ${this.config.position.includes('right') ? 'right: 20px' : 'left: 20px'};
        bottom: 20px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: ${this.config.primaryColor};
        color: white;
        font-size: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9999;
        transition: transform 0.2s;
      `;

      // Chat window
      const widget = document.createElement('div');
      widget.id = 'soulfra-widget-window';
      widget.className = 'soulfra-widget-window';
      widget.style.cssText = `
        position: fixed;
        ${this.config.position.includes('right') ? 'right: 20px' : 'left: 20px'};
        bottom: 90px;
        width: ${this.config.width};
        height: ${this.config.height};
        background: white;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        z-index: 9999;
        display: none;
        flex-direction: column;
        overflow: hidden;
      `;

      widget.innerHTML = `
        <div style="background: ${this.config.primaryColor}; color: white; padding: 16px; font-weight: 600; display: flex; justify-content: space-between; align-items: center;">
          <span>${this.config.brandName}</span>
          <span id="soulfra-widget-close" style="cursor: pointer; font-size: 20px;">&times;</span>
        </div>
        <div id="soulfra-widget-messages" style="flex: 1; overflow-y: auto; padding: 16px; background: #f9f9f9;"></div>
        <div style="padding: 16px; border-top: 1px solid #ddd; background: white;">
          <div style="display: flex; gap: 8px;">
            <input type="text" id="soulfra-widget-input" placeholder="${this.config.placeholder}" style="flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px;">
            <button id="soulfra-widget-send" style="padding: 12px 20px; background: ${this.config.primaryColor}; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">Send</button>
          </div>
        </div>
      `;

      container.appendChild(button);
      container.appendChild(widget);

      // Add welcome message
      this.addMessage('assistant', this.config.welcomeMessage);
    },

    attachEventListeners: function() {
      const button = document.getElementById('soulfra-widget-button');
      const closeBtn = document.getElementById('soulfra-widget-close');
      const sendBtn = document.getElementById('soulfra-widget-send');
      const input = document.getElementById('soulfra-widget-input');

      button.addEventListener('click', () => this.toggleWidget());
      closeBtn.addEventListener('click', () => this.toggleWidget());
      sendBtn.addEventListener('click', () => this.sendMessage());
      input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') this.sendMessage();
      });
    },

    toggleWidget: function() {
      const widget = document.getElementById('soulfra-widget-window');
      const button = document.getElementById('soulfra-widget-button');

      this.isOpen = !this.isOpen;
      widget.style.display = this.isOpen ? 'flex' : 'none';
      button.style.transform = this.isOpen ? 'scale(0.9)' : 'scale(1)';
    },

    sendMessage: function() {
      const input = document.getElementById('soulfra-widget-input');
      const message = input.value.trim();

      if (!message) return;

      // Add user message
      this.addMessage('user', message);
      input.value = '';

      // Send to backend
      fetch(`${this.config.apiEndpoint}/assistant/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: this.sessionId,
          message: message
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.response) {
          this.addMessage('assistant', data.response);
        }
        if (data.error) {
          this.addMessage('error', 'Error: ' + data.error);
        }
      })
      .catch(error => {
        this.addMessage('error', 'Connection error. Please try again.');
        console.error('Widget error:', error);
      });
    },

    addMessage: function(sender, content) {
      const messagesDiv = document.getElementById('soulfra-widget-messages');
      const messageDiv = document.createElement('div');

      messageDiv.style.cssText = `
        margin-bottom: 12px;
        padding: 12px;
        border-radius: 8px;
        ${sender === 'user' ?
          'background: ' + this.config.primaryColor + '; color: white; text-align: right; margin-left: 20%;' :
          'background: white; color: #333; margin-right: 20%;'}
        ${sender === 'error' ? 'background: #fee; color: #c33; border: 1px solid #fcc;' : ''}
      `;

      messageDiv.textContent = content;
      messagesDiv.appendChild(messageDiv);
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
  };

  // Expose globally
  window.SoulWidget = SoulWidget;
})();
```

**Host this file** on your Soulfra server at `/static/widget-embed.js`.

---

## Self-Hosted Setup

If you want to self-host the entire widget:

### 1. Copy Widget Files

```bash
# On your WordPress server
mkdir -p /var/www/html/soulfra-widget
cd /var/www/html/soulfra-widget

# Download widget files
curl -O https://your-soulfra.com/static/widget-embed.js
curl -O https://your-soulfra.com/static/widget-styles.css
```

### 2. Update Embed Code

```html
<div id="soulfra-widget-container"></div>
<script src="/soulfra-widget/widget-embed.js"></script>
<script>
  SoulWidget.init({
    apiEndpoint: 'https://your-soulfra-backend.com'  // Your Soulfra API
  });
</script>
```

---

## CORS Configuration

If widget is on different domain than API, enable CORS in `app.py`:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/assistant/*": {
        "origins": ["https://your-wordpress-site.com"],
        "methods": ["POST", "GET"],
        "allow_headers": ["Content-Type"]
    }
})
```

Install CORS:
```bash
pip install flask-cors
```

---

## Advanced: WordPress Plugin

**Create a custom plugin** for easier installation:

**File:** `wp-content/plugins/soulfra-widget/soulfra-widget.php`

```php
<?php
/**
 * Plugin Name: Soulfra Chat Widget
 * Description: Embeds Soulfra AI chat widget on your WordPress site
 * Version: 1.0
 * Author: Your Name
 */

// Add settings page
add_action('admin_menu', 'soulfra_widget_menu');

function soulfra_widget_menu() {
    add_options_page(
        'Soulfra Widget Settings',
        'Soulfra Widget',
        'manage_options',
        'soulfra-widget',
        'soulfra_widget_settings_page'
    );
}

function soulfra_widget_settings_page() {
    ?>
    <div class="wrap">
        <h1>Soulfra Widget Settings</h1>
        <form method="post" action="options.php">
            <?php
            settings_fields('soulfra_widget_options');
            do_settings_sections('soulfra-widget');
            submit_button();
            ?>
        </form>
    </div>
    <?php
}

// Register settings
add_action('admin_init', 'soulfra_widget_settings');

function soulfra_widget_settings() {
    register_setting('soulfra_widget_options', 'soulfra_api_endpoint');
    register_setting('soulfra_widget_options', 'soulfra_primary_color');

    add_settings_section(
        'soulfra_widget_main',
        'Main Settings',
        null,
        'soulfra-widget'
    );

    add_settings_field(
        'soulfra_api_endpoint',
        'API Endpoint',
        'soulfra_api_endpoint_callback',
        'soulfra-widget',
        'soulfra_widget_main'
    );

    add_settings_field(
        'soulfra_primary_color',
        'Primary Color',
        'soulfra_primary_color_callback',
        'soulfra-widget',
        'soulfra_widget_main'
    );
}

function soulfra_api_endpoint_callback() {
    $value = get_option('soulfra_api_endpoint', 'https://your-domain.com');
    echo '<input type="text" name="soulfra_api_endpoint" value="' . esc_attr($value) . '" style="width: 100%; max-width: 400px;">';
}

function soulfra_primary_color_callback() {
    $value = get_option('soulfra_primary_color', '#667eea');
    echo '<input type="color" name="soulfra_primary_color" value="' . esc_attr($value) . '">';
}

// Inject widget into footer
add_action('wp_footer', 'soulfra_widget_inject');

function soulfra_widget_inject() {
    $api_endpoint = get_option('soulfra_api_endpoint', 'https://your-domain.com');
    $primary_color = get_option('soulfra_primary_color', '#667eea');
    ?>
    <div id="soulfra-widget-container"></div>
    <script src="<?php echo esc_url($api_endpoint); ?>/static/widget-embed.js"></script>
    <script>
      SoulWidget.init({
        apiEndpoint: '<?php echo esc_js($api_endpoint); ?>',
        primaryColor: '<?php echo esc_js($primary_color); ?>'
      });
    </script>
    <?php
}
?>
```

**Install:**
1. Create `wp-content/plugins/soulfra-widget/` directory
2. Add `soulfra-widget.php` file
3. **Activate** in WordPress Plugins
4. **Configure** in Settings → Soulfra Widget

---

## Iframe Embed (Alternative)

If you can't use JavaScript, use an iframe:

```html
<iframe
  src="https://your-soulfra.com/widget-embed"
  width="100%"
  height="600px"
  frameborder="0"
  style="border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
</iframe>
```

**Add route to `app.py`:**

```python
@app.route('/widget-embed')
def widget_embed():
    """Standalone embeddable widget page"""
    return render_template('widget_embed.html')
```

**Create `templates/widget_embed.html`:**

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Soulfra Widget</title>
  <style>
    body {
      margin: 0;
      font-family: system-ui, sans-serif;
      background: transparent;
    }
  </style>
</head>
<body>
  <!-- Your existing widget HTML from base.html -->
  <div id="assistant-widget">...</div>
  <script src="/static/assistant-widget.js"></script>
</body>
</html>
```

---

## Testing

**Test the widget works:**

1. **Open WordPress page** with widget
2. **Click chat bubble** in bottom-right
3. **Send message:** "Hello"
4. **Verify response** from Soulfra AI
5. **Check browser console** for errors (F12)

**Common Issues:**

- **CORS error:** Enable CORS on Soulfra backend
- **404 on widget.js:** Check file path and server HTTPS
- **No response:** Verify API endpoint URL is correct
- **Widget not appearing:** Check container div exists

---

## Production Checklist

- [ ] Widget loads on all pages
- [ ] HTTPS enabled (required for cross-origin)
- [ ] CORS configured correctly
- [ ] Session persistence works
- [ ] Mobile responsive
- [ ] Conversation history saved
- [ ] Rate limiting enabled on backend
- [ ] Error messages user-friendly
- [ ] Analytics tracking (optional)

---

## Next Steps

Once embedded, users can:

- **Chat naturally** with your AI
- **Generate blog posts** with `/generate post`
- **Search content** with `/research <topic>`
- **Create QR codes** with `/qr <text>`
- **Play D&D campaigns** with `/dnd start`

**Your Soulfra widget is now embeddable anywhere.** 🎉

---

## Documentation

- [Main Deployment Guide](DEPLOYMENT.md)
- [How It All Connects](HOW_IT_ALL_CONNECTS.md)
- [Blog Generator Guide](BLOG_GENERATOR_GUIDE.md)
