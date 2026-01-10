# 🚀 Practice Room Demo - PROOF IT WORKS

Quick demo to prove the practice room system works from your phone.

## What This Proves

✅ Scan QR code from phone
✅ Submit data through form
✅ Data goes into database
✅ Multiple people can join same room
✅ Real-time submissions visible

## Quick Start (2 minutes)

### 1. Run the demo script

```bash
python3 start_demo.py
```

You'll see:
- A QR code in ASCII art
- URLs for accessing from computer and phone
- Real-time activity monitor

### 2. Scan QR with your phone

- Open phone camera
- Point at QR code on screen
- Tap notification to open

### 3. Submit a message

- Enter your name
- Type a message
- Hit "Submit Message 🚀"

### 4. Watch it appear

- Message shows up instantly in terminal
- Also visible in "Room Recordings" section
- You'll appear in participant list

### 5. Test with multiple people

- Share the QR code with friends
- Everyone scans same code
- All submissions go to same room
- All visible in database

## Manual Access (without QR)

### From your computer:
```
http://localhost:5001/practice/room/ROOM_ID
```

### From your phone (same WiFi):
```
http://192.168.1.74:5001/practice/room/ROOM_ID
```

## Verify in Database

```bash
# Check messages in database
sqlite3 soulfra.db "SELECT transcription, created_at FROM practice_room_recordings ORDER BY created_at DESC LIMIT 10"

# Check participants
sqlite3 soulfra.db "SELECT username, joined_at FROM practice_room_participants ORDER BY joined_at DESC LIMIT 10"
```

## Troubleshooting

**Can't scan QR code?**
- Make sure phone and computer on same WiFi
- Try accessing the URL manually

**Form not submitting?**
- Check server is running (`lsof -i:5001`)
- Look for errors in terminal

**Messages not appearing?**
- Refresh the page
- Check database directly with sqlite3 commands above

## What's Happening Behind the Scenes

1. **QR Scan** → Opens room URL on phone
2. **Submit Form** → POST to `/practice/room/<id>/message`
3. **Backend**:
   - Adds you as participant
   - Creates voice_input entry (text-only)
   - Creates practice_room_recording
   - Stores in database
4. **Redirect** → Back to room page with submission visible

## Next Steps

Now that you've proven it works:
- Customize the form fields
- Add image uploads
- Integrate with Ollama for AI responses
- Add real-time chat with WebSockets
- Deploy to production

## Files Modified

- `start_demo.py` - Demo launcher with QR code
- `app.py` - Added `/practice/room/<id>/message` endpoint (line 12140)
- `templates/practice/room.html` - Added submission form

## Database Tables Used

- `practice_rooms` - Room metadata
- `practice_room_participants` - Who joined
- `practice_room_recordings` - Submissions (messages + voice)
- `voice_inputs` - Audio/text storage

---

**The system works. Scan, submit, verify.** 🎯
