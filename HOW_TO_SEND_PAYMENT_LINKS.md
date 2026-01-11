# How To Send Payment Links (Brain Dead Simple!)

## From Your Phone:

### **Step 1: Open This Page**
```
https://soulfra.com/pay.html
```

### **Step 2: Fill In 2 Things**
1. Amount: `$10`
2. For what: `Tampa Plumber`

### **Step 3: Click "Generate Payment Link"**

### **Step 4: Send The Link**
- Click "📱 Share" → Text it to someone
- Or "📋 Copy Link" → Paste anywhere

---

## That's It!

No login. No signup. No Python. No server. No bullshit.

Just:
1. Open page
2. Type amount
3. Send link

---

## What The Link Does:

When someone clicks your link, they see a payment page with:
- The amount you set
- The description you wrote
- A "Pay Now" button (Stripe coming soon)

---

## Live URL (After Git Push):

```
https://soulfra.com/pay.html
```

Currently works locally at:
```
file:///Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/output/soulfra/pay.html
```

---

## Next Git Push Will Deploy It:

```bash
git add output/soulfra/pay.html
git commit -m "Add brain-dead simple payment link generator"
git push
```

Then it'll be live at soulfra.com/pay.html for anyone to use.

---

## Why This Works:

- **No server needed** - Pure HTML + JavaScript
- **Works offline** - Generate links even without internet
- **Mobile-first** - Built for iPhone
- **Instant** - No loading, no waiting
- **Share-ready** - Native iOS share sheet

---

## The 4 Styles:

1. **Normal** - Purple gradient (default)
2. **Matrix** - Green hacker aesthetic
3. **Cyberpunk** - Pink/cyan CringeProof vibes
4. **Receipt** - Black/white retail style

Pick a style, generate link, send. Done.

---

## Examples:

**Coffee**: `$5` → soulfra.com/pay/pay-TEST.html?amount=5&label=Coffee

**Plumbing**: `$50` → soulfra.com/pay/pay-UPC001-upc.html?amount=50&label=Plumbing

**Tip**: `$1` → soulfra.com/pay/pay-MATRIX01-matrix.html?amount=1&label=Tip

---

## No Confusion:

- ❌ No Flask server
- ❌ No Python commands
- ❌ No database
- ❌ No qr-pay.py
- ❌ No terminal

- ✅ Just a webpage
- ✅ Just your phone
- ✅ Just 2 inputs
- ✅ Just works

---

## Deploy Right Now:

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple
git add .
git commit -m "Add dead simple payment links"
git push
```

Wait 30 seconds → soulfra.com/pay.html is live.
