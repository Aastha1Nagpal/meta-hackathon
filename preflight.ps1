$ErrorActionPreference = "Stop"

Write-Host "Installing dev dependencies..."
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw "Failed to install dev dependencies." }

if (-not (Test-Path "uv.lock")) { throw "Missing uv.lock." }

Write-Host "Running unit test..."
.\.venv\Scripts\python.exe -m pytest tests\test_env.py
if ($LASTEXITCODE -ne 0) { throw "Unit tests failed." }

if (-not (Test-Path ".openenv-venv")) {
    Write-Host "Creating isolated OpenEnv validation environment..."
    python -m venv .openenv-venv
    if ($LASTEXITCODE -ne 0) { throw "Failed to create .openenv-venv." }
}

Write-Host "Installing OpenEnv validator in isolated environment..."
.\.openenv-venv\Scripts\python.exe -m pip install "openenv-core[cli]>=0.2.1"
if ($LASTEXITCODE -ne 0) { throw "Failed to install openenv-core in .openenv-venv." }

Write-Host "Running OpenEnv validation..."
.\.openenv-venv\Scripts\openenv.exe validate
if ($LASTEXITCODE -ne 0) { throw "OpenEnv validation failed." }

Write-Host "Checking Docker..."
docker --version
if ($LASTEXITCODE -ne 0) { throw "Docker is not available." }

Write-Host "Building Docker image..."
$env:DOCKER_BUILDKIT = "0"
docker build -t support-inbox-triage .
$buildExit = $LASTEXITCODE
Remove-Item Env:DOCKER_BUILDKIT -ErrorAction SilentlyContinue
if ($buildExit -ne 0) { throw "Docker build failed." }

Write-Host "Preflight complete."
