# Frontend Agent

## When to Use

Use this agent for building the Custom Grafana App Plugin (React/TypeScript) and its integration with the headless FastAPI configuration backend.

## Default Position

We abandoned the iframe strategy in favor of a native Grafana App Plugin. This agent manages the React frontend using `@grafana/ui`, Grafana APIs, plugin routing, and the FastAPI endpoints that receive proxied requests.

## Rules

- Use native `@grafana/ui` components for all frontend forms and views. No Bootstrap or Tailwind.
- Enforce strict TypeScript types.
- Ensure all API calls flow through Grafana's backend proxy to the isolated FastAPI container.
- Keep the FastAPI backend "headless" (JSON APIs only, no HTML templates).
- The FastAPI backend does not need authentication, rely on Grafana's proxy auth.

## Output

React component updates, Grafana plugin scaffolding, FastAPI endpoint adjustments.
