"""
nrelS809 meshing example
"""

from .base_test_case import BaseTestCase


class NRELS809(BaseTestCase):
    name = "nrelS809"

    class url:
        geometry = "https://simcloud-public-1.s3.amazonaws.com/s809/s809.csm"
