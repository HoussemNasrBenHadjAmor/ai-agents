# AI DevOps Agent

A read-only multi-agent AI system for investigating infrastructure problems across Docker, PostgreSQL, and networking.

The project uses specialist AI agents, MCP servers, a central orchestrator, FastAPI, Next.js, PostgreSQL, and a configurable LLM provider.

The main goal of this project is to learn how real AI agent systems work by building one from scratch.

---

# 1. Project Goal

The AI DevOps Agent allows a user to ask infrastructure questions such as:

```text
List any Docker containers that are currently restarting or unhealthy.
```

or:

```text
Investigate why my application is unavailable.
```

The system can then:

1. Understand the request.
2. Select the appropriate specialist agent.
3. Use real infrastructure tools through MCP.
4. Collect evidence.
5. Investigate further when necessary.
6. Produce a structured diagnosis.
7. Stream investigation progress to the dashboard.
8. Save the investigation and events to history.

The system is intentionally:

> READ-ONLY

Agents can inspect infrastructure but must not automatically restart, stop, delete, modify, or reconfigure infrastructure.

---

# 2. Architecture

```text
                         Internet
                            │
                            ▼
                   Nginx Proxy Manager
                            │
                            ▼
                     Next.js Dashboard
                            │
                            │ HTTP / SSE
                            ▼
                       FastAPI API
                            │
                            ▼
                    Agent Orchestrator
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
       Docker Agent    Database Agent   Network Agent
             │              │              │
             ▼              ▼              ▼
        Docker MCP      Database MCP    Network Tools
             │              │              │
             ▼              ▼              ▼
      Docker Engine     PostgreSQL      HTTP / DNS /
      Containers        Databases       TCP / Host
      Networks
      Volumes
      Compose

                            │
                            ▼
                     Structured Diagnosis
                            │
                            ▼
                    Investigation History
                            │
                            ▼
                  PostgreSQL History DB
```

---

# 3. Current Technology Stack

## AI / Agent Layer

- Python 3.12
- DeepSeek
- OpenAI-compatible API client
- MCP — Model Context Protocol
- Custom agent orchestration
- Tool calling
- Structured JSON diagnosis

The LLM provider is configurable through `.env`.

Example:

```env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-flash
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=YOUR_API_KEY
```

The provider/model configuration is not hard-coded into the agents.

This allows the project to later switch between providers such as:

```text
DeepSeek
GPT
Claude
other compatible providers
```

without rewriting the agent architecture.

---

# 4. Application Layer

## Backend

FastAPI provides:

- agent initialization
- orchestration
- investigation requests
- Server-Sent Events streaming
- investigation history
- investigation detail retrieval
- structured diagnosis delivery

## Frontend

Next.js provides the web dashboard.

The dashboard currently supports:

- investigation prompt input
- real-time investigation progress
- specialist selection visibility
- tool execution visibility
- structured diagnosis
- severity badges
- issue tables
- evidence display
- likely root-cause display
- recommended next investigation steps
- investigation history
- loading previous investigations

---

# 5. Docker Deployment

The project runs in Docker.

The development philosophy is:

> Application services should run in containers rather than requiring manually activated Python virtual environments.

Main containers include:

```text
ai-agents-api
ai-agents-dashboard
ai-agents-history-db
```

The API container has access to:

```text
/var/run/docker.sock
```

which allows the Docker MCP server to inspect the host Docker environment.

The Docker tools exposed to the LLM are restricted to approved read-only diagnostic operations.

---

# 6. Networking

The dashboard is connected to:

```text
benca-network
```

because the existing Nginx Proxy Manager also uses this Docker network.

Example:

```yaml
dashboard:
  networks:
    - benca-network

networks:
  benca-network:
    external: true
```

The dashboard is exposed locally on:

```text
127.0.0.1:3005
```

Nginx Proxy Manager can proxy traffic to the dashboard through the shared Docker network.

The API currently uses host networking because it needs access to several host-level services and MCP resources.

