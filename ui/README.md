# UpstreamDrift Web UI

The UpstreamDrift web UI — React 19 + TypeScript + Vite + Tauri wrapper — provides an interactive dashboard for golf ball flight simulation, visualization, and analysis. It communicates with the FastAPI backend in `src/api/` over REST and WebSocket connections.

## Quick Start

### Prerequisites

- Node.js 18+ (with npm or yarn)
- Python 3.10+ with the UpstreamDrift dependencies installed
- Rust toolchain (for Tauri desktop app builds)

### Local Development

Start the Python API server in one terminal:

```bash
# From repo root
python3 start_api_server.py --port 8000
```

Then start the React dev server in another terminal:

```bash
# From repo root
cd ui
npm install
npm run dev
```

The UI will be available at `http://localhost:5173` with hot module reload (HMR) enabled.

## Architecture at a Glance

- **`ui/src/pages/`** — Route-level components: Dashboard, Simulation, ModelExplorer, Chat
- **`ui/src/components/`** — Presentational and domain-specific UI components
- **`ui/src/api/`** — React Query hooks wrapping REST and WebSocket endpoints
- **`ui/src/stores/`** — Zustand global state: engine selection, simulation parameters, UI state
- **`ui/src-tauri/`** — Rust backend for the desktop shell (native window, file dialogs, system integration)
- **`ui/public/`** — Static assets (fonts, icons, initial HTML)

## API Contracts

The UI depends on the FastAPI server defined in `src/api/routes/`. Key endpoints:

- **REST endpoints** (`src/api/routes/`):
  - `GET /engines` — list available physics engines
  - `POST /engines/{engine}/initialize` — configure and start simulation
  - `GET /models` — list available URDF/MJCF models
  - `POST /tools/model-explorer/inspect` — inspect model structure

- **WebSocket endpoints** (`src/api/websockets/`):
  - `/ws/simulate/{engineType}` — real-time simulation stream (initial state, trajectory points, energy)
  - `/ws/chat/{session_id}` — chat with simulation assistant

See `src/api/routes/` for full route definitions and `src/api/websockets/` for WebSocket protocol details.

## Build Commands

### Development Server

```bash
npm run dev
```

### Type Checking

```bash
npm run typecheck
```

### Linting

```bash
npm run lint
```

### Testing

```bash
npm run test      # Run Vitest unit tests
npm run test:ui   # Run Vitest with UI
```

Integration tests are in `ui/src/integration/`.

### Production Build

```bash
npm run build
```

Output is in `ui/dist/`.

### Desktop App (Tauri)

To build the native desktop application:

```bash
npm run tauri build
```

**Prerequisites:**
- Rust toolchain (`rustup install stable`)
- Cargo and tauri CLI (`npm install -D @tauri-apps/cli@next`)
- Platform-specific build tools (Visual Studio Build Tools on Windows, Xcode on macOS, build-essential on Linux)

For detailed Tauri setup, see the [Tauri documentation](https://tauri.app/develop/).

## Contributing

- Read the main `CONTRIBUTING.md` and `CLAUDE.md` for repository policies
- ESLint config is in `ui/eslint.config.js`; run `npm run lint` before pushing
- All new features should include tests in `ui/src/integration/` or component tests
- Coordinate API changes with `src/api/` maintainers

## Known Gaps

The UpstreamDrift UI is under active development. See the [Track G issues](https://github.com/D-sorganization/UpstreamDrift/issues?q=label%3Aui+label%3Aadversarial-review) for planned work:

- **#G1**: Chat sidebar implementation
- **#G6**: Scaffolding for additional analysis pages
- **#G10**: Integrated help panel with API documentation
- **#G13**: Model authoring and parameter editor UI

## Project Structure

```
ui/
├── src/
│   ├── pages/          # Route components
│   ├── components/     # Reusable UI components
│   ├── api/            # React Query hooks
│   ├── stores/         # Zustand state management
│   ├── integration/    # Integration tests
│   ├── App.tsx         # Root component
│   └── main.tsx        # React entry point
├── src-tauri/          # Tauri Rust backend
├── public/             # Static assets
├── eslint.config.js    # ESLint configuration
├── vite.config.ts      # Vite build configuration
├── tsconfig.*.json     # TypeScript configurations
├── package.json        # Node dependencies
└── README.md           # This file
```

## Troubleshooting

### API Connection Errors

If the UI shows "API server unreachable":

1. Verify the API server is running: `curl http://localhost:8000/health`
2. Check that the base URL in `ui/src/api/client.ts` matches your server address
3. Ensure CORS is enabled in `src/api/server.py`

### Build Failures

- Clear node modules and reinstall: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf .vite`
- Check Node version: `node --version` (should be 18+)

### Hot Module Reload Not Working

The dev server enables HMR by default. If changes aren't reflected:

1. Hard refresh the browser (`Ctrl+Shift+R` or `Cmd+Shift+R`)
2. Check that Vite dev server is still running (check terminal for errors)
3. Ensure you're editing in the correct directory (`ui/src/`, not `ui/dist/`)
