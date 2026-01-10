# iPhone SSL Certificate Setup

## Why This Is Needed

iOS Safari blocks microphone access on HTTP connections (security sandbox). Your laptop now has HTTPS with a self-signed certificate, but your iPhone doesn't trust it yet.

This is the **one-time setup** to make your iPhone trust your laptop's HTTPS certificate - just like how Apple devices trust each other with AirDrop/Handoff.

---

## Step 1: AirDrop the CA Certificate to iPhone

**On your Mac:**

1. Open Finder
2. Navigate to: `/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/`
3. Find file: `mkcert-root-CA.pem`
4. Right-click → Share → AirDrop
5. Select your iPhone from AirDrop menu

**On your iPhone:**

1. Tap "Accept" when AirDrop notification appears
2. File will download to Files app

---

## Step 2: Install the Certificate Profile

**On your iPhone:**

1. Open **Settings** app
2. Tap the banner at the top that says **"Profile Downloaded"**
   - If you don't see it, go to: **General → VPN & Device Management**
3. Tap **"mkcert matthewmauer@Mac.lan"** (or similar name)
4. Tap **"Install"** (top right)
5. Enter your iPhone passcode
6. Tap **"Install"** again (confirmation)
7. Tap **"Install"** a third time (final warning)
8. Tap **"Done"**

---

## Step 3: Enable Full Trust for Root Certificates

**CRITICAL STEP - Don't skip this!**

1. Still in **Settings** app
2. Go to: **General → About**
3. Scroll all the way to the bottom
4. Tap **"Certificate Trust Settings"**
5. Under "Enable Full Trust for Root Certificates":
   - Toggle **ON** the switch next to **"mkcert matthewmauer@Mac.lan"**
6. Tap **"Continue"** on the warning dialog

---

## Step 4: Test the Connection

**On your iPhone (connected to same WiFi):**

1. Open **Safari**
2. Navigate to: `https://192.168.1.87:5001/voice`
3. You should now see:
   - ✅ **No SSL warning** (secure connection)
   - ✅ **Microphone permission prompt** (iOS allows it now)
   - ✅ **🎤 Record button works**

4. Tap **"Allow"** for microphone
5. Tap 🎤 button
6. Speak for a few seconds
7. Tap **Stop**
8. Tap **Submit**

**On your laptop browser:**

- Open: `http://localhost:5001/suggestion-box`
- Your new voice memo should appear! 🎉

---

## Troubleshooting

### "Profile Downloaded" banner doesn't appear

1. Open **Files** app on iPhone
2. Browse to **Downloads**
3. Tap `mkcert-root-CA.pem`
4. Tap **"Install Profile"**
5. Follow Step 2 instructions above

---

### Still getting SSL warning after install

**Check 1: Did you enable Certificate Trust?**
- Settings → General → About → Certificate Trust Settings
- Toggle must be **ON** (green)

**Check 2: Correct IP address?**
- Laptop IP might have changed
- On Mac, run: `ipconfig getifaddr en0`
- Update URL if IP changed

**Check 3: Same WiFi network?**
- iPhone WiFi: Settings → WiFi → Check network name
- Mac WiFi: Menu bar → WiFi → Check network name
- Must be **identical**

---

### Certificate shows as "Not Verified"

This is normal for local development certificates. As long as:
1. You installed the profile
2. You enabled full trust in Certificate Trust Settings
3. Connection shows 🔒 (padlock) in Safari

...it's working correctly.

---

## What This Does

This certificate trust setup:
- ✅ Lets iPhone trust your Mac's HTTPS server
- ✅ Enables microphone access in Safari (no sandbox blocking)
- ✅ Works for all `https://192.168.1.87:*` connections
- ✅ Persists across iPhone reboots
- ✅ Only trusts YOUR laptop (not other devices)

It's the same system Apple uses for enterprise device management (MDM) and development certificates.

---

## Security Note

The `mkcert-root-CA.pem` certificate:
- Only works on your local WiFi network (192.168.1.x)
- Can't be used by anyone else (laptop-specific)
- Doesn't compromise iPhone security
- Can be removed anytime: Settings → General → VPN & Device Management → Delete Profile

---

## Next Steps

Once this works, we'll add:
1. **Bonjour/mDNS** - Access via `https://soulfra.local:5001` (no IP needed!)
2. **iOS Shortcuts** - Siri voice recording: "Hey Siri, record to Soulfra"
3. **Auto-discovery** - iPhone finds laptop automatically (like AirDrop)

But first, let's get this basic HTTPS connection working! 🚀
