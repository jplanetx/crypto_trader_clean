"""Configure pytest for the project."""
import pytest

# Set pytest-asyncio defaults
pytest_plugins = ["pytest_asyncio"]
pytest_asyncio_mode = "strict"

# Define fixture loop scope to avoid deprecation warning
@pytest.fixture(scope="session", autouse=True)
def set_asyncio_fixture_loop_scope():
    """Set the default asyncio fixture loop scope to function."""
    pass
