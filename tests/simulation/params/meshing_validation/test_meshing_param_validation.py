import pydantic as pd
import pytest

from flow360.component.simulation.meshing_param.params import MeshingParams
from flow360.component.simulation.meshing_param.volume_params import (
    AutomatedFarfield,
    AxisymmetricRefinement,
    RotationCylinder,
    UniformRefinement,
)
from flow360.component.simulation.primitives import Cylinder, Surface
from flow360.component.simulation.simulation_params import SimulationParams
from flow360.component.simulation.unit_system import CGS_unit_system


def test_disable_multiple_cylinder_in_one_ratataion_cylinder():
    with pytest.raises(
        pd.ValidationError,
        match="Only single instance is allowed in entities for each RotationCylinder.",
    ):
        with CGS_unit_system:
            cylinder_1 = Cylinder(
                name="1",
                outer_radius=12,
                height=2,
                axis=(0, 1, 0),
                center=(0, 5, 0),
            )
            cylinder_2 = Cylinder(
                name="2",
                outer_radius=2,
                height=2,
                axis=(0, 1, 0),
                center=(0, 5, 0),
            )
            SimulationParams(
                meshing=MeshingParams(
                    volume_zones=[
                        RotationCylinder(
                            entities=[cylinder_1, cylinder_2],
                            spacing_axial=20,
                            spacing_radial=0.2,
                            spacing_circumferential=20,
                            enclosed_entities=[
                                Surface(name="hub"),
                            ],
                        ),
                        AutomatedFarfield(),
                    ],
                )
            )


def test_limit_cylinder_entity_name_length_in_rotataion_cylinder():
    with pytest.raises(
        pd.ValidationError,
        match=r"The name \(very_long_cylinder_name\) of `Cylinder` entity in `RotationCylinder`"
        + " exceeds 18 characters limit.",
    ):
        with CGS_unit_system:
            cylinder = Cylinder(
                name="very_long_cylinder_name",
                outer_radius=12,
                height=2,
                axis=(0, 1, 0),
                center=(0, 5, 0),
            )
            SimulationParams(
                meshing=MeshingParams(
                    volume_zones=[
                        RotationCylinder(
                            entities=[cylinder],
                            spacing_axial=20,
                            spacing_radial=0.2,
                            spacing_circumferential=20,
                            enclosed_entities=[
                                Surface(name="hub"),
                            ],
                        ),
                        AutomatedFarfield(),
                    ],
                )
            )


def test_reuse_of_same_cylinder():
    with pytest.raises(
        pd.ValidationError,
        match=r"The same cylinder named `I am reused` is used in both RotationCylinder and UniformRefinement.",
    ):
        with CGS_unit_system:
            cylinder = Cylinder(
                name="I am reused",
                outer_radius=1,
                height=12,
                axis=(0, 1, 0),
                center=(0, 5, 0),
            )
            SimulationParams(
                meshing=MeshingParams(
                    volume_zones=[
                        RotationCylinder(
                            entities=[cylinder],
                            spacing_axial=20,
                            spacing_radial=0.2,
                            spacing_circumferential=20,
                            enclosed_entities=[
                                Surface(name="hub"),
                            ],
                        ),
                        AutomatedFarfield(),
                    ],
                    refinements=[UniformRefinement(entities=[cylinder], spacing=0.1)],
                )
            )

    with pytest.raises(
        pd.ValidationError,
        match=r"The same cylinder named `I am reused` is used in both UniformRefinement and AxisymmetricRefinement.",
    ):
        with CGS_unit_system:
            cylinder = Cylinder(
                name="I am reused",
                outer_radius=1,
                height=12,
                axis=(0, 1, 0),
                center=(0, 5, 0),
            )
            SimulationParams(
                meshing=MeshingParams(
                    refinements=[
                        UniformRefinement(entities=[cylinder], spacing=0.1),
                        AxisymmetricRefinement(
                            entities=[cylinder],
                            spacing_axial=0.1,
                            spacing_radial=0.1,
                            spacing_circumferential=0.1,
                        ),
                    ],
                )
            )