---

# 7. Agent Architecture

The project currently contains four important agent components.

```text
Agent Orchestrator
        │
        ├── Docker Agent
        │
        ├── Database Agent
        │
        └── Network Agent
```

---

# 8. Agent Orchestrator

The orchestrator is the central decision-making agent.

It does not directly inspect infrastructure.

Instead, it determines which specialist should investigate the user's request.

Example:

```text
User:
Why is my container restarting?
```

The orchestrator determines:

```text
Docker problem
      │
      ▼
Docker Agent
```

For:

```text
Are any PostgreSQL sessions blocked?
```

it routes to:

```text
Database Agent
```

For:

```text
Why can't the API domain be reached?
```

it can route to:

```text
Network Agent
```

For more complicated problems, multiple specialists may eventually collaborate.

Example:

```text
User
 │
 ▼
Orchestrator
 │
 ├── Docker Agent
 │      │
 │      └── API container appears healthy
 │
 ├── Database Agent
 │      │
 │      └── Database appears healthy
 │
 └── Network Agent
        │
        └── DNS points to wrong host
```

The orchestrator then combines the evidence into the final diagnosis.

---

# 9. Docker Agent

The Docker Agent investigates the Docker environment.

Instead of manually implementing every Docker command as a Python function, the project uses a Docker MCP server.

The MCP server exposes Docker capabilities to the agent.

During testing, the MCP server exposed approximately:

```text
76 Docker tools
```

Examples included:

```text
container_list
container_inspect
container_logs
container_stats
container_top

compose_list
compose_ps
compose_logs
compose_config

network_list
network_inspect

volume_list
volume_inspect

image_list
image_inspect

system_info
system_df
system_events
```

However, the AI is not given unrestricted access to all tools.

The application maintains an approved read-only tool list.

Approximately:

```text
20 approved Docker tools
```

are currently exposed to the Docker Agent.

This provides an important safety boundary.

---

# 10. Docker Investigation Example

The Docker Agent successfully detected real infrastructure problems.

Example:

```text
css-proxy
```

was found continuously restarting.

The agent inspected the logs and discovered:

```text
host not found in upstream "cssportal_app:8080"
```

The agent concluded that the likely cause was Docker hostname/network resolution between:

```text
css-proxy
```

and:

```text
cssportal_app
```

Another real problem detected was:

```text
ai-job-platform-worker-1
```

which was repeatedly restarting.

The agent attempted further log investigation while respecting the read-only policy.

This demonstrated the core agent loop:

```text
Observe
   │
   ▼
Reason
   │
   ▼
Choose Tool
   │
   ▼
Collect Evidence
   │
   ▼
Reason Again
   │
   ▼
Diagnosis
```

---

# 11. Database Agent

The Database Agent uses DBHub as a PostgreSQL MCP server.

The agent currently has tools such as:

```text
execute_sql
search_objects
```

This allows the AI to inspect:

- schemas
- tables
- application data
- PostgreSQL statistics
- connections
- locks
- blocked sessions
- database size
- long-running queries
- incidents

without receiving administrative database privileges.

---

# 12. Database Lab

A PostgreSQL lab database was created specifically for learning and testing the Database Agent.

Database:

```text
agent_lab
```

Example tables:

```text
services
incidents
```

These allow us to simulate application state and incidents without risking production data.

---

# 13. Read-Only Database User

The Database Agent connects using:

```text
agent_reader
```

This account is intentionally restricted.

The agent should not connect as:

```text
postgres
```

or another administrative account.

This enforces database safety at the permission level rather than relying only on the AI prompt.

---

# 14. Database Password Issue We Solved

During setup, PostgreSQL returned:

```text
FATAL: password authentication failed for user "agent_reader"
```

The PostgreSQL logs revealed the actual problem:

```text
User "agent_reader" has no password assigned.
```

The role existed:

```text
agent_reader
```

but it did not have a password.

