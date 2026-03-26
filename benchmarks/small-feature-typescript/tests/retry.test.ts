import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { retry } from '../src/retry.js';

describe('retry', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('basic retry on failure — fails twice then succeeds', async () => {
    let callCount = 0;
    const fn = async () => {
      callCount++;
      if (callCount < 3) throw new Error(`fail #${callCount}`);
      return 'success';
    };

    const result = await retry(fn, { maxRetries: 3, initialDelay: 1, backoffMultiplier: 1 });
    expect(result).toBe('success');
    expect(callCount).toBe(3);
  });

  it('succeeds on first try — no retries needed', async () => {
    const fn = vi.fn().mockResolvedValue('first-try');

    const result = await retry(fn, { maxRetries: 3, initialDelay: 1 });
    expect(result).toBe('first-try');
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('respects maxRetries limit', async () => {
    const fn = vi.fn().mockRejectedValue(new Error('always fails'));

    await expect(retry(fn, { maxRetries: 2, initialDelay: 1, backoffMultiplier: 1 }))
      .rejects.toThrow('always fails');

    // 1 initial + 2 retries = 3 total attempts
    expect(fn).toHaveBeenCalledTimes(3);
  });

  it('exponential backoff timing', async () => {
    vi.useFakeTimers();

    const fn = vi.fn().mockRejectedValue(new Error('fail'));

    const promise = retry(fn, {
      maxRetries: 3,
      initialDelay: 100,
      backoffMultiplier: 2,
    });

    // Initial call happens immediately
    await vi.advanceTimersByTimeAsync(0);
    expect(fn).toHaveBeenCalledTimes(1);

    // After 100ms: first retry
    await vi.advanceTimersByTimeAsync(100);
    expect(fn).toHaveBeenCalledTimes(2);

    // After 200ms: second retry
    await vi.advanceTimersByTimeAsync(200);
    expect(fn).toHaveBeenCalledTimes(3);

    // After 400ms: third retry
    await vi.advanceTimersByTimeAsync(400);
    expect(fn).toHaveBeenCalledTimes(4);

    await expect(promise).rejects.toThrow('fail');

    vi.useRealTimers();
  });

  it('max delay cap', async () => {
    vi.useFakeTimers();

    const fn = vi.fn().mockRejectedValue(new Error('fail'));

    const promise = retry(fn, {
      maxRetries: 2,
      initialDelay: 50,
      maxDelay: 100,
      backoffMultiplier: 4,
    });

    // Initial call
    await vi.advanceTimersByTimeAsync(0);
    expect(fn).toHaveBeenCalledTimes(1);

    // First retry after 50ms
    await vi.advanceTimersByTimeAsync(50);
    expect(fn).toHaveBeenCalledTimes(2);

    // Second retry: 50*4=200 but capped at 100
    await vi.advanceTimersByTimeAsync(100);
    expect(fn).toHaveBeenCalledTimes(3);

    await expect(promise).rejects.toThrow('fail');

    vi.useRealTimers();
  });

  it('abort signal cancellation', async () => {
    const controller = new AbortController();
    let callCount = 0;

    const fn = async () => {
      callCount++;
      throw new Error('fail');
    };

    const promise = retry(fn, {
      maxRetries: 10,
      initialDelay: 1,
      backoffMultiplier: 1,
      abortSignal: controller.signal,
    });

    // Give the first attempt time to run and delay to start
    await new Promise((r) => setTimeout(r, 50));
    controller.abort();

    await expect(promise).rejects.toThrow();
    // Should not have completed all 11 attempts
    expect(callCount).toBeLessThan(11);
  });

  it('custom onRetry callback', async () => {
    let callCount = 0;
    const onRetryCalls: Array<{ error: Error; attempt: number }> = [];

    const fn = async () => {
      callCount++;
      if (callCount < 3) throw new Error(`error-${callCount}`);
      return 'done';
    };

    const onRetry = (error: Error, attempt: number) => {
      onRetryCalls.push({ error, attempt });
    };

    await retry(fn, { maxRetries: 3, initialDelay: 1, backoffMultiplier: 1, onRetry });

    expect(onRetryCalls).toHaveLength(2);
    expect(onRetryCalls[0].error.message).toBe('error-1');
    expect(onRetryCalls[0].attempt).toBe(1);
    expect(onRetryCalls[1].error.message).toBe('error-2');
    expect(onRetryCalls[1].attempt).toBe(2);
  });

  it('zero retries = single attempt', async () => {
    const fn = vi.fn().mockRejectedValue(new Error('one-shot'));

    await expect(retry(fn, { maxRetries: 0, initialDelay: 1 }))
      .rejects.toThrow('one-shot');

    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('negative delay treated as 0', async () => {
    let callCount = 0;
    const fn = async () => {
      callCount++;
      if (callCount < 2) throw new Error('fail');
      return 'ok';
    };

    const start = Date.now();
    const result = await retry(fn, { maxRetries: 1, initialDelay: -100, backoffMultiplier: 2 });
    const elapsed = Date.now() - start;

    expect(result).toBe('ok');
    // With negative delay treated as 0, this should be near-instant
    expect(elapsed).toBeLessThan(100);
  });

  it('concurrent retries don\'t interfere', async () => {
    const makeFn = (id: string, failCount: number) => {
      let calls = 0;
      return async () => {
        calls++;
        if (calls <= failCount) throw new Error(`${id}-fail-${calls}`);
        return `${id}-success`;
      };
    };

    const [r1, r2, r3] = await Promise.all([
      retry(makeFn('a', 1), { maxRetries: 3, initialDelay: 1, backoffMultiplier: 1 }),
      retry(makeFn('b', 2), { maxRetries: 3, initialDelay: 1, backoffMultiplier: 1 }),
      retry(makeFn('c', 0), { maxRetries: 3, initialDelay: 1, backoffMultiplier: 1 }),
    ]);

    expect(r1).toBe('a-success');
    expect(r2).toBe('b-success');
    expect(r3).toBe('c-success');
  });

  it('rejects with last error', async () => {
    let callCount = 0;
    const fn = async () => {
      callCount++;
      throw new Error(`error-${callCount}`);
    };

    await expect(retry(fn, { maxRetries: 2, initialDelay: 1, backoffMultiplier: 1 }))
      .rejects.toThrow('error-3');
  });

  it('works with sync-wrapped functions', async () => {
    const fn = () => Promise.resolve(42);

    const result = await retry(fn, { maxRetries: 3, initialDelay: 1 });
    expect(result).toBe(42);
  });
});
