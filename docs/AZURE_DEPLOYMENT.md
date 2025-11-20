# Azure Container Apps Deployment Guide

This guide will help you deploy AI X Account Manager to Azure Container Apps.

## Prerequisites

1. **Azure CLI** installed
   ```bash
   # Install Azure CLI (if not already installed)
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```

2. **Docker** installed and running

3. **Azure subscription** with Container Apps enabled

## Step 1: Login to Azure

```bash
az login
```

## Step 2: Set Variables

```bash
# Set your variables
RESOURCE_GROUP="ai-x-manager-rg"
LOCATION="eastus"  # or your preferred location
ACR_NAME="aixmanageracr"  # must be globally unique, lowercase, no hyphens
APP_NAME="ai-x-manager"
CONTAINER_APP_ENV="ai-x-manager-env"
```

## Step 3: Create Resource Group

```bash
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

## Step 4: Create Azure Container Registry (ACR)

```bash
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true
```

## Step 5: Build and Push Docker Image

### Option A: Build locally and push

```bash
# Login to ACR
az acr login --name $ACR_NAME

# Build the image
docker build -t $ACR_NAME.azurecr.io/$APP_NAME:latest .

# Push to ACR
docker push $ACR_NAME.azurecr.io/$APP_NAME:latest
```

### Option B: Build in Azure (recommended for slower connections)

```bash
az acr build \
  --registry $ACR_NAME \
  --image $APP_NAME:latest \
  --file Dockerfile \
  .
```

## Step 6: Create Container Apps Environment

```bash
az containerapp env create \
  --name $CONTAINER_APP_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

## Step 7: Get ACR Credentials

```bash
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)
```

## Step 8: Create Container App

```bash
az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_APP_ENV \
  --image $ACR_NAME.azurecr.io/$APP_NAME:latest \
  --registry-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1Gi \
  --env-vars \
    "ENVIRONMENT=production" \
    "LOG_LEVEL=INFO" \
    "SCHEDULER_TIMEZONE=UTC"
```

## Step 9: Set Secrets as Environment Variables

**IMPORTANT**: Don't put secrets in the command above. Set them separately:

```bash
# Get your app's FQDN first
APP_URL=$(az containerapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv)

echo "Your app URL: https://$APP_URL"

# Set secrets
az containerapp secret set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --secrets \
    twitter-client-id="YOUR_TWITTER_CLIENT_ID" \
    twitter-client-secret="YOUR_TWITTER_CLIENT_SECRET" \
    azure-openai-key="YOUR_AZURE_OPENAI_KEY" \
    secret-key="$(openssl rand -base64 32)" \
    dashboard-password="YOUR_STRONG_PASSWORD"

# Update container with secret references
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars \
    "TWITTER_CLIENT_ID=secretref:twitter-client-id" \
    "TWITTER_CLIENT_SECRET=secretref:twitter-client-secret" \
    "TWITTER_REDIRECT_URI=https://$APP_URL/api/auth/twitter/callback" \
    "AZURE_OPENAI_ENDPOINT=YOUR_AZURE_OPENAI_ENDPOINT" \
    "AZURE_OPENAI_API_KEY=secretref:azure-openai-key" \
    "AZURE_OPENAI_DEPLOYMENT_NAME=YOUR_DEPLOYMENT_NAME" \
    "AZURE_OPENAI_API_VERSION=2024-02-15-preview" \
    "SECRET_KEY=secretref:secret-key" \
    "DASHBOARD_USERNAME=admin" \
    "DASHBOARD_PASSWORD=secretref:dashboard-password" \
    "DATABASE_URL=sqlite:///./ai_x_manager.db"
```

## Step 10: Update Twitter App with Production Callback URL

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Select your app
3. Go to "User authentication settings"
4. Update **Callback URI** to: `https://YOUR_APP_URL/api/auth/twitter/callback`
5. Update **Website URL** to: `https://YOUR_APP_URL`
6. Save changes

Replace `YOUR_APP_URL` with the URL from Step 9.

## Quick Deploy Script

Save this as `deploy.sh`:

```bash
#!/bin/bash
set -e

# Configuration
RESOURCE_GROUP="ai-x-manager-rg"
LOCATION="eastus"
ACR_NAME="aixmanageracr"  # Change this to something unique
APP_NAME="ai-x-manager"
CONTAINER_APP_ENV="ai-x-manager-env"

echo "🚀 Deploying AI X Account Manager to Azure Container Apps..."

# Build and push image
echo "📦 Building and pushing Docker image..."
az acr build \
  --registry $ACR_NAME \
  --image $APP_NAME:latest \
  --file Dockerfile \
  .

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# Update container app
echo "🔄 Updating container app..."
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --image $ACR_NAME.azurecr.io/$APP_NAME:latest

echo "✅ Deployment complete!"

# Get app URL
APP_URL=$(az containerapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv)

echo "🌐 Your app is running at: https://$APP_URL"
```

Make it executable:
```bash
chmod +x deploy.sh
```

## Update Deployment (after initial setup)

After the first deployment, use this simple command to redeploy:

```bash
# Build and push new image
az acr build \
  --registry $ACR_NAME \
  --image $APP_NAME:latest \
  --file Dockerfile \
  .

# Container Apps will automatically update with the new image
# Or force update:
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --image $ACR_NAME.azurecr.io/$APP_NAME:latest
```

## Enable Custom Domain (Optional)

```bash
# Add custom domain
az containerapp hostname add \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --hostname yourdomain.com

# Bind certificate
az containerapp hostname bind \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --hostname yourdomain.com \
  --environment $CONTAINER_APP_ENV \
  --validation-method CNAME
```

## View Logs

```bash
# Stream logs
az containerapp logs show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --follow

# View recent logs
az containerapp logs show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --tail 100
```

## Scale Container

```bash
# Scale manually
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --min-replicas 2 \
  --max-replicas 5

# Scale based on CPU
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --scale-rule-name cpu-scaling \
  --scale-rule-type cpu \
  --scale-rule-metadata type=Utilization value=70
```

## Troubleshooting

### Check container status
```bash
az containerapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.runningStatus
```

### Restart container
```bash
az containerapp revision restart \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP
```

### Check environment variables
```bash
az containerapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.template.containers[0].env
```

## Cost Optimization

- **Development**: Use `--min-replicas 0` to scale to zero when not in use
- **Production**: Use `--min-replicas 1` for always-on availability
- **CPU/Memory**: Start with 0.5 CPU / 1Gi memory and adjust based on usage

## Security Checklist

- ✅ Dashboard authentication enabled (DASHBOARD_USERNAME/PASSWORD)
- ✅ Secrets stored in Azure Container Apps secrets
- ✅ HTTPS enabled by default
- ✅ Twitter OAuth callback uses HTTPS URL
- ✅ Strong SECRET_KEY generated
- ✅ Environment set to "production"

## Monitoring

Enable Application Insights:

```bash
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --enable-dapr \
  --dapr-app-id $APP_NAME \
  --dapr-app-port 8000
```

## Clean Up

To delete all resources:

```bash
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

## Support

- Azure Container Apps Docs: https://learn.microsoft.com/en-us/azure/container-apps/
- Azure CLI Reference: https://learn.microsoft.com/en-us/cli/azure/containerapp

---

**Next Steps After Deployment:**
1. Visit your app URL
2. Sign in with your dashboard credentials (admin/password)
3. Authenticate with Twitter OAuth
4. Start managing your tweets!
