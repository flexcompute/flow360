#import flow360.v1 as fl
import os
os.environ["FLOW360_BETA_FEATURES"] = "1"
from flow360.component.project import Project
from flow360.component.simulation.meshing_param.params import (
    MeshingDefaults,
    MeshingParams,
)
from flow360.component.simulation.meshing_param.volume_params import AutomatedFarfield
from flow360.component.simulation.models.surface_models import Freestream, Wall
from flow360.component.simulation.operating_condition.operating_condition import (
    AerospaceCondition,
)
from flow360.component.simulation.outputs.outputs import SurfaceOutput
from flow360.component.simulation.primitives import ReferenceGeometry
from flow360.component.simulation.simulation_params import SimulationParams
from flow360.component.simulation.time_stepping.time_stepping import Steady, Unsteady
from flow360.component.simulation.unit_system import SI_unit_system, u
from flow360.examples import Airplane
from flow360 import *
import numpy as np
import math

Env.preprod.active()
project_name = "xiao_v4_step_11"

# diameter of each finger hole is 9.5mm
finger_hole_diameter_in_mm = 9.5
length_flute_in_mm = 608

project = Project.from_file("../../Xiao_v4.stp", name=project_name, length_unit="mm")

geometry = project.geometry
geometry.show_available_groupings(verbose_mode=True)
geometry.group_faces_by_tag("faceId")

finger_hole_center_list_z_in_mm = [270, 310, 336, 356, 416, 440, 466, 496]
finger_porous_medium_size_in_mm = (finger_hole_diameter_in_mm+1, 4, finger_hole_diameter_in_mm+1)
finger_hole_boxes = []
for index, center_z in enumerate(finger_hole_center_list_z_in_mm):
    box = Box(
        name=f"finger_hole_{index}",
        center=(0, 18, center_z)*u.mm,
        size=finger_porous_medium_size_in_mm*u.mm
    )
    finger_hole_boxes.append(box)
        

lips_boxes=[
    Box(
        name="lip_down",
        center=(0,-7,-10)*u.mm,
        size=(40,20,25)*u.mm
    ),
    Box(
        name="lip_up",
        center=(0,18.5,-19.5)*u.mm,
        size=(40,20,25)*u.mm
    )
]

blow_angle_degree = 20

        
thermal_state = ThermalState(temperature=288.15*u.Kelvin)
acoustics_pressure = thermal_state.density * thermal_state.speed_of_sound**2

# create points for monitoring purpose

monitor_points_inside = []
for index, z_in_mm in enumerate(np.linspace(0, length_flute_in_mm*1.3, num=30)):
    point = Point(name=f"axial_point_{index}", location=(0,0,z_in_mm)*u.mm)
    monitor_points_inside.append(point)


with SI_unit_system:
    params = SimulationParams(
        meshing=MeshingParams(
            defaults=MeshingDefaults(
                boundary_layer_first_layer_thickness=1e-2*u.mm, surface_max_edge_length=10*u.mm
            ),
            volume_zones=[AutomatedFarfield()],
        ),
        reference_geometry=ReferenceGeometry(),
        operating_condition=AerospaceCondition(velocity_magnitude=1*u.m/u.s, alpha=0 * u.deg),
        time_stepping=Unsteady(
            steps=8000,
            max_pseudo_steps=25,
            #step_size=1.2637867647058825e-05*u.s,
            step_size=2.0e-05*u.s,
            CFL=AdaptiveCFL.default_unsteady(),
        ),
        models=[
            Wall(
                surfaces=[geometry["*"]],
                name="Wall",
            ),
            Freestream(surfaces=[AutomatedFarfield().farfield], name="Freestream"),
            PorousMedium(
                name="fingers",
                entities=finger_hole_boxes,
                darcy_coefficient= (1e6,1e6,1e6),
                forchheimer_coefficient=(5,5,5),
            ),
            PorousMedium(
                name="lips",
                entities=lips_boxes,
                darcy_coefficient= (1e6,1e6,1e6),
                forchheimer_coefficient=(5,5,5),
            ),
            ActuatorDisk(
                name="mouth_actuator_disk",
                entities=[Cylinder(
                    name="mouth",
                    axis=(0,
                          -math.sin(math.radians(blow_angle_degree)),
                          -math.cos(math.radians(blow_angle_degree))),
                    center=(0,4,-7)*u.mm,
                    height=3*u.mm,
                    outer_radius=8*u.mm,
                )],
                force_per_area = ForcePerArea(
                    radius=(0, 12, 14)*u.mm,
                    thrust=(0.0005,0.0005,0)*acoustics_pressure,
                    circumferential=(0,0,0),
                ),
            ),
        ],
        outputs=[
            SurfaceOutput(name="all_surfaces", surfaces=geometry["*"], output_fields=["Cp", "Cf", "yPlus", "CfVec"]),
            ProbeOutput(name="outside1", 
                        output_fields=["primitiveVars", "Cp"], 
                        entities=[
                Point(name="point1", location=(0,300,length_flute_in_mm)*u.mm),
            ]),
            ProbeOutput(name="axial_monitor_points", 
                        output_fields=["primitiveVars", "Cp"], 
                        entities=monitor_points_inside
            ),
            AeroAcousticOutput(
                name="aero_acoustics_observers",
                observers=[
                (0, 550, length_flute_in_mm)*u.mm,
                (0,0,length_flute_in_mm)*u.mm
            ]),
        ],
    )

project.run_case(params=params, name=project_name)
