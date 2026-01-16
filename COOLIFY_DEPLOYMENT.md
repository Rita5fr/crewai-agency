# Coolify Deployment Guide for CrewAI Agency

## Prerequisites
- Coolify instance with Traefik configured
- GitHub repository access

## Step 1: Push to GitHub

```bash
cd my_ai_agency
git init
git add .
git commit -m "Initial commit - CrewAI Agency"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/crewai-agency.git
git push -u origin main
```

## Step 2: Create Application in Coolify

1. Go to **Projects** → **Add New Resource** → **Public Repository**
2. Enter your GitHub repo URL
3. Select **Docker Compose** as build pack
4. Set **Port** to `8000`

## Step 3: Configure Environment Variables

In Coolify → Your App → **Environment Variables**, add:

| Variable | Value |
|----------|-------|
| `API_KEY` | Your API key for authenticating requests |
| `DEFAULT_LLM_PROVIDER` | `deepseek` |
| `DEEPSEEK_API_KEY` | Your DeepSeek API key |
| `DEEPSEEK_MODEL` | `deepseek-chat` |
| `GOOGLE_API_KEY` | Your Google API key |
| `GEMINI_API_KEY` | Your Google API key |
| `GEMINI_MODEL` | `gemini-2.0-flash` |
| `PERPLEXITY_API_KEY` | Your Perplexity API key |
| `PERPLEXITY_MODEL` | `sonar-pro` |

## Step 4: Configure Domain

1. Go to **Settings** → **General**
2. Add your domain (e.g., `crewai.yourdomain.com`)
3. Enable **HTTPS** (Traefik auto-generates SSL via Let's Encrypt)

## Step 5: Deploy

Click **Deploy** and wait for the build to complete.

## API Endpoints

| Crew | Endpoint | Input Fields |
|------|----------|--------------|
| Marketing | `/crews/marketing/run` | `topic` |
| Support | `/crews/support/run` | `issue` |
| Analysis | `/crews/analysis/run` | `data_description` |
| Social Media | `/crews/social_media/run` | `industry`, `company_name` |

## Example Request

```bash
curl -X POST "https://your-domain.com/crews/social_media/run" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"input": {"industry": "hypnotherapy", "company_name": "MindWorks"}}'
```

## Health Check

```bash
curl https://your-domain.com/health
# Returns: {"ok": true}
```
