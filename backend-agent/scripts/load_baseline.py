"""单实例容量基线（BACKLOG C7）：分级并发压 SSE，量首 token / 错误率 / 峰值内存。

前置：无。脚本自己起两个子进程，跑完自己收尸：

    uvicorn tests.stub_llm:app   （桩模型，首 token 延迟可配，仿真真实模型节奏）
    uvicorn app.main:app         （被测服务，每个并发档重启一次，内存峰值可归因）

跑：

    .venv\\Scripts\\python -m scripts.load_baseline
    .venv\\Scripts\\python -m scripts.load_baseline --levels 1,5,10,20 --requests 40
    .venv\\Scripts\\python -m scripts.load_baseline --json-out .tmp-load.json

量什么（每一档一行）：
- **首 token**：第一个 `event: delta` 到达的毫秒数（`route` 事件在模型调用前就发了，量它没意义）；
- **全程**：从发出请求到收到 `event: done`；
- **错误率**：非 200、连接异常、流里出现 `event: error`、没有 `done` 收尾都算失败；
- **峰值工作集**：被测进程的 `PeakWorkingSetSize`（Windows `psapi` / Linux `VmHWM`），起一个、压完再读一个；
- **对账**：`/metrics` 前后差里的 `pet_agent_runs_total` 与 `pet_agent_http_requests_total`。

口径与取舍见 `docs/plans/s1.29-capacity-baseline.md`；核心前提是**桩不是真模型**，
所以结论只覆盖「Agent 服务自身的调度/内存上限」，不代表真实模型的并发表现。
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import math
import os
import socket
import subprocess
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parent.parent  # backend-agent/
CHAT_PATH = "/agent/chat"
HEALTH_PATH = "/healthz"
METRICS_PATH = "/metrics"
RUNS_METRIC = "pet_agent_runs_total"
HTTP_METRIC = "pet_agent_http_requests_total"

DEFAULT_LEVELS = (1, 5, 10, 20)
DEFAULT_REQUESTS = 40
DEFAULT_FIRST_TOKEN_MS = 900.0  # 对齐 docs/spec/agent-runtime-api.md 里模型首 token 的实测 P50
DEFAULT_CHUNK_GAP_MS = 20.0
DEFAULT_CHUNK_CHARS = 4
DEFAULT_MAX_P95_MS = 3000.0
DEFAULT_MAX_ERROR_RATE = 0.01


# ---------------------------------------------------------------- 纯函数（可单测）
def percentile(values: Sequence[float], q: float) -> float:
    """线性插值百分位，口径与 numpy 默认一致（不引 numpy）。

    空样本返回 0；单样本恒等于它自己；q<=0 取最小、q>=1 取最大。
    """
    if not values:
        return 0.0
    ordered = sorted(float(v) for v in values)
    if q <= 0:
        return ordered[0]
    if q >= 1:
        return ordered[-1]
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def stats(values: Sequence[float]) -> dict[str, float]:
    """样本数与 P50/P95/P99/max。"""
    return {
        "n": float(len(values)),
        "p50": percentile(values, 0.5),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
        "max": percentile(values, 1.0),
    }


def judge(*, error_rate: float, p95_ms: float, max_error_rate: float, max_p95_ms: float) -> str:
    """判定这一档是否还在单实例上限内。只影响报告，不影响退出码。"""
    reasons: list[str] = []
    if error_rate > max_error_rate:
        reasons.append(f"错误率 {error_rate:.1%} > {max_error_rate:.1%}")
    if p95_ms > max_p95_ms:
        reasons.append(f"首 token P95 {p95_ms:.0f}ms > {max_p95_ms:.0f}ms")
    return "达标" if not reasons else "超上限：" + "；".join(reasons)


def parse_metrics(text: str) -> dict[str, float]:
    """Prometheus 文本 → {`name{labels}`: value}；注释与坏行跳过。"""
    parsed: dict[str, float] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        head, _, raw = line.rpartition(" ")
        if not head or not raw:
            continue
        try:
            parsed[head] = float(raw)
        except ValueError:
            continue
    return parsed


def counter_delta(
    before: dict[str, float], after: dict[str, float], prefix: str, *, contains: str = ""
) -> float:
    """按前缀（可再要求标签片段）汇总增量。新序列按全量算，消失的序列忽略。"""
    return sum(
        value - before.get(key, 0.0)
        for key, value in after.items()
        if key.startswith(prefix) and contains in key
    )


# ---------------------------------------------------------------- 进程与资源
@dataclass
class Service:
    """一个 uvicorn 子进程：日志落 log_dir（默认 %TEMP%），退出时收尸。"""

    name: str
    module: str
    port: int
    env: dict[str, str]
    log_dir: Path
    proc: subprocess.Popen[bytes] = field(init=False)
    log_path: Path = field(init=False)
    _handle: Any = field(init=False, default=None)

    def __post_init__(self) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.log_dir / f"petlumina-load-{self.name}-{self.port}.log"
        self._handle = self.log_path.open("wb")
        self.proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                self.module,
                "--host",
                "127.0.0.1",
                "--port",
                str(self.port),
                "--log-level",
                "warning",
                "--no-access-log",
            ],
            cwd=str(ROOT),
            env=self.env,
            stdout=self._handle,
            stderr=subprocess.STDOUT,
        )

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def stop(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                with contextlib.suppress(subprocess.TimeoutExpired):
                    self.proc.wait(timeout=10)
        if self._handle is not None:
            self._handle.close()
            self._handle = None

    def tail(self, lines: int = 20) -> str:
        try:
            text = self.log_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        return "\n".join(text.splitlines()[-lines:])


def free_port() -> int:
    """要一个当下空闲的本地端口（起服务前临时占用再放开）。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _peak_working_set_windows(pid: int) -> float:
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(Counters),
        wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

    counters = Counters()
    counters.cb = ctypes.sizeof(Counters)
    # PROCESS_QUERY_LIMITED_INFORMATION：只读统计信息，够用且权限最小
    handle = kernel32.OpenProcess(0x1000, False, pid)
    if not handle:
        raise OSError(f"OpenProcess 失败（pid={pid}）")
    try:
        if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            raise OSError(f"GetProcessMemoryInfo 失败（pid={pid}）")
    finally:
        kernel32.CloseHandle(handle)
    return counters.PeakWorkingSetSize / (1024 * 1024)


