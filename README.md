# AI DevOps Agent Platform

A learning project for building a **read-only, multi-agent AI DevOps
assistant** that can investigate Docker, PostgreSQL, and network
problems on a Linux VPS.

The long-term goal is to provide a simple web dashboard where a user can
ask questions such as:

> Why is my application unhealthy?

The system will route the request to specialized AI agents, collect real
infrastructure evidence through constrained tools, and return a combined
diagnosis **without modifying the infrastructure**.

---

## 1. Project Goal

This project is being built from scratch to learn how AI agents work in
a real application.

Instead of building a chatbot that only answers from model knowledge,
the project gives AI agents access to **tools** that let them inspect a
real server.

Core principle:

> **The AI can reason about the environment, but it should not be able
> to change it.**

The agents are therefore designed to be read-only.

---

## 2. Target Architecture

```text
                         Internet
                            │
                            ▼
                         Nginx
                            │
                            ▼
                      Next.js UI
                            │
                            ▼
                       FastAPI API
                            │
                            ▼
                       Orchestrator
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
        Docker Agent   Database Agent   Network Agent
             │              │              │
             ▼              ▼              ▼
        Docker MCP       DBHub MCP      Safe network
             │              │             tools
             ▼              ▼              │
          Docker         PostgreSQL         ├── DNS
                                            ├── HTTP/HTTPS
                                            ├── TCP
                                            └── host info
```

The dashboard and reverse-proxy layer are still to be completed.

---

## 3. AI Provider

The project currently uses **DeepSeek** because it is inexpensive for
experimentation.

The provider configuration is not intended to be hard-coded.
Model/provider settings are stored in `.env` so the application can
later switch to another OpenAI-compatible provider with minimal code
changes.

Example:

```env
AI_PROVIDER=deepseek
AI_BASE_URL=https://api.deepseek.com
AI_MODEL=deepseek-v4-flash
AI_API_KEY=...

AGENT_MAX_ITERATIONS=2
ORCHESTRATOR_MAX_ITERATIONS=2
```

The project uses an OpenAI-compatible Python client to communicate with
the configured model.

---

## 4. What Is an Agent in This Project?

An agent is not simply the LLM.

Conceptually:

```text
Agent
 │
 ├── LLM
 ├── instructions
 ├── tools
 ├── tool-selection loop
 └── collected evidence
```

For example, the Docker Agent can reason:

```text
User asks about server health
        │
        ▼
container_list
        │
        ▼
Find restarting container
        │
        ▼
container_logs
        │
        ▼
Inspect evidence
        │
        ▼
Explain likely root cause
```

The LLM does not automatically have Docker, database, or shell access.
It can only use capabilities explicitly exposed to it.

---

## 5. Safety Model

Safety is a central design requirement.

The current project is intended to be **diagnostic only**.

Agents must not:

- start containers
- stop containers
- restart containers
- delete containers
- execute arbitrary commands inside containers
- modify Docker networks
- modify Docker volumes
- modify database records
- change firewall rules
- change routes
- modify DNS configuration
- make infrastructure changes automatically

The preferred security principle is:

> Do not merely tell the model not to perform an action --- do not
> expose the capability in the first place.

---

# 6. Docker Agent

## Status

**Implemented and working.**

The Docker Agent uses a Docker MCP server rather than maintaining a
large collection of custom Docker functions.

Architecture:

```text
DeepSeek
   │
   ▼
Docker Agent
   │
   ▼
Python MCP Client
   │
   ▼
Docker MCP Server
   │
   ▼
Docker daemon
```

The MCP server is started with read-only mode enabled:

```text
DOCKER_MCP_SERVER_READONLY=1
```

The MCP server originally advertised 76 read-only tools. The application
applies an additional Python allowlist and currently exposes only about
20 diagnostic tools to the model.

Examples include:

```text
container_list
container_inspect
container_logs
container_stats
container_top

network_list
network_inspect

volume_list
volume_inspect

image_list
image_inspect

compose_list
compose_ps
compose_logs
compose_config

system_info
system_df
system_events
system_version
```

This reduces both risk and unnecessary tool-schema/token overhead.

### Real diagnostic test

The Docker Agent successfully inspected the VPS and found real issues.

Examples included:

- `css-proxy` in a restart/crash loop
- `ai-job-platform-worker-1` restarting
- exited containers that needed classification as expected or
  unexpected

