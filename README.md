# my_ai_agency

## Overview

This project implements an AI Agency using CrewAI, exposed via FastAPI and Cloudflare Tunnel.

## Architecture

The system follows this data flow:

1.  **n8n** sends HTTP requests to the exposed endpoint.
2.  **FastAPI** receives the request and routes it to the specific CrewAI workflow.
3.  **CrewAI** agents execute the task.
4.  **Response** is returned to n8n.
5.  **Cloudflare Tunnel** exposes the local FastAPI server to the public internet securely.

## Structure

- `app/`: Main application code.
    - `crews/`: CrewAI agent definitions (Marketing, Support, Analysis).
    - `core/`: Core configurations, security, and schemas.
    - `utils/`: Utility functions.
- `cloudflared/`: Configuration for Cloudflare Tunnel.

## Setup

1.  Copy `.env.example` to `.env` and fill in secrets.
2.  Run with Docker Compose:
    ```bash
    docker compose up --build
    ```
3.  Test the health endpoint:
    ```bash
    curl localhost:8000/health
    ```

## Cloudflare Tunnel Setup

To expose your API securely to the internet:

1.  **Create a Tunnel**: Go to the [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/) -> Access -> Tunnels -> Create a Tunnel.
2.  **Download Credentials**: 
    - Save the credentials JSON file (e.g., `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.json`).
    - Move it to the `./cloudflared/` directory in this project.
    - Rename it to match your Tunnel ID if needed, or update the config path.
3.  **Configure Config File**:
    - Edit `./cloudflared/config.yml`.
    - Replace `YOUR_TUNNEL_ID` with your actual Tunnel UUID.
    - Update `credentials-file` path if you renamed the JSON file.
    - Change `hostname` to your desired domain (e.g., `api.example.com`).
4.  **Route Traffic**: In the Cloudflare Dashboard, ensure a Public Hostname is set pointing to your tunnel.
5.  **Run**:
    ```bash
    docker compose up --build
    ```
    Your API will be available at `https://api.yourdomain.com/crews/marketing/run`.

## API Usage

### Run a Crew (Default Provider)

```bash
curl -X POST http://localhost:8000/crews/marketing/run \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "input": {"topic": "AI automation", "target_audience": "developers"},
    "meta": null
  }'
```

### Run a Crew with Anthropic Claude

```bash
curl -X POST http://localhost:8000/crews/marketing/run \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "input": {"topic": "AI automation"},
    "meta": {"llm_provider": "anthropic", "model": "claude-3-5-sonnet-20240620"}
  }'
```

### Run a Crew with Google Gemini

```bash
curl -X POST http://localhost:8000/crews/marketing/run \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "input": {"topic": "AI automation"},
    "meta": {"llm_provider": "google", "model": "gemini-1.5-pro"}
  }'
```

### Async Execution Mode

For long-running tasks, use async mode to avoid timeouts:

**Start async job:**
```bash
curl -X POST "http://localhost:8000/crews/marketing/run?async=true" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "input": {"topic": "AI automation"},
    "meta": {"llm_provider": "anthropic"}
  }'
```

**Response:**
```json
{
  "ok": true,
  "trace_id": "abc-123",
  "crew": "marketing",
  "job_id": "def-456"
}
```

**Poll for result:**
```bash
curl "http://localhost:8000/jobs/def-456" \
  -H "X-API-Key: your-api-key"
```

**Job status response:**
```json
{
  "ok": true,
  "job_id": "def-456",
  "status": "done",
  "crew": "marketing",
  "trace_id": "abc-123",
  "result": { "output": "Generated content..." },
  "error": null
}
```

**Status values:** `queued` → `running` → `done` | `failed`

## n8n Integration

Integrate this API into your n8n workflows using the **HTTP Request** node.

### HTTP Request Configuration

*   **Method**: `POST`
*   **URL**: `https://api.yourdomain.com/crews/{{ $json.crew }}/run`
    *   *Tip*: Use an Expression for the URL to dynamically select the crew (e.g., `marketing`, `support`, `analysis`).
*   **Authentication**: Generic Credential Type -> Header Auth (or manually add header)
*   **Headers**:
    *   `Content-Type`: `application/json`
    *   `X-API-Key`: `your-api-key` (Ensure this matches `API_KEY` in `.env`)
*   **Body Parameters**:
    *   **Send Body**: On
    *   **Mode**: JSON
    *   **Body**:
        ```json
        {
          "input": {{ $json.input }},
          "meta": {
            "llm_provider": "anthropic",
            "model": "claude-3-5-sonnet-20240620"
          }
        }
        ```

### Sample Payloads

Before the HTTP Request node, use a **Set** node or **LLM Chain** to prepare the data.

#### 1. Marketing Payloads
**Set `crew` to `marketing`**
```json
{
  "input": {
    "topic": "Generative AI for Healthcare",
    "target_audience": "Hospital Administrators"
  }
}
```

#### 2. Support Payloads
**Set `crew` to `support`**
```json
{
  "input": {
    "issue": "I cannot reset my password via email",
    "customer_context": "User ID: 12345, Tier: Pro"
  }
}
```

#### 3. Analysis Payloads
**Set `crew` to `analysis`**
```json
{
  "input": {
    "data_description": "Customer churn increased by 5% last month globally",
    "analysis_goal": "Identify geographic patterns"
  }
}
```

### Response Handling

The API returns a structured JSON response. You can reference the final output in subsequent nodes (e.g., to send to Slack or Email).

**Response Schema**:
```json
{
  "ok": true,
  "crew": "marketing",
  "result": {
    "output": "Here is the generated content...",
    "workflow": "marketing",
    "provider": "anthropic"
  }
}
```

**Mapping in n8n**:
*   To use the generated text: `{{ $json.result.output }}`
*   To check success: `{{ $json.ok }}`

### Async Polling Pattern (for Long-Running Tasks)

For workflows that may take longer than HTTP timeout limits:

1.  **HTTP Request Node (Trigger Async Job)**
    *   URL: `https://api.yourdomain.com/crews/{{ $json.crew }}/run?async=true`
    *   This returns immediately with a `job_id`.

2.  **Wait Node**
    *   Set delay to 5-10 seconds.

3.  **HTTP Request Node (Poll Job Status)**
    *   URL: `https://api.yourdomain.com/jobs/{{ $json.job_id }}`
    *   Check response: `{{ $json.status }}`

4.  **IF Node (Check Status)**
    *   Condition: `{{ $json.status }}` equals `done` or `failed`
    *   **True**: Continue to next node (use `{{ $json.result.output }}`).
    *   **False**: Loop back to Wait Node.

**Loop Configuration**:
Use an n8n **Loop Over Items** or **SplitInBatches** node to implement retry logic, or connect the "False" branch back to the Wait node.
