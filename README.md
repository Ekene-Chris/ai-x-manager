# 🤖 AI X Account Manager

An intelligent Twitter/X account management system powered by Azure OpenAI. Automate tweet generation, scheduling, and posting while maintaining full control over your content.

## ✨ Features

### Core Features
- **🤖 AI Tweet Generation**: Generate engaging tweets using Azure OpenAI with customizable style and tone
- **📅 Smart Scheduling**: Schedule tweets for optimal posting times
- **✅ Approval Workflow**: Review and approve AI-generated tweets before posting
- **📊 Analytics Dashboard**: Track engagement metrics (likes, retweets, replies, impressions)
- **🔄 Auto-Posting**: Automated posting at scheduled times
- **✏️ Manual Tweets**: Create and schedule your own tweets
- **💬 Comment Monitoring**: Watch for specific comments and auto-respond (coming soon)

### Technical Features
- RESTful API built with FastAPI
- SQLite/PostgreSQL database support
- Background job scheduling with APScheduler
- Azure OpenAI integration for content generation
- Twitter API v2 integration
- Comprehensive logging and error handling

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Web UI / Frontend                     │
│              (View, Schedule, Approve Tweets)            │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI REST API                        │
│         (Tweet Management, AI, Analytics)                │
└─────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   Twitter    │ │  Azure Open  │ │  Scheduler   │
    │     API      │ │     AI       │ │   Service    │
    └──────────────┘ └──────────────┘ └──────────────┘
                            │
                            ▼
                  ┌──────────────────┐
                  │    Database      │
                  │ (SQLite/Postgres)│
                  └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Twitter Developer Account with API credentials
- Azure OpenAI account with API access
- Git

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd ai-x-manager
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` file with your credentials:

```env
# Twitter API Credentials
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name

# Application
SECRET_KEY=your-secret-key-change-this
```

5. **Run the application**
```bash
python -m uvicorn app.main:app --reload
```

The application will be available at:
- Web UI: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 🔑 Getting API Credentials

### Twitter API Setup

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a new project and app
3. Generate API keys and tokens:
   - API Key and Secret
   - Access Token and Secret
   - Bearer Token (optional, but recommended)
4. Set app permissions to "Read and Write"
5. Copy credentials to `.env` file

### Azure OpenAI Setup

1. Go to [Azure Portal](https://portal.azure.com)
2. Create an Azure OpenAI resource
3. Deploy a model (e.g., GPT-4, GPT-3.5-turbo)
4. Get the endpoint URL and API key from the resource
5. Copy credentials to `.env` file

## 📖 API Usage

### Create a Manual Tweet

```bash
curl -X POST "http://localhost:8000/api/tweets/" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello from AI X Manager!",
    "source": "manual"
  }'
```

### Schedule a Tweet

```bash
curl -X POST "http://localhost:8000/api/tweets/" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This tweet will be posted later!",
    "scheduled_time": "2024-12-25T10:00:00Z",
    "source": "manual"
  }'
```

### Generate AI Tweets

```bash
curl -X POST "http://localhost:8000/api/ai/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "artificial intelligence trends",
    "style": "professional",
    "tone": "engaging",
    "count": 3
  }'
```

### Get All Tweets

```bash
curl "http://localhost:8000/api/tweets/"
```

### Approve an AI-Generated Tweet

```bash
curl -X POST "http://localhost:8000/api/tweets/1/approve"
```

### Post a Tweet Immediately

```bash
curl -X POST "http://localhost:8000/api/tweets/1/post"
```

### Get Analytics

```bash
curl "http://localhost:8000/api/analytics/summary?days=30"
```

## 🎯 Usage Workflow

### Manual Tweet Workflow
1. Create a tweet via API or manually
2. Optionally schedule it for later
3. Tweet gets posted at scheduled time (or post immediately)
4. Monitor engagement metrics

### AI-Assisted Workflow
1. Generate tweets using AI with specific topics/styles
2. Review AI-generated tweets (saved as drafts)
3. Edit if needed
4. Approve or reject
5. Schedule approved tweets
6. Monitor performance

## 📊 Database Schema

### Tables

- **tweets**: Store all tweets (drafts, scheduled, posted)
- **user_preferences**: Store user settings and preferences
- **activity_logs**: Track all system actions
- **comment_rules**: Rules for auto-responding to comments (future)

## 🛠️ Development

### Project Structure

```
ai-x-manager/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── api/                 # API routes
│   │   ├── tweets.py        # Tweet endpoints
│   │   ├── ai.py            # AI generation endpoints
│   │   └── analytics.py     # Analytics endpoints
│   └── services/            # Business logic
│       ├── twitter_service.py    # Twitter API integration
│       ├── llm_service.py        # Azure OpenAI integration
│       └── scheduler_service.py  # Tweet scheduling
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black app/
```

## 🔒 Security Best Practices

1. **Never commit `.env` file** - Contains sensitive credentials
2. **Use environment variables** for all secrets
3. **Rotate API keys regularly**
4. **Use HTTPS** in production
5. **Implement rate limiting** for API endpoints
6. **Regular backups** of database

## 🚢 Deployment

### Using Docker (Recommended)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t ai-x-manager .
docker run -p 8000:8000 --env-file .env ai-x-manager
```

### Using systemd (Linux)

Create `/etc/systemd/system/ai-x-manager.service`:

```ini
[Unit]
Description=AI X Account Manager
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/ai-x-manager
Environment="PATH=/opt/ai-x-manager/venv/bin"
ExecStart=/opt/ai-x-manager/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable ai-x-manager
sudo systemctl start ai-x-manager
```

## 📝 Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | Database connection string | No | `sqlite:///./ai_x_manager.db` |
| `TWITTER_API_KEY` | Twitter API key | Yes | - |
| `TWITTER_API_SECRET` | Twitter API secret | Yes | - |
| `TWITTER_ACCESS_TOKEN` | Twitter access token | Yes | - |
| `TWITTER_ACCESS_TOKEN_SECRET` | Twitter access token secret | Yes | - |
| `TWITTER_BEARER_TOKEN` | Twitter bearer token | No | - |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | Yes | - |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | Yes | - |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Model deployment name | Yes | - |
| `AZURE_OPENAI_API_VERSION` | API version | No | `2024-02-15-preview` |
| `SECRET_KEY` | Application secret key | Yes | - |
| `ENVIRONMENT` | Environment (development/production) | No | `development` |
| `LOG_LEVEL` | Logging level | No | `INFO` |
| `SCHEDULER_TIMEZONE` | Timezone for scheduler | No | `UTC` |

## 🐛 Troubleshooting

### Twitter API Errors

- **401 Unauthorized**: Check your API credentials
- **403 Forbidden**: Verify app permissions (Read and Write)
- **429 Rate Limit**: You've exceeded Twitter's rate limits, wait before retrying

### Azure OpenAI Errors

- **401 Unauthorized**: Check your API key
- **404 Not Found**: Verify your deployment name and endpoint
- **429 Rate Limit**: You've exceeded your quota

### Scheduler Issues

- **Jobs not running**: Check scheduler service is started
- **Time zone issues**: Ensure `SCHEDULER_TIMEZONE` is set correctly
- **Missed jobs**: Check system time and database timestamps

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [Tweepy](https://www.tweepy.org/)
- [Azure OpenAI](https://azure.microsoft.com/en-us/products/cognitive-services/openai-service)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [APScheduler](https://apscheduler.readthedocs.io/)

## 📮 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Built with ❤️ using Python, FastAPI, and Azure OpenAI**
