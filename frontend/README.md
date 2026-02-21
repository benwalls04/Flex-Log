# FlexLog Frontend

React + Vite + Tailwind CSS. Auth via Supabase; tracking API via gateway (JWT only, no X-User-Id).

## Environment variables

Create a `.env` file in this directory (see `.env.example`). Required:

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | Backend API gateway base URL (no trailing slash). Same base for tracking and recommendation. |
| `VITE_SUPABASE_URL` | Supabase project URL. |
| `VITE_SUPABASE_ANON_KEY` | Supabase anonymous/public key. |

All Vite env vars must be prefixed with `VITE_` to be exposed to the client.

## Theming

Colors are driven by CSS variables in `src/index.css`:

- `:root` — default light theme (edit `--color-primary`, `--color-surface`, etc.).
- `.dark` — dark theme; add class `dark` to `<html>` or `<body>` to enable.

You can add more theme classes (e.g. `.theme-ocean`) and override the same variables to try different looks.

## Scripts

- `npm run dev` — start dev server
- `npm run build` — production build
- `npm run preview` — preview production build
