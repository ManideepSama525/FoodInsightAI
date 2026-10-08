# Frontend build fix

The frontend build exposed malformed calls in `frontend/app/page.tsx`.
The affected functions now invoke their API helpers correctly:

- `getIncidentCenter()`
- `getApiContract()`
- `getReleaseManifest()`
- `getReleaseReadiness()`
- `getRecovery()`

The frontend `package.json` also explicitly declares the TypeScript React/Node type packages.
