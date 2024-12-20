import flow360 as fl
from flow360.component.simulation.outputs.outputs import SurfaceSliceOutput
from flow360.examples import OM6wing

# Step 1: Create a new project from a predefined geometry file in the Airplane example
# Download the predefined geometry files
OM6wing.get_files()
# This initializes a project with the specified geometry and assigns it a name.
project = fl.Project.from_file(OM6wing.geometry, name="Automated Meshing Quick Start")

# Access the geometry of the project
geometry = project.geometry

# Step 2: Display available groupings in the geometry (helpful for identifying group names)
geometry.show_available_groupings(verbose_mode=True)

# Step 3: Group edges and faces by a specific tag for easier reference in defining objects
geometry.group_edges_by_tag("edgeName")
geometry.group_faces_by_tag("faceName")

# Step 4: Define simulation parameters within a specific unit system
with fl.SI_unit_system:
    # Define cylinder entities for mesh refinement
    cylinders = [
        fl.Cylinder(
            name=f"cylinder{i+1}",
            axis=[0, 1, 0],  # Axis of the cylinder
            center=[0.7, -1, 0],  # Center point of the cylinder
            outer_radius=outer_radius,  # Outer radius of the cylinder
            height=2,  # Height of the cylinder
        )
        # Create cylinder of outer radiuses 1.1, 2.2, 3.3 and 4.5
        for i, outer_radius in enumerate([1.1, 2.2, 3.3, 4.5])
    ]
    cylinder5 = fl.Cylinder(
        name="cylinder5", axis=[-1, 0, 0], center=[2, -1, 0], outer_radius=6.5, height=14.5
    )

    # Define an automated far-field boundary condition for the simulation
    farfield = fl.AutomatedFarfield(name="farfield")

    # Set up the main simulation parameters
    params = fl.SimulationParams(
        # Meshing parameters, including boundary layer and maximum edge length
        meshing=fl.MeshingParams(
            defaults=fl.MeshingDefaults(
                surface_edge_growth_rate=1.07,  # Growth rate of anisotropic layers grown from edges
                surface_max_edge_length=0.15,  # Maximum edge length on surfaces
                curvature_resolution_angle=10 * fl.u.deg,  # Maximum angle a single element can span
                boundary_layer_first_layer_thickness=1.35e-6,  # Boundary layer thickness
                boundary_layer_growth_rate=1.04,  # Growth rate of the boundary layer
            ),
            refinement_factor=1.45,  # 1.45 times finer mesh in refinement regions
            volume_zones=[farfield],  # Apply the automated far-field boundary condition
            # Local mesh refinements
            refinements=[
                fl.SurfaceEdgeRefinement(
                    edges=[
                        geometry["wingLeadingEdge"],
                        geometry["wingTrailingEdge"],
                    ],  # Apply refinement on leading and trailing edges
                    method=fl.HeightBasedRefinement(
                        value=3e-4
                    ),  # Refine the mesh to have a first layer height of 3e-04
                ),
                fl.SurfaceEdgeRefinement(
                    edges=[
                        geometry["rootAirfoilEdge"],
                        geometry["tipAirfoilEdge"],
                    ],  # Apply refinement on root and tip of the airfoil
                    method=fl.ProjectAnisoSpacing(),  # Refine the mesh to have anisotropic spacing from neighboring faces to the edge
                ),
                fl.SurfaceRefinement(
                    faces=[geometry["wing"]],  # Apply refinement to wing surfaces
                    max_edge_length=0.15,  # Refine the mesh to have maximum edge length of 0.15
                ),
                # Uniform spacing refinements for cylinders around and behind the geometry
                fl.UniformRefinement(name="refinement1", spacing=0.075, entities=[cylinders[0]]),
                fl.UniformRefinement(name="refinement2", spacing=0.1, entities=[cylinders[1]]),
                fl.UniformRefinement(name="refinement3", spacing=0.175, entities=[cylinders[2]]),
                fl.UniformRefinement(name="refinement4", spacing=0.225, entities=[cylinders[3]]),
                fl.UniformRefinement(name="refinement5", spacing=0.3, entities=[cylinder5]),
            ],
        ),
        # Reference geometry parameters for the simulation (e.g., center of pressure)
        reference_geometry=fl.ReferenceGeometry(
            area=1.15315084119231,  # Reference area
            moment_center=[0, 0, 0],  # Reference moment center
            moment_length=[1.47602, 0.801672958512342, 1.47602],  # Reference moment length
        ),
        # Operating conditions
        operating_condition=fl.operating_condition_from_mach_reynolds(
            reynolds=14.6e6,  # Reynolds number of 14.6e+06
            mach=0.84,  # Mach number of 0.84
            project_length_unit=fl.u.m,  # Length/Grid unit for nondimensionalization
            temperature=297.78,  # Temperature of 297.78 K
            alpha=3.06 * fl.u.deg,  # Angle of attack of 3.06 degrees
        ),
        # Time-stepping configuration: specifying steady-state with a maximum step limit
        time_stepping=fl.Steady(
            max_steps=5000,  # Maximum step limit
            CFL=fl.RampCFL(
                initial=1,  # Initial CFL value
                final=200,  # Final CFL value
                ramp_steps=2250,  # Number of steps before reaching final value starting from initial
            ),
        ),
        # Define models for the simulation, such as walls and freestream conditions
        models=[
            fl.Fluid(),  # Solver settings can be defined here, in this case they are default
            fl.Wall(
                surfaces=[
                    geometry["wing"]
                ],  # Apply no-slip wall boundary condition to wing surfaces
                name="NoSlipWall",
            ),
            fl.SlipWall(
                surfaces=farfield.symmetry_planes,  # Apply slip wall boundary condition on symmetry planes
                name="SlipWall",
            ),
            fl.Freestream(
                surfaces=farfield.farfield,  # Apply freestream boundary condition on farfield
                name="Freestream",
            ),
        ],
        # Define output parameters for the simulation
        outputs=[
            fl.SurfaceOutput(
                surfaces=[geometry["wing"]],  # Select wing surface for output
                output_fields=["primitiveVars", "Cp", "Cf"],  # Output fields for post-processing
            ),
            fl.VolumeOutput(
                output_fields=["primitiveVars", "Mach"]  # Output fields for post-processing
            ),
        ],
    )

# Step 5: Run the simulation case with the specified parameters
project.run_case(params, name="Automated meshing")
