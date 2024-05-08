"""
I have my volume mesh, want to run my first simulation
"""

from ..inputs import VolumeMesh
from ..mesh import MeshingParameters, ZoneRefinement
from ..operating_condition import ExternalFlowOperatingConditions
from ..references import ReferenceGeometry
from ..simulation import Simulation
from ..volumes import FluidDynamics
from ..zones import BoxZone

volume_zone = BoxZone(name="WholeDomain", x_range=(1, 2), y_range=(1, 2), z_range=(1, 2))

sim = Simulation(
    VolumeMesh.from_file("mesh.cgns"),
    reference_geometry=ReferenceGeometry(area=0.1),
    zones=[FluidDynamics(entities=[volume_zone])],
)


# execute
results = sim.run()
# or
results = web.run(sim)