export interface RetryOptions {
  /** Maximum number of retry attempts (default: 3) */
  maxRetries?: number;
  /** Initial delay in ms before first retry (default: 1000) */
  initialDelay?: number;
  /** Maximum delay in ms between retries (default: 30000) */
  maxDelay?: number;
  /** Multiplier for exponential backoff (default: 2) */
  backoffMultiplier?: number;
  /** AbortSignal to cancel retries */
  abortSignal?: AbortSignal;
  /** Callback fired before each retry */
  onRetry?: (error: Error, attempt: number) => void;
  /** Add random jitter to delay (default: false) */
  jitter?: boolean;
}

export interface RetryResult<T> {
  result: T;
  attempts: number;
}
