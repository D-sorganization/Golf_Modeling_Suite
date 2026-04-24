# SPEC.md — Repository Specification Document

│   └── tools/                      # Development and analysis tools
│       ├── analysis_tools.py       # Biomechanical analysis utilities
│       └── validation_tools.py     # Cross-engine validation
├── rust_core/
│   └── upstream-physics/           # Rust physics kernels
│       ├── src/
│       │   ├── lib.rs
│       │   └── physics.rs
│       └── Cargo.toml
├── ui/
│   ├── src/
│   │   ├── main.ts                 # Tauri app entry point
│   │   └── components/             # React/Vue components
│   ├── tauri.conf.json
│   └── package.json
├── shared/
│   └── models/                     # URDF/model definitions
│       ├── golf_swing_models/
│       ├── human_body_models/
│       └── pendulum_models/
├── tests/
│   ├── unit/                       # Unit tests per module
│   ├── integration/                # Cross-engine integration tests
│   ├── acceptance/                 # End-to-end scenario tests
│   ├── cross_engine/               # Cross-validation tests
│   ├── physics_validation/         # Physics accuracy tests
│   ├── benchmarks/                 # Performance benchmarks
│   └── conftest.py                 # Pytest fixtures and configuration
├── .github/
│   └── workflows/
│       ├── ci-standard.yml         # Standard CI checks
│       ├── heavy-tests-opt-in.yml  # Heavy tests (custom runner)
│       ├── nightly-cross-validation.yml
│       ├── tauri-build.yml
│       ├── vendor-freshness.yml
│       └── docker-size-gates.yml
├── pyproject.toml
├── poetry.lock
├── SPEC.md                         # This file
└── README.md
```

### Key Components
