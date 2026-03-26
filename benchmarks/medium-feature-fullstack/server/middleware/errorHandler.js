/**
 * Custom error class for validation errors.
 */
class ValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ValidationError';
    this.statusCode = 400;
  }
}

/**
 * Custom error class for not-found errors.
 */
class NotFoundError extends Error {
  constructor(message) {
    super(message || 'Resource not found');
    this.name = 'NotFoundError';
    this.statusCode = 404;
  }
}

/**
 * Custom error class for authorization errors.
 */
class ForbiddenError extends Error {
  constructor(message) {
    super(message || 'Access denied');
    this.name = 'ForbiddenError';
    this.statusCode = 403;
  }
}

/**
 * Express error-handling middleware.
 * Catches all errors thrown in route handlers and returns a consistent JSON response.
 */
function errorHandler(err, req, res, _next) {
  // Log the error in development
  if (process.env.NODE_ENV !== 'production') {
    console.error(`[Error] ${err.name}: ${err.message}`);
    if (err.stack && process.env.NODE_ENV === 'development') {
      console.error(err.stack);
    }
  }

  // Handle known error types
  if (err instanceof ValidationError) {
    return res.status(err.statusCode).json({
      error: err.message,
      status: err.statusCode,
    });
  }

  if (err instanceof NotFoundError) {
    return res.status(err.statusCode).json({
      error: err.message,
      status: err.statusCode,
    });
  }

  if (err instanceof ForbiddenError) {
    return res.status(err.statusCode).json({
      error: err.message,
      status: err.statusCode,
    });
  }

  // Handle SQLite constraint errors
  if (err.message && err.message.includes('UNIQUE constraint failed')) {
    return res.status(409).json({
      error: 'A record with that value already exists.',
      status: 409,
    });
  }

  // Handle JSON parse errors
  if (err.type === 'entity.parse.failed') {
    return res.status(400).json({
      error: 'Invalid JSON in request body.',
      status: 400,
    });
  }

  // Default: 500 Internal Server Error
  const statusCode = err.statusCode || 500;
  const message =
    process.env.NODE_ENV === 'production'
      ? 'Internal server error'
      : err.message || 'Internal server error';

  return res.status(statusCode).json({
    error: message,
    status: statusCode,
  });
}

module.exports = {
  errorHandler,
  ValidationError,
  NotFoundError,
  ForbiddenError,
};
