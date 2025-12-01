# Google Calendar API Setup Guide

This guide will walk you through setting up Google Calendar API access for your Second-Brain-Agent.

## Overview

To access your Google Calendar, you need to:
1. Create a Google Cloud Project
2. Enable the Google Calendar API
3. Create OAuth 2.0 credentials
4. Download the `credentials.json` file
5. Authenticate and generate a token

**Note**: This setup gives the agent **read-only** access to your calendar for privacy and security.

---

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)

2. Click on the project dropdown at the top of the page

3. Click **"New Project"**

4. Enter project details:
   - **Project name**: `Second-Brain-Agent` (or any name you prefer)
   - **Location**: Leave as default or choose your organization

5. Click **"Create"**

6. Wait for the project to be created (this takes a few seconds)

7. Make sure your new project is selected in the project dropdown

---

## Step 2: Enable Google Calendar API

1. In the Google Cloud Console, make sure your project is selected

2. Go to **"APIs & Services"** > **"Library"**
   - Or use this direct link: [API Library](https://console.cloud.google.com/apis/library)

3. In the search bar, type **"Google Calendar API"**

4. Click on **"Google Calendar API"** from the results

5. Click the **"Enable"** button

6. Wait for the API to be enabled (a few seconds)

---

## Step 3: Configure OAuth Consent Screen

Before creating credentials, you need to configure the OAuth consent screen:

1. Go to **"APIs & Services"** > **"OAuth consent screen"**
   - Or use this link: [OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent)

2. Choose **"External"** user type (unless you have a Google Workspace account)

3. Click **"Create"**

4. Fill in the required fields:
   - **App name**: `Second-Brain-Agent`
   - **User support email**: Your email address
   - **Developer contact information**: Your email address

5. Click **"Save and Continue"**

6. On the **"Scopes"** page, click **"Add or Remove Scopes"**

7. Search for **"Google Calendar API"** and select:
   - `https://www.googleapis.com/auth/calendar.readonly` (See your calendar events)

8. Click **"Update"** then **"Save and Continue"**

9. On the **"Test users"** page, click **"Add Users"**

10. Add your Gmail address as a test user

11. Click **"Save and Continue"** and then **"Back to Dashboard"**

---

## Step 4: Create OAuth 2.0 Credentials

1. Go to **"APIs & Services"** > **"Credentials"**
   - Or use this link: [Credentials](https://console.cloud.google.com/apis/credentials)

2. Click **"Create Credentials"** at the top

3. Select **"OAuth client ID"**

4. Choose application type:
   - Select **"Desktop app"**

5. Enter a name:
   - **Name**: `Second-Brain-Agent Desktop Client`

6. Click **"Create"**

7. A dialog will appear showing your client ID and secret - click **"OK"**

---

## Step 5: Download credentials.json

1. On the **Credentials** page, find your newly created OAuth 2.0 Client ID

2. Click the **download icon** (⬇️) on the right side of the credential

3. The file will download as something like `client_secret_xxxxx.json`

4. **Rename** this file to `credentials.json`

5. **Move** `credentials.json` to your project root directory:
   ```
   Second-Brain-Agent/
   ├── credentials.json  ← Place it here
   ├── src/
   ├── data/
   └── ...
   ```

---

## Step 6: First-Time Authentication

1. Make sure `credentials.json` is in your project root

2. Run the calendar test script:
   ```bash
   python src/tools/google_calendar.py
   ```

3. A browser window will open automatically asking you to:
   - Choose your Google account
   - Review the permissions (read-only calendar access)
   - Click **"Continue"** or **"Allow"**

4. You might see a warning that the app isn't verified:
   - Click **"Advanced"**
   - Click **"Go to Second-Brain-Agent (unsafe)"**
   - This is safe because it's your own application

5. After authorizing, you'll see a success message in the browser

6. The script will automatically save a `token.json` file for future use

7. You should see your calendar events printed in the terminal!

---

## Troubleshooting

### "credentials.json not found"
- Make sure `credentials.json` is in the project root directory (same level as `src/` and `data/`)

### "Access blocked: This app's request is invalid"
- Make sure you added your email as a test user in the OAuth consent screen
- Make sure the Google Calendar API is enabled

### "The user did not consent to the scopes"
- Make sure you clicked "Allow" during the OAuth flow
- Make sure the calendar.readonly scope is added to your OAuth consent screen

### Token expired or invalid
- Simply delete `token.json` and run the script again
- You'll go through the authentication flow again

### Browser doesn't open automatically
- Look for a URL printed in the terminal
- Copy and paste it into your browser manually

---

## Security Notes

### What access does the agent have?
- **Read-only** access to your calendar events
- Cannot create, modify, or delete events
- Cannot access other Google services (Gmail, Drive, etc.)

### Credentials files
- `credentials.json`: OAuth client configuration (safe to keep)
- `token.json`: Your personal access token (keep private!)

### Revoking access
If you want to revoke access:
1. Go to [Google Account Permissions](https://myaccount.google.com/permissions)
2. Find "Second-Brain-Agent"
3. Click "Remove Access"

---

## File Structure After Setup

```
Second-Brain-Agent/
├── credentials.json    # OAuth client config (from Google Cloud Console)
├── token.json          # Auto-generated on first auth (keep private!)
├── .gitignore          # Should exclude token.json
├── src/
│   └── tools/
│       └── google_calendar.py
└── ...
```

---

## Next Steps

Once you have the calendar integration working:
- Test with `python src/tools/google_calendar.py`
- Integrate calendar data into your Second Brain queries
- Build agentic workflows that consider your schedule

---

## Additional Resources

- [Google Calendar API Documentation](https://developers.google.com/calendar/api/v3/reference)
- [Google Cloud Console](https://console.cloud.google.com/)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)