# GitHub Code Reviewer Bot

An intelligent microservices-based system that automatically reviews GitHub pull requests using AI. When a PR is opened, the bot analyzes the code and posts actionable feedback directly as comments on the PR.

## Architecture

The system uses three independent microservices communicating asynchronously via Redis:

```
GitHub Webhook Event (PR opened)
         ↓
┌─────────────────────────────────┐
│  Webhook Service (Port 3000)    │
│  - Receives GitHub events       │
│  - Publishes to Redis queue     │
└─────────────────────────────────┘
         ↓ (Redis: pull-request channel)
┌─────────────────────────────────┐
│  Review Service (Port 3000)     │
│  - Listens for PR events        │
│  - Calls DeepSeek AI API        │
│  - Publishes reviews to Redis   │
└─────────────────────────────────┘
         ↓ (Redis: reviews channel)
┌─────────────────────────────────┐
│  GitHub Service (Port 3000)     │
│  - Posts reviews as PR comments │
│  - Handles GitHub API calls     │
└─────────────────────────────────┘
         ↓
   GitHub PR Comment Posted
```

**Why this architecture?** Loose coupling means services fail independently. If the AI API is slow, the webhook service keeps working. If GitHub API is down, reviews still get generated.

## Features

- **Microservices Architecture** — Three independent services with Redis pub/sub messaging
- **Async Processing** — Non-blocking, event-driven workflow
- **Error Handling** — Graceful failures with retry logic and detailed logging
- **AI-Powered Reviews** — Integration with DeepSeek API for intelligent code analysis
- **Docker Support** — Single `docker compose up` to run everything
- **Production-Ready** — Environment variables, health checks, proper signal handling

## Tech Stack

- **NestJS** — Backend framework with dependency injection
- **Redis** — Message broker (pub/sub)
- **DeepSeek API** — AI code review generation
- **GitHub API** — PR integration and comment posting
- **Docker & Docker Compose** — Containerization and orchestration
- **TypeScript** — Type-safe development

## Prerequisites

- Node.js 20+
- Docker & Docker Compose
- GitHub personal access token ([create here](https://github.com/settings/tokens))
- DeepSeek API key ([get here](https://platform.deepseek.com/api_keys))

## Setup

### 1. Clone & Install

```bash
git clone git@github.com:nurgissas/github-code-reviewer.git
cd github-code-reviewer
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
GITHUB_TOKEN=your-github-personal-access-token
DEEPSEEK_API_KEY=your-deepseek-api-key
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=
```

### 3. Run with Docker

```bash
docker compose up --build
```

App runs on `http://localhost:3000`

### 4. Configure GitHub Webhook

1. Go to your repository → Settings → Webhooks
2. Click "Add webhook"
3. **Payload URL**: `http://your-domain/webhook`
4. **Content type**: `application/json`
5. **Events**: Select "Pull requests"
6. Check "Active"

## How It Works

1. **PR Created**: Developer opens a pull request on GitHub
2. **Webhook Triggered**: GitHub sends POST request to `/webhook` endpoint
3. **Queued**: Webhook Service extracts PR data, publishes to `pull-request` Redis channel
4. **Reviewed**: Review Service subscribes to channel, receives message, calls DeepSeek API with PR details
5. **Generated**: DeepSeek returns code review (markdown format)
6. **Posted**: GitHub Service subscribes to `reviews` channel, receives completed review, posts it as a comment on the PR via GitHub API

All services run in parallel. If one fails, others keep working.

## Project Structure

```
src/
├── app.module.ts              # Root module
├── app.controller.ts          # Health check endpoint
├── redis.service.ts           # Redis client & pub/sub
├── redis.module.ts            # Redis module wrapper
├── webhook/                   # Service 1: Receive PR events
│   ├── webhook.controller.ts  # HTTP POST endpoint
│   ├── webhook.service.ts     # Process & publish to Redis
│   └── webhook.module.ts
├── review/                    # Service 2: AI review generation
│   ├── review.service.ts      # Subscribe → Call DeepSeek → Publish
│   └── review.module.ts
└── github/                    # Service 3: Post reviews
    ├── github.service.ts      # Subscribe → Post to GitHub
    └── github.module.ts

Dockerfile                      # Multi-stage build for production
docker-compose.yml             # Redis + NestJS app orchestration
.env.example                   # Environment variable template
```

## Environment Variables

| Variable           | Description                  | Example                  |
| ------------------ | ---------------------------- | ------------------------ |
| `GITHUB_TOKEN`     | GitHub personal access token | `ghp_xxxxx...`           |
| `DEEPSEEK_API_KEY` | DeepSeek API key             | `sk-xxxxx...`            |
| `REDIS_URL`        | Redis connection URL         | `redis://redis:6379`     |
| `REDIS_PASSWORD`   | Redis password (optional)    | `` (empty for local dev) |
| `NODE_ENV`         | Environment                  | `development`            |

## Key Implementation Details

### Error Handling

Each service has try-catch blocks around critical operations:

- Webhook: Validates payload, catches Redis publish errors
- Review: Checks API key, handles DeepSeek API failures, returns fallback review
- GitHub: Validates token, catches GitHub API errors

### Async Messaging

Services communicate via Redis pub/sub, not HTTP. No service waits for another:

- Webhook publishes and returns immediately
- Review Service picks it up whenever it's ready
- GitHub Service posts whenever review is ready

### Docker Networking

Inside Docker containers, services communicate by hostname (`redis://redis:6379`), not localhost. The `docker-compose.yml` creates an internal network where service names resolve as hostnames.

## Future Improvements

- **GitLab Support** — Accept merge request webhooks alongside GitHub PRs
- **Rate Limiting** — Prevent API quota exhaustion
- **PR Diff Analysis** — Include actual code changes in review prompt
- **Multiple AI Providers** — Support Claude, GPT-4, other models
- **Review History** — Store review results in database
- **Metrics Dashboard** — Track review stats and performance
- **Webhook Verification** — Validate GitHub webhook signatures for security

## License

MIT