A password was assigned to the role and the `.env` configuration was updated to use the matching credential.

After fixing the credentials, the Database MCP server successfully connected:

```text
Connecting to 1 database source(s)...

lab:
postgres://agent_reader@127.0.0.1:55433/agent_lab
```

The important lesson was:

```text
Role existence != valid authentication configuration
```

---

# 15. Database Agent Test

The Database Agent successfully inspected PostgreSQL and discovered:

```text
PostgreSQL 16.x
Database: agent_lab
User: agent_reader
Schema: public
```

It found:

```text
services
incidents
```

and inspected PostgreSQL statistics.

The test demonstrated that the LLM could autonomously choose database queries through MCP instead of requiring us to manually code every SQL diagnostic operation.

---

# 16. Network Agent

The Network Agent handles networking investigations.

Its responsibilities include:

```text
DNS
HTTP
HTTPS
TCP
listening ports
routes
host networking
connectivity
```

The Network Agent remains read-only.

It can investigate questions such as:

```text
Can the server resolve api.example.com?
```

```text
Is port 443 reachable?
```

```text
What process is listening on port 8000?
```

```text
Does this HTTP endpoint respond?
```

---

# 17. Agent Safety Model

Safety is one of the core architectural requirements.

The project uses multiple layers.

## Layer 1 — System Prompts

Agents are explicitly instructed:

```text
Do not modify anything.
```

## Layer 2 — Tool Allowlist

Only approved diagnostic tools are exposed.

## Layer 3 — Database Permissions

The database agent uses:

```text
agent_reader
```

instead of an administrative account.

## Layer 4 — MCP Tool Restrictions

Write-capable MCP operations are not exposed to the LLM.

The intended architecture is therefore:

```text
AI reasoning
     │
     ▼
Allowed tool?
     │
 ┌───┴───┐
 │       │
NO      YES
 │       │
BLOCK   Execute
         │
         ▼
      Read-only
```

This is much safer than simply telling the model:

```text
please don't delete anything
```

while still giving it destructive tools.

---

# 18. Investigation Iterations

Agents operate using bounded investigation loops.

For example:

```env
MAX_ITERATIONS=2
```

Limiting iterations helps control:

- token consumption
- API costs
- runaway investigations
- excessive tool calls

The trade-off is that complex investigations may stop before all evidence has been collected.

This happened during our Database Agent testing when only two iterations were available.

The architecture therefore allows iteration limits to be adjusted based on the desired balance between:

```text
cost
vs
investigation depth
```

---

# 19. Real-Time Investigation Progress

The API uses:

```text
Server-Sent Events (SSE)
```

to stream investigation progress to the dashboard.

Instead of waiting with no feedback:

```text
User
 │
 │
 │ waiting...
 │
 │
 ▼
Result
```

the user can see:

```text
Investigation started

Docker Agent selected

Docker Agent started

container_list started

container_list completed

container_logs started

container_logs completed

Building final diagnosis

Investigation completed
```

This makes agent behavior much easier to understand.

---

# 20. Investigation Events

Events are generated during agent execution.

Examples:

```text
investigation_started
specialist_selected
agent_started
tool_started
tool_completed
agent_completed
synthesizing
investigation_completed
```

Tool events can also contain metadata such as:

```json
{
  "agent": "docker",
  "tool": "container_logs",
  "arguments": {
    "id_or_name": "css-proxy",
    "tail": 40
  }
}
```

This gives us observability into the agent's behavior.

---

# 21. Investigation History

Investigations are persisted in PostgreSQL.

Each investigation stores information such as:

```text
ID
user message
status
text result
structured diagnosis
error
creation time
completion time
events
```

Example investigation ID:

```text
27f9b6b8-6401-416a-8575-aab6c91f9ead
```

The API supports retrieving previous investigations.

Example:

```text
GET /investigations
```

and:

```text
GET /investigations/{id}
```

This means investigations survive page refreshes and container restarts as long as the history database persists.

---

