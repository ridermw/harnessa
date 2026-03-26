/**
 * Creates a debounced version of a function that delays invoking
 * until after `wait` ms have elapsed since the last call.
 *
 * The debounced function has `cancel` and `flush` methods:
 * - `cancel()` cancels any pending invocation
 * - `flush()` immediately invokes any pending invocation
 */
export function debounce<T extends (...args: any[]) => any>(
  fn: T,
  wait: number
): T & { cancel: () => void; flush: () => void } {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  let lastArgs: Parameters<T> | null = null;
  let lastThis: any = null;
  let result: ReturnType<T> | undefined;

  function invoke() {
    if (lastArgs !== null) {
      result = fn.apply(lastThis, lastArgs);
      lastArgs = null;
      lastThis = null;
    }
  }

  function debounced(this: any, ...args: Parameters<T>): ReturnType<T> {
    lastArgs = args;
    lastThis = this;

    if (timeoutId !== null) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(() => {
      timeoutId = null;
      invoke();
    }, wait);

    return result as ReturnType<T>;
  }

  debounced.cancel = function cancel(): void {
    if (timeoutId !== null) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
    lastArgs = null;
    lastThis = null;
  };

  debounced.flush = function flush(): void {
    if (timeoutId !== null) {
      clearTimeout(timeoutId);
      timeoutId = null;
      invoke();
    }
  };

  return debounced as T & { cancel: () => void; flush: () => void };
}

/**
 * Creates a throttled version of a function that only invokes
 * at most once per every `wait` ms.
 *
 * The first call is invoked immediately. Subsequent calls within
 * the wait period are deferred until the period ends.
 */
export function throttle<T extends (...args: any[]) => any>(
  fn: T,
  wait: number
): T & { cancel: () => void } {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  let lastArgs: Parameters<T> | null = null;
  let lastThis: any = null;
  let lastCallTime = 0;
  let result: ReturnType<T> | undefined;

  function invoke() {
    lastCallTime = Date.now();
    if (lastArgs !== null) {
      result = fn.apply(lastThis, lastArgs);
      lastArgs = null;
      lastThis = null;
    }
  }

  function throttled(this: any, ...args: Parameters<T>): ReturnType<T> {
    const now = Date.now();
    const remaining = wait - (now - lastCallTime);

    lastArgs = args;
    lastThis = this;

    if (remaining <= 0 || remaining > wait) {
      if (timeoutId !== null) {
        clearTimeout(timeoutId);
        timeoutId = null;
      }
      invoke();
    } else if (timeoutId === null) {
      timeoutId = setTimeout(() => {
        timeoutId = null;
        invoke();
      }, remaining);
    }

    return result as ReturnType<T>;
  }

  throttled.cancel = function cancel(): void {
    if (timeoutId !== null) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
    lastArgs = null;
    lastThis = null;
    lastCallTime = 0;
  };

  return throttled as T & { cancel: () => void };
}

/**
 * Memoizes a function using a Map cache. Supports custom key generation.
 *
 * By default, uses the first argument's string representation as the cache key.
 * A custom `keyFn` can be provided for more complex key generation.
 *
 * The memoized function exposes:
 * - `cache` — the underlying Map
 * - `clear()` — clears the cache
 */
export function memoize<T extends (...args: any[]) => any>(
  fn: T,
  keyFn?: (...args: Parameters<T>) => string
): T & { cache: Map<string, ReturnType<T>>; clear: () => void } {
  const cache = new Map<string, ReturnType<T>>();

  const defaultKeyFn = (...args: Parameters<T>): string => {
    if (args.length === 0) return '__no_args__';
    if (args.length === 1) return String(args[0]);
    return JSON.stringify(args);
  };

  const resolvedKeyFn = keyFn ?? defaultKeyFn;

  function memoized(this: any, ...args: Parameters<T>): ReturnType<T> {
    const key = resolvedKeyFn(...args);

    if (cache.has(key)) {
      return cache.get(key)!;
    }

    const result = fn.apply(this, args) as ReturnType<T>;
    cache.set(key, result);
    return result;
  }

  memoized.cache = cache;

  memoized.clear = function clear(): void {
    cache.clear();
  };

  return memoized as T & { cache: Map<string, ReturnType<T>>; clear: () => void };
}

/**
 * Delays execution for the specified number of milliseconds.
 * Returns a promise that resolves after the delay.
 *
 * @param ms - The number of milliseconds to delay
 * @returns A promise that resolves after the delay
 */
export function delay(ms: number): Promise<void> {
  return new Promise<void>((resolve) => {
    setTimeout(resolve, Math.max(0, ms));
  });
}

/**
 * Creates a timeout promise that rejects after the specified duration.
 * Wraps an existing promise and races it against a timeout.
 *
 * If the original promise resolves before the timeout, its value is returned.
 * If the timeout fires first, the returned promise rejects with a TimeoutError.
 *
 * @param promise - The promise to wrap
 * @param ms - The timeout duration in milliseconds
 * @returns The result of the original promise, or rejects on timeout
 */
export function timeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  let timeoutId: ReturnType<typeof setTimeout>;

  const timeoutPromise = new Promise<never>((_, reject) => {
    timeoutId = setTimeout(() => {
      reject(new Error(`Operation timed out after ${ms}ms`));
    }, ms);
  });

  return Promise.race([promise, timeoutPromise]).finally(() => {
    clearTimeout(timeoutId);
  });
}
