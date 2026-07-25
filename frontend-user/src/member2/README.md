# Member 2 isolated frontend preview

This directory contains only the user frontend/UI work owned by member 2. It does not modify the existing app shell, router, stores, API wrapper, admin frontend, backend, or other members' feature pages.

Run the existing Vite dev server and open:

```text
http://localhost:5173/member2-preview.html
```

The preview consumes the existing `/api/v1/cultures` endpoint. When the backend is unavailable, it shows an explicit retry state instead of mock success data. The AI guide clearly marks the member 3 question-answering contract as pending.

Before integration, the owner of `src/router/index.ts` can review and selectively mount these additive components into the main application.
