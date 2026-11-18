param(
  [string]$Grep = ''
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$appDir = Join-Path $root 'pet-lumina-app'
$adminDir = Join-Path $root 'pet-lumina-web'
$agentDir = Join-Path $root 'backend-agent'
$py = Join-Path $agentDir '.venv\Scripts\python.exe'
if (-not (Test-Path $py)) { $py = 'python' }

$logDir = Join-Path $env:TEMP 'petlumina-e2e'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$procs = @()

function Start-Logged {
  param(
    [string]$Name,
    [string]$File,
    [string[]]$Arguments,
    [string]$WorkDir
  )
  $out = Join-Path $logDir "$Name.out.log"
  $err = Join-Path $logDir "$Name.err.log"
  $p = Start-Process -FilePath $File -ArgumentList $Arguments -WorkingDirectory $WorkDir `
    -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden -PassThru
  $script:procs += $p
  Write-Host "[e2e] $Name pid=$($p.Id) log=$out"
  return $p
}

function Wait-Port {
  param([int]$Port, [int]$TimeoutSec = 60)
  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  while ((Get-Date) -lt $deadline) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
      $client.Connect('127.0.0.1', $Port)
      return
    } catch {
      Start-Sleep -Milliseconds 400
    } finally {
      $client.Close()
    }
  }
  throw "port $Port not ready after ${TimeoutSec}s"
}

function Wait-Http {
  param([string]$Url, [int]$TimeoutSec = 60)
  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  while ((Get-Date) -lt $deadline) {
    try {
      $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
      if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) { return }
    } catch {
      Start-Sleep -Milliseconds 500
    }
  }
  throw "http $Url not ready after ${TimeoutSec}s"
}

$ports = @(8080, 8098, 8099, 5174, 3000)
$busy = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
  Where-Object { $ports -contains $_.LocalPort } |
  Select-Object LocalPort, OwningProcess
if ($busy) {
  $busy | Format-Table -AutoSize | Out-String | Write-Host
  throw '端口被占用；先清理残留进程再跑 e2e'
}

try {
  Write-Host '[e2e] starting stub_java :8080'
  Start-Logged -Name 'stub-java' -File $py -WorkDir $agentDir -Arguments @(
    '-u', '-m', 'uvicorn', '--app-dir', 'tests', 'stub_java:app',
    '--host', '0.0.0.0', '--port', '8080', '--log-level', 'warning'
  ) | Out-Null

  Write-Host '[e2e] starting stub_llm :8098'
  Start-Logged -Name 'stub-llm' -File $py -WorkDir $agentDir -Arguments @(
    '-u', '-m', 'uvicorn', '--app-dir', 'tests', 'stub_llm:app',
    '--host', '0.0.0.0', '--port', '8098', '--log-level', 'warning'
  ) | Out-Null

  $env:PET_AGENT_ENV = 'dev'
  $env:PET_AGENT_REPO_BACKEND = 'memory'
  $env:PET_AGENT_EVENT_BACKEND = 'memory'
  $env:PET_AGENT_AUTH_MODE = 'backend'
  $env:PET_AGENT_BACKEND_BASE_URL = 'http://127.0.0.1:8080/api/v1'
  $env:PET_AGENT_LLM_BASE_URL = 'http://127.0.0.1:8098/v1'
  $env:PET_AGENT_LLM_API_KEY = 'stub-key'
  $env:PET_AGENT_LLM_MODEL = 'stub'
  $env:PET_AGENT_RATE_LIMIT_ENABLED = 'true'
  $env:PET_AGENT_RATE_LIMIT_PER_MINUTE = '1'
  $env:PET_AGENT_RATE_LIMIT_PER_DAY = '1000'
  $env:PET_AGENT_LOG_LEVEL = 'WARNING'
  Write-Host '[e2e] starting agent :8099'
  Start-Logged -Name 'agent' -File $py -WorkDir $agentDir -Arguments @(
    '-u', '-m', 'uvicorn', 'app.main:app',
    '--host', '0.0.0.0', '--port', '8099', '--log-level', 'warning'
  ) | Out-Null

  $env:VITE_API_BASE_URL = 'http://127.0.0.1:8080/api/v1'
  $env:VITE_AGENT_BASE_URL = 'http://127.0.0.1:8099'
  Write-Host '[e2e] starting app vite :5174'
  Start-Logged -Name 'app' -File 'cmd.exe' -WorkDir $appDir -Arguments @(
    '/c', 'npx', '--no-install', 'vite', '--host', '127.0.0.1', '--port', '5174', '--strictPort'
  ) | Out-Null

  $env:NODE_OPTIONS = '--dns-result-order=ipv4first'
  Write-Host '[e2e] starting admin vite :3000'
  Start-Logged -Name 'admin' -File 'cmd.exe' -WorkDir $adminDir -Arguments @(
    '/c', 'npx', '--no-install', 'vite', '--host', '127.0.0.1', '--port', '3000', '--strictPort'
  ) | Out-Null

  Wait-Port -Port 8080
  Wait-Port -Port 8098
  Wait-Http -Url 'http://127.0.0.1:8099/healthz'
  Wait-Port -Port 5174
  Wait-Port -Port 3000
  Write-Host '[e2e] all services up'

  $testArgs = @('/c', 'npx', '--no-install', 'playwright', 'test')
  if ($Grep) { $testArgs += $Grep }
  $test = Start-Process -FilePath 'cmd.exe' -ArgumentList $testArgs -WorkingDirectory $appDir `
    -NoNewWindow -Wait -PassThru
  $code = $test.ExitCode
  Write-Host "[e2e] playwright exit=$code"
  exit $code
}
catch {
  Write-Host "[e2e] FAILED: $($_.Exception.Message)"
  Write-Host "[e2e] logs: $logDir"
  exit 1
}
finally {
  $ErrorActionPreference = 'Continue'
  foreach ($p in $procs) {
    if ($p) {
      & taskkill.exe /F /T /PID $p.Id 2>&1 | Out-Null
    }
  }
  Start-Sleep -Milliseconds 500

  # taskkill /T 在父进程先退出时可能漏掉孙进程；按端口兜底清理本轮自己占的端口。
  $listeners = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $ports -contains $_.LocalPort }
  foreach ($l in $listeners) {
    & taskkill.exe /F /T /PID $l.OwningProcess 2>&1 | Out-Null
  }
}
