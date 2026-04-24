# UpstreamDrift UI

The UpstreamDrift web interface—React 19 + TypeScript + Vite + Tauri wrapper. The UI communicates with the Python FastAPI server in `src/api/` over REST and WebSockets to provide interactive physics simulation, trajectory analysis, and real-time visualization.

## Quick Start (Development)

### Prerequisites

- Node.js 18+ and npm 9+
- Python 3.10+ with the UpstreamDrift package installed (`pip install -e .`)
- Rust 1.70+ (only required for Tauri desktop builds)

### Running the Web UI

From the **repository root**:

```bash
# Start the Python API server
python start_api_server.py --port 8000

# In a new terminal, start the Vite dev server
cd ui
npm install
npm run dev
```

The UI will be available at `http://localhost:5173` by default. It connects to the API at `http://localhost:8000`.

## Architecture

### Key Directories

- **`src/pages/`** — Top-level route components (Dashboard, Simulation, etc.)
- **`src/components/`** — Reusable presentational and domain-specific components
- **`src/api/`** — React Query hooks wrapping REST endpoints and WebSocket connections
- **`src/stores/`** — Zustand global state (active engines, simulation config, UI theme)
- **`src/integration/`** — Vitest integration tests
- **`src-tauri/`** — Rust backend for the Tauri desktop shell

### API Contracts

The UI depends on the following FastAPI endpoints and WebSocket protocols defined in `src/api/`:

- **REST** — `/engines`, `/models`, `/simulate`, `/tools/*`
- **WebSocket** — `/ws/simulate/{engineType}` (trajectory updates), `/ws/chat/{sessionId}` (assistant chat)

See `src/api/routes/` for endpoint documentation and `src/api/websocket/` for protocol details.

## Development

### Scripts

```bash
npm run dev          # Start Vite dev server with HMR
npm run build        # Build production bundle (dist/)
npm run lint         # Run ESLint (see eslint.config.js)
npm run test         # Run Vitest suite
npm run preview      # Preview production build
```

### Code Style

- **Linting**: `npm run lint` (ESLint with TypeScript rules)
- **Formatting**: Configure your IDE to use Prettier (`.prettierrc.json`)
- **Type checking**: `npm run lint` includes `tsc --noEmit`

### Building the Desktop App

To build the Tauri desktop application:

```bash
npm run tauri build
```

Platform prerequisites:

- **Windows**: Visual Studio Build Tools or full Visual Studio
- **macOS**: Xcode Command Line Tools (`xcode-select --install`)
- **Linux**: `libwebkit2gtk-4.1` and related dev packages (see [Tauri docs](https://v2.tauri.app/start/prerequisites/))

## Project Status

The UI is under active development. Known gaps and planned features are tracked in the [Adversarial Review G track](https://github.com/D-sorganization/UpstreamDrift/issues/3160):

- **#3161** — Ship a chat component in the React/Tauri UI
- **#3166** — Four scaffolding pages need backend wiring (MotionCapture, VideoAnalyzer, PuttingGreen, DataExplorer)
- **#3170** — HelpPanel needs content (topic descriptions and feature explanations)
- **#3174** — Model authoring and parameter editor UI

See [`docs/ui/`](../docs/ui/) for additional developer guides and architecture documentation.

## Contributing

Please see [`CONTRIBUTING.md`](../CONTRIBUTING.md) in the repository root for contribution guidelines and branch naming conventions.

The UI codebase adheres to the same quality standards as the Python backend—see [`CLAUDE.md`](../CLAUDE.md) for:

- Linting and type-checking requirements
- Test coverage expectations
- Design-by-contract principles applied to TypeScript

## License & Acknowledgments

This project is part of UpstreamDrift, a humanoid modeling and physics simulation suite. See the repository README for full project context and team information.