# 22. Structured Diagnosis

Originally, the LLM returned free-form Markdown such as:

```text
**Unhealthy containers found:**

- css-proxy — crash looping
- floci-ui_floci_1 — unhealthy
```

This worked, but made dashboard rendering difficult.

The project now uses a structured diagnosis format.

Example:

```json
{
  "summary": {
    "status": "critical",
    "total_issues": 2,
    "critical": 1,
    "warnings": 1,
    "healthy": 0,
    "headline": "Docker problems detected"
  },
  "issues": [
    {
      "resource": "css-proxy",
      "resource_type": "docker",
      "status": "restarting",
      "severity": "critical",
      "problem": "Crash loop",
      "evidence": "host not found in upstream \"cssportal_app:8080\"",
      "likely_cause": "Docker networking or hostname resolution",
      "recommendation": "Inspect the Docker network configuration."
    }
  ],
  "narrative": "The Docker environment contains an active proxy crash loop."
}
```

This separates:

```text
AI reasoning/output
        │
        ▼
Structured data
        │
        ▼
UI presentation
```

The LLM no longer decides how the dashboard should visually display the result.

---

# 23. Diagnosis Dashboard

The dashboard can now display structured findings as a table.

Example:

```text
┌──────────────────────┬──────────┬────────────┬──────────────┬──────────┐
│ RESOURCE             │ TYPE     │ STATUS     │ PROBLEM      │ SEVERITY │
├──────────────────────┼──────────┼────────────┼──────────────┼──────────┤
│ css-proxy            │ Docker   │ Restarting │ Crash loop   │ Critical │
│ floci-ui_floci_1     │ Docker   │ Exited     │ Health check │ Warning  │
└──────────────────────┴──────────┴────────────┴──────────────┴──────────┘
```

Each finding can also display:

```text
Problem
Evidence
Likely Cause
Recommended Next Step
```

Severity levels currently include:

```text
Critical
Warning
Info
Healthy
```

The same UI structure can later display findings from all specialist agents:

```text
RESOURCE            TYPE       STATUS       PROBLEM
────────────────────────────────────────────────────────
css-proxy           Docker     Restarting   Crash loop
postgres            Database   Blocked      Lock contention
api.example.com     Network    Timeout      TCP unreachable
```

---

# 24. History Database Structured Results

The `investigations` table now stores both:

```text
result
```

and:

```text
result_json
```

`result` stores the readable narrative.

`result_json` stores the structured diagnosis.

The existing database was migrated with:

```sql
ALTER TABLE investigations
ADD COLUMN IF NOT EXISTS result_json JSONB;
```

Older investigations remain compatible.

If an old investigation does not contain structured JSON, the dashboard falls back to displaying the original textual diagnosis.

---

# 25. Current Investigation Flow

The complete current workflow is:

```text
User
 │
 ▼
Next.js Dashboard
 │
 │ POST investigation
 ▼
FastAPI
 │
 ├── Create history record
 │
 ▼
Orchestrator
 │
 ├── Understand request
 │
 ├── Select specialist
 │
 ▼
Specialist Agent
 │
 ├── Select MCP tool
 │
 ├── Execute read-only tool
 │
 ├── Inspect result
 │
 ├── Possibly select another tool
 │
 ▼
Specialist Result
 │
 ▼
Orchestrator
 │
 ├── Combine evidence
 │
 ├── Generate structured JSON
 │
 ▼
Structured Diagnosis
 │
 ├── Summary
 │
 ├── Issues
 │
 ├── Severity
 │
 ├── Evidence
 │
 ├── Likely Cause
 │
 ├── Recommendation
 │
 └── Narrative
 │
 ├──────────────► PostgreSQL History
 │
 ▼
FastAPI SSE
 │
 ▼
Next.js Dashboard
 │
 ├── Progress
 ├── Diagnosis table
 ├── Severity badges
 ├── Evidence cards
 └── Analysis
```

---

# 26. Project Structure

