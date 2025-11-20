# Twitter OAuth 2.0 Setup Guide

This guide will help you set up Twitter OAuth 2.0 authentication for AI X Account Manager. This is the **recommended** method as it's much simpler than managing API keys.

## Why OAuth?

✅ **No API Keys Needed** - Just authenticate through your browser
✅ **Secure** - Your credentials are never exposed
✅ **Easy Setup** - Simple "Sign in with Twitter" flow
✅ **Better UX** - Like "Sign in with Google"

## Step-by-Step Setup

### 1. Create a Twitter App

1. Go to the [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Sign in with your Twitter account
3. Click **"Create Project"** (if you don't have one)
   - Enter a project name (e.g., "AI Tweet Manager")
   - Select a use case (e.g., "Making a bot")
   - Provide a project description

4. Click **"Create App"** or select an existing app
   - Enter an app name (e.g., "AI X Account Manager")

### 2. Enable OAuth 2.0

1. In your app settings, go to **"User authentication settings"**
2. Click **"Set up"** or **"Edit"**
3. Configure OAuth 2.0:
   - **App permissions**: Select **"Read and write"**
   - **Type of App**: Select **"Web App, Automated App or Bot"**
   - **App info**:
     - **Callback URI**: `http://localhost:8000/api/auth/twitter/callback`
     - **Website URL**: `http://localhost:8000` (or your production URL)
   - Click **"Save"**

4. You'll see your **OAuth 2.0 Client ID** and **Client Secret**
   - **IMPORTANT**: Copy and save these immediately! The Client Secret is only shown once.

### 3. Configure Your Application

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your OAuth credentials:
   ```env
   # Twitter OAuth 2.0
   TWITTER_CLIENT_ID=your_client_id_here
   TWITTER_CLIENT_SECRET=your_client_secret_here
   TWITTER_REDIRECT_URI=http://localhost:8000/api/auth/twitter/callback

   # Azure OpenAI (still required)
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_API_KEY=your_api_key
   AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
   ```

3. **That's it!** You don't need any other Twitter credentials.

### 4. Authenticate Your Account

1. Start the application:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

2. Open your browser and go to: `http://localhost:8000`

3. Click **"Sign in with Twitter"**

4. You'll be redirected to Twitter to authorize the app

5. After authorizing, you'll be redirected back and see a success page

6. You're now authenticated! The app can post tweets on your behalf.

## Testing Your Setup

### Check Authentication Status

```bash
curl http://localhost:8000/api/auth/twitter/status
```

You should see:
```json
{
  "authenticated": true,
  "user": {
    "id": "123456789",
    "username": "your_username",
    "name": "Your Name"
  },
  "token_expires_at": "2024-03-01T12:00:00+00:00"
}
```

### Generate and Post a Test Tweet

1. Generate an AI tweet:
   ```bash
   curl -X POST "http://localhost:8000/api/ai/generate" \
     -H "Content-Type: application/json" \
     -d '{"topic": "testing my new AI tweet manager", "count": 1}'
   ```

2. Post it immediately:
   ```bash
   curl -X POST "http://localhost:8000/api/tweets/1/post"
   ```

## Production Setup

For production deployment:

1. Update your Twitter App callback URI:
   - Go to Twitter Developer Portal → Your App → User authentication settings
   - Add your production callback URI: `https://yourdomain.com/api/auth/twitter/callback`

2. Update your `.env`:
   ```env
   TWITTER_REDIRECT_URI=https://yourdomain.com/api/auth/twitter/callback
   ```

3. Use HTTPS for security

## Troubleshooting

### Error: "OAuth service not configured"

**Solution**: Make sure you've set `TWITTER_CLIENT_ID` and `TWITTER_CLIENT_SECRET` in your `.env` file.

### Error: "Callback URL mismatch"

**Solution**:
- Check that the callback URI in your `.env` matches exactly what's configured in Twitter Developer Portal
- For local development, use: `http://localhost:8000/api/auth/twitter/callback`
- Don't forget the protocol (`http://` or `https://`)

### Error: "Invalid client credentials"

**Solution**: Double-check your Client ID and Client Secret. They should be from the OAuth 2.0 section, not the API keys section.

### Token Expired

The app automatically refreshes tokens, but if you see token expiry issues:

```bash
# Re-authenticate
curl http://localhost:8000/api/auth/twitter/login
```

### Logout and Re-authenticate

```bash
# Logout
curl -X POST http://localhost:8000/api/auth/twitter/logout

# Then login again through browser
open http://localhost:8000/api/auth/twitter/login
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/twitter/login` | GET | Start OAuth flow (open in browser) |
| `/api/auth/twitter/callback` | GET | OAuth callback (handled automatically) |
| `/api/auth/twitter/status` | GET | Check authentication status |
| `/api/auth/twitter/logout` | POST | Logout and revoke access |

## Security Notes

1. **Never commit your `.env` file** - It contains your Client Secret
2. **Rotate credentials regularly** - Generate new OAuth credentials periodically
3. **Use HTTPS in production** - Required for secure OAuth flow
4. **Review app permissions** - Only grant necessary permissions
5. **Monitor token usage** - Check authentication logs regularly

## Comparison: OAuth vs Legacy API Keys

| Feature | OAuth 2.0 (Recommended) | Legacy API Keys |
|---------|------------------------|-----------------|
| Setup Complexity | ⭐ Simple | ⭐⭐⭐ Complex |
| User Experience | Browser-based auth | Manual key entry |
| Security | High (tokens auto-refresh) | Medium (static keys) |
| Credentials Needed | 2 (Client ID + Secret) | 5 (API keys + tokens) |
| Suitable For | Single user, personal use | Multiple accounts, bots |

## Getting Help

- Check the [main README](../README.md) for general setup
- Review [Twitter's OAuth 2.0 documentation](https://developer.twitter.com/en/docs/authentication/oauth-2-0)
- Open an issue if you need help

---

**Need the legacy API key method instead?** See [LEGACY_AUTH.md](./LEGACY_AUTH.md)
