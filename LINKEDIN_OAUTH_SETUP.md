# LinkedIn OAuth Setup Guide

This guide walks you through creating LinkedIn OAuth credentials (Client ID and Client Secret) for the social login feature.

## Prerequisites

- A LinkedIn account
- A company page on LinkedIn (required for OAuth apps)

## Step 1: Create a LinkedIn App

1. Go to the [LinkedIn Developer Portal](https://www.linkedin.com/developers/apps)
2. Click **"Create app"**
3. Fill in the required fields:
   - **App name**: e.g., "Founding Mindset Portal"
   - **LinkedIn Page**: Select your company page (create one if needed)
   - **Privacy policy URL**: Your app's privacy policy URL (can use a placeholder for development)
   - **App logo**: Upload a logo (any square image works)
4. Check the legal agreement box and click **"Create app"**

## Step 2: Configure OAuth 2.0

1. After creating the app, go to the **"Auth"** tab
2. Under **"OAuth 2.0 settings"**, find:
   - **Client ID** - Copy this value
   - **Client Secret** - Click the eye icon to reveal, then copy
3. Under **"Authorized redirect URLs for your app"**, add:
   ```
   http://localhost:5001/api/auth/linkedin/callback
   ```
   For production, also add your production callback URL:
   ```
   https://your-domain.com/api/auth/linkedin/callback
   ```
4. Click **"Update"** to save

## Step 3: Request API Products

1. Go to the **"Products"** tab
2. Request access to **"Sign In with LinkedIn using OpenID Connect"**
   - This gives you the `openid`, `profile`, and `email` scopes
3. Wait for approval (usually instant for OpenID Connect)

## Step 4: Update Your .env File

Open the `.env` file in the project root and update these values:

```env
LINKEDIN_CLIENT_ID=your_actual_client_id_here
LINKEDIN_CLIENT_SECRET=your_actual_client_secret_here
LINKEDIN_REDIRECT_URI=http://localhost:5001/api/auth/linkedin/callback
```

## Step 5: Verify Setup

1. Start the backend: `cd backend && python app.py`
2. Start the frontend: `cd frontend && npm start`
3. Go to Profile Edit page
4. Click **"Login with LinkedIn"**
5. You should be redirected to LinkedIn's consent page
6. After granting consent, you'll be redirected back to the app
7. The "Authenticated" badge should appear, and you can now scrape profiles

## How the Flow Works

```
User clicks "Login with LinkedIn"
    |
    v
Frontend calls POST /api/auth/linkedin/consent-url
    |
    v
Backend generates LinkedIn OAuth URL with state token
    |
    v
User is redirected to LinkedIn consent page
    |
    v
User grants permission
    |
    v
LinkedIn redirects to GET /api/auth/linkedin/callback?code=...&state=...
    |
    v
Backend exchanges code for access token
    |
    v
Backend stores linkedinAuthed=true on user document
    |
    v
User is redirected back to /profile/edit?linkedin_success=true
    |
    v
Frontend detects success param and enables scraping
```

## Troubleshooting

### "LinkedIn OAuth is not configured" error
- Make sure `LINKEDIN_CLIENT_ID` and `LINKEDIN_CLIENT_SECRET` are set in `.env`
- Restart the backend after updating `.env`

### "token_exchange_failed" error
- Verify your Client Secret is correct
- Check that the redirect URI in `.env` exactly matches what's configured in the LinkedIn app
- Make sure the redirect URI uses the same protocol (http vs https)

### LinkedIn consent page shows an error
- Verify the Client ID is correct
- Make sure you've requested the "Sign In with LinkedIn using OpenID Connect" product
- Check that the redirect URI is properly registered in the LinkedIn app settings

### Redirect URI mismatch
- The redirect URI must match EXACTLY between your `.env` and LinkedIn app settings
- Watch for trailing slashes, http vs https, and port numbers

## Production Considerations

- Use HTTPS for the redirect URI in production
- Store credentials securely (environment variables, secrets manager)
- Consider implementing token refresh for long-lived sessions
- Set `LINKEDIN_REDIRECT_URI` to your production callback URL
