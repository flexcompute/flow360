import pytest

import flow360.component.simulation.units as u
from flow360.component.simulation.models.material import Air, Sutherland
from flow360.component.simulation.models.solver_numerics import (
    LinearSolver,
    NavierStokesSolver,
    NoneSolver,
)
from flow360.component.simulation.models.surface_models import (
    Freestream,
    SlipWall
)

from flow360.component.simulation.models.volume_models import (
    BETDisk,
    Fluid,
    NavierStokesInitialCondition)

from flow360.component.simulation.operating_condition import (
    AerospaceCondition,
    ThermalState
)
from flow360.component.simulation.outputs.outputs import SurfaceOutput, VolumeOutput
from flow360.component.simulation.primitives import Cylinder, ReferenceGeometry, Surface
from flow360.component.simulation.simulation_params import SimulationParams
from flow360.component.simulation.unit_system import (
    LengthType,
    ViscosityType,
    SI_unit_system,
)

from flow360.component.simulation.time_stepping.time_stepping import RampCFL, Unsteady

def create_vortex_propagation_freestream_surfaces():
    return [Surface(name="Zone 7/7BOTTOM"),
            Surface(name="Zone 7/7EXIT"),
            Surface(name="Zone 7/7INLET"),
            Surface(name="Zone 7/7TOP")]

def create_initial_condition():
    U_inf = 0.5
    P_inf = 1.0/1.4
    T_inf = 1.0;
    Beta = 1.0/5
    Radius = 1
    Cp = 1.0/(1.4 - 1)
    Rgas = 1.0/1.4
    Xc = 0.0
    Yc = 0.0
    alpha = 0.0
    return NavierStokesInitialCondition(rho=f"{P_inf}/({Rgas}*{T_inf})*pow(({T_inf}-({U_inf}*{U_inf}*{Beta}*{Beta})/(2*{Cp})*exp(-(pow(x-{Xc},2)+pow(y-{Yc},2))/({Radius}*{Radius})))/{T_inf},1/(1.4-1.))",
                                        u=f"{U_inf}*{Beta}*exp(-0.5*(pow(x-{Xc}, 2)+pow(y-{Yc},2))/({Radius}*{Radius}))/{Radius}*(-1*(y-{Yc})) + cos({alpha})*{U_inf}",
                                        v=f"{U_inf}*{Beta}*exp(-0.5*(pow(x-{Xc},2)+pow(y-{Yc},2))/({Radius}*{Radius}))/{Radius}*(x-{Xc}) + sin({alpha})*{U_inf}",
                                        w="0",
                                        p=f"{P_inf}/({Rgas}*{T_inf})*pow(({T_inf}-({U_inf}*{U_inf}*{Beta}*{Beta})/(2*{Cp})*exp(-(pow(x-{Xc}, 2)+pow(y-{Yc}, 2))/({Radius}*{Radius})))/{T_inf},1/(1.4-1.)) * {Rgas} * ({T_inf}-({U_inf}*{U_inf}*{Beta}*{Beta})/(2*{Cp})*exp(-(pow(x-{Xc}, 2)+pow(y-{Yc}, 2))/({Radius}*{Radius})))")


default_thermal_state = ThermalState()

def append_vortex_propagation_boundaries(params):
    params.models.append(Freestream(entities=create_vortex_propagation_freestream_surfaces()))
    params.models.append(SlipWall(entities=[Surface(name="Zone 7/7FRONT"),
                                            Surface(name="Zone 7/7BACK")]))
    


def apply_vortex_propagation_time_stepping(params):
    params.time_stepping = Unsteady(
        steps=16,
        step_size= 0.25 * u.m / params.operating_condition.thermal_state.speed_of_sound,
        max_pseudo_steps=10,
        CFL=RampCFL(initial=100, final=1000, ramp_steps=10))

def append_periodic_euler_vortex_boundaries(params):
    params.models.append(SlipWall(entities=[Surface(name="VOLUME/BACK"),
                                            Surface(name="VOLUME/FRONT")]))

def apply_periodic_euler_vortex_time_stepping(params):
    params.time_stepping = Unsteady(
        steps=800,
        step_size= 0.125 * u.m / params.operating_condition.thermal_state.speed_of_sound,
        max_pseudo_steps=20,
        CFL=RampCFL(initial=100, final=10000, ramp_steps=5))

def create_vortex_base():
    with SI_unit_system:
        params = SimulationParams(
            reference_geometry=ReferenceGeometry(
                moment_center=(0, 0, 0),
                moment_length=1 * u.m,
                area=1.0 * u.m * u.m,
            ),
            operating_condition=AerospaceCondition.from_mach(
                mach=0.5,
                alpha=0 * u.deg,
                thermal_state=ThermalState(
                    temperature=288.18,
                    material=Air(dynamic_viscosity=Sutherland(
                            reference_temperature=default_thermal_state.temperature,
                            reference_viscosity=0,
                            effective_temperature=default_thermal_state.material.dynamic_viscosity.effective_temperature,
                        )
                    )
                )
            ),
            models=[
                Fluid(
                    navier_stokes_solver=NavierStokesSolver(
                        absolute_tolerance=1e-9,
                        linear_solver=LinearSolver(max_iterations=25),
                        kappa_MUSCL=-1.0,
                        update_jacobian_frequency=4,
                    ),
                    turbulence_model_solver=NoneSolver(),
                    initial_condition=create_initial_condition(),
                )
            ],
            outputs=[
                VolumeOutput(
                    output_format="paraview",
                    output_fields=["primitiveVars"],
                ),
                SurfaceOutput(
                    output_format="paraview",
                    output_fields=[]
                )
            ],
        )
    return params


@pytest.fixture
def create_vortex_propagation_param():
    """
       parameters for running Euler vortex propagation case with freestream
       boundary conditions.
    """
    params = create_vortex_base()
    apply_vortex_propagation_time_stepping(params)
    append_vortex_propagation_boundaries(params)
    
    return params

@pytest.fixture
def create_periodic_euler_vortex_param():
    """
       parameters for running Euleler vortex propagation case with 
       periodic boundary conditions..
    """
    params = create_vortex_base()
    apply_periodic_euler_vortex_time_stepping(params)
    append_periodic_euler_vortex_boundaries(params)
    
    return params

