import flow360 as fl
from flow360.component.geometry import Geometry
from flow360.component.simulation import cloud

from flow360.component.simulation.meshing_param.params import (
    MeshingDefaults,
    MeshingParams,
)
from flow360.component.simulation.meshing_param.volume_params import (
    AutomatedFarfield,
    UniformRefinement
)
from flow360.component.simulation.meshing_param.face_params import SurfaceRefinement
from flow360.component.simulation.meshing_param.edge_params import (
    SurfaceEdgeRefinement,
    HeightBasedRefinement,
    ProjectAnisoSpacing
)
from flow360.component.simulation.models.surface_models import (
    Freestream,
    Wall,
    SlipWall
)
from flow360.component.simulation.models.volume_models import Fluid
from flow360.component.simulation.models.solver_numerics import (
    NavierStokesSolver,
    LinearSolver,
    SpalartAllmaras
)
from flow360.component.simulation.operating_condition.operating_condition import (
    create_operating_condition_from_mach_reynolds
)
from flow360.component.simulation.primitives import (
    ReferenceGeometry,
    Cylinder
)
from flow360.component.simulation.simulation_params import SimulationParams
from flow360.component.simulation.time_stepping.time_stepping import (
    Steady,
    RampCFL
)
from flow360.component.simulation.outputs.outputs import (
    SurfaceOutput,
    VolumeOutput
)
from flow360.component.simulation.unit_system import SI_unit_system, u
from flow360.examples import Tutorial_2dcrm


fl.Env.preprod.active()

SOLVER_VERSION = "workbench-24.9.3"

#you can use this to upload geometry from your computer
geometry_draft = Geometry.from_file(Tutorial_2dcrm.geometry, project_name='Tutorial 2D CRM from Python', solver_version=SOLVER_VERSION)
geometry = geometry_draft.submit()
# you can use this if geometry was submitted eariler:
#geometry = Geometry.from_cloud(id=<provide-geo-id>)

#show face and edge groupings
geometry.show_available_groupings(verbose_mode=True)
geometry.group_faces_by_tag("faceName")
geometry.group_edges_by_tag("edgeName")


with SI_unit_system:
    cylinders = [Cylinder(name=f'cylinder{i}', axis=[0,1,0], center=[0.7,0.5,0], outer_radius=outer_radius, height=1.0 ) for i, outer_radius in enumerate([1.1, 2.2, 3.3, 4.5])]
    cylinder5 = Cylinder(name='cylinder5', axis=[-1,0,0], center=[6.5,0.5,0], outer_radius=6.5, height=1.0 )
    farfield = AutomatedFarfield(name='farfield', method='quasi-3d')
    params = SimulationParams(
        meshing=MeshingParams(
            defaults=MeshingDefaults(
                surface_edge_growth_rate=1.17,
                surface_max_edge_length=1.1,
                curvature_resolution_angle=12*u.deg,
                boundary_layer_growth_rate=1.17,
                boundary_layer_first_layer_thickness=1.8487111e-06
            ),
            refinement_factor=1.35,
            gap_treatment_strength=0.5,
            volume_zones=[farfield],
            refinements=[
                UniformRefinement(name='refinement1', spacing=0.1, entities=[cylinder1]),
                UniformRefinement(name='refinement2', spacing=0.15, entities=[cylinder2]),
                UniformRefinement(name='refinement3', spacing=0.225, entities=[cylinder3]),
                UniformRefinement(name='refinement4', spacing=0.275, entities=[cylinder4]),
                UniformRefinement(name='refinement5', spacing=0.325, entities=[cylinder5]),
                SurfaceRefinement(name='wing', max_edge_length=0.74, faces=[
                    geometry['wing']
                    ]
                ),
                SurfaceRefinement(name='flap-slat', max_edge_length=0.55, faces=[
                    geometry['flap'],
                    geometry['slat']
                    ]
                ),
                #this can be done by grouping using their ID's and not the grouped names since it gets reset at the mesh step
                SurfaceRefinement(name='trailing', max_edge_length=0.36, faces=[
                    geometry['wingTrailing'],
                    geometry['flapTrailing'],
                    geometry['slatTrailing']
                    ]
                ),
                SurfaceEdgeRefinement(name='edges', method=HeightBasedRefinement(value=0.0007) ,edges=[
                    geometry['wingtrailingEdge'],
                    geometry['wingleadingEdge'],
                    geometry['flaptrailingEdge'],
                    geometry['flapleadingEdge'],
                    geometry['slattrailingEdge'],
                    geometry['slatFrontLEadingEdge']
                    ]
                ),
                SurfaceEdgeRefinement(name='symmetry', method=ProjectAnisoSpacing(), edges=[
                    geometry['symmetry']
                    ]
                )
            ]
        ),
        reference_geometry=ReferenceGeometry(
            moment_center=[0.25,0.005,0],
            moment_length=[1,1,1],
            area=0.01
        ),
        operating_condition=create_operating_condition_from_mach_reynolds(
            mach=0.2,
            reynolds=5e+6,
            temperature=272.1,
            alpha=16*u.deg,
            beta=0*u.deg
        ),
        time_stepping=Steady(
            max_steps=3000,
            CFL=RampCFL(
                initial=20,
                final=300,
                ramp_steps=500
            )
        ),
        outputs=[
            VolumeOutput(
                name='VolumeOutput',
                output_fields=[
                    'primitiveVars',
                    'vorticity',
                    'residualNavierStokes',
                    'residualTurbulence',
                    'Cp',
                    'Mach',
                    'qcriterion',
                    'mut'
                    ]
            ),
            SurfaceOutput(
                name='SurfaceOutput',
                surfaces=geometry["*"],
                output_fields=[
                    'primitiveVars',
                    'Cp',
                    'Cf',
                    'CfVec',
                    'yPlus'
                ]
            )
        ],
        models=[
            Wall(
                surfaces=[
                    geometry['wing'],
                    geometry['flap'],
                    geometry['slat'],
                    geometry['wingTrailing'],
                    geometry['flapTrailing'],
                    geometry['slatTrailing']
                ],
                name='wall'
            ),
            Freestream(
                surfaces=farfield.farfield,
                name='Freestream'
            ), 
            SlipWall(
                surfaces=farfield.symmetry_planes,
                name='slipwall'
            ),
            Fluid(
                navier_stokes_solver=NavierStokesSolver(
                    absolute_tolerance=1e-11,
                    relative_tolerance=1e-2,
                    linear_solver=LinearSolver(max_iterations=35),
                    kappa_MUSCL=0.33,
                    order_of_accuracy=2,
                    update_jacobian_frequency=4,
                    equation_evaluation_frequency=1
                ), 
                turbulence_model_solver=SpalartAllmaras(
                    absolute_tolerance=1e-10,
                    relative_tolerance=1e-2,
                    linear_solver=LinearSolver(max_iterations=25),
                    order_of_accuracy=2,
                    update_jacobian_frequency=4,
                    equation_evaluation_frequency=1
                )
            )
        ]
    )


case = cloud.run_case(geometry, params=params, draft_name="Case of tutorial 2D CRM from Python", async_mode=True)