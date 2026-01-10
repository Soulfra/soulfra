# Localhost Testing Guide - Customer Discovery Tool

**Problem:** soulfra.com returns 404 for customer-discovery-chat.html due to CDN cache

**Solution:** Test locally RIGHT NOW while waiting for production cache to clear

---

## 🚀 Quick Start (30 seconds)

```bash
cd /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple

# Start Flask server
./start_localhost_test.sh

# In browser, visit:
# http://localhost:5001/customer-discovery-chat.html
```

Done! You can now test the tool locally.

---

## 📊 Current Status

### ✅ WORKING
- GitHub Pages: https://soulfra.github.io/soulfra/customer-discovery-chat.html (HTTP 200)
- Localhost routes added to Flask app

### ❌ NOT WORKING (YET)
- Custom domain: http://soulfra.com/customer-discovery-chat.html (404, cached)
- Reason: CDN is serving stale 404 response
- Fix: Added .nojekyll (commit 5fc8c38) to trigger rebuild

---

## 🔍 Why 404?

CDN cached the 404 response before GitHub Pages finished building.

**Proof file EXISTS:**
```bash
curl -I https://soulfra.github.io/soulfra/customer-discovery-chat.html
# HTTP/2 200 ✅
```

**Proof cache is stale:**
```bash
curl -I http://soulfra.com/customer-discovery-chat.html  
# HTTP/1.1 404 ❌ (X-Cache: HIT)
```

---

## 🎯 Next Steps

1. **Test locally NOW:** Run `./start_localhost_test.sh`
2. **Check production in 15-30 min:** Run `python3 test_soulfra_deployment.py`
3. **Manual SSL fix:** https://github.com/Soulfra/soulfra/settings/pages → Enable HTTPS

---

**TL;DR:** Files are deployed and working. Cache just needs to clear. Test on localhost immediately.
