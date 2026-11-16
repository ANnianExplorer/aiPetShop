"""容量基线脚本的纯函数单测：压测本身要有真进程，这里只钉住统计口径。

想的是：网络/子进程测不了，但「百分位怎么插值、错误率怎么算、判定怎么给、
指标怎么对账」一旦错了，报告里的数字就是假的——这几条必须能被单测钉死。
"""

from __future__ import annotations

import pytest

from scripts.load_baseline import (
    Sample,
    counter_delta,
    judge,
    parse_metrics,
    percentile,
    stats,
    summarize_level,
)


class TestPercentile:
    def test_empty_returns_zero(self):
        assert percentile([], 0.95) == 0.0

    def test_single_value_is_itself(self):
        for q in (0.0, 0.5, 0.95, 1.0):
            assert percentile([42.0], q) == 42.0

    def test_median_interpolates(self):
        values = [1.0, 2.0, 3.0, 4.0]
        assert percentile(values, 0.5) == pytest.approx(2.5)
        # pos = 3 * 0.95 = 2.85 → 3 + (4 - 3) * 0.85
        assert percentile(values, 0.95) == pytest.approx(3.85)
        assert percentile(values, 0.99) == pytest.approx(3.97)

    def test_clamps_at_both_ends(self):
        values = [1.0, 5.0, 9.0]
        assert percentile(values, -1.0) == 1.0
        assert percentile(values, 0.0) == 1.0
        assert percentile(values, 1.0) == 9.0
        assert percentile(values, 1.5) == 9.0

    def test_stats_reports_all_buckets(self):
        out = stats([10.0, 20.0, 30.0])
        assert out["n"] == 3
        assert out["p50"] == 20.0
        assert out["max"] == 30.0
        assert set(out) == {"n", "p50", "p95", "p99", "max"}


class TestJudge:
    def test_clean_level_passes(self):
        assert judge(error_rate=0.0, p95_ms=950, max_error_rate=0.01, max_p95_ms=3000) == "达标"

    def test_error_rate_over_threshold_is_named(self):
        verdict = judge(error_rate=0.05, p95_ms=950, max_error_rate=0.01, max_p95_ms=3000)
        assert verdict.startswith("超上限")
        assert "错误率" in verdict

    def test_slow_p95_is_named(self):
        verdict = judge(error_rate=0.0, p95_ms=4200, max_error_rate=0.01, max_p95_ms=3000)
        assert verdict.startswith("超上限")
        assert "P95" in verdict

    def test_both_reasons_are_reported(self):
        verdict = judge(error_rate=0.5, p95_ms=9999, max_error_rate=0.01, max_p95_ms=3000)
        assert "错误率" in verdict and "P95" in verdict


class TestMetrics:
    TEXT = "\n".join(
        [
            "# TYPE pet_agent_runs_total counter",
            'pet_agent_runs_total{route="L1",status="succeeded"} 12',
            'pet_agent_runs_total{route="unknown",status="failed"} 1',
            "# TYPE pet_agent_http_request_duration_seconds summary",
            'pet_agent_http_request_duration_seconds_sum{method="POST",path="/agent/chat"} 1.234567',
            'pet_agent_http_request_duration_seconds_count{method="POST",path="/agent/chat"} 3',
            "",
            "坏行没有空格",
            "another_bad_line not_a_number",
        ]
    )

    def test_parses_label_sets_and_skips_noise(self):
        parsed = parse_metrics(self.TEXT)
        assert parsed['pet_agent_runs_total{route="L1",status="succeeded"}'] == 12.0
        assert parsed['pet_agent_http_request_duration_seconds_count{method="POST",path="/agent/chat"}'] == 3.0
        assert "坏行没有空格" not in parsed
        assert all(isinstance(v, float) for v in parsed.values())

    def test_delta_counts_new_series_from_zero(self):
        after = parse_metrics(self.TEXT)
        assert counter_delta({}, after, "pet_agent_runs_total") == 13.0

    def test_delta_subtracts_previous_snapshot(self):
        before = {'pet_agent_runs_total{route="L1",status="succeeded"}': 10.0}
        after = parse_metrics(self.TEXT)
        assert counter_delta(before, after, "pet_agent_runs_total") == 3.0

    def test_delta_filters_by_label_fragment(self):
        after = parse_metrics(self.TEXT)
        assert counter_delta({}, after, "pet_agent_runs_total", contains='status="failed"') == 1.0
        assert counter_delta({}, after, "pet_agent_runs_total", contains='status="running"') == 0.0


class TestSummarizeLevel:
    def _samples(self):
        return [
            Sample(ok=True, first_token_ms=900.0, total_ms=1100.0, status=200),
            Sample(ok=True, first_token_ms=950.0, total_ms=1150.0, status=200),
            Sample(ok=True, first_token_ms=1000.0, total_ms=1200.0, status=200),
            Sample(ok=False, first_token_ms=None, total_ms=800.0, status=500, error="HTTP 500"),
        ]

    def test_counts_successes_and_error_rate(self):
        result = summarize_level(
            level=20,
            samples=self._samples(),
            peak_startup_mb=80.0,
            peak_after_mb=95.0,
            before={},
            after={},
            max_error_rate=0.01,
            max_p95_ms=3000.0,
        )
        assert result.total == 4
        assert result.ok == 3
        assert result.error_rate == pytest.approx(0.25)
        assert result.first_token["n"] == 3
        assert result.first_token["p50"] == pytest.approx(950.0)
        assert result.verdict.startswith("超上限")

    def test_ok_samples_without_first_token_do_not_crash(self):
        result = summarize_level(
            level=1,
            samples=[Sample(ok=True, first_token_ms=None, total_ms=500.0, status=200)],
            peak_startup_mb=0.0,
            peak_after_mb=0.0,
            before={},
            after={},
            max_error_rate=0.01,
            max_p95_ms=3000.0,
        )
        assert result.ok == 1
        assert result.first_token["n"] == 0
        assert result.first_token["p95"] == 0.0
        # 没有首 token 样本时按 0 判定，不会凭空判成超上限
        assert result.verdict == "达标"

    def test_metrics_reconciliation_is_carried_into_result(self):
        before = {'pet_agent_http_requests_total{method="POST",path="/agent/chat",status="200"}': 2.0}
        after = {
            'pet_agent_http_requests_total{method="POST",path="/agent/chat",status="200"}': 6.0,
            'pet_agent_runs_total{route="L1",status="succeeded"}': 4.0,
        }
        result = summarize_level(
            level=5,
            samples=self._samples(),
            peak_startup_mb=70.0,
            peak_after_mb=71.0,
            before=before,
            after=after,
            max_error_rate=1.0,
            max_p95_ms=3000.0,
        )
        assert result.http_chat == 4.0
        assert result.runs_ok == 4.0
        assert result.runs_failed == 0.0
