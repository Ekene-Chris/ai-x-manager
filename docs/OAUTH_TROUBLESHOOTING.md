# OAuth Troubleshooting Guide

## Common OAuth Errors and Solutions

### Error: "OAuth 2 MUST utilize https"

**Cause**: The OAuth library detects HTTP instead of HTTPS in the OAuth flow.

**Solutions**:

#### 1. Check Your Environment Variable (Most Common Fix)

Make sure your `TWITTER_REDIRECT_URI` uses HTTPS in production:

```bash
# ❌ Wrong (will cause the error)
TWITTER_REDIRECT_URI=http://your-app.azurecontainerapps.io/api/auth/twitter/callback

# ✅ Correct
TWITTER_REDIRECT_URI=https://your-app.azurecontainerapps.io/api/auth/twitter/callback
```

**Update in Azure Container Apps**:

```bash
az containerapp update \
  --name ai-x-manager \
  --resource-group ai-x-manager-rg \
  --set-env-vars \
    "TWITTER_REDIRECT_URI=https://YOUR_APP_URL/api/auth/twitter/callback"
```

Replace `YOUR_APP_URL` with your actual Azure Container Apps URL.

#### 2. Verify Environment is Set to Production

```bash
az containerapp update \
  --name ai-x-manager \
  --resource-group ai-x-manager-rg \
  --set-env-vars \
    "ENVIRONMENT=production"
```

This enables the OAuth insecure transport flag that allows the library to work behind Azure's HTTPS proxy.

#### 3. Check Twitter Developer Portal Settings

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Select your app
3. Go to "User authentication settings"
4. Verify **Callback URI** is set to: `https://your-app.azurecontainerapps.io/api/auth/twitter/callback`
5. Verify **Website URL** is set to: `https://your-app.azurecontainerapps.io`

#### 4. Restart Your Container

```bash
az containerapp revision restart \
  --name ai-x-manager \
  --resource-group ai-x-manager-rg
```

### Error: "Invalid callback URL"

**Cause**: The callback URL in your request doesn't match what's configured in Twitter.

**Solution**:

1. Get your exact app URL:
   ```bash
   az containerapp show \
     --name ai-x-manager \
     --resource-group ai-x-manager-rg \
     --query properties.configuration.ingress.fqdn -o tsv
   ```

2. Update environment variable to match:
   ```bash
   APP_URL=$(az containerapp show \
     --name ai-x-manager \
     --resource-group ai-x-manager-rg \
     --query properties.configuration.ingress.fqdn -o tsv)

   az containerapp update \
     --name ai-x-manager \
     --resource-group ai-x-manager-rg \
     --set-env-vars \
       "TWITTER_REDIRECT_URI=https://$APP_URL/api/auth/twitter/callback"
   ```

3. Update Twitter Developer Portal with the exact same URL

### Error: "Invalid client credentials"

**Cause**: Twitter Client ID or Client Secret is incorrect.

**Solution**:

1. Go to Twitter Developer Portal and get fresh credentials
2. Update secrets in Azure:
   ```bash
   az containerapp secret set \
     --name ai-x-manager \
     --resource-group ai-x-manager-rg \
     --secrets \
       twitter-client-id="YOUR_NEW_CLIENT_ID" \
       twitter-client-secret="YOUR_NEW_CLIENT_SECRET"
   ```

3. Restart container

### Error: "401 Unauthorized" when accessing dashboard

**Cause**: Dashboard authentication is enabled but credentials are incorrect.

**Solution**:

Check your credentials in the browser's basic auth dialog:
- **Username**: Value of `DASHBOARD_USERNAME` (default: `admin`)
- **Password**: Value of `DASHBOARD_PASSWORD`

To reset password:

```bash
az containerapp secret set \
  --name ai-x-manager \
  --resource-group ai-x-manager-rg \
  --secrets \
    dashboard-password="YOUR_NEW_PASSWORD"

az containerapp update \
  --name ai-x-manager \
  --resource-group ai-x-manager-rg \
  --set-env-vars \
    "DASHBOARD_PASSWORD=secretref:dashboard-password"
```

## Verification Checklist

Before attempting OAuth login, verify:

- [ ] App is deployed and accessible at HTTPS URL
- [ ] `ENVIRONMENT=production` is set
- [ ] `TWITTER_REDIRECT_URI` starts with `https://`
- [ ] `TWITTER_REDIRECT_URI` matches Twitter Developer Portal callback URI **exactly**
- [ ] Twitter app has "Read and Write" permissions
- [ ] Twitter Client ID and Secret are correct
- [ ] Dashboard authentication credentials are correct

## Debug Commands

### View current environment variables

```bash
az containerapp show \
  --name ai-x-manager \
  --resource-group ai-x-manager-rg \
  --query properties.template.containers[0].env
```

### View logs

```bash
az containerapp logs show \
  --name ai-x-manager \
  --resource-group ai-x-manager-rg \
  --follow
```

### Check container status

```bash
az containerapp show \
  --name ai-x-manager \
  --resource-group ai-x-manager-rg \
  --query properties.runningStatus
```

### Get app URL

```bash
az containerapp show \
  --name ai-x-manager \
  --resource-group ai-x-manager-rg \
  --query properties.configuration.ingress.fqdn -o tsv
```

## Complete Fix Script

Run this if you're having OAuth issues:

```bash
#!/bin/bash

# Get app URL
APP_URL=$(az containerapp show \
  --name ai-x-manager \
  --resource-group ai-x-manager-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

echo "Your app URL: https://$APP_URL"
echo "Callback URL should be: https://$APP_URL/api/auth/twitter/callback"

# Update environment variables
az containerapp update \
  --name ai-x-manager \
  --resource-group ai-x-manager-rg \
  --set-env-vars \
    "ENVIRONMENT=production" \
    "TWITTER_REDIRECT_URI=https://$APP_URL/api/auth/twitter/callback"

echo "✅ Environment variables updated"
echo "⚠️  Now update your Twitter app settings:"
echo "   1. Go to https://developer.twitter.com/en/portal/dashboard"
echo "   2. Set Callback URI to: https://$APP_URL/api/auth/twitter/callback"
echo "   3. Set Website URL to: https://$APP_URL"

# Restart container
az containerapp revision restart \
  --name ai-x-manager \
  --resource-group ai-x-manager-rg

echo "✅ Container restarted"
echo "🎉 Try OAuth login again at: https://$APP_URL"
```

## Still Having Issues?

1. Check logs for specific error messages
2. Verify Twitter app is in production mode (not restricted)
3. Try creating a new Twitter app from scratch
4. Ensure your Azure Container Apps has public ingress enabled

## Contact Support

If none of these solutions work:
1. Export your logs: `az containerapp logs show --name ai-x-manager --resource-group ai-x-manager-rg > logs.txt`
2. Check Twitter API status: https://api.twitterstat.us/
3. Review Azure Container Apps status: https://azure.status.microsoft/
