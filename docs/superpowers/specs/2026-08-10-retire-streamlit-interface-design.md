# Retire the Streamlit Interface

## Objective

Remove Streamlit from the active FraudLens Bharat product so the supported application has one user experience: the modern Next.js website backed by FastAPI. The removal must reduce dependencies and maintenance surface without changing analysis, OCR, storage, graph, privacy, or API behavior.

## Product Boundary

After this change, the supported stack is:

- Next.js for the professor-facing website;
- FastAPI for text analysis, screenshot OCR, case storage, graph reads, health, and readiness;
- the existing shared Python domain and persistence services behind FastAPI;
- Docker Compose for the complete local evaluation path.

There is no compatibility dashboard and no Streamlit runtime dependency.

## Runtime Removal

Delete the legacy Streamlit entry point and adapters that exist only to support it:

- `src/fraudlens/dashboard.py`;
- `src/fraudlens/dashboard_workflow.py`;
- `src/fraudlens/graph_dashboard.py`.

Remove dashboard-only tests rather than carrying mocks for an interface that no longer exists. Tests for reusable behavior remain at the shared service, API, OCR, privacy, graph-analysis, database, and web layers.

Any comments that describe non-API callers generically will be rewritten around the actual remaining boundary rather than retaining obsolete dashboard terminology.

## Dependencies and Containers

Remove Streamlit from `requirements.txt`, then regenerate the universal hashed runtime and contributor lockfiles using the repository's existing lock workflow. Packages that remain necessary through another direct or transitive dependency stay locked; packages reachable only through Streamlit are removed.

Remove Streamlit-specific Docker environment settings. The Python image continues to run FastAPI, while the web image continues to run Next.js. Existing container hardening, OCR packages, health checks, loopback defaults, and smoke verification remain unchanged.

## Documentation

Active documentation will describe only the Next.js website and FastAPI:

- README and installation instructions;
- professor, user, deployment, test-case, release, and demo-video guidance;
- current research, capstone, comparative, and presentation evidence;
- generated architecture diagrams and labels.

Historical Phase 1 records may state that Streamlit was built during Phase 1, but they must identify it as retired when discussing the current project. Historical claims will not be silently rewritten into a false account of earlier work. No historical page may retain an executable Streamlit command or imply that Streamlit is currently supported.

The current user manual becomes a website workflow guide. Presentation evidence must show Next.js/FastAPI labels instead of API/dashboard labels.

## Verification Contract

A repository contract test will prevent Streamlit from returning to active surfaces. It will reject:

- Streamlit imports or runtime modules under `src/`;
- Streamlit pins in direct or locked requirements;
- Streamlit Docker configuration;
- Streamlit run commands or current-support claims in active operational documentation.

Historical documentation is allowed to use the word only when it clearly describes the retired Phase 1 interface.

Verification must include:

- the new retirement contract failing before removal and passing afterward;
- the complete Python test suite on supported Python 3.11;
- dependency compatibility and vulnerability audits where available;
- all web unit, lint, typecheck, build, and Playwright/accessibility checks;
- Docker/container smoke checks through CI;
- regenerated presentation evidence matching current sources;
- `git diff --check` and a scoped final review.

## Non-goals

- No FastAPI endpoint or response-contract redesign.
- No changes to model artifacts, training data, or evaluation metrics.
- No redesign of the modern website.
- No erasure of truthful Phase 1 history.
- No replacement Python UI framework.

## Acceptance Criteria

1. `streamlit` is absent from active source, dependency locks, containers, and run commands.
2. The deleted dashboard modules have no remaining imports or callers.
3. Next.js and FastAPI are the only documented application interfaces.
4. Historical mentions are explicitly framed as retired legacy work.
5. Runtime, web, privacy, OCR, graph, and research tests remain green.
6. Generated presentation evidence contains no current Streamlit or dashboard architecture label.
