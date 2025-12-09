# D2L Announcements Pipeline - Interactive Setup Guide

**For Local Testing with Manual 2FA Approval**

---

## Quick Start (5 minutes)

### Step 1: Enable Interactive Mode

Edit the pipeline to use a headed (visible) Firefox browser:

```bash
# Open the file
nano src/scrapers/d2l/announcements_testing.py

# Find line ~633 that says:
#   browser = await p.firefox.launch(headless=True)

# Change it to:
#   browser = await p.firefox.launch(headless=False)

# Save and exit (Ctrl+X, then Y, then Enter)
```

**Or use sed to do it automatically:**

```bash
sed -i 's/headless=True/headless=False/' src/scrapers/d2l/announcements_testing.py
```

### Step 2: Verify .env Configuration

```bash
# Make sure your .env file has:
cat .env
```

Should show:
```
D2L_USERNAME=your_email@fanshaweonline.ca
D2L_PASSWORD=your_password
```

### Step 3: Run the Pipeline

```bash
python3 src/scrapers/d2l/announcements_testing.py
```

---

## What Happens Next

### Stage 1: Browser Opens (5-10 seconds)

A Firefox browser window opens showing the Fanshawe login page.

```
[1/4] Accessing D2L course announcements page...
[AUTH] Authentication required, logging in...
```

### Stage 2: Email Entry (automatic)

The pipeline automatically fills in your email address.

```
[AUTH] Login required. Starting authentication...
  → Filling email...
    ✓ Found with selector: input#i0116
    ✓ Email filled
  → Clicking submit button for email...
    ✓ Found submit button: input#idSIButton9
    ✓ Email submitted
```

You'll see the email appear in the browser form and the page advance to the password screen.

### Stage 3: Password Entry (automatic)

The pipeline automatically fills in your password.

```
  → Filling password...
    ✓ Found with selector: input#i0118
    ✓ Password filled
  → Clicking submit button for password...
    ✓ Found submit button: input#idSIButton9
    ✓ Password submitted
```

You'll see the password field fill and the page advance to the 2FA screen.

### Stage 4: 2FA Approval (MANUAL - Your Action Required!)

The pipeline prints:

```
╔════════════════════════════════════════════════════════════════════════════════╗
║                  🔐 TWO-FACTOR AUTHENTICATION REQUIRED                         ║
╚════════════════════════════════════════════════════════════════════════════════╝

📱 ACTION REQUIRED:
   1. Open Microsoft Authenticator app on your phone
   2. Look for approval notification
   3. Tap 'Approve' or enter code if prompted

⏳ Waiting for approval...
```

**What you do:**
1. Pick up your phone
2. Open the **Microsoft Authenticator** app
3. Look for a notification about Fanshawe/D2L login
4. Tap **"Approve"**
5. The browser and script will automatically continue

**Code Detection (Optional):**
If a 6-digit code appears on the browser, the script tries to automatically fill it. You can either:
- Let the script fill it automatically ✓
- Tap "Approve" on your phone instead ✓
- Manually enter the code in the browser ✓

### Stage 5: Announcement Extraction (automatic)

Once 2FA is approved, you'll see:

```
✓ AUTHENTICATION APPROVED SUCCESSFULLY!

[2/4] Extracting announcements from home page...
✓ Found 5 announcements!

[3/4] Extracting details from 5 announcements...

[1/5] Quiz 2 will be on Friday, November 28.
  → URL: https://www.fanshaweonline.ca/d2l/le/news/2001539/2256285/view...
  ✓ Accessible - 245 chars

[4/4] Saving results...

================================================================================
EXTRACTION COMPLETE
================================================================================
Output file: data/course_2001539/announcements_testing_20251208_200519.json
Announcements found: 5
Details extracted: 5
Successful: 5
Failed: 0
================================================================================
```

---

## Troubleshooting

### Issue: Browser doesn't open

**Solution:**
```bash
# Make sure Firefox is installed
firefox --version

# If not installed:
# Ubuntu/Debian:
sudo apt install firefox

# macOS:
brew install firefox

# Windows:
# Download from https://www.mozilla.org/firefox/
```

### Issue: Email not auto-filling

**Possible causes:**
1. Firefox hasn't fully loaded the form
2. Your email in .env is incorrect
3. The form structure changed

