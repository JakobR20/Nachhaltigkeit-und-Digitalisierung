# Dashboard — THWS Energie-Anomalien

Next.js 15 (App Router) cost-first browser for the energy manager, styled to the
Apple Human Interface Guidelines. Talks to the FastAPI backend (`../backend`).

## Setup

```bash
npm install
```

## Run (dev)

```bash
npm run dev
```

Opens `http://localhost:3000`. **The backend must run on port 8000** — start it first:

```bash
# from the repo root
uvicorn app.main:app --reload --app-dir backend
```

Otherwise the list shows a friendly "Backend nicht erreichbar" message.

## Pages

- `/` — cost-prioritised anomaly list with ensemble overview + filters
- `/anomaly/[id]` — detail: load chart, transparent cost breakdown, AI analysis
- `/research` — method-comparison view (κ heatmap, inference cost, sweep, table)

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | dev server (Turbopack) |
| `npm run build` | production build |
| `npm run start` | serve the production build |
| `npm run lint` | ESLint |
| `npm run test` | Vitest (component + util tests) |

## Configuration

- API base URL: `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`)
- Apple-HIG tokens live in `app/globals.css`; method/severity colours in `lib/format.ts`
- Types mirror the backend Pydantic schemas in `types/anomaly.ts`

## Stack

Next.js 15 · React 19 · TypeScript · Tailwind v4 · shadcn/ui · Recharts ·
@tanstack/react-query · axios · Vitest + React Testing Library
