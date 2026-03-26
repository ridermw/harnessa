# small-feature-typescript

A lightweight TypeScript utility library providing common async patterns: retry with exponential backoff, debounce, throttle, memoize, delay, and timeout.

## Usage

```typescript
import { retry, debounce, throttle, memoize, delay, timeout } from './src/index.js';
```

## Development

```bash
npm install
npm run build    # Compile TypeScript
npm test         # Run tests with vitest
npm run test:watch  # Run tests in watch mode
```

## Structure

- `src/types.ts` — Type definitions
- `src/retry.ts` — Retry with exponential backoff
- `src/utils.ts` — Debounce, throttle, memoize, delay, timeout utilities
- `src/index.ts` — Barrel exports
- `tests/` — Test suites