def _child_pids_windows(pid: int) -> list[int]:
    """Toolhelp 快照里找直接子进程（venv 的 python.exe 是瘦启动器，真进程是它的子进程）。"""
    import ctypes
    from ctypes import wintypes

    class Entry(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    snapshot = kernel32.CreateToolhelp32Snapshot(0x2, 0)  # TH32CS_SNAPPROCESS
    if not snapshot or snapshot == ctypes.c_void_p(-1).value:
        return []
    children: list[int] = []
    entry = Entry()
    entry.dwSize = ctypes.sizeof(Entry)
    try:
        alive = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while alive:
            if entry.th32ParentProcessID == pid:
                children.append(int(entry.th32ProcessID))
            alive = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    return children


def _child_pids_proc(pid: int) -> list[int]:
    children: list[int] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / "stat").read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # comm 里可能带空格/括号，切掉最后一个 ')' 后再按列取 state/ppid
        fields = raw.rpartition(")")[2].split()
        if len(fields) > 1 and fields[1] == str(pid):
            children.append(int(entry.name))
    return children


def _peak_working_set_proc(pid: int) -> float:
    try:
        text = Path(f"/proc/{pid}/status").read_text(encoding="utf-8")
    except OSError:
        return 0.0
    for line in text.splitlines():
        if line.startswith("VmHWM:"):
            return int(line.split()[1]) / 1024
    return 0.0


def peak_working_set_mb(pid: int) -> float:
    """某进程至今的峰值工作集（MB）。读不到就返回 0，不让统计拖垮压测。"""
    try:
        if sys.platform == "win32":
            return _peak_working_set_windows(pid)
        return _peak_working_set_proc(pid)
    except OSError:
        return 0.0


def process_tree_peak_mb(pid: int, depth: int = 0) -> float:
    """进程树里的峰值工作集最大值。

    单独量 `Popen.pid` 会量到错的对象：本机 venv 的 `python.exe` 只是个几 MB 的启动器，
    真正跑 uvicorn 的是它 fork 出来的子进程。取整棵树的最大值才不会被启动器骗到。
    """
    peak = peak_working_set_mb(pid)
    if depth >= 3:
        return peak
    children = _child_pids_windows(pid) if sys.platform == "win32" else _child_pids_proc(pid)
    for child in children:
        peak = max(peak, process_tree_peak_mb(child, depth + 1))
    return peak