For `css-proxy`, logs showed an nginx error involving:

```text
host not found in upstream "cssportal_app:8080"
```

The agent correctly reasoned that Docker networking/name resolution was
involved and used Docker evidence to investigate further.

No infrastructure was modified.

---

# 7. MCP

This project uses **Model Context Protocol (MCP)** to connect agents to
external capabilities.

Instead of manually implementing every possible Docker operation:

```python
list_containers()
get_logs()
inspect_container()
get_stats()
inspect_network()
...
```

the MCP server advertises its available tools dynamically.

Conceptually:

```text
Agent
  │
  ▼
list_tools()
  │
  ▼
MCP Server
  │
  ├── container_list
  ├── container_logs
  ├── container_inspect
  └── ...
```

The Python application converts MCP tool schemas into the
OpenAI-compatible function/tool format understood by DeepSeek.

This was one of the main learning goals of the project.

---

# 8. PostgreSQL Lab Database

## Status

**Implemented and working.**

A separate PostgreSQL database was intentionally created for learning
and testing the Database Agent.

Database:

```text
agent_lab
```

This is **not currently the production database for the other
applications on the VPS**.

It exists so the Database Agent can safely practice real database
investigation before being connected to important databases.

Example tables include:

```text
services
incidents
```

Example service state:

```text
api        healthy
dashboard  healthy
worker     degraded
redis      healthy
```

The database can therefore contain intentionally interesting diagnostic
information for the agent to discover.

---

# 9. PostgreSQL Read-Only User

A dedicated PostgreSQL account was created:

```text
agent_reader
```

The AI does not connect as the database administrator.

The intended privilege model is:

```text
agent_admin
    │
    └── administrative privileges

agent_reader
    │
    └── SELECT/read privileges only
```

This provides a database-level security boundary independent of the AI
instructions.

## Password issue encountered

During initialization, `agent_reader` was created, but PostgreSQL
reported:

```text
User "agent_reader" has no password assigned.
```

Therefore authentication failed even though `AGENT_DB_READONLY_PASSWORD`
existed in `.env`.

The existing role was fixed by explicitly assigning the configured
password using `ALTER ROLE`.

Afterward, authentication was tested again.

The goal was also to verify:

```sql
SELECT ...
```

works, while write operations such as:

```sql
DELETE ...
```

are rejected by PostgreSQL permissions.

This was an important lesson: application-level "read-only" instructions
are not enough; the underlying database user should also be restricted.

---

# 10. Database Agent

## Status

**Implemented and working.**

The Database Agent uses **DBHub MCP**.

Current MCP tools:

```text
execute_sql
search_objects
```

DBHub is configured in read-only mode and connects using the restricted
`agent_reader` PostgreSQL account.

Architecture:

```text
DeepSeek
   │
   ▼
Database Agent
   │
   ▼
DBHub MCP
   │
   ├── search_objects
   └── execute_sql
          │
          ▼
     agent_reader
          │
          ▼
      PostgreSQL
```

An important design decision was to avoid writing dozens of functions
such as:

```python
get_database_size()
get_active_connections()
get_locks()
get_incidents()
get_long_queries()
```

Instead, the model receives a constrained read-only SQL tool and can
generate appropriate PostgreSQL `SELECT` queries.

### Successful diagnostic test

The Database Agent successfully:

- identified PostgreSQL version information
- discovered schemas
- discovered `services` and `incidents`
- inspected database statistics
- checked database size
- checked connection counts
- reasoned about cache statistics
- identified evidence that still needed further investigation

With only two investigation iterations configured, the agent also
correctly explained which checks it had not yet completed rather than
pretending they had been performed.

---

# 11. Network Agent

## Status

**Implemented/planned as the third specialist in the current
architecture.**

The Network Agent is intentionally more constrained than a generic shell
agent.

Its tools are designed around:

```text
resolve_dns()
check_tcp_port()
check_http()
get_host_network_info()
```

This allows investigation of:

- DNS resolution
- HTTP/HTTPS reachability
- TCP connectivity
- listening ports
- host addresses
- routing information

without exposing:

```text
shell(command)
run_command(command)
exec(command)
```

The goal is to keep network diagnostics read-only and predictable.

---

# 12. Orchestrator

## Status

**Implemented as the multi-agent coordination layer.**

The orchestrator sits above the specialist agents.

