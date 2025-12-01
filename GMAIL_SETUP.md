# Gmail API Setup Guide

This guide will walk you through setting up Gmail API access for your Second-Brain-Agent to create draft emails.

## Overview

To create draft emails in Gmail, you need to:
1. Enable the Gmail API in your Google Cloud Project (same project as Calendar)
2. Add Gmail scope to OAuth consent screen
3. Authenticate and generate a Gmail token

**Note**: This setup gives the agent **compose-only** access - it can create drafts but cannot read your emails or send automatically.

---

## Step 1: Enable Gmail API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)

2. Select your existing project (Second-Brain-Agent)

3. Go to **"APIs & Services"** > **"Library"**
   - Or use this direct link: [API Library](https://console.cloud.google.com/apis/library)

4. In the search bar, type **"Gmail API"**

5. Click on **"Gmail API"** from the results

6. Click the **"Enable"** button

7. Wait for the API to be enabled (a few seconds)

---

## Step 2: Update OAuth Consent Screen Scopes

You need to add Gmail permissions to your existing OAuth consent screen:

1. Go to **"APIs & Services"** > **"OAuth consent screen"**
   - Or use this link: [OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent)

2. Click **"Edit App"**

3. Click **"Save and Continue"** on the first page

4. On the **"Scopes"** page, click **"Add or Remove Scopes"**

5. Search for **"Gmail API"** and select:
   - `https://www.googleapis.com/auth/gmail.compose` (Create, read, update, and delete drafts. Send messages and drafts.)

   **Note**: This scope allows creating drafts but does NOT allow reading your emails or automatically sending.

6. Click **"Update"** then **"Save and Continue"**

7. Click **"Save and Continue"** through the remaining pages

8. Click **"Back to Dashboard"**

---

## Step 3: Use Existing Credentials

Good news! You can use the same `credentials.json` file from the Calendar setup. No need to download new credentials.

The Gmail API will create a separate token file (`gmail_token.json`) to keep permissions separated.

---

## Step 4: First-Time Gmail Authentication

1. Make sure `credentials.json` is in your project root

2. Run the Gmail test script:
   ```bash
   python src/tools/gmail.py
   ```

3. A browser window will open automatically asking you to:
   - Choose your Google account
   - Review the permissions (create Gmail drafts)
   - Click **"Continue"** or **"Allow"**

4. You might see a warning that the app isn't verified:
   - Click **"Advanced"**
   - Click **"Go to Second-Brain-Agent (unsafe)"**
   - This is safe because it's your own application

5. After authorizing, you'll see a success message in the browser

6. The script will automatically save a `gmail_token.json` file for future use

7. A test draft email will be created in your Gmail drafts!

---

## Troubleshooting

### "credentials.json not found"
- Make sure `credentials.json` is in the project root directory
- You can use the same file from Calendar setup

### "Access blocked: This app's request is invalid"
- Make sure you added the Gmail compose scope to your OAuth consent screen
- Make sure the Gmail API is enabled

### "Insufficient permissions"
- Delete `gmail_token.json` and re-authenticate
- Make sure you added the `gmail.compose` scope

### Token expired or invalid
- Simply delete `gmail_token.json` and run the script again
- You'll go through the authentication flow again

### Draft not appearing in Gmail
- Check your Gmail Drafts folder
- Drafts are created in "me" (your account)
- Refresh your Gmail interface

---

## Security Notes

### What access does the agent have?
- **Create drafts** only - cannot read your emails
- **Cannot automatically send** - all emails stay as drafts
- You manually review and send from Gmail
- Cannot access other Google services beyond Calendar and Gmail drafts

### Permissions breakdown
- `gmail.compose`: Create and manage drafts
- Does NOT include read access to your inbox
- Does NOT include automatic send permissions

### Credentials files
- `credentials.json`: OAuth client configuration (shared with Calendar)
- `gmail_token.json`: Your Gmail access token (keep private!)
- Both are gitignored for security

### Revoking access
If you want to revoke Gmail access:
1. Go to [Google Account Permissions](https://myaccount.google.com/permissions)
2. Find "Second-Brain-Agent"
3. Click "Remove Access"

---

## File Structure After Setup

```
Second-Brain-Agent/
├── credentials.json    # OAuth client config (shared with Calendar)
├── token.json          # Calendar token
├── gmail_token.json    # Gmail token (auto-generated, keep private!)
├── .gitignore          # Should exclude both tokens
├── src/
│   └── tools/
│       ├── google_calendar.py
│       └── gmail.py
└── ...
```

---

## Testing

Test creating a draft email:

```bash
python src/tools/gmail.py
```

This will:
1. Authenticate (if needed)
2. Create a test draft email
3. List your current drafts

Check your Gmail Drafts folder to see the created draft!

---

## Integration with Chief of Staff

Once Gmail is set up, the Chief of Staff agent will automatically:
1. Analyze your daily briefing
2. Identify when you should send emails (follow-ups, prep, etc.)
3. Create draft emails for you to review
4. You review and send from Gmail manually

Example workflow:
```
Agent: "You have a meeting with Ryan about React migration.
       I've created a draft email to Ryan asking about migration timeline."
```

The draft appears in your Gmail, ready for you to review and send!

---

## Additional Resources

- [Gmail API Documentation](https://developers.google.com/gmail/api/guides)
- [Gmail API Scopes](https://developers.google.com/gmail/api/auth/scopes)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)