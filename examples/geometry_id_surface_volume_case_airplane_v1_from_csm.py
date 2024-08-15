import os

import flow360 as fl

#fl.Env.preprod.active()
fl.Env.dev.active()

from flow360.component.geometry_v1 import Geometry
from flow360.component.meshing.params import Farfield, Volume, VolumeMeshingParams
from flow360.examples import Airplane

# geometry
geometry_draft = Geometry.from_file(
        Airplane.geometry, 
        project_name="testing-airplane-csm-geometry",
        solver_version="workbenchGeometry-28.1.0",
        )
geometry = geometry_draft.submit()
print(geometry)

# surface mesh
params = fl.SurfaceMeshingParams(max_edge_length=0.16)

surface_mesh_draft = fl.SurfaceMesh.create(
    geometry_id=geometry.id,
    params=params,
    name="airplane-surface-mesh-from-geometry-id-v1",
    solver_version="workbenchGeometry-28.1.0",
)
surface_mesh = surface_mesh_draft.submit()

print(surface_mesh)

