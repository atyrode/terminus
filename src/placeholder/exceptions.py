""" Custom exceptions for the application. """


class AsyncTimeoutError(Exception):
    """
    Exception raised when an async operation exceeds its timeout limit.

    This exception is used by the `async_timeout` decorator to signal that the wrapped
    asynchronous function has exceeded the specified time limit for execution.
    """
