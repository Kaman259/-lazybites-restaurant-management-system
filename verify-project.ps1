param(
    [switch]$SkipInstall,
    [switch]$SkipFrontend
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$BackendPath = Join-Path $ProjectRoot "backend"
$FrontendPath = Join-Path $ProjectRoot "frontend"
$VenvPython = Join-Path $BackendPath "venv\Scripts\python.exe"

$PassedChecks = 0
$Warnings = 0
$FailedChecks = 0

$FailureMessages = [System.Collections.Generic.List[string]]::new()

function Write-Section {
    param([string]$Title)

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor DarkCyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor DarkCyan
}

function Write-Pass {
    param([string]$Message)

    $script:PassedChecks++
    Write-Host "[PASS] $Message" -ForegroundColor Green
}

function Write-WarningMessage {
    param([string]$Message)

    $script:Warnings++
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Failure {
    param([string]$Message)

    $script:FailedChecks++
    $script:FailureMessages.Add($Message)
    Write-Host "[FAIL] $Message" -ForegroundColor Red
}

function Test-RequiredPath {
    param(
        [string]$RelativePath,
        [string]$Description
    )

    $FullPath = Join-Path $ProjectRoot $RelativePath

    if (Test-Path $FullPath) {
        Write-Pass "$Description exists."
        return $true
    }

    Write-Failure "$Description is missing: $RelativePath"
    return $false
}

function Invoke-CheckedCommand {
    param(
        [string]$Description,
        [scriptblock]$Command
    )

    try {
        & $Command

        if ($LASTEXITCODE -ne 0) {
            throw "Command returned exit code $LASTEXITCODE."
        }

        Write-Pass $Description
        return $true
    }
    catch {
        Write-Failure "$Description $($_.Exception.Message)"
        return $false
    }
}

Write-Host ""
Write-Host "LazyBites Project Verification" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"
Write-Host "Started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

Write-Section "1. Required project files"

$RequiredPaths = @(
    @{ Path = "README.md"; Description = "README" },
    @{ Path = ".gitignore"; Description = "Git ignore file" },
    @{ Path = "backend"; Description = "Backend folder" },
    @{ Path = "backend\.env"; Description = "Backend environment file" },
    @{ Path = "backend\.env.example"; Description = "Backend environment example" },
    @{ Path = "backend\requirements.txt"; Description = "Backend requirements" },
    @{ Path = "backend\alembic.ini"; Description = "Alembic configuration" },
    @{ Path = "backend\app\main.py"; Description = "FastAPI application" },
    @{ Path = "backend\create_admin.py"; Description = "Admin creation script" },
    @{ Path = "backend\create_staff.py"; Description = "Staff creation script" },
    @{ Path = "backend\migrations\versions\20260721_0001_initial_schema.py"; Description = "Initial database migration" },
    @{ Path = "backend\tests"; Description = "Backend tests folder" },
    @{ Path = "frontend"; Description = "Frontend folder" },
    @{ Path = "frontend\.env"; Description = "Frontend environment file" },
    @{ Path = "frontend\.env.example"; Description = "Frontend environment example" },
    @{ Path = "frontend\package.json"; Description = "Frontend package file" },
    @{ Path = "frontend\src\main.jsx"; Description = "React entry file" }
)

foreach ($RequiredPath in $RequiredPaths) {
    Test-RequiredPath `
        -RelativePath $RequiredPath.Path `
        -Description $RequiredPath.Description | Out-Null
}

Write-Section "2. Backend model files"

$ModelFiles = @(
    "backend\app\models\user.py",
    "backend\app\models\restaurant_settings.py",
    "backend\app\models\dining_table.py",
    "backend\app\models\customer.py",
    "backend\app\models\reservation.py",
    "backend\app\models\menu_category.py",
    "backend\app\models\menu_item.py",
    "backend\app\models\order.py",
    "backend\app\models\order_item.py",
    "backend\app\models\invoice.py"
)

foreach ($ModelFile in $ModelFiles) {
    Test-RequiredPath `
        -RelativePath $ModelFile `
        -Description "Model file $ModelFile" | Out-Null
}

Write-Section "3. Backend virtual environment"

if (-not (Test-Path $VenvPython)) {
    Write-Failure "Backend virtual environment is missing."

    Write-Host ""
    Write-Host "Create it with:" -ForegroundColor Yellow
    Write-Host "cd backend"
    Write-Host "python -m venv venv"

    Write-Section "Verification stopped"
    exit 1
}

Write-Pass "Backend virtual environment exists."

try {
    $PythonVersion = & $VenvPython --version 2>&1
    Write-Pass "Virtual environment Python works: $PythonVersion"
}
catch {
    Write-Failure "Virtual environment Python could not run."
}

Write-Section "4. Backend dependencies"

Push-Location $BackendPath

try {
    if (-not $SkipInstall) {
        Invoke-CheckedCommand `
            -Description "Backend dependencies installed." `
            -Command {
                & $VenvPython -m pip install -r requirements.txt
            } | Out-Null
    }
    else {
        Write-WarningMessage "Backend dependency installation skipped."
    }

    Invoke-CheckedCommand `
        -Description "Python dependency check passed." `
        -Command {
            & $VenvPython -m pip check
        } | Out-Null

    $ImportCheck = @"
from zoneinfo import ZoneInfo

import alembic
import fastapi
import firebase_admin
import httpx
import multipart
import pydantic
import pydantic_settings
import pytest
import sqlalchemy

print("Timezone:", ZoneInfo("Asia/Kolkata"))
print("Backend dependencies imported successfully.")
"@

    Invoke-CheckedCommand `
        -Description "Required backend packages and timezone data work." `
        -Command {
            $ImportCheck | & $VenvPython -
        } | Out-Null
}
finally {
    Pop-Location
}

Write-Section "5. Firebase credentials"

$FirebaseCredentials = Join-Path $BackendPath "firebase-service-account.json"

if (Test-Path $FirebaseCredentials) {
    Write-Pass "Firebase service-account file exists."
}
else {
    Write-Failure "Firebase service-account file is missing."
}

Write-Section "6. Python syntax and application import"

Push-Location $BackendPath

try {
    Invoke-CheckedCommand `
        -Description "Backend Python files pass syntax compilation." `
        -Command {
            & $VenvPython -m compileall -q app migrations tests
        } | Out-Null

    $ApplicationImportCheck = @"
from app.main import app as fastapi_app
from app.database.base import Base

import app.models

expected_tables = {
    "users",
    "restaurant_settings",
    "dining_tables",
    "customers",
    "reservations",
    "menu_categories",
    "menu_items",
    "orders",
    "order_items",
    "invoices",
}

actual_tables = set(Base.metadata.tables.keys())
missing_tables = expected_tables - actual_tables

print("FastAPI title:", fastapi_app.title)
print("Registered tables:", sorted(actual_tables))

if missing_tables:
    raise SystemExit(
        "Missing SQLAlchemy tables: " +
        ", ".join(sorted(missing_tables))
    )
"@

    Invoke-CheckedCommand `
        -Description "FastAPI application and all ten models import correctly." `
        -Command {
            $ApplicationImportCheck | & $VenvPython -
        } | Out-Null
}
finally {
    Pop-Location
}

Write-Section "7. Database migration"

Push-Location $BackendPath

try {
    Invoke-CheckedCommand `
        -Description "Alembic history loads." `
        -Command {
            & $VenvPython -m alembic history
        } | Out-Null

    Invoke-CheckedCommand `
        -Description "Database upgraded to the latest migration." `
        -Command {
            & $VenvPython -m alembic upgrade head
        } | Out-Null

    $RevisionCheck = @"
from sqlalchemy import text
from app.database.session import engine

with engine.connect() as connection:
    revision = connection.execute(
        text("SELECT version_num FROM alembic_version")
    ).scalar_one()

print(revision)

if revision != "20260721_0001":
    raise SystemExit(
        f"Expected 20260721_0001 but found {revision}"
    )
"@

    Invoke-CheckedCommand `
        -Description "Database uses migration 20260721_0001." `
        -Command {
            $RevisionCheck | & $VenvPython -
        } | Out-Null
}
finally {
    Pop-Location
}

Write-Section "8. Backend test suite"

Push-Location $BackendPath

try {
    Invoke-CheckedCommand `
        -Description "All backend tests pass." `
        -Command {
            & $VenvPython -m pytest tests -v
        } | Out-Null
}
finally {
    Pop-Location
}

Write-Section "9. FastAPI runtime"

$ApiPort = 8010
$ApiBaseUrl = "http://127.0.0.1:$ApiPort"
$UvicornProcess = $null

$OutputLog = Join-Path $BackendPath "verification-uvicorn-output.log"
$ErrorLog = Join-Path $BackendPath "verification-uvicorn-error.log"

Remove-Item $OutputLog -Force -ErrorAction SilentlyContinue
Remove-Item $ErrorLog -Force -ErrorAction SilentlyContinue

try {
    $UvicornProcess = Start-Process `
        -FilePath $VenvPython `
        -ArgumentList @(
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            $ApiPort
        ) `
        -WorkingDirectory $BackendPath `
        -RedirectStandardOutput $OutputLog `
        -RedirectStandardError $ErrorLog `
        -PassThru `
        -WindowStyle Hidden

    $ServerReady = $false

    for ($Attempt = 1; $Attempt -le 20; $Attempt++) {
        Start-Sleep -Milliseconds 500

        if ($UvicornProcess.HasExited) {
            break
        }

        try {
            $HealthResponse = Invoke-RestMethod `
                -Uri "$ApiBaseUrl/health" `
                -Method Get `
                -TimeoutSec 2

            if ($HealthResponse.success -eq $true) {
                $ServerReady = $true
                break
            }
        }
        catch {
        }
    }

    if (-not $ServerReady) {
        $ErrorText = ""

        if (Test-Path $ErrorLog) {
            $ErrorText = Get-Content $ErrorLog -Raw
        }

        throw "FastAPI did not become ready. $ErrorText"
    }

    Write-Pass "FastAPI starts successfully."

    $SwaggerResponse = Invoke-WebRequest `
        -Uri "$ApiBaseUrl/docs" `
        -Method Get `
        -TimeoutSec 5 `
        -UseBasicParsing

    if ($SwaggerResponse.StatusCode -eq 200) {
        Write-Pass "Swagger documentation opens."
    }
    else {
        Write-Failure "Swagger documentation returned an unexpected status."
    }
}
catch {
    Write-Failure "FastAPI runtime test failed. $($_.Exception.Message)"
}
finally {
    if (
        $null -ne $UvicornProcess -and
        -not $UvicornProcess.HasExited
    ) {
        Stop-Process `
            -Id $UvicornProcess.Id `
            -Force `
            -ErrorAction SilentlyContinue

        $UvicornProcess.WaitForExit()
    }

    Remove-Item $OutputLog -Force -ErrorAction SilentlyContinue
    Remove-Item $ErrorLog -Force -ErrorAction SilentlyContinue
}

Write-Section "10. Frontend verification"

if ($SkipFrontend) {
    Write-WarningMessage "Frontend verification skipped."
}
elseif (-not (Test-Path $FrontendPath)) {
    Write-Failure "Frontend folder is missing."
}
else {
    try {
        $NodeVersion = & node --version 2>&1

        if ($LASTEXITCODE -ne 0) {
            throw "Node.js returned exit code $LASTEXITCODE."
        }

        Write-Pass "Node.js works: $NodeVersion"
    }
    catch {
        Write-Failure "Node.js is unavailable."
    }

    try {
        $NpmVersion = & npm --version 2>&1

        if ($LASTEXITCODE -ne 0) {
            throw "npm returned exit code $LASTEXITCODE."
        }

        Write-Pass "npm works: $NpmVersion"
    }
    catch {
        Write-Failure "npm is unavailable."
    }

    Push-Location $FrontendPath

    try {
        if (-not $SkipInstall) {
            Invoke-CheckedCommand `
                -Description "Frontend dependencies installed." `
                -Command {
                    & npm install
                } | Out-Null
        }
        else {
            Write-WarningMessage "Frontend dependency installation skipped."
        }

        Invoke-CheckedCommand `
            -Description "Frontend lint check passed." `
            -Command {
                & npm run lint
            } | Out-Null

        Invoke-CheckedCommand `
            -Description "Frontend production build passed." `
            -Command {
                & npm run build
            } | Out-Null
    }
    finally {
        Pop-Location
    }
}

Write-Section "11. Git safety"

if (Test-Path (Join-Path $ProjectRoot ".git")) {
    Write-Pass "Git repository is initialized."

    Push-Location $ProjectRoot

    try {
        $TrackedPrivateFiles = & git ls-files 2>$null |
            Where-Object {
                $_ -match "(^|/)\.env$" -or
                $_ -match "service-account.*\.json$" -or
                $_ -match "\.(db|sqlite|sqlite3)$"
            }

        if ($TrackedPrivateFiles) {
            Write-Failure (
                "Private files are tracked by Git: " +
                ($TrackedPrivateFiles -join ", ")
            )
        }
        else {
            Write-Pass "No environment file, Firebase key, or local database is tracked."
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-WarningMessage "Git repository is not initialized."
}

Write-Section "Final result"

Write-Host "Passed:   $PassedChecks" -ForegroundColor Green
Write-Host "Warnings: $Warnings" -ForegroundColor Yellow
Write-Host "Failed:   $FailedChecks" -ForegroundColor Red

if ($FailedChecks -gt 0) {
    Write-Host ""
    Write-Host "Problems to fix:" -ForegroundColor Red

    foreach ($FailureMessage in $FailureMessages) {
        Write-Host "  * $FailureMessage" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "Verification failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "LazyBites backend tests and frontend checks passed." -ForegroundColor Green
Write-Host "The application is ready for full manual workflow testing." -ForegroundColor Green
exit 0