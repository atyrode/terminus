"""Basic test examples to demonstrate pytest usage."""

import pytest

# Note: for pytest to work, you have to prefix your functions with "test_"
# and the same goes for the .py test files!


def test_sync_example():
    """Example of a synchronous test."""
    assert True, "This test should always pass"


@pytest.mark.asyncio
async def test_async_example():
    """Example of an asynchronous test."""
    result = await async_operation()
    assert result == "success"


async def async_operation():
    """Example async operation that always succeeds."""
    return "success"
