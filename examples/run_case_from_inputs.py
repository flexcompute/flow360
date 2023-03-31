import flow360 as fl
from flow360.examples import OM6wing

OM6wing.get_files()

# submit mesh with manual configuration
volume_mesh = fl.VolumeMesh.from_file(OM6wing.mesh_filename, name="OM6wing-mesh")
volume_mesh = volume_mesh.submit()
print(volume_mesh)


# submit case manual configuration
params = fl.Flow360Params(
    geometry = fl.Geometry(
        ref_area=1.15315084119231, 
        moment_length=(1.47602, 0.801672958512342, 1.47602),
        mesh_unit='m'
    ),
    freestream=fl.Freestream.from_speed((286, 'm/s'), alpha=3.06),
    time_stepping=fl.TimeStepping(max_pseudo_steps=500),
    boundaries = {
        "1": fl.NoSlipWall(name="wing"),
        "2": fl.SlipWall(name="symmetry"),
        "3": fl.FreestreamBoundary(name="freestream"),
    }
)

print(params.geometry)
print(params.freestream)
print(params.navier_stokes_solver)
print(params.turbulence_model_solver)
print(params.time_stepping)
print(params.boundaries)

case = fl.Case.new("OM6wing", params, volume_mesh.id)
case = case.submit()
print(case)
