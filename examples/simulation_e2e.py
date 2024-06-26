import os

import flow360 as fl
from flow360.component.simulation.meshing_param.face_params import (
    BoundaryLayer,
    SurfaceRefinement,
)
from flow360.component.simulation.models.volume_models import BETDisk, Fluid
from tests.simulation.translator.utils.xv15_bet_disk_helper import (
    createBETDiskSteady,
    createBETDiskUnsteady,
    createSteadyTimeStepping,
    createUDDInstance,
    createUnsteadyTimeStepping,
)
from flow360.component.simulation.primitives import Cylinder
from flow360.component.simulation.operating_condition import ThermalState
from flow360.component.simulation.models.surface_models import Freestream, Wall
from flow360.component.simulation.models.volume_models import Fluid
from flow360.component.simulation.operating_condition import AerospaceCondition
from flow360.component.simulation.primitives import ReferenceGeometry, Surface
from flow360.component.simulation.user_defined_dynamics.user_defined_dynamics import UserDefinedDynamic
from flow360.component.simulation.services import (
    simulation_to_case_json,
    simulation_to_surface_meshing_json,
    simulation_to_volume_meshing_json,
)
from flow360.component.simulation.simulation_params import (
    MeshingParams,
    SimulationParams,
)
from flow360.component.simulation.time_stepping.time_stepping import Steady, Unsteady, RampCFL
from flow360.component.simulation.unit_system import SI_unit_system, u, imperial_unit_system

#fl.UserConfig.set_profile("auto_test_1")
fl.Env.dev.active()

from flow360.component.geometry import Geometry
from flow360.examples import Airplane

SOLVER_VERSION = "workbench-24.6.10"
rpm_hover = 588

def dt_to_revolve_one_degree(rpm):
    return (1.0 / (rpm / 60 * 360)) * u.s

def createUDDInstance():
    udd = UserDefinedDynamic(
        name="BET_Controller",
        input_vars=["bet_0_thrust"],
        output_vars={"bet_0_omega": "state[0];"},
        constants={
            "ThrustTarget": 300,
            "PConst": 1e-7,
            "IConst": 1e-7,
            "omega0": 0.003,
        },
        state_vars_initial_value=["0.003", "0.0", "0", "0", "0"],
        update_law=[
            "if (physicalStep > 150 and pseudoStep == 0) PConst * (ThrustTarget - bet_0_thrust)  + IConst * state[1] + omega0; else state[0];",
            "if (physicalStep > 150 and pseudoStep == 0) state[1] + (ThrustTarget - bet_0_thrust); else state[1];",
            "(physicalStep > 150 and pseudoStep == 0)",
            "ThrustTarget - bet_0_thrust",
            "IConst * state[1]",
        ],
    )
    return udd

if __name__ == "__main__":
    print("1")
    _BET_cylinder = Cylinder(
        name="my_bet_disk_volume",
        center=(0, 0, 0) * u.inch,
        axis=[0, 0, 1],
        outer_radius=150 * u.inch,
        height=15 * u.inch,
    )
    betdisk_unsteady = createBETDiskUnsteady(_BET_cylinder, 10, rpm_hover)
    udd_instance = createUDDInstance()

    with imperial_unit_system:
        param = SimulationParams(
            reference_geometry=ReferenceGeometry(
                moment_center=(0,0,0),
                moment_length=1.0 * u.inch,
                area=70685.83470577035 * u.inch * u.inch
            ),
            operating_condition=AerospaceCondition.from_mach(mach=0, reference_mach=0.69, thermal_state=ThermalState()),
            models=[
                Fluid(
                ),
                Wall(
                    entities=[
                        Surface(name="2"),
                    ],
                ),
                Freestream(entities=[Surface(name="1")]),
                betdisk_unsteady,
            ],
            time_stepping=Unsteady(max_pseudo_steps=25, 
                       steps=1800, 
                       step_size=2*dt_to_revolve_one_degree(rpm_hover), 
                       CFL=RampCFL(initial=100, final=10000, ramp_steps=15)
            ),
            user_defined_dynamics = [udd_instance],
        )

    print("3")
    import json
    params_as_dict = param.model_dump()
    with open('simulation_generated.json', 'w') as fh:
        json.dump(params_as_dict, fh, indent=4)

    case_json, hash = simulation_to_case_json(params_as_dict, "Imperial", {"value": 1.0, "units": "inch"})
    print(case_json)

    prefix = "testing-workbench-integration-xv15_unsteady"

    #
    volume_mesh = fl.VolumeMesh.from_file(
        "single_disk_with_sphere_zAxis_R150_290K.lb8.ugrid",
        name="xv15-BET-290k",
        solver_version=SOLVER_VERSION,
    )
    volume_mesh = volume_mesh.submit()
    # case
    params = fl.Flow360Params(**case_json, legacy_fallback=True)
    case_draft = volume_mesh.create_case(f"{prefix}-case", params, solver_version=SOLVER_VERSION)
    case = case_draft.submit()