**Solution:**
1. Check that your email is correct in .env
2. Wait for the form to fully load before the script tries to fill it
3. You can manually type the email if the script doesn't fill it

### Issue: Password field not found

**Solution:**
1. Manually type the password
2. The script will still detect when it's done
3. Press Tab or Enter to move to the next step

### Issue: 2FA notification doesn't appear

**Possible causes:**
1. Check your phone for the notification (might be on a different screen)
2. Open Microsoft Authenticator manually
3. Make sure Authenticator is set up for your account

**Solution:**
1. Open Authenticator app
2. Check the "Accounts" or "Notifications" section
3. Look for "Sign in to Fanshawe" or "D2L"
4. Tap to approve

### Issue: Script times out waiting for 2FA (5 minutes)

**Solution:**
1. The 5-minute timeout is built in
2. Approve on your phone within that time
3. Or press Ctrl+C and run the script again

---

## Important Notes

⚠️ **Security Notes:**

1. **Keep your .env file private**
   - Don't commit it to git
   - Don't share it with others
   - Delete it when you're done testing

2. **Use while watching**
   - Don't run this in the background
   - You need to approve 2FA manually
   - It only takes 30 seconds of your time

3. **The browser window is real**
   - It's actual Firefox running
   - You can see everything it does
   - You can intervene if something looks wrong

4. **Close the browser when done**
   - The script closes it automatically
   - Or close it manually if needed

---

## Advanced Options

### Run for Different Course

```bash
python3 src/scrapers/d2l/announcements_testing.py --course-id 2001234
```

### Save to Custom Location

```bash
python3 src/scrapers/d2l/announcements_testing.py --output /path/to/output.json
```

### Run Multiple Times

```bash
# Run every morning at 8 AM (Linux/macOS)
# Add to crontab:
0 8 * * * cd ~/projects/d2l && python3 src/scrapers/d2l/announcements_testing.py
```

---

## What Gets Saved

After successful extraction, you'll find:

```
data/course_2001539/announcements_testing_[timestamp].json
```

Example output file content:

```json
{
  "metadata": {
    "source": "d2l_announcements_testing",
    "generated_at": "2025-12-08T20:05:19.123456",
    "course_id": "2001539",
    "home_url": "https://www.fanshaweonline.ca/d2l/home/2001539",
    "total_announcements_found": 5,
    "total_detailed": 5,
    "successful_details": 5,
    "failed_details": 0
  },
  "announcements_list": [
    {
      "title": "Quiz 2 will be on Friday, November 28.",
      "date": "2025-12-01",
      "url": "https://www.fanshaweonline.ca/d2l/le/news/2001539/2256285/view"
    }
  ],
  "announcements_detailed": [
    {
      "index": 1,
      "title": "Quiz 2 will be on Friday, November 28.",
      "date": "2025-12-01",
      "url": "https://www.fanshaweonline.ca/d2l/le/news/2001539/2256285/view",
      "details": {
        "accessible": true,
        "content": "Full announcement content here...",
        "content_length": 245
      }
    }
  ]
}
```

---

## Success Criteria

✅ You've succeeded if you see:

```
================================================================================
EXTRACTION COMPLETE
================================================================================
Output file: data/course_2001539/announcements_testing_*.json
Announcements found: [> 0]
Details extracted: [> 0]
Successful: [= Details extracted]
Failed: 0
================================================================================
```

---

## Next Steps

1. **Review the JSON output** - Check that the announcements look correct
2. **Integrate with your system** - Use the JSON in your application
3. **Schedule for automation** - Set up cron job for regular extraction
4. **Add to database** - Store results in your database
5. **Build a dashboard** - Create a UI to display announcements

---

## Support

If you encounter issues:

1. **Check the debug HTML**
   - If authentication fails, check `/tmp/login_page_email_debug.html`
   - Save it for analysis

2. **Check the JSON output**
   - Even partial results are saved
   - Look at the error messages in metadata

3. **Review the logs**
   - The script prints detailed progress
   - Copy-paste relevant error messages when asking for help

---

**Status:** Ready to use! ✅

Run the pipeline now with:
```bash
python3 src/scrapers/d2l/announcements_testing.py
```

Have your phone ready to approve 2FA! 📱