# ---------------------------------------------------------------- 压测
@dataclass
class Sample:
    ok: bool
    first_token_ms: float | None
    total_ms: float
    status: int
    error: str = ""


@dataclass
class LevelResult:
    level: int
    total: int
    ok: int
    first_token: dict[str, float]
    total_ms: dict[str, float]
    peak_startup_mb: float
    peak_after_mb: float
    runs_ok: float
    runs_failed: float
    http_chat: float
    verdict: str

    @property
    def error_rate(self) -> float:
        return 0.0 if self.total == 0 else (self.total - self.ok) / self.total

    def as_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "total": self.total,
            "ok": self.ok,
            "error_rate": round(self.error_rate, 4),
            "first_token": {k: round(v, 1) for k, v in self.first_token.items()},
            "total_ms": {k: round(v, 1) for k, v in self.total_ms.items()},
            "peak_startup_mb": round(self.peak_startup_mb, 1),
            "peak_after_mb": round(self.peak_after_mb, 1),
            "runs_ok": self.runs_ok,
            "runs_failed": self.runs_failed,
            "http_chat": self.http_chat,
            "verdict": self.verdict,
        }


async def wait_ready(base_url: str, *, timeout_s: float, path: str = HEALTH_PATH) -> dict[str, Any]:
    """等子进程开始答 HTTP。

    - 被测服务走 `/healthz`，要求 200 且 `status=ok`；
    - 桩模型（`tests.stub_llm:app`）没有健康接口，用 FastAPI 自带的 `/docs` 探活。
    """
    expect_health = path == HEALTH_PATH
    deadline = time.monotonic() + timeout_s
    last = "还没连上"
    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
        while time.monotonic() < deadline:
            try:
                resp = await client.get(base_url + path)
                if resp.status_code != 200:
                    last = f"HTTP {resp.status_code}"
                elif not expect_health:
                    return {}
                elif resp.json().get("status") == "ok":
                    return dict(resp.json())
                else:
                    last = f"healthz 不是 ok：{resp.text[:120]}"
            except Exception as exc:  # 起进程期间连接被拒是正常的
                last = f"{type(exc).__name__}: {exc}"
            await asyncio.sleep(0.1)
    raise RuntimeError(f"{base_url}{path} 在 {timeout_s:.0f}s 内没就绪（最后一次：{last}）")


async def fetch_metrics(base_url: str) -> dict[str, float]:
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        resp = await client.get(base_url + METRICS_PATH)
        resp.raise_for_status()
        return parse_metrics(resp.text)


async def one_request(client: httpx.AsyncClient, *, level: int, index: int) -> Sample:
    """发一次 L1 闲聊，量首 token 与全程。`done` 收尾且无 `error` 才算成功。"""
    headers = {
        "Authorization": f"Bearer stub-{level}-{index}",
        "X-User-Id": f"load{level}-{index}",
    }
    payload = {"message": "你好", "channel": "app"}
    started = time.perf_counter()
    first_token: float | None = None
    done = False
    stream_error = ""
    status = 0
    current = ""
    try:
        async with client.stream("POST", CHAT_PATH, json=payload, headers=headers) as resp:
            status = resp.status_code
            if status != 200:
                await resp.aread()
                return Sample(False, None, (time.perf_counter() - started) * 1000, status, f"HTTP {status}")
            async for line in resp.aiter_lines():
                if line.startswith("event:"):
                    current = line[6:].strip()
                elif line.startswith("data:"):
                    if current == "delta" and first_token is None:
                        first_token = (time.perf_counter() - started) * 1000
                    elif current == "done":
                        done = True
                    elif current == "error":
                        stream_error = line[5:].strip()[:200]
    except Exception as exc:
        return Sample(
            False, first_token, (time.perf_counter() - started) * 1000, status, f"{type(exc).__name__}: {exc}"
        )

    total_ms = (time.perf_counter() - started) * 1000
    if not done:
        return Sample(False, first_token, total_ms, status, stream_error or "流里没有 done 事件")
    return Sample(True, first_token, total_ms, status)


