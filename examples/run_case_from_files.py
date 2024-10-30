import flow360 as fl
from flow360.examples import OM6wing

fl.Env.dev.active()
OM6wing.get_files()

# submit mesh
volume_mesh = fl.VolumeMesh.from_file(
    OM6wing.mesh_filename, solver_version="beta20241029-24.11.1", name="OM6wing-mesh"
)
volume_mesh = volume_mesh.submit()
print(volume_mesh)

# # submit case using json file
params = fl.Flow360Params(OM6wing.case_json)
case = fl.Case.create("OM6wing", params, volume_mesh.id)
case = case.submit()
print(case)
