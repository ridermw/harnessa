# Task: Implement the retry() Function

Implement the `retry()` function in `src/retry.ts`. All tests in `tests/` should pass.

## Requirements
- Retry an async function with exponential backoff
- Support all options defined in `RetryOptions` (see `src/types.ts`)
- Default values: maxRetries=3, initialDelay=1000ms, maxDelay=30000ms, backoffMultiplier=2
- Support AbortSignal for cancellation
- Fire onRetry callback before each retry attempt
- Reject with the last error after exhausting all retries
- Handle edge cases: zero retries, negative delays, concurrent usage

## Files
- `src/retry.ts` — implement here (stub exists with type signature)
- `src/types.ts` — RetryOptions interface (do not modify)
- `tests/retry.test.ts` — test suite (do not modify)
