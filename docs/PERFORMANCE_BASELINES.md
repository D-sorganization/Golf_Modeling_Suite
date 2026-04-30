# Performance Baselines

This page documents how the project records and (eventually) regresses on
runtime performance for hot physics paths. Tracked under
[issue #3510](https://github.com/D-sorganization/UpstreamDrift/issues/3510).

## Status

- **Harness landed:** yes -- [`pytest-benchmark`](https://pytest-benchmark.readthedocs.io/)
  is wired up via the `benchmark` pytest marker and a dedicated CI workflow
  (`.github/workflows/benchmarks.yml`).
- **Regression thresholds enforced:** **not yet.** The benchmarks workflow
  records results but does not fail the build on slowdowns. Thresholds will be
  introduced in a follow-up PR once we have several runs of baseline data.
- **Baseline numbers committed to the repo:** none yet, by design. We do not
  want stale or fabricated numbers checked in. Live results live in CI
  artifacts (see below).

## Running locally

Make sure dev dependencies are installed (this includes `pytest-benchmark`):

```bash
python3 -m pip install -e '.[dev]'
```

Run only the benchmark-marked tests:

```bash
python3 -m pytest tests/benchmarks -m benchmark --benchmark-only
```

For a quick smoke run of just the scaffolding benchmarks:

```bash
python3 -m pytest tests/benchmarks/test_benchmarks_smoke.py -m benchmark --benchmark-only
```

To save a JSON report locally (same format CI uploads):

```bash
python3 -m pytest tests/benchmarks -m benchmark --benchmark-only \
    --benchmark-json=benchmark.json
```

## Where CI results land

The `Performance Benchmarks` workflow (`.github/workflows/benchmarks.yml`)
runs on every pull request and on manual `workflow_dispatch`. It uploads
`benchmark.json` as a GitHub Actions artifact named
`benchmark-results-<sha>` with a 30-day retention. To inspect:

1. Open the PR's **Checks** tab.
2. Select the *Performance Benchmarks* workflow run.
3. Download the `benchmark-results-<sha>` artifact from the run summary.

## Adding a new benchmark

Drop a test into `tests/benchmarks/`, mark it `@pytest.mark.benchmark`, and
use the `benchmark` fixture:

```python
import pytest

@pytest.mark.benchmark
def test_my_hot_path(benchmark):
    result = benchmark(my_function, *args)
    assert result is not None
```

If the target imports a heavy optional engine (MuJoCo, Drake, Pinocchio),
guard the import with `pytest.importorskip` so the benchmark skips cleanly
in lean environments rather than erroring.

## Roadmap

1. (this PR) Land the harness, smoke benchmarks, CI workflow, artifact upload.
2. Collect a handful of runs on `main` to characterise noise floor.
3. Add `--benchmark-compare` against a stored baseline and turn the workflow
   into a blocking check with a tunable regression threshold (likely 15-20%
   on mean to start).
4. Expand benchmark coverage to include trajectory integration, terrain
   queries, and any Rust-kernel-backed paths.
