---
title: Support Inbox Triage OpenEnv
sdk: docker
app_port: 7860
tags:
  - openenv
  - reinforcement-learning
  - agents
---

# Support Inbox Triage OpenEnv

Support Inbox Triage OpenEnv is a real-world OpenEnv environment built for customer support operations. Instead of solving a toy problem, an agent must handle realistic support tickets by setting priority, routing to the correct team, adding tags, drafting a customer reply, and resolving or escalating the case. The project is designed for local development, validation, Docker execution, and deployment as a Hugging Face Docker Space.

## Getting Started

These instructions will help you run the project locally for development, testing, and validation. This README is written so that even someone who has not seen the original hackathon task can still set up and use the project properly.

### Prerequisites

You need the following installed on your machine:

- Python 3.11 or newer
- PowerShell if you are on Windows
- Docker Desktop if you want to run Docker checks and container builds
- A valid Hugging Face token if you want to use the model-driven inference mode

Check your versions with:

```powershell
python --version
docker --version
```

### Installing

A step-by-step setup guide is below.

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate the virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

Install the runtime dependencies:

```powershell
pip install -r requirements.txt
```

If you want to run local validation and tests, also install the dev dependencies:

```powershell
pip install -r requirements-dev.txt
```

Start the local API server:

```powershell
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

You should see output similar to:

```text
INFO:     Started server process [...]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:7860
```

End with a quick demo request to confirm the system is working:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:7860/reset -ContentType "application/json" -Body '{"task_id":"duplicate_refund"}'
```

You should receive an observation object containing values such as:

```text
task_id           : duplicate_refund
difficulty        : easy
ticket_id         : TCK-1001
remaining_steps   : 8
```

## Project Structure

This is the main structure of the repository:

```text
.
|-- server/
|   |-- __init__.py
|   `-- app.py
|-- support_triage_env/
|   |-- __init__.py
|   |-- app.py
|   |-- env.py
|   |-- graders.py
|   |-- models.py
|   `-- tasks.py
|-- tests/
|   `-- test_env.py
|-- Dockerfile
|-- inference.py
|-- openenv.yaml
|-- preflight.ps1
|-- pyproject.toml
|-- README.md
|-- requirements-dev.txt
|-- requirements.txt
`-- uv.lock
```

Important files:

- `server/app.py` is the deployment-facing FastAPI entrypoint
- `support_triage_env/env.py` contains the main environment logic
- `support_triage_env/tasks.py` defines the tasks
- `support_triage_env/graders.py` contains the grading logic
- `support_triage_env/models.py` defines the Pydantic models
- `inference.py` runs the baseline inference loop
- `openenv.yaml` stores the environment metadata
- `preflight.ps1` runs local validation checks

## Environment Overview

This project simulates customer support ticket triage. The agent interacts through:

- `reset()` to start a task
- `step(action)` to perform an action
- `state()` to inspect the current internal state

### Tasks

The environment includes three deterministic tasks:

1. `duplicate_refund`
   Easy task about a duplicate billing charge and refund request.

2. `phishing_escalation`
   Medium task involving phishing detection and security escalation.

3. `enterprise_outage_credit`
   Hard task involving an enterprise outage, incident response, and SLA credit handling.

### Action Space

Supported action types:

- `set_priority`
- `assign_team`
- `add_tag`
- `draft_reply`
- `resolve_ticket`
- `request_clarification`

Valid priorities:

- `low`
- `medium`
- `high`
- `urgent`

Valid teams:

- `billing`
- `security`
- `incident_response`
- `technical_support`

### Observation Space

Each observation includes:

- task id
- difficulty
- objective
- ticket id
- customer tier
- customer message
- current priority
- assigned team
- tags
- drafted reply
- resolution status
- remaining steps
- last action error
- action history
- hints

## Running the Tests

This project includes both environment-level testing and end-to-end validation checks.

### Break down into end to end tests