async def run_level(*, level: int, requests: int, base_url: str) -> list[Sample]:
    """一档并发：`level` 路同时压 `requests` 个请求（先热身一次，不计入结果）。"""
    limits = httpx.Limits(max_connections=requests + 8, max_keepalive_connections=requests + 8)
    timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=120.0)
    semaphore = asyncio.Semaphore(level)
    async with httpx.AsyncClient(base_url=base_url, limits=limits, timeout=timeout) as client:
        # 热身：把 keep-alive 建起来，别让第一个请求替后面所有人付握手钱
        await one_request(client, level=level, index=-1)

        async def worker(index: int) -> Sample:
            async with semaphore:
                return await one_request(client, level=level, index=index)

        return list(await asyncio.gather(*(worker(i) for i in range(requests))))


# ---------------------------------------------------------------- 编排与输出
def app_env(*, llm_port: int) -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "PET_AGENT_ENV": "test",
            "PET_AGENT_AUTH_MODE": "header",
            "PET_AGENT_REPO_BACKEND": "memory",
            "PET_AGENT_LLM_API_KEY": "stub-key",
            "PET_AGENT_LLM_BASE_URL": f"http://127.0.0.1:{llm_port}/v1",
            "PET_AGENT_LLM_MODEL": "stub",
            "PET_AGENT_LLM_MAX_RETRIES": "0",
            "PET_AGENT_RATE_LIMIT_ENABLED": "false",
            "PET_AGENT_RUN_SWEEP_INTERVAL_S": "0",
            "PET_AGENT_LOG_LEVEL": "WARNING",
        }
    )
    return env


def stub_env(*, first_token_ms: float, chunk_gap_ms: float, chunk_chars: int) -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "STUB_LLM_FIRST_TOKEN_MS": f"{first_token_ms:g}",
            "STUB_LLM_CHUNK_GAP_MS": f"{chunk_gap_ms:g}",
            "STUB_LLM_CHUNK_CHARS": str(chunk_chars),
        }
    )
    return env


def summarize_level(
    *,
    level: int,
    samples: Sequence[Sample],
    peak_startup_mb: float,
    peak_after_mb: float,
    before: dict[str, float],
    after: dict[str, float],
    max_error_rate: float,
    max_p95_ms: float,
) -> LevelResult:
    ok_samples = [s for s in samples if s.ok]
    tokens = [s.first_token_ms for s in ok_samples if s.first_token_ms is not None]
    token_stats = stats(tokens)
    total_stats = stats([s.total_ms for s in ok_samples])
    error_rate = 0.0 if not samples else (len(samples) - len(ok_samples)) / len(samples)
    return LevelResult(
        level=level,
        total=len(samples),
        ok=len(ok_samples),
        first_token=token_stats,
        total_ms=total_stats,
        peak_startup_mb=peak_startup_mb,
        peak_after_mb=peak_after_mb,
        runs_ok=counter_delta(before, after, RUNS_METRIC, contains='status="succeeded"'),
        runs_failed=counter_delta(before, after, RUNS_METRIC, contains='status="failed"'),
        http_chat=counter_delta(before, after, HTTP_METRIC, contains='path="/agent/chat"'),
        verdict=judge(
            error_rate=error_rate,
            p95_ms=token_stats["p95"],
            max_error_rate=max_error_rate,
            max_p95_ms=max_p95_ms,
        ),
    )


