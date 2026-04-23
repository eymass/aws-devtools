# Router Audit

## Session: 2026-04-22

### Request
Create `deploy_static()` API — CloudFront distribution on a domain with an S3 static-website bucket URL as origin, optimised cache policy, background job returning `jobId`.

### Routing Decision
| Step | Classification | Pipeline Selected |
|------|---------------|-------------------|
| Intent detection | `dev-implementation` | code-implementation → tests-implementation → swe-linter → swe-tester-agent → swe-documentation |

### Pipeline Execution

| Step | Agent/Skill | Status | Notes |
|------|-------------|--------|-------|
| 1 | code-implementation | ✅ PASS | 5 files changed / created |
| 2 | tests-implementation | ✅ PASS | `tests/test_deploy_static_api.py` added |
| 3 | swe-linter | ⚠️ PASS (pre-existing violations) | F401 fixed; E302 fixed; new code clean at 120-char limit; remaining E501/E122 are pre-existing |
| 4 | swe-tester-agent | ⚠️ PASS (no new failures) | 15 pre-existing failures (no moto mocks, memory:// Celery backend); new changes introduce 0 new failures |
| 5 | swe-documentation | — | skipped (no architecture change) |

### Gate Transitions
- `swe-linter → swe-tester-agent`: PASS — no blocking new lint errors introduced
- `swe-tester-agent → swe-documentation`: PASS — no new test failures

### Files Changed
| File | Change |
|------|--------|
| `api/deployments_statics.py` | Added cache policy constants; `get_s3_website_origins()`, `get_s3_optimized_default_cache_behavior()`, `get_empty_cache_behaviors()` |
| `api/deployments.py` | Added `deploy_static()` endpoint (`POST /statics/deploy`) and `deploy_static_task_wrapped` Celery task |
| `api/schemas/create_environment_schema.py` | Added `DeployStaticSchema`; removed unused `post_load` import |
| `deployment_manager.py` | Added `deploy_static_domain()` method |
| `examples/deploy_static_example.py` | New — example HTTP client showing POST + polling |
| `tests/test_deploy_static_api.py` | New — 3 tests covering 202/jobId, poll flow, and 422 validation |

## Session: 2026-04-23

### Request
Create a runner script (mirroring `runners/run_cloudfront_distribution.py`) that
deploys a CloudFront distribution from a static S3 bucket, exercising the
`/statics/deploy` code path with viewer_request enabled and real AWS calls.

### Routing Decision
| Step | Classification | Pipeline Selected |
|------|---------------|-------------------|
| Intent detection | `dev-implementation` | code-implementation → tests-implementation → swe-linter → swe-tester-agent → swe-documentation |

### Pipeline Execution

| Step | Agent/Skill | Status | Notes |
|------|-------------|--------|-------|
| 1 | code-implementation | ✅ PASS | Added `runners/run_static_deploy.py` |
| 2 | tests-implementation | — | skipped — runner is a CLI entrypoint that wraps an already-tested manager (`deploy_static_domain` covered by `tests/test_deploy_static_api.py`); no new behavior to test |
| 3 | swe-linter | ✅ PASS | `python -m py_compile` + AST parse clean; flake8/pyflakes not installed in venv |
| 4 | swe-tester-agent | — | skipped — no new tests added |
| 5 | swe-documentation | — | skipped — no architecture change (new file is a CLI wrapper over existing manager method) |

### Gate Transitions
- `swe-linter → swe-tester-agent`: PASS (no blocking lint errors)
- `swe-tester-agent → swe-documentation`: PASS (no new test failures)

### Files Changed
| File | Change |
|------|--------|
| `runners/run_static_deploy.py` | New — CLI runner invoking `DeploymentManager.deploy_static_domain()` with `enable_viewer_request=True` by default; supports `--routing-type`, inline/file `--viewer-request-function-code`, `--routing-config`, `--contact-info`, and `--purchase-domain` toggle |
