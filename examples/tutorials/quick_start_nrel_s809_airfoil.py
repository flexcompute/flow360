import flow360 as fl
from flow360.examples import NRELS809

# Step 1: Create a new project from a predefined geometry file in the NRELS809 example
# Download the predefined geometry file
NRELS809.get_files()
# This initializes a project with the specified geometry and assigns it a name.
project = fl.Project.from_file(NRELS809.geometry, name="NREL S809 Quick Start")

# Access the geometry of the project
geometry = project.geometry

# Step 2: Display available groupings in the geometry (helpful for identifying group names)
geometry.show_available_groupings(verbose_mode=True)

# Step 3: Group edges and faces by a specific tag for easier reference in defining objects
geometry.group_faces_by_tag("faceName")
geometry.group_edges_by_tag("edgeName")

# Step 4: Define simulation parameters within a specific unit system
with fl.SI_unit_system:
    # Define cylinder entities for mesh refinement
    cylinders = [
        fl.Cylinder(
            name=f"cylinder{i+1}",
            axis=[0, 1, 0], # Axis of the cylinder
            center=[0.7, 0.5, 0],   # Center point of the cylinder
            outer_radius=outer_radius,  # Outer radius of the cylinder
            height=1.0  # Height of the cylinder
        )
        # Create cylinder of outer radiuses 1.1, 2.2, 3.3 and 4.5
        for i, outer_radius in enumerate([1.1, 2.2, 3.3, 4.5])
    ]
    cylinder5 = fl.Cylinder(
        name="cylinder5", axis=[-1, 0, 0], center=[2, 0.5, 0], outer_radius=6.5, height=14.5
    )

    # Define an automated far-field boundary condition for the simulation
    farfield = fl.AutomatedFarfield(
        name="farfield",
        method="quasi-3d"   # Generates a thin disk for quasi-3D cases with both of its sides being symmetry planes
    )

    # Set up the main simulation parameters
    params = fl.SimulationParams(
        # Meshing parameters, including boundary layer and maximum edge length
        meshing=fl.MeshingParams(
            defaults=fl.MeshingDefaults(
                surface_edge_growth_rate=1.08,  # Growth rate of anisotropic layers grown from edges
                surface_max_edge_length=0.58,   # Maximum edge length on surfaces
                curvature_resolution_angle=10 * fl.u.deg,   # Maximum angle a single element can span
                boundary_layer_growth_rate=1.04,    # Boundary layer thickness
                boundary_layer_first_layer_thickness=4.29e-06   # Growth rate of the boundary layer
            ),
            volume_zones=[farfield],    # Apply the automated far-field boundary condition
            # Local mesh refinements
            refinements=[
                fl.SurfaceEdgeRefinement(
                    name="edges",
                    method=fl.HeightBasedRefinement(value=4e-04),
                    edges=[geometry["wingleadingEdge"], geometry["wingtrailingEdge"]]   # Apply refinement on leading and trailing edges
                ),
                fl.SurfaceEdgeRefinement(
                    name="symmetry",
                    method=fl.ProjectAnisoSpacing(),    # Refine the mesh to have maximum edge length of 0.15
                    edges=[geometry["symmetry"]]    # Apply refinement on the symmetry edges of the geometry
                ),
                # Uniform spacing refinements for cylinders around and behind the geometry
                fl.UniformRefinement(name="refinement1", spacing=0.08, entities=[cylinders[0]]),
                fl.UniformRefinement(name="refinement2", spacing=0.13, entities=[cylinders[1]]),
                fl.UniformRefinement(name="refinement3", spacing=0.2, entities=[cylinders[2]]),
                fl.UniformRefinement(name="refinement4", spacing=0.25, entities=[cylinders[3]]),
                fl.UniformRefinement(name="refinement5", spacing=0.29, entities=[cylinder5]),
                fl.SurfaceRefinement(name="wing", max_edge_length=0.4, faces=[geometry["wing"]])
            ],
        ),
        # Reference geometry parameters for the simulation (e.g., center of pressure)
        reference_geometry=fl.ReferenceGeometry(
            moment_center=[0.25, 0, 0], # Reference moment center
            moment_length=[1, 1, 1],    # Reference moment length
            area=0.01   # Reference area
        ),
        # Operating conditions
        operating_condition=fl.operating_condition_from_mach_reynolds(
            mach=0.15,  # Mach number of 0.15
            reynolds=2e06,  # Reynolds number of 2.0e+06
            project_length_unit=1 * fl.u.m, # Length/Grid unit for nondimensionalization
            temperature=293.15, # Temperature of 293.15 K
            alpha=5.13 * fl.u.deg   # Angle of attack of 3.06 degrees
        ),
        # Time-stepping configuration: specifying steady-state with a maximum step limit
        time_stepping=fl.Steady(
            max_steps=5000, # Maximum step limit
            CFL=fl.RampCFL(
                initial=20, # Initial CFL value
                final=200,  # Final CFL value
                ramp_steps=100  # Number of steps before reaching final value starting from initial
            )
        ),
        # Define models for the simulation, such as walls and freestream conditions
        models=[
            fl.Wall(
                surfaces=[geometry["*"]],   # Apply no-slip wall boundary condition to all surfaces
                name="wall"
            ),
            fl.Freestream(
                surfaces=farfield.farfield, # Apply freestream boundary condition on farfield
                name="Freestream"
            ),
            fl.SlipWall(
                surfaces=farfield.symmetry_planes,  # Apply slip wall boundary condition on symmetry planes
                name="slipwall"
            ),
            # Solver settings for Navier-Stokes and turbulence
            fl.Fluid(
                navier_stokes_solver=fl.NavierStokesSolver(
                    absolute_tolerance=1e-11,   # Tolerance below which the solver finishes the simulation for steady case
                    linear_solver=fl.LinearSolver(max_iterations=35),   # Maximum number of linear solver iterations
                    kappa_MUSCL=0.33    # Kappa value for the MUSCL scheme
                ),
                turbulence_model_solver=fl.SpalartAllmaras(
                    absolute_tolerance=1e-10,   # Tolerance below which the solver finishes the simulation for steady case
                    linear_solver=fl.LinearSolver(max_iterations=25)    # Maximum number of linear solver iterations
                ),
            ),
        ],
        # Define output parameters for the simulation
        outputs=[
            fl.VolumeOutput(
                name="fl.VolumeOutput",
                output_fields=["primitiveVars", "Mach"] # Output fields for post-processing
            ),
            fl.SurfaceOutput(
                name="fl.SurfaceOutput",
                surfaces=geometry["*"], # Select all surfaces for output
                output_fields=["primitiveVars", "Cp", "Cf"] # Output fields for post-processing
            ),
        ],
    )

# Step 5: Run the simulation case with the specified parameters
project.run_case(params=params, name="Case of NREL S809 Quick Start")