def render_markdown(results: Sequence[LevelResult], args: argparse.Namespace) -> str:
    lines = [
        f"桩模型首 token 延迟 {args.first_token_ms:g}ms / 帧间隔 {args.chunk_gap_ms:g}ms / "
        f"每档 {args.requests} 个请求 / 判定阈值：错误率 ≤ {args.max_error_rate:.0%}、"
        f"首 token P95 ≤ {args.max_p95_ms:.0f}ms",
        "",
        "| 并发 | 请求 | 成功 | 首token P50 | P95 | P99 | 全程 P95 | 峰值(MB) | 起/增(MB) "
        "| metrics runs ok/fail | 判定 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        rise = r.peak_after_mb - r.peak_startup_mb
        lines.append(
            f"| {r.level} | {r.total} | {r.ok} | {r.first_token['p50']:.0f}ms | "
            f"{r.first_token['p95']:.0f}ms | {r.first_token['p99']:.0f}ms | {r.total_ms['p95']:.0f}ms | "
            f"{r.peak_after_mb:.0f} | {r.peak_startup_mb:.0f} / {rise:+.0f} | "
            f"{r.runs_ok:.0f}/{r.runs_failed:.0f} | {r.verdict} |"
        )
    return "\n".join(lines)


def render_conclusion(results: Sequence[LevelResult], args: argparse.Namespace) -> str:
    if not results:
        return "## 结论\n\n没有跑出任何一档数据。"
    over = [r for r in results if r.verdict != "达标"]
    top = max(results, key=lambda r: r.level)
    lines = ["## 结论", ""]
    if over:
        first_over = over[0].level
        lower = [r for r in results if r.level < first_over and r.verdict == "达标"]
        higher = [r for r in results if r.level > first_over and r.verdict == "达标"]
        if higher:
            # 高档位又达标说明不是单调拐点：多半是机器抖动/噪声，不能当成上限写进报告。
            lines.append(
                f"- 上限：**{first_over} 并发超上限**（{over[0].verdict}），但更高档 "
                f"{max(r.level for r in higher)} 又达标——结果非单调，疑似抖动，需复测该档。"
            )
        else:
            previous = max((r.level for r in lower), default=None)
            lines.append(
                f"- 上限：**{first_over} 并发开始超上限**（{over[0].verdict}）；"
                f"上一档 {previous if previous is not None else '无'} 并发达标。"
            )
    else:
        lines.append(f"- 上限：扫到的最高档 {top.level} 并发仍达标，单实例上限未被触到。")
    overhead = top.first_token["p50"] - args.first_token_ms
    lines.append(
        f"- 服务侧额外开销（首 token P50 − 桩延迟）：{overhead:+.0f}ms @ {top.level} 并发；"
        f"全程 P95 {top.total_ms['p95']:.0f}ms。"
    )
    lines.append(
        f"- 峰值工作集：{top.peak_after_mb:.0f}MB（含启动 {top.peak_startup_mb:.0f}MB，"
        f"压测增量 {top.peak_after_mb - top.peak_startup_mb:+.0f}MB）@ {top.level} 并发。"
    )
    if top.http_chat and top.runs_ok:
        expected = top.total + 1  # 计时请求 + 1 次热身，热身也是真请求
        same = top.http_chat == expected and top.runs_ok == expected and top.runs_failed == 0
        lines.append(
            f"- 对账：/agent/chat 计数 +{top.http_chat:.0f}、runs 成功 +{top.runs_ok:.0f}/"
            f"失败 +{top.runs_failed:.0f}；期望 {expected}（{top.total} 计时 + 1 热身）→ "
            f"{'一致' if same else '不一致，见上表'}。"
        )
    lines.append("- 前提：桩模型 + 同机压测 + memory 仓储 + 限流关闭；结论只覆盖 Agent 服务自身上限。")
    return "\n".join(lines)


def default_log_dir() -> Path:
    """子进程日志目录：优先 %TEMP%。

    不能直接用 `tempfile.gettempdir()`：在 DSH 沙箱下 Python 子进程写 %TEMP% 会被拒，
    而 gettempdir() 会**静默回退到当前目录**（见 backend-agent/AGENTS.md 的踩坑记录），
    结果日志就撒进仓库了。所以这里逐个试环境变量并真的写一次探针，都不行才退到仓库内
    `.tmp-load-logs/`（已 gitignore，且 .tmp- 前缀符合临时文件约定）。
    """
    for key in ("TEMP", "TMP", "TMPDIR"):
        raw = os.environ.get(key)
        if not raw:
            continue
        candidate = Path(raw)
        probe = candidate / f".petlumina-probe-{os.getpid()}"
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    fallback = ROOT / ".tmp-load-logs"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


async def sweep(args: argparse.Namespace) -> list[LevelResult]:
    log_dir = Path(args.log_dir) if args.log_dir else default_log_dir()
    llm_port = args.llm_port or free_port()
    app_port = args.app_port or free_port()

    stub = Service(
        name="stub-llm",
        module="tests.stub_llm:app",
        port=llm_port,
        env=stub_env(
            first_token_ms=args.first_token_ms,
            chunk_gap_ms=args.chunk_gap_ms,
            chunk_chars=args.chunk_chars,
        ),
        log_dir=log_dir,
    )
    results: list[LevelResult] = []
    try:
        await wait_ready(stub.base_url, timeout_s=args.startup_wait_s, path="/docs")
        for level in args.levels:
            app = Service(
                name="app",
                module="app.main:app",
                port=app_port,
                env=app_env(llm_port=llm_port),
                log_dir=log_dir,
            )
            try:
                await wait_ready(app.base_url, timeout_s=args.startup_wait_s)
                before = await fetch_metrics(app.base_url)
                peak_startup = process_tree_peak_mb(app.proc.pid)
                samples = await run_level(level=level, requests=args.requests, base_url=app.base_url)
                peak_after = process_tree_peak_mb(app.proc.pid)
                after = await fetch_metrics(app.base_url)
            except Exception:
                print(f"[{level} 并发] 失败，服务日志尾部：\n{app.tail()}", file=sys.stderr)
                raise
            finally:
                app.stop()

            result = summarize_level(
                level=level,
                samples=samples,
                peak_startup_mb=peak_startup,
                peak_after_mb=peak_after,
                before=before,
                after=after,
                max_error_rate=args.max_error_rate,
                max_p95_ms=args.max_p95_ms,
            )
            results.append(result)
            print(
                f"[{level} 并发] {result.ok}/{result.total} 成功，首token p50={result.first_token['p50']:.0f}ms "
                f"p95={result.first_token['p95']:.0f}ms，峰值={result.peak_after_mb:.0f}MB → {result.verdict}",
                file=sys.stderr,
            )
            if args.cooldown_s > 0:
                await asyncio.sleep(args.cooldown_s)
    finally:
        stub.stop()
    return results


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="单实例容量基线：分级并发压 SSE")
    parser.add_argument(
        "--levels",
        default=",".join(str(v) for v in DEFAULT_LEVELS),
        help=f"并发档位，逗号分隔（默认 {','.join(str(v) for v in DEFAULT_LEVELS)}）",
    )
    parser.add_argument("--requests", type=int, default=DEFAULT_REQUESTS, help="每档请求总数")
    parser.add_argument("--first-token-ms", type=float, default=DEFAULT_FIRST_TOKEN_MS)
    parser.add_argument("--chunk-gap-ms", type=float, default=DEFAULT_CHUNK_GAP_MS)
    parser.add_argument("--chunk-chars", type=int, default=DEFAULT_CHUNK_CHARS)
    parser.add_argument("--app-port", type=int, default=0, help="被测服务端口，0=自动挑")
    parser.add_argument("--llm-port", type=int, default=0, help="桩模型端口，0=自动挑")
    parser.add_argument("--startup-wait-s", type=float, default=30.0)
    parser.add_argument("--cooldown-s", type=float, default=0.5, help="档位之间歇一下，别让上一档的收尾混进来")
    parser.add_argument("--max-p95-ms", type=float, default=DEFAULT_MAX_P95_MS)
    parser.add_argument("--max-error-rate", type=float, default=DEFAULT_MAX_ERROR_RATE)
    parser.add_argument("--log-dir", default="", help="子进程日志目录（默认 %%TEMP%%）")
    parser.add_argument("--json-out", default="", help="把逐档结果再落一份 JSON（建议 .tmp- 前缀）")
    args = parser.parse_args(argv)
    args.levels = [int(part) for part in str(args.levels).split(",") if part.strip()]
    if not args.levels:
        parser.error("--levels 至少要有一个档位")
    if args.requests < 1:
        parser.error("--requests 必须 >= 1")
    if max(args.levels) > args.requests:
        parser.error(
            f"--requests ({args.requests}) 必须 >= 最大档位 ({max(args.levels)})："
            "请求总数小于并发档位时，该档实际并发会被任务数封顶，测出来的不是目标并发。"
        )
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    print(
        f"起桩模型（首 token {args.first_token_ms:g}ms）+ 被测服务，档位 {args.levels}，"
        f"每档 {args.requests} 个请求…（子进程日志：{args.log_dir or default_log_dir()}）",
        file=sys.stderr,
    )
    results = asyncio.run(sweep(args))
    print()
    print(render_markdown(results, args))
    print()
    print(render_conclusion(results, args))
    if args.json_out:
        payload = {
            "config": {
                "levels": args.levels,
                "requests": args.requests,
                "first_token_ms": args.first_token_ms,
                "chunk_gap_ms": args.chunk_gap_ms,
                "chunk_chars": args.chunk_chars,
                "max_p95_ms": args.max_p95_ms,
                "max_error_rate": args.max_error_rate,
            },
            "levels": [r.as_dict() for r in results],
        }
        Path(args.json_out).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\nJSON 已写入 {args.json_out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n被 Ctrl+C 打断", file=sys.stderr)
        sys.exit(130)
