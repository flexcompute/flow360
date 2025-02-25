import re
import unittest

import pytest

from flow360 import exceptions as ex
from flow360.component.surface_mesh import SurfaceMesh

assertions = unittest.TestCase("__init__")


@pytest.fixture(autouse=True)
def change_test_dir(request, monkeypatch):
    monkeypatch.chdir(request.fspath.dirname)


def test_draft_surface_mesh_from_file():
    with pytest.raises(
        ex.Flow360ValueError,
        match=re.escape(
            "Unsupported surface mesh file extensions: MeshFileFormat.UNKNOWN. Supported: [stl,ugrid,cgns]."
        ),
    ):
        sm = SurfaceMesh.from_file("file.unsupported")

    with pytest.raises(ex.Flow360FileError, match=re.escape("file_does_not_exist.stl not found.")):
        sm = SurfaceMesh.from_file("file_does_not_exist.stl")

    sm = SurfaceMesh.from_file("data/surface_mesh/airplaneGeometry.stl")
    assert sm
