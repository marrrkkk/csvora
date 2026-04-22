from __future__ import annotations

from collections import Counter, defaultdict
from threading import Lock


_lock = Lock()
_counters: Counter[tuple[str, ...]] = Counter()
_latency_buckets: dict[tuple[str, str], list[int]] = defaultdict(list)
_task_durations: dict[str, list[int]] = defaultdict(list)


def increment_http_request(method: str, path: str, status_code: int) -> None:
    with _lock:
        _counters[("http_requests_total", method, path, str(status_code))] += 1


def observe_http_latency(method: str, path: str, duration_ms: int) -> None:
    with _lock:
        _latency_buckets[(method, path)].append(duration_ms)


def increment_task_event(task_name: str, event: str) -> None:
    with _lock:
        _counters[("worker_tasks_total", task_name, event)] += 1


def increment_csvora(event: str, **labels: str) -> None:
    with _lock:
        parts: tuple[str, ...] = ("csvora_events_total", event)
        for k in sorted(labels):
            parts = parts + (k, labels[k])
        _counters[parts] += 1


def observe_task_duration(task_name: str, duration_ms: int) -> None:
    with _lock:
        _task_durations[task_name].append(duration_ms)


def render_prometheus() -> str:
    lines: list[str] = []
    with _lock:
        for key, value in sorted(_counters.items()):
            metric = key[0]
            if metric == "http_requests_total":
                _, method, path, status = key
                lines.append(
                    f'http_requests_total{{method="{method}",path="{path}",status="{status}"}} {value}'
                )
            elif metric == "worker_tasks_total":
                _, task, event = key
                lines.append(f'worker_tasks_total{{task="{task}",event="{event}"}} {value}')
            elif metric == "csvora_events_total":
                event_name = key[1]
                rest = key[2:]
                label_parts: list[str] = []
                for i in range(0, len(rest), 2):
                    label_parts.append(f'{rest[i]}="{rest[i + 1]}"')
                lbl = ",".join(label_parts)
                if lbl:
                    lines.append(f'csvora_events_total{{event="{event_name}",{lbl}}} {value}')
                else:
                    lines.append(f'csvora_events_total{{event="{event_name}"}} {value}')

        for (method, path), values in sorted(_latency_buckets.items()):
            if values:
                avg = sum(values) / len(values)
                lines.append(f'http_request_duration_ms_avg{{method="{method}",path="{path}"}} {avg:.2f}')

        for task_name, values in sorted(_task_durations.items()):
            if values:
                avg = sum(values) / len(values)
                lines.append(f'worker_task_duration_ms_avg{{task="{task_name}"}} {avg:.2f}')
    return "\n".join(lines) + ("\n" if lines else "")

