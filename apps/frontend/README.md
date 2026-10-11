# PawCare Frontend

This is the Next.js frontend for PawCare, the AI-powered pet health assistant. The app currently provides the route shell and page scaffolding required by the project’s design and backlog, with no real auth or data-fetching logic yet.

## Stack

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS

## Local development

```bash
cd apps/frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Then open http://localhost:3000.

## Current scaffold

The app includes placeholder route shells for:
- `/login`
- `/register`
- `/pets`
- `/pets/[id]`
- `/pets/[id]/records`
- `/pets/[id]/assess`
- `/pets/[id]/chat`
- `/dashboard`
- `/admin`

These pages are intentionally minimal and are meant to be filled in by later feature tasks.

## Environment

The frontend reads its API base URL from `NEXT_PUBLIC_API_BASE_URL`, with a default of `http://localhost:8000`.