```text
                     User
                      │
                      ▼
                 Orchestrator
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Docker      Database     Network
        Agent        Agent       Agent
```

The orchestrator does not directly inspect Docker or PostgreSQL.

Instead, it receives high-level specialist tools such as:

```text
docker_agent(task)
database_agent(task)
network_agent(task)
```

This creates two levels of agent reasoning.

Example:

```text
User
"Why is my worker failing?"

        │
        ▼

Orchestrator
"Likely Docker-related."

        │
        ▼

Docker Agent
container_list
container_logs
container_inspect

        │
        ▼

Orchestrator
"Database may also be relevant."

        │
        ▼

Database Agent
execute_sql

        │
        ▼

Orchestrator
combines evidence

        │
        ▼

Final diagnosis
```

This is the project's first real multi-agent workflow.

---

# 13. Agent Iteration Limits

Token/cost control is important because nested agents can produce many
model calls.

Current development configuration uses a small limit:

```env
AGENT_MAX_ITERATIONS=2
```

The intent is also to configure:

```env
ORCHESTRATOR_MAX_ITERATIONS=2
```

A specialist may therefore perform approximately:

```text
Iteration 1
    ↓
discover/check

Iteration 2
    ↓
investigate further

    ↓
forced final summary
```

If the investigation limit is reached while the model is still
requesting tools, the code makes a final model call without tools and
asks it to summarize only the evidence already collected.

This avoids ending with:

```text
Agent stopped after reaching maximum iterations.
```

without a useful result.

---

# 14. FastAPI

## Status

**Initial API implementation created; Dockerization is currently in
progress.**

The FastAPI layer is intended to expose the multi-agent system as an
HTTP service.

Planned/current endpoints:

```text
GET  /health
POST /investigate
```

Example:

```http
POST /investigate
Content-Type: application/json
```

```json
{
  "message": "Why is my worker failing?"
}
```

Flow:

```text
HTTP request
    │
    ▼
FastAPI
    │
    ▼
Orchestrator
    │
    ▼
Specialist agents
    │
    ▼
MCP/tools
    │
    ▼
Diagnosis
    │
    ▼
JSON response
```

---

# 15. Dockerizing the AI Platform

## Status

**In progress.**

The project was initially developed using a Python virtual environment.

The runtime is now being moved into Docker so the final application does
not depend on manually activating `.venv`.

The intended API container includes:

```text
Python 3.12
Node.js 22+
Docker CLI
DBHub
FastAPI/Uvicorn
MCP Python SDK
OpenAI-compatible Python client
project source code
```

The container needs Docker access because the Docker MCP server must
inspect the host Docker daemon.

The current Compose design mounts:

```text
/var/run/docker.sock
```

and uses the existing Docker MCP read-only configuration plus the
application tool allowlist.

The API is also intended to use host networking during this learning
stage so it can reach the lab PostgreSQL endpoint at:

```text
127.0.0.1:55433
```

and inspect host networking accurately.

### Current build issue

The first Docker build stopped on a Dockerfile syntax error caused by
writing the JSON-form `CMD` across multiple Dockerfile instructions.

Incorrect:

```dockerfile
CMD [
    "uvicorn",
    "main:app",
    ...
]
```

It was changed to:

```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

The next step is to rebuild and verify that Docker CLI and DBHub are
correctly available inside the resulting image.

---

# 16. Current Project Structure

Approximate structure:

```text
ai-agents/
│
├── .env
├── .env.example
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
│
├── apps/
│   │
│   ├── agent/
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── docker_agent.py
│   │   │   ├── database_agent.py
│   │   │   ├── network_agent.py
│   │   │   └── orchestrator.py
│   │   │
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── docker_tools.py
│   │   │   ├── tool_registry.py
│   │   │   └── network_tools.py
│   │   │
│   │   ├── config.py
│   │   ├── llm.py
│   │   ├── mcp_client.py
│   │   ├── database_mcp_client.py
│   │   ├── dbhub.toml
│   │   ├── main.py
│   │   └── test_*.py
│   │
│   └── api/
│       └── main.py
│
└── infra/
    └── database/
        ├── docker-compose.yml
        └── init/
            └── 01-init.sh
```

Some old manually implemented Docker tools remain intentionally as
learning/reference code even though the Docker Agent now uses MCP.

---

# 17. What We Have Learned So Far

The project has already covered several important AI-agent concepts.

### Tool calling

An LLM cannot inspect Docker simply because it "knows Docker."

It needs a tool:

```text
LLM
 ↓
