# Integrate Working Demo - 3 Steps to See It Working

**Goal:** Show the 10 demo professionals on your EXISTING cringeproof.com site

**Time:** 2 minutes

---

## Step 1: Add to app.py

Open `app.py` and add this line around line 180 (with the other blueprint imports):

```python
from working_demo_routes import professional_bp
```

Then add this line around line 220 (with the other blueprint registrations):

```python
app.register_blueprint(professional_bp)
```

**That's it for code changes.**

---

## Step 2: Run Your Flask App

```bash
python3 app.py
```

You should see:
```
 * Running on http://127.0.0.1:5001
```

---

## Step 3: Visit the URLs

Open your browser:

**Professional Directory:**
```
http://localhost:5001/professionals
```

**Individual Professionals:**
```
http://localhost:5001/pro/1   (Joe's Plumbing)
http://localhost:5001/pro/2   (Tampa Electric)
http://localhost:5001/pro/3   (Cool Breeze HVAC)
http://localhost:5001/pro/4   (Tampa Tech Talk Podcast)
http://localhost:5001/pro/5   (Florida Lifestyle Vlog)
http://localhost:5001/pro/6   (Chef Mike Miami)
http://localhost:5001/pro/7   (Tampa Meal Prep Co)
http://localhost:5001/pro/8   (HollowGaming Streams)
http://localhost:5001/pro/9   (DevOps Consulting FL)
http://localhost:5001/pro/10  (Privacy Consulting Group)
```

---

## What You'll See

**Professional Directory Page:**
- Grid of 10 professional cards
- Each shows business name, category, location
- Click any card to see full profile

**Professional Profile Page:**
- Business name and category
- Bio/description
- Contact info (phone, email, address)
- Call/Email buttons
- Verified badge

---

## It's Working On:

- ✅ Your EXISTING Flask app
- ✅ Your EXISTING database (`professionals` table)
- ✅ Localhost:5001 (same port you use now)
- ✅ NO multi-domain complexity

---

## Once It Works Locally

Then you can deploy to cringeproof.com:

1. **Deploy Flask app** to your server (DigitalOcean/AWS/etc.)
2. **Run it:** `python3 app.py` or use gunicorn/uwsgi
3. **Visit:** `https://cringeproof.com/professionals`

That's it. ONE site. Working now.

---

## Multi-Domain LATER

Once this works on cringeproof.com, THEN we can:
- Point stpetepros.com DNS to same server
- Add domain routing logic
- Show different pros on different domains

But for now: **Prove it works on ONE site first.**

---

## Troubleshooting

**"Import error":**
```bash
# Make sure working_demo_routes.py is in same directory as app.py
ls working_demo_routes.py
```

**"No professionals found":**
```bash
# Re-run the seeding script
python3 prove_it_works.py
```

**"Port already in use":**
```bash
# Kill existing Flask process
pkill -f "python.*app.py"

# Or use different port in app.py
app.run(port=5002)
```

---

## Next Steps After It Works

1. ✅ See it working locally
2. Deploy to cringeproof.com
3. Add professional signup form
4. Let real users create profiles
5. THEN worry about multi-domain routing

**One step at a time. Prove it works first.** 🚀
