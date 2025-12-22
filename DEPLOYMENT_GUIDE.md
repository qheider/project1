# Deployment Guide: Project1 to AWS and Azure

## Overview
This guide covers deploying the Flask application with Azure AI Search integration to both AWS and Azure cloud platforms.

---

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Azure Deployment](#azure-deployment)
3. [AWS Deployment](#aws-deployment)
4. [Post-Deployment Configuration](#post-deployment-configuration)
5. [Monitoring and Maintenance](#monitoring-and-maintenance)

---

## Pre-Deployment Checklist

### 1. Prepare Application for Production

#### Update `app.py` for Production
```python
import os

if __name__ == "__main__":
    # Get port from environment variable (for cloud platforms)
    port = int(os.environ.get('PORT', 5000))
    # Disable debug mode in production
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
```

#### Create `wsgi.py` for Production WSGI Server
```python
"""WSGI entry point for production deployment."""
from app import app

if __name__ == "__main__":
    app.run()
```

#### Update `requirements.txt` for Production
Add production dependencies:
```txt
Flask>=2.0
pytest
requests
python-dotenv
openai
azure-search-documents
azure-identity
gunicorn==21.2.0  # Production WSGI server
```

Install:
```powershell
pip install gunicorn
pip freeze > requirements.txt
```

### 2. Security Hardening

#### Create `.env.example` (Template without secrets)
```bash
# Azure Foundry / Azure OpenAI Configuration
AZURE_FOUNDRY_MODEL_ENDPOINT="https://your-endpoint.cognitiveservices.azure.com/"
AZURE_FOUNDRY_MODEL_DEPLOYMENT="gpt-4.1-nano"
AZURE_FOUNDRY_MODEL_API_VERSION=2025-01-01-preview
AZURE_FOUNDRY_MODEL_API_KEY="your-api-key-here"

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT="https://your-endpoint.cognitiveservices.azure.com/openai/deployments/gpt-4.1-nano/chat/completions?api-version=2024-05-01-preview"
AZURE_OPENAI_API_KEY="your-api-key-here"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4.1-nano"

# Azure AI Search Configuration
AZURE_SEARCH_SERVICE_ENDPOINT="https://your-search-service.search.windows.net"
AZURE_SEARCH_INDEX_NAME="your-index-name"
AZURE_SEARCH_API_KEY="your-search-api-key"

# Flask Configuration
FLASK_ENV=production
SECRET_KEY="generate-a-secure-random-key"
```

#### Update `.gitignore`
```
.env
.venv/
__pycache__/
*.pyc
*.pyo
*.log
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.DS_Store
```

### 3. Test Locally with Production Settings
```powershell
# Set production environment
$env:FLASK_ENV="production"

# Test with Gunicorn (if on Linux/WSL)
gunicorn --bind 0.0.0.0:5000 wsgi:app

# On Windows, test with waitress
pip install waitress
waitress-serve --port=5000 wsgi:app
```

---

## Azure Deployment

### Option 1: Azure App Service (Recommended)

#### Step 1: Install Azure CLI
```powershell
# Install Azure CLI
winget install Microsoft.AzureCLI

# Login
az login

# Set subscription
az account set --subscription <subscription-id>
```

#### Step 2: Create Azure Resources
```powershell
# Set variables
$RESOURCE_GROUP="project1-rg"
$LOCATION="eastus2"
$APP_NAME="project1-flask-app"  # Must be globally unique
$APP_SERVICE_PLAN="project1-plan"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create App Service Plan (Linux)
az appservice plan create `
  --name $APP_SERVICE_PLAN `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION `
  --sku B1 `
  --is-linux

# Create Web App
az webapp create `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --plan $APP_SERVICE_PLAN `
  --runtime "PYTHON:3.11"
```

#### Step 3: Configure Environment Variables
```powershell
# Set application settings (environment variables)
az webapp config appsettings set `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --settings `
    FLASK_ENV="production" `
    AZURE_FOUNDRY_MODEL_ENDPOINT="<your-endpoint>" `
    AZURE_FOUNDRY_MODEL_DEPLOYMENT="gpt-4.1-nano" `
    AZURE_FOUNDRY_MODEL_API_KEY="<your-key>" `
    AZURE_OPENAI_ENDPOINT="<your-endpoint>" `
    AZURE_OPENAI_API_KEY="<your-key>" `
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4.1-nano" `
    AZURE_SEARCH_SERVICE_ENDPOINT="<your-endpoint>" `
    AZURE_SEARCH_INDEX_NAME="<your-index>" `
    AZURE_SEARCH_API_KEY="<your-key>" `
    SCM_DO_BUILD_DURING_DEPLOYMENT="true"
```

#### Step 4: Configure Startup Command
```powershell
# Set startup command
az webapp config set `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --startup-file "gunicorn --bind=0.0.0.0:8000 wsgi:app"
```

#### Step 5: Deploy Code

**Option A: Deploy from Local Git**
```powershell
# Configure local git deployment
az webapp deployment source config-local-git `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP

# Get deployment URL
$GIT_URL = az webapp deployment source show `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --query "repoUrl" -o tsv

# Add Azure as git remote
git remote add azure $GIT_URL

# Deploy
git add .
git commit -m "Deploy to Azure"
git push azure main
```

**Option B: Deploy with ZIP**
```powershell
# Create deployment package (exclude unnecessary files)
Compress-Archive -Path `
  app.py, `
  azure_foundry_client.py, `
  azure_search_client.py, `
  call_Azure_endpoints.py, `
  wsgi.py, `
  requirements.txt, `
  static, `
  templates `
  -DestinationPath deploy.zip -Force

# Deploy ZIP
az webapp deployment source config-zip `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --src deploy.zip
```

**Option C: Deploy from GitHub**
```powershell
# Configure GitHub deployment
az webapp deployment source config `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --repo-url https://github.com/qheider/project1 `
  --branch Azure-AI_search_connection `
  --manual-integration
```

#### Step 6: Enable Managed Identity (Optional, for better security)
```powershell
# Enable system-assigned managed identity
az webapp identity assign `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP

# Get the principal ID
$PRINCIPAL_ID = az webapp identity show `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --query principalId -o tsv

# Assign roles to managed identity for Azure Search
az role assignment create `
  --role "Search Index Data Reader" `
  --assignee $PRINCIPAL_ID `
  --scope "/subscriptions/<subscription-id>/resourceGroups/<rg>/providers/Microsoft.Search/searchServices/<search-service>"
```

#### Step 7: Verify Deployment
```powershell
# Get app URL
az webapp show `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --query defaultHostName -o tsv
```

Visit: `https://<app-name>.azurewebsites.net`

#### Step 8: View Logs
```powershell
# Enable application logging
az webapp log config `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --application-logging filesystem `
  --level information

# Stream logs
az webapp log tail `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP
```

---

### Option 2: Azure Container Instances

#### Step 1: Create Dockerfile
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 5000

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "wsgi:app"]
```

#### Step 2: Build and Push Docker Image
```powershell
# Create Azure Container Registry
$ACR_NAME="project1acr"  # Must be globally unique
az acr create `
  --resource-group $RESOURCE_GROUP `
  --name $ACR_NAME `
  --sku Basic `
  --admin-enabled true

# Login to ACR
az acr login --name $ACR_NAME

# Build and push image
az acr build `
  --registry $ACR_NAME `
  --image project1-app:latest `
  --file Dockerfile .
```

#### Step 3: Deploy Container
```powershell
# Get ACR credentials
$ACR_USERNAME = az acr credential show --name $ACR_NAME --query username -o tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv

# Create container instance
az container create `
  --resource-group $RESOURCE_GROUP `
  --name project1-container `
  --image "$ACR_NAME.azurecr.io/project1-app:latest" `
  --dns-name-label project1-app `
  --ports 5000 `
  --registry-login-server "$ACR_NAME.azurecr.io" `
  --registry-username $ACR_USERNAME `
  --registry-password $ACR_PASSWORD `
  --environment-variables `
    FLASK_ENV=production `
    AZURE_OPENAI_ENDPOINT="<value>" `
    AZURE_OPENAI_API_KEY="<value>" `
  --secure-environment-variables `
    AZURE_SEARCH_API_KEY="<value>"

# Get URL
az container show `
  --resource-group $RESOURCE_GROUP `
  --name project1-container `
  --query ipAddress.fqdn -o tsv
```

---

## AWS Deployment

### Option 1: AWS Elastic Beanstalk (Recommended)

#### Step 1: Install AWS CLI and EB CLI
```powershell
# Install AWS CLI
winget install Amazon.AWSCLI

# Configure AWS credentials
aws configure

# Install EB CLI
pip install awsebcli
```

#### Step 2: Prepare Application

Create `.ebextensions/python.config`:
```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: wsgi:app
  aws:elasticbeanstalk:application:environment:
    FLASK_ENV: production
```

Create `.ebignore`:
```
.git/
.venv/
__pycache__/
*.pyc
.env
tests/
.pytest_cache/
```

#### Step 3: Initialize EB Application
```powershell
# Initialize EB
eb init -p python-3.11 project1-flask-app --region us-east-2

# Create environment
eb create project1-prod-env `
  --instance-type t3.small `
  --envvars `
    FLASK_ENV=production,`
    AZURE_FOUNDRY_MODEL_ENDPOINT=<value>,`
    AZURE_FOUNDRY_MODEL_API_KEY=<value>,`
    AZURE_OPENAI_ENDPOINT=<value>,`
    AZURE_OPENAI_API_KEY=<value>,`
    AZURE_SEARCH_SERVICE_ENDPOINT=<value>,`
    AZURE_SEARCH_INDEX_NAME=<value>,`
    AZURE_SEARCH_API_KEY=<value>
```

#### Step 4: Deploy
```powershell
# Deploy application
eb deploy

# Open in browser
eb open

# Check status
eb status

# View logs
eb logs
```

#### Step 5: Update Environment Variables
```powershell
# Set environment variables
eb setenv `
  AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1-nano `
  FLASK_ENV=production

# Or use AWS Console
aws elasticbeanstalk update-environment `
  --environment-name project1-prod-env `
  --option-settings `
    Namespace=aws:elasticbeanstalk:application:environment,OptionName=AZURE_OPENAI_API_KEY,Value=<value>
```

---

### Option 2: AWS EC2 with Manual Setup

#### Step 1: Launch EC2 Instance
```powershell
# Create key pair
aws ec2 create-key-pair `
  --key-name project1-key `
  --query 'KeyMaterial' `
  --output text > project1-key.pem

# Create security group
$SG_ID = aws ec2 create-security-group `
  --group-name project1-sg `
  --description "Security group for Project1" `
  --query 'GroupId' `
  --output text

# Allow HTTP traffic
aws ec2 authorize-security-group-ingress `
  --group-id $SG_ID `
  --protocol tcp `
  --port 80 `
  --cidr 0.0.0.0/0

# Allow SSH
aws ec2 authorize-security-group-ingress `
  --group-id $SG_ID `
  --protocol tcp `
  --port 22 `
  --cidr 0.0.0.0/0

# Launch instance (Ubuntu 22.04)
$INSTANCE_ID = aws ec2 run-instances `
  --image-id ami-0c7217cdde317cfec `
  --instance-type t3.small `
  --key-name project1-key `
  --security-group-ids $SG_ID `
  --query 'Instances[0].InstanceId' `
  --output text

# Get public IP
aws ec2 describe-instances `
  --instance-ids $INSTANCE_ID `
  --query 'Reservations[0].Instances[0].PublicIpAddress' `
  --output text
```

#### Step 2: Connect and Configure Server
```bash
# SSH into instance
ssh -i project1-key.pem ubuntu@<public-ip>

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.11 python3.11-venv python3-pip nginx -y

# Create application directory
sudo mkdir -p /var/www/project1
sudo chown ubuntu:ubuntu /var/www/project1
cd /var/www/project1

# Clone repository
git clone https://github.com/qheider/project1.git .
git checkout Azure-AI_search_connection

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn
```

#### Step 3: Configure Environment Variables
```bash
# Create .env file
nano .env

# Paste your environment variables, then save (Ctrl+X, Y, Enter)
```

#### Step 4: Create Systemd Service
```bash
# Create service file
sudo nano /etc/systemd/system/project1.service
```

Add:
```ini
[Unit]
Description=Project1 Flask Application
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/var/www/project1
Environment="PATH=/var/www/project1/.venv/bin"
ExecStart=/var/www/project1/.venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Start and enable service
sudo systemctl start project1
sudo systemctl enable project1
sudo systemctl status project1
```

#### Step 5: Configure Nginx
```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/project1
```

Add:
```nginx
server {
    listen 80;
    server_name <your-domain-or-ip>;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/project1/static;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/project1 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### Option 3: AWS ECS (Elastic Container Service)

#### Step 1: Create ECR Repository
```powershell
# Create repository
aws ecr create-repository --repository-name project1-app

# Get repository URI
$ECR_URI = aws ecr describe-repositories `
  --repository-names project1-app `
  --query 'repositories[0].repositoryUri' `
  --output text

# Login to ECR
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin $ECR_URI
```

#### Step 2: Build and Push Docker Image
```powershell
# Build image
docker build -t project1-app .

# Tag image
docker tag project1-app:latest "$ECR_URI:latest"

# Push to ECR
docker push "$ECR_URI:latest"
```

#### Step 3: Create ECS Task Definition
Create `task-definition.json`:
```json
{
  "family": "project1-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "project1-container",
      "image": "<ecr-uri>:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "FLASK_ENV", "value": "production"}
      ],
      "secrets": [
        {
          "name": "AZURE_OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:name"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/project1",
          "awslogs-region": "us-east-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Step 4: Create ECS Cluster and Service
```powershell
# Create cluster
aws ecs create-cluster --cluster-name project1-cluster

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service with load balancer (requires VPC setup)
aws ecs create-service `
  --cluster project1-cluster `
  --service-name project1-service `
  --task-definition project1-task `
  --desired-count 2 `
  --launch-type FARGATE `
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

---

## Post-Deployment Configuration

### 1. Set Up Custom Domain

#### Azure
```powershell
# Add custom domain
az webapp config hostname add `
  --webapp-name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --hostname www.yourdomain.com

# Enable HTTPS
az webapp config ssl bind `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --certificate-thumbprint <thumbprint> `
  --ssl-type SNI
```

#### AWS (Route 53)
```powershell
# Create hosted zone (if needed)
aws route53 create-hosted-zone --name yourdomain.com --caller-reference $(Get-Date -Format "yyyyMMddHHmmss")

# Add A record pointing to your EB environment or ALB
```

### 2. Enable HTTPS/SSL

#### Azure
- Azure App Service provides free SSL certificates
- Use Azure Front Door or Application Gateway for advanced scenarios

#### AWS
```powershell
# Request certificate (ACM)
aws acm request-certificate `
  --domain-name yourdomain.com `
  --validation-method DNS

# Attach to load balancer
aws elbv2 add-listener-certificates `
  --listener-arn <arn> `
  --certificates CertificateArn=<cert-arn>
```

### 3. Configure Secrets Management

#### Azure Key Vault
```powershell
# Create Key Vault
az keyvault create `
  --name project1-kv `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION

# Add secrets
az keyvault secret set `
  --vault-name project1-kv `
  --name AZURE-OPENAI-API-KEY `
  --value "<your-key>"

# Grant access to App Service
az keyvault set-policy `
  --name project1-kv `
  --object-id $PRINCIPAL_ID `
  --secret-permissions get list
```

Update code to use Key Vault:
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://project1-kv.vault.azure.net/", credential=credential)
api_key = client.get_secret("AZURE-OPENAI-API-KEY").value
```

#### AWS Secrets Manager
```powershell
# Create secret
aws secretsmanager create-secret `
  --name project1/azure-openai-key `
  --secret-string "<your-key>"

# Grant EC2 instance access via IAM role
aws iam attach-role-policy `
  --role-name EC2-Project1-Role `
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
```

---

## Monitoring and Maintenance

### Azure Monitoring

#### Application Insights
```powershell
# Create Application Insights
az monitor app-insights component create `
  --app project1-insights `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION

# Get instrumentation key
$INSTRUMENTATION_KEY = az monitor app-insights component show `
  --app project1-insights `
  --resource-group $RESOURCE_GROUP `
  --query instrumentationKey -o tsv

# Add to app settings
az webapp config appsettings set `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY
```

#### View Metrics
```powershell
# View application logs
az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP

# View metrics in portal
# Navigate to: Azure Portal > App Service > Monitoring > Metrics
```

### AWS Monitoring

#### CloudWatch Logs
```powershell
# Create log group
aws logs create-log-group --log-group-name /aws/elasticbeanstalk/project1

# View logs
aws logs tail /aws/elasticbeanstalk/project1 --follow
```

#### CloudWatch Metrics
```powershell
# Get CPU utilization
aws cloudwatch get-metric-statistics `
  --namespace AWS/EC2 `
  --metric-name CPUUtilization `
  --dimensions Name=InstanceId,Value=$INSTANCE_ID `
  --start-time 2025-12-19T00:00:00Z `
  --end-time 2025-12-19T23:59:59Z `
  --period 3600 `
  --statistics Average
```

### Scaling

#### Azure Auto-Scaling
```powershell
# Configure auto-scale
az monitor autoscale create `
  --resource-group $RESOURCE_GROUP `
  --resource $APP_NAME `
  --resource-type Microsoft.Web/serverFarms `
  --name autoscale-project1 `
  --min-count 1 `
  --max-count 5 `
  --count 2

# Add CPU-based scaling rule
az monitor autoscale rule create `
  --resource-group $RESOURCE_GROUP `
  --autoscale-name autoscale-project1 `
  --condition "Percentage CPU > 70 avg 5m" `
  --scale out 1
```

#### AWS Auto-Scaling
```powershell
# EB auto-scaling (configured in console or .ebextensions)
# EC2 auto-scaling groups
aws autoscaling create-auto-scaling-group `
  --auto-scaling-group-name project1-asg `
  --launch-configuration-name project1-lc `
  --min-size 1 `
  --max-size 5 `
  --desired-capacity 2
```

---

## Cost Optimization

### Azure
- **Free Tier**: F1 App Service Plan (limited)
- **Basic**: B1 (~$13/month) - Good for small apps
- **Standard**: S1 (~$69/month) - Production with auto-scale
- **Reserved Instances**: Save up to 72% with 1-3 year commitment

### AWS
- **Free Tier**: t2.micro EC2 for 12 months
- **Elastic Beanstalk**: No additional charge (pay for EC2/RDS)
- **ECS Fargate**: Pay per vCPU/memory/second
- **Savings Plans**: Save up to 72% with commitment

---

## Troubleshooting

### Common Deployment Issues

#### Azure: "Application Error"
```powershell
# Check logs
az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP

# Check app settings
az webapp config appsettings list --name $APP_NAME --resource-group $RESOURCE_GROUP

# Restart app
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP
```

#### AWS: "502 Bad Gateway"
```powershell
# Check EB health
eb health

# Check logs
eb logs

# SSH into instance
eb ssh
```

#### Common Fixes
1. Verify all environment variables are set
2. Check Python version compatibility
3. Ensure dependencies are in requirements.txt
4. Verify startup command (gunicorn path)
5. Check port bindings (use PORT environment variable)
6. Review security groups/firewall rules

---

## Rollback Procedures

### Azure
```powershell
# Swap deployment slots
az webapp deployment slot swap `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --slot staging `
  --target-slot production

# Or redeploy previous version
git push azure previous-commit-sha:main --force
```

### AWS
```powershell
# EB: Deploy previous version
eb deploy --version <previous-version>

# Or use AWS Console to deploy previous application version
```

---

## Security Checklist

- [ ] All secrets in environment variables or secret manager
- [ ] `.env` file in `.gitignore`
- [ ] HTTPS/SSL enabled
- [ ] Security groups/firewall configured
- [ ] Regular dependency updates (`pip list --outdated`)
- [ ] Application logging enabled
- [ ] Monitoring and alerts configured
- [ ] Backup strategy in place
- [ ] Rate limiting configured (if needed)
- [ ] CORS configured properly (if needed)

---

## Additional Resources

### Azure
- [Azure App Service Documentation](https://learn.microsoft.com/en-us/azure/app-service/)
- [Azure Container Instances](https://learn.microsoft.com/en-us/azure/container-instances/)
- [Azure Key Vault](https://learn.microsoft.com/en-us/azure/key-vault/)

### AWS
- [Elastic Beanstalk Documentation](https://docs.aws.amazon.com/elasticbeanstalk/)
- [ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [EC2 Documentation](https://docs.aws.amazon.com/ec2/)

---

*Last Updated: December 19, 2025*