tool call
 ↓
real system
 ↓
tool result
 ↓
LLM reasoning
```

### MCP

MCP allows external servers to advertise reusable tools instead of
requiring every integration to be implemented manually.

### Agent loops

Agents may repeatedly:

```text
reason
 ↓
select tool
 ↓
receive evidence
 ↓
reason again
```

until they have enough evidence.

### Specialized agents

Instead of giving one model every tool:

```text
Docker + SQL + networking + everything
```

the system uses focused specialists.

### Orchestration

A higher-level agent can delegate tasks to specialists and combine their
findings.

### Least privilege

Read-only behavior should be enforced at multiple layers:

```text
LLM instructions
       ↓
application allowlist
       ↓
MCP restrictions
       ↓
database permissions
       ↓
underlying infrastructure
```

### Cost control

Agent systems can generate more model calls than ordinary chat because
an orchestrator may call specialists that themselves perform multiple
LLM/tool iterations.

Iteration limits and smaller tool sets help control cost.

---

# 18. Current Milestone

The current milestone is:

> **Containerize the FastAPI + multi-agent runtime.**

Current work:

```text
Dockerfile
   ↓
build API/agent image
   ↓
verify Docker CLI
   ↓
verify DBHub
   ↓
start FastAPI container
   ↓
GET /health
   ↓
POST /investigate
```

---

# 19. Next Milestones

After the API container works:

```text
1. Finish FastAPI container
        ↓
2. Build simple Next.js dashboard
        ↓
3. Containerize dashboard
        ↓
4. Connect dashboard → FastAPI
        ↓
5. Display investigation result
        ↓
6. Display agent/tool activity
        ↓
7. Store investigation history
        ↓
8. Add authentication
        ↓
9. Put application behind Nginx
        ↓
10. Carefully connect agents to real application resources
```

The first dashboard does not need to be sophisticated.

Target:

```text
┌─────────────────────────────────────────────┐
│ AI DevOps Agent                             │
├─────────────────────────────────────────────┤
│                                             │
│ Ask about your infrastructure               │
│ ┌─────────────────────────────────────────┐ │
│ │ Why is my worker failing?               │ │
│ └─────────────────────────────────────────┘ │
│                                    [Ask]    │
│                                             │
│ Investigation                              │
│ ✓ Docker Agent                             │
│ ✓ Checked containers                       │
│ ✓ Read logs                                │
│ ✓ Database Agent                           │
│                                             │
│ Result                                     │
│ ─────────────────────────────────────────  │
│ The worker appears to be failing because… │
│                                             │
└─────────────────────────────────────────────┘
```

---

# 20. Long-Term Ideas

Once the core learning project is stable, possible extensions include:

- investigation history
- streaming tool activity to the dashboard
- Prometheus/Grafana metrics integration
- Redis diagnostics
- log-analysis agent
- security agent
- Kubernetes agent
- cloud provider agent
- GitHub/CI agent
- alerts
- scheduled health investigations
- incident reports
- agent memory
- user authentication
- multiple infrastructure environments
- approval-based remediation

Any future remediation should use explicit human approval rather than
silently giving the diagnostic agents unrestricted write access.

---

## Current Status

```text
DeepSeek                         ✅
Configurable provider/model      ✅
Custom agent loop                ✅
Tool calling                     ✅
MCP                              ✅
Docker MCP                       ✅
Docker Agent                     ✅
PostgreSQL lab                   ✅
Read-only DB account             ✅
DBHub MCP                        ✅
Database Agent                   ✅
Network diagnostic tools         ✅
Network Agent                    ✅ / integration stage
Orchestrator                     ✅
Multi-agent delegation           ✅
FastAPI                          🚧
Dockerized API runtime           🚧
Next.js dashboard                ⏳
Nginx/public deployment          ⏳
```

---

## Philosophy

The project is intentionally being built incrementally.

The goal is not merely to produce a working AI application, but to
understand each layer:

```text
LLM
 ↓
tool calling
 ↓
MCP
 ↓
specialist agent
 ↓
orchestration
 ↓
API
 ↓
dashboard
 ↓
production deployment
```

That makes the project both a practical DevOps assistant and a hands-on
environment for learning modern AI-agent architecture.