Current structure is approximately:

```text
ai-agents/
│
├── .env
├── docker-compose.yml
├── Dockerfile
├── README.md
│
├── apps/
│   │
│   ├── agent/
│   │   │
│   │   ├── agents/
│   │   │   ├── docker_agent.py
│   │   │   ├── database_agent.py
│   │   │   ├── network_agent.py
│   │   │   └── orchestrator.py
│   │   │
│   │   ├── tools/
│   │   ├── config.py
│   │   ├── events.py
│   │   ├── llm.py
│   │   ├── mcp_client.py
│   │   ├── database_mcp_client.py
│   │   ├── dbhub.toml
│   │   └── main.py
│   │
│   ├── api/
│   │   ├── main.py
│   │   └── history.py
│   │
│   └── dashboard/
│       │
│       ├── app/
│       │   ├── page.tsx
│       │   └── ...
│       │
│       ├── Dockerfile
│       ├── package.json
│       └── ...
│
└── ...
```

---

# 27. Running the Project

The application should be run through Docker.

Build:

```bash
cd ~/ai-agents

docker compose build
```

Start:

```bash
docker compose up -d
```

Check containers:

```bash
docker compose ps
```

Check API logs:

```bash
docker logs ai-agents-api --tail 100
```

Check dashboard logs:

```bash
docker logs ai-agents-dashboard --tail 100
```

---

# 28. Example Low-Cost Investigation

Because LLM usage costs tokens, small focused prompts are useful during development.

Example:

```text
List any Docker containers that are currently restarting or unhealthy. Use the minimum tools needed. Keep the diagnosis concise.
```

This helps test:

```text
Dashboard
→ API
→ Orchestrator
→ Docker Agent
→ MCP
→ Docker
→ Structured Diagnosis
→ History
→ Dashboard
```

without running an unnecessarily large investigation.

---

# 29. What We Have Achieved

The project is no longer just a simple chatbot.

We have built the foundations of a real agentic system.

Completed:

- [x] Linux VPS environment
- [x] Docker-based deployment
- [x] Configurable LLM provider
- [x] DeepSeek integration
- [x] Tool-calling architecture
- [x] Docker MCP integration
- [x] Docker Agent
- [x] Docker read-only tool allowlist
- [x] Real Docker infrastructure inspection
- [x] Container log investigation
- [x] Database MCP integration
- [x] PostgreSQL lab
- [x] Read-only PostgreSQL user
- [x] Database Agent
- [x] Database diagnostics
- [x] Network Agent
- [x] Agent Orchestrator
- [x] Specialist routing
- [x] FastAPI backend
- [x] Next.js dashboard
- [x] Dockerized dashboard
- [x] Nginx Proxy Manager integration
- [x] Real-time SSE progress
- [x] Tool execution progress
- [x] PostgreSQL investigation history
- [x] Investigation event persistence
- [x] Structured JSON diagnosis
- [x] Severity classification
- [x] Diagnosis table
- [x] Evidence cards
- [x] Root-cause presentation
- [x] Backward compatibility for old textual investigations
- [x] Read-only safety architecture

---

# 30. What We Are Learning

This project demonstrates several important AI-agent concepts.

## Tool Calling

An LLM cannot magically access Docker.

It needs tools.

```text
LLM
 │
 ▼
Tool Call
 │
 ▼
Docker MCP
 │
 ▼
Docker Engine
```

---

## MCP

Instead of manually implementing every possible tool:

```python
def list_containers():
    ...

def inspect_container():
    ...

def read_logs():
    ...
```

an MCP server can expose an existing standardized toolset.

---

## Agent Loops

Agents do not necessarily call one tool and stop.

They can perform:

```text
Observe
→ Reason
→ Tool
→ Observe
→ Reason
→ Tool
→ Diagnose
```

---

## Specialist Agents

Rather than giving one AI every capability, responsibilities are separated:

```text
Docker Agent
Database Agent
Network Agent
```

