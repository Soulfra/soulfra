# Soulfra Project Audit - January 2026

## DEPLOYED WEBSITES (Live on Internet)

### 1. cringeproof.com
- **Source**: `soulfra-simple/voice-archive/`
- **Hosting**: GitHub Pages
- **Files**: 18 HTML pages
- **Key Pages**:
  - index.html (homepage)
  - signup.html, login.html (auth)
  - record-simple.html (voice recorder)
  - encyclopedia.html, wordmap.html (features)
  - onboarding.html, account.html
- **Backend API**: Points to `https://192.168.1.87:5001` (local Flask)
- **Status**: ✅ ACTIVE & WORKING

### 2. soulfra.com  
- **Source**: `soulfra-simple/soulfra.github.io/`
- **Hosting**: GitHub Pages
- **Purpose**: Different project/experiment
- **Status**: ✅ DEPLOYED (unknown if actively used)

## BACKEND (Local Development)

### Flask Application
- **Location**: `soulfra-simple/app.py`
- **Running on**: https://192.168.1.87:5001
- **Access**: Same WiFi only (no public URL currently)

### Admin Routes
- `/admin/domains` - Domain management
- `/admin` - Main dashboard (requires login)
- `/admin/users` - User management
- `/api/auth/signup` - User registration
- `/api/voice/*` - Voice memo APIs

## DATABASES (Confusing - Multiple Copies!)

### Database 1: `/soulfra-simple/soulfra.db` ✅ ACTIVE

- **Used by**: Flask app.py
- **Tables**: (see above)
- **Key Data**:
  - **Users**: 23 total (10 from previous session + 13 new signups)
  - **Voice Ideas**: 5 recorded ideas
  - **Domain Contexts**: 13 domains configured

###Database 2: `/soulfra.db` (parent directory) ❌ OLD/UNUSED
- Different schema (has `brands` table instead of `domain_contexts`)
- NOT used by current Flask app
- **Recommendation**: DELETE or archive

### Database 3: `/soulfra.sqlite` ❓ UNKNOWN
- Purpose unclear
- **Recommendation**: Investigate or delete

## PROJECT DIRECTORIES

### Active Development
- `/soulfra-simple/` - Main project directory
  - `app.py` - Flask backend
  - `voice-archive/` - cringeproof.com frontend
  - `soulfra.github.io/` - soulfra.com frontend  
  - `templates/` - Backend admin templates
  - `static/` - Backend static assets

### Confusing/Unclear
- `/soulfra/` - Another directory, unclear purpose
- `/__pycache__/` - Python cache (add to .gitignore)
- `/core/` - Duplicated route files?
- `/archive/` - Old experiments

## CSS & STYLING CONFUSION

The "emojis throwing you off" issue:
- `voice-archive/css/soulfra.css` has emoji-heavy brutalist design
- This is INTENTIONAL for cringeproof.com branding
- Different from soulfra.github.io styling
- Both are valid, just different projects

## WHAT'S ACTUALLY WORKING

✅ **cringeproof.com**
- Deployed on GitHub Pages
- Backend connects to local Flask (same WiFi only)
- Signup, login, voice recording, encyclopedia all functional

✅ **Flask Backend**
- Running on https://192.168.1.87:5001
- Has admin dashboard
- Multi-domain authentication system working
- 23 users registered

❌ **NOT Working/Deployed**
- All those 200+ domains in admin panel (just database entries)
- Cloudflare Tunnel (keeps dying)
- Public access (need Railway/VPS deployment)

## CLEANUP RECOMMENDATIONS

### Immediate (Low Risk)
1. Delete `/soulfra.db` and `/soulfra.sqlite` (old databases)
2. Add `__pycache__/` to .gitignore (already done)
3. Document which directory is which

### Medium Priority
4. Clean up `/archive/` and `/core/` duplicates
5. Remove unused domain entries from database
6. Deploy to Railway for public access

### Low Priority  
7. Unify styling if you want consistency
8. Consolidate frontends if they're the same project
9. Set up proper git repositories

## NEXT STEPS

1. **Test cringeproof.com signup** - Visit on phone (same WiFi)
2. **Deploy to Railway** - Get public URL instead of local IP
3. **Clean up databases** - Delete old .db files
4. **Document** - Create README explaining architecture

---

Generated: January 3, 2026
Location: `/tmp/project_audit.md`
