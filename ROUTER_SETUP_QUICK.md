# Router Setup - Quick Start

**Your Mac's IP:** `192.168.1.87`
**Port to forward:** `5001`

## Step 1: Access Your Router

Open browser and try these addresses:
- http://192.168.1.1 (most common)
- http://192.168.0.1
- http://10.0.0.1

Login with router password (check sticker on router).

## Step 2: Add Port Forwarding Rule

Look for menu item called:
- "Port Forwarding"
- "Virtual Server"
- "NAT"
- "Applications & Gaming"

**Create this rule:**
```
Service Name: CringeProof
External Port: 5001
Internal IP: 192.168.1.87
Internal Port: 5001
Protocol: TCP (or Both)
```

Save and restart router if needed.

## Step 3: Test It

1. Get your public IP: Google "what is my ip" → Copy the IP address

2. From your phone (use cellular, NOT WiFi):
   ```
   Visit: http://YOUR_PUBLIC_IP:5001/status
   ```

3. If you see the status page → **IT WORKS!**

## Step 4 (Optional): Get Permanent URL with DuckDNS

Your home IP changes occasionally. DuckDNS fixes this for free.

1. Go to: https://www.duckdns.org
2. Sign in with GitHub
3. Create subdomain: `matthewmauer` (or whatever you want)
4. You'll get: `matthewmauer.duckdns.org`

Then set up auto-updater (see LAPTOP_SERVER_SETUP.md for full instructions).

## If Port 5001 Is Blocked by ISP

Some ISPs block port 5001. Try these alternatives:
- Port 8080 (common alternative)
- Port 8443 (HTTPS alternative)
- Port 3000 (dev server port)

Update both router forwarding and Flask app.py to use the new port.

## Troubleshooting

**Can't access router?**
```bash
# Find router IP:
netstat -nr | grep default
```

**Port forwarding not working?**
1. Check Mac firewall: System Preferences → Security → Firewall
2. Allow incoming connections for Python
3. Try DMZ mode temporarily (router setting - opens ALL ports to your Mac)

**ISP blocking ports?**
- Some ISPs block server hosting on residential plans
- Call ISP and ask about "port 5001 blocking"
- Alternative: Use Cloudflare Tunnel (what you have now)

## Current Setup

✅ Flask running on: `https://localhost:5001`
✅ Cloudflare Tunnel URL: `https://sega-affordable-soviet-weed.trycloudflare.com`
⏳ Router port forwarding: Not set up yet
⏳ DuckDNS permanent URL: Not set up yet

Once router is configured, you can kill Cloudflare Tunnel and use your own URL.
