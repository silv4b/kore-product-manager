"""
Test package for products app.

This package contains all test modules for the products app.
Run tests with:
- All tests: python manage.py test products.tests
- Specific module: python manage.py test products.tests.test_models
- Quick test: python manage.py test products.tests.test_models products.tests.test_forms
"""

# Import all test modules for test discovery
from . import (
    factories as factories,
)
from . import (
    test_forms as test_forms,
)
from . import (
    test_integration as test_integration,
)
from . import (
    test_models as test_models,
)
from . import (
    test_utils as test_utils,
)
from . import (
    test_views as test_views,
)