This improves specialization and makes permissions easier to control.

---

## Orchestration

The orchestrator decides:

```text
Which agent should investigate this?
```

This separates routing from specialist execution.

---

## Structured Outputs

Free-form text is useful for humans.

Structured output is better for applications.

Therefore:

```text
LLM
 │
 ▼
Structured JSON
 │
 ▼
Frontend
 │
 ▼
Tables / badges / cards
```

---

## Agent Observability

A production-quality agent system should expose what it is doing.

Our event architecture gives visibility into:

```text
agent selection
tool selection
tool execution
investigation progress
completion
```

---

## Safety

Agent safety should not depend only on prompts.

Better:

```text
Prompt restrictions
        +
Tool allowlist
        +
Read-only credentials
        +
Infrastructure permissions
```

---

# 31. Current Limitations

The project still has several limitations.

### Investigation depth

Low iteration limits can prevent specialists from completing complex investigations.

### Structured output

The structured diagnosis is currently generated by prompting the LLM for JSON and validating/parsing the response.

Future versions should use stronger schema validation.

### Network Agent

The Network Agent can be expanded with more standardized MCP tooling.

### Cross-agent reasoning

The orchestrator can route to specialists, but deeper multi-agent collaboration can still be improved.

### Authentication

The dashboard/API should eventually have authentication before being treated as a production management interface.

### Resource usage

The VPS has limited RAM and no swap was initially configured, so Docker image builds and multiple services can consume significant memory.

---

# 32. Recommended Next Milestones

## Milestone 1 — Strong Diagnosis Schema

Add Pydantic models for:

```text
Diagnosis
DiagnosisSummary
DiagnosisIssue
```

so malformed model responses cannot silently enter the application.

---

## Milestone 2 — Better Investigation Details

Allow clicking a finding such as:

```text
css-proxy
```

to inspect:

```text
tool calls
raw evidence
container metadata
logs
timeline
```

---

## Milestone 3 — Cross-Agent Investigation

Allow the orchestrator to correlate:

```text
Docker
+
Database
+
Network
```

during one investigation.

Example:

```text
API unavailable
   │
   ├── Docker Agent → container healthy
   ├── Database Agent → database healthy
   └── Network Agent → DNS incorrect
```

---

## Milestone 4 — Infrastructure Overview

Add a dashboard overview showing:

```text
Docker
Database
Network
Investigations
Critical findings
Recent incidents
```

---

## Milestone 5 — Better Observability

Track:

```text
LLM calls
tokens
tool calls
investigation duration
agent duration
errors
cost per investigation
```

---

## Milestone 6 — Safe Action Proposals

The system should remain read-only.

Later, agents may be allowed to **propose** remediation:

```text
Recommended action:

Attach css-proxy to network X.

[Copy command]
```

but execution should still require explicit human action.

The architecture should remain:

```text
AI investigates
AI recommends
Human decides
Human executes
```

rather than:

```text
AI detects
AI changes production automatically
```

---

# 33. Current Project Status

Current stage:

```text
             AI DEVOPS AGENT

                    User
                     │
                     ▼
              Web Dashboard        ✓
                     │
                     ▼
               FastAPI API         ✓
                     │
                     ▼
               Orchestrator        ✓
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
     Docker       Database      Network
      Agent         Agent        Agent
        ✓             ✓            ✓
        │             │            │
        ▼             ▼            ▼
    Docker MCP     DB MCP      Network Tools
        ✓             ✓            ✓
        │             │            │
        └─────────────┼────────────┘
                      │
                      ▼
              Structured Diagnosis ✓
                      │
               ┌──────┴──────┐
               ▼             ▼
          History DB       Dashboard
               ✓             ✓
```

We have completed the main foundation of the multi-agent system.

The next phase is no longer about simply making an LLM call tools.

The next phase is about making the system:

```text
more reliable
more observable
more structured
more efficient
and better at coordinating multiple agents
```

while preserving the read-only safety model.
