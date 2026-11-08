"""最小指标注册表（Prometheus 文本格式），不引入任何外部依赖。

设计取舍：
- 只用进程内累加，不做聚合推送——抓取模型（Prometheus scrape）足够，
  多副本时由 Prometheus 按 instance 聚合；
- 标签只放低基数字段（方法/路由模板/状态码/route/tool），
  绝不放 session_id、user_id、消息内容；
- 路由用**模板**（`/agent/documents/{id}`）而不是原始 URL，
  否则 `/agent/sessions/1794.../messages` 会造出成千上万个时间序列。
"""

from __future__ import annotations

import threading
from collections.abc import Iterable, Mapping

Labels = Mapping[str, str]


def _format_labels(labels: Labels | None) -> str:
    if not labels:
        return ""
    inner = ",".join(f'{k}="{_escape(v)}"' for k, v in sorted(labels.items()))
    return "{" + inner + "}"


def _escape(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


class Metrics:
    """计数器 + 摘要（sum/count）。线程安全，够用于单进程 asyncio + 线程池。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, dict[str, float]] = {}
        self._observations: dict[str, dict[str, tuple[float, int]]] = {}

    def inc(self, name: str, labels: Labels | None = None, value: float = 1.0) -> None:
        key = _format_labels(labels)
        with self._lock:
            series = self._counters.setdefault(name, {})
            series[key] = series.get(key, 0.0) + value

    def observe(self, name: str, value: float, labels: Labels | None = None) -> None:
        key = _format_labels(labels)
        with self._lock:
            series = self._observations.setdefault(name, {})
            total, count = series.get(key, (0.0, 0))
            series[key] = (total + float(value), count + 1)

    def counter_value(self, name: str, labels: Labels | None = None) -> float:
        with self._lock:
            return self._counters.get(name, {}).get(_format_labels(labels), 0.0)

    def render(self, extra: Iterable[str] = ()) -> str:
        """渲染成 `text/plain; version=0.0.4` 文本。"""
        lines: list[str] = []
        with self._lock:
            counters = {name: dict(series) for name, series in self._counters.items()}
            observations = {name: dict(series) for name, series in self._observations.items()}
        for name in sorted(counters):
            lines.append(f"# TYPE {name} counter")
            for key, value in sorted(counters[name].items()):
                lines.append(f"{name}{key} {value:.0f}")
        for name in sorted(observations):
            lines.append(f"# TYPE {name} summary")
            for key, (total, count) in sorted(observations[name].items()):
                lines.append(f"{name}_sum{key} {total:.6f}")
                lines.append(f"{name}_count{key} {count}")
        lines.extend(extra)
        return "\n".join(lines) + "\n"

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._observations.clear()


# 进程级单例：中间件、runner、gateway 都往这里记；`/metrics` 从这里读
metrics = Metrics()

HTTP_REQUESTS = "pet_agent_http_requests_total"
HTTP_DURATION = "pet_agent_http_request_duration_seconds"
RUNS = "pet_agent_runs_total"
TOOL_CALLS = "pet_agent_tool_calls_total"
QUEUE_DEPTH = "pet_agent_queue_depth"
TOKENS = "pet_agent_tokens_total"
