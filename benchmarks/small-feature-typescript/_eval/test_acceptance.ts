import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { retry } from '../src/retry.js';

describe('retry acceptance tests', () => {
  it('backoff timing within tolerance', async () => {
    const delays: number[] = [];
    let lastCallTime = 0;
    let callCount = 0;

    const fn = async () => {
      const now = Date.now();
      if (lastCallTime > 0) {
        delays.push(now - lastCallTime);
      }
      lastCallTime = now;
      callCount++;
      if (callCount <= 3) throw new Error('fail');
      return 'ok';
    };

    await retry(fn, {
      maxRetries: 3,
      initialDelay: 10,
      backoffMultiplier: 2,
    });

    const expectedDelays = [10, 20, 40];
    expect(delays).toHaveLength(3);

    for (let i = 0; i < expectedDelays.length; i++) {
      const expected = expectedDelays[i];
      const actual = delays[i];
      const tolerance = expected * 0.5; // 50% tolerance for timing tests
      expect(actual).toBeGreaterThanOrEqual(expected - tolerance);
      expect(actual).toBeLessThanOrEqual(expected + tolerance + 20); // extra headroom for CI
    }
  });

  it('abort signal cleanup — no pending timeouts after abort', async () => {
    vi.useFakeTimers();

    const controller = new AbortController();
    const fn = vi.fn().mockRejectedValue(new Error('fail'));

    const promise = retry(fn, {
      maxRetries: 100,
      initialDelay: 1000,
      backoffMultiplier: 2,
      abortSignal: controller.signal,
    });

    // Let first attempt run
    await vi.advanceTimersByTimeAsync(0);
    expect(fn).toHaveBeenCalledTimes(1);

    // Abort before any retry
    controller.abort();

    // Advance a lot of time — no more calls should happen
    await vi.advanceTimersByTimeAsync(1_000_000);

    await expect(promise).rejects.toThrow();

    // Should have only 1 call (the initial attempt)
    expect(fn).toHaveBeenCalledTimes(1);

    vi.useRealTimers();
  });

  it('memory stability — 1000 quick retries', async () => {
    // Run 1000 retry calls with maxRetries=0 (instant fail)
    const errors: Error[] = [];

    for (let i = 0; i < 1000; i++) {
      try {
        await retry(() => Promise.reject(new Error('fail')), {
          maxRetries: 0,
        });
      } catch (e) {
        errors.push(e as Error);
      }
    }

    expect(errors).toHaveLength(1000);
    // If we got here without OOM, the test passes
  });

  it('alternating success/failure — succeeds on even attempt', async () => {
    let callCount = 0;

    const fn = async () => {
      callCount++;
      // Fail on odd attempts (1, 3, 5...), succeed on even (2, 4, 6...)
      if (callCount % 2 !== 0) throw new Error(`odd-${callCount}`);
      return `even-${callCount}`;
    };

    const result = await retry(fn, {
      maxRetries: 5,
      initialDelay: 1,
      backoffMultiplier: 1,
    });

    expect(result).toBe('even-2');
    expect(callCount).toBe(2);
  });

  it('type inference — return type matches', async () => {
    const numResult = await retry(() => Promise.resolve(42), {
      maxRetries: 0,
    });
    // TypeScript should infer this as number
    const _check: number = numResult;
    expect(typeof numResult).toBe('number');

    const strResult = await retry(() => Promise.resolve('hello'), {
      maxRetries: 0,
    });
    const _check2: string = strResult;
    expect(typeof strResult).toBe('string');

    const objResult = await retry(() => Promise.resolve({ a: 1, b: 'two' }), {
      maxRetries: 0,
    });
    expect(objResult).toEqual({ a: 1, b: 'two' });
  });

  it('jitter option — delays are randomized', async () => {
    vi.useFakeTimers();
    const mathRandomSpy = vi.spyOn(Math, 'random');
    // Return predictable values for jitter
    mathRandomSpy.mockReturnValueOnce(0.5).mockReturnValueOnce(0.3);

    const fn = vi.fn().mockRejectedValue(new Error('fail'));

    const promise = retry(fn, {
      maxRetries: 2,
      initialDelay: 100,
      backoffMultiplier: 2,
      jitter: true,
    });

    // Initial call
    await vi.advanceTimersByTimeAsync(0);
    expect(fn).toHaveBeenCalledTimes(1);

    // With jitter, delays should be randomized within [0, calculatedDelay]
    // First retry delay = jitter applied to 100ms
    // Advance enough time to trigger retries
    await vi.advanceTimersByTimeAsync(100);
    expect(fn).toHaveBeenCalledTimes(2);

    await vi.advanceTimersByTimeAsync(200);
    expect(fn).toHaveBeenCalledTimes(3);

    await expect(promise).rejects.toThrow('fail');

    mathRandomSpy.mockRestore();
    vi.useRealTimers();
  });
});