These tests confirm that the environment, validator-facing packaging, and Docker setup are working together properly.

Run the full local preflight:

```powershell
.\preflight.ps1
```

This script checks:

- unit test execution
- OpenEnv validation
- Docker availability
- Docker image build success

Expected successful ending:

```text
1 passed
[OK] Meta-hackathon: Ready for multi-mode deployment
Successfully tagged support-inbox-triage:latest
Preflight complete.
```

### And coding style tests

There is currently a focused unit test for the environment logic rather than a full style-lint setup. The main automated code check ensures the easy task can be solved end to end and graded correctly.

Run the unit test manually:

```powershell
python -m pytest tests\test_env.py
```

Expected result:

```text
1 passed
```

## Running Inference

The root-level `inference.py` script is the baseline runner required by the task.

It:

- uses the OpenAI Python client
- reads `API_BASE_URL`
- reads `MODEL_NAME`
- reads `HF_TOKEN`
- also accepts `OPENAI_API_KEY`
- emits logs in the required `[START]`, `[STEP]`, and `[END]` format

### Reliable local fallback mode

This mode is useful if you want a stable demo without depending on external model access.

```powershell
$env:USE_SCRIPTED_BASELINE="true"
python inference.py
```

Expected behavior:

- all three tasks run
- each task prints `[START]`, multiple `[STEP]`, and `[END]`
- each task should end with `success=true`

Example:

```text
[START] task=duplicate_refund env=support_inbox_triage model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=set_priority("medium") reward=0.19 done=false error=null
...
[END] success=true steps=6 rewards=0.19,0.19,0.09,0.09,0.24,0.14
```

### Model-driven mode

This mode uses a real model endpoint and follows the brief more strictly.

```powershell
Remove-Item Env:USE_SCRIPTED_BASELINE -ErrorAction SilentlyContinue
$env:API_BASE_URL="https://router.huggingface.co/v1"
$env:MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
$env:HF_TOKEN="your-real-token"
python inference.py
```

If your credentials are correct, the script should run all three tasks and print the same structured log format.

## Deployment

This project is designed to be deployed as a Docker-based Hugging Face Space.

### Local Docker deployment

Build the image:

```powershell
docker build -t support-inbox-triage .
```

Run the container:

```powershell
docker run -p 7860:7860 support-inbox-triage
```

The API should then be available locally on port `7860`.

### Hugging Face Space deployment

To deploy this on a live system:

1. Create a new Hugging Face Space
2. Select `Docker` as the SDK
3. Upload or push this repository
4. Add the `openenv` tag
5. Set environment variables or secrets if needed:
   - `API_BASE_URL`
   - `MODEL_NAME`
   - `HF_TOKEN`
6. Deploy the Space
7. Verify that `POST /reset` responds with HTTP `200`

## Built With

* [FastAPI](https://fastapi.tiangolo.com/) - Web framework for serving the environment API
* [Pydantic](https://docs.pydantic.dev/) - Typed action, observation, reward, and state models
* [OpenAI Python Client](https://github.com/openai/openai-python) - Used for model-driven inference in `inference.py`
* [Docker](https://www.docker.com/) - Containerized deployment
* [OpenEnv Core](https://pypi.org/project/openenv-core/) - Validation and OpenEnv compatibility tooling

## Contributing

If you are extending the project:

- keep the environment deterministic unless intentionally changing benchmark behavior
- preserve the required `[START]`, `[STEP]`, and `[END]` output format in `inference.py`
- keep task grading reproducible
- rerun `.\preflight.ps1` before handing changes off

## Versioning

This project currently uses the version declared in `pyproject.toml` and `openenv.yaml`:

- `0.1.0`

## Authors

- **Aastha** - OpenEnv Round 1 hackathon submission author and project creator

## Acknowledgments

- The OpenEnv hackathon brief for defining the environment requirements
- Hugging Face and OpenEnv tooling for validation and deployment conventions
- The customer support operations domain as the basis for a realistic agent benchmark