"""
airplane meshing example
"""

from .base_test_case import BaseTestCase


class Airplane(BaseTestCase):
    name = "airplane"

    class url:
        geometry = "https://simcloud-public-1.s3.amazonaws.com/airplane/quick_start_airplane.csm"
        surface_json = "local://surface_params.json"
        volume_json = "local://volume_params.json"
        case_json = "local://case_params.json"
