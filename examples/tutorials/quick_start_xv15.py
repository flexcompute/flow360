import flow360 as fl
from flow360.examples import TutorialRANSXv15

# Step 1: Create a new project from a predefined mesh file in the XV15 example
# Download the predefined mesh file
TutorialRANSXv15.get_files()
# This initializes a project with the specified mesh file and assigns it a name.
project = fl.Project.from_file(TutorialRANSXv15.mesh_filename,name="XV-15 Quick Start")

# Access the volume mesh of the project
volume_mesh = project.volume_mesh

# Step 2: Define simulation parameters within a specific unit system
with fl.SI_unit_system:
    # Define rotating cylinder based off of volume mesh entity
    rotation_zone = volume_mesh["innerRotating"]
    # Set the cylinder's center point
    rotation_zone.center = (0, 0, 0) * fl.u.m
    # Set the cylinder's axis
    rotation_zone.axis = (0, 0, -1)
    # Set up the main simulation parameters
    params = fl.SimulationParams(
        # Reference geometry parameters for the simulation (e.g., center of pressure)
        reference_geometry=fl.ReferenceGeometry(
            moment_center=(0, 0, 0),    # Reference moment center
            moment_length=(3.81, 3.81, 3.81),   # Reference moment length
            area=45.604 # Reference area
        ),
        # Operating conditions
        operating_condition=fl.AerospaceCondition(
            velocity_magnitude=5,   # Velocity of 5 m/s
            alpha=-90 * fl.u.deg,   # Angle of attack of -90 degrees meaning the flow comes from above
            reference_velocity_magnitude=238.14,    # Reference velocity of 238.14 m/s
        ),
        # Time-stepping configuration: unsteady simulation with a specified amount of physical steps
        time_stepping=fl.Unsteady(
            max_pseudo_steps=35,    # Maximum pseudo step limit
            steps=600,  # Number of physical steps
            step_size=0.5 / 600 * fl.u.s,   # Physical step size
            CFL=fl.AdaptiveCFL()    # CFL method set to adaptive with default values
        ),
        # Define output parameters for the simulation
        outputs=[
            fl.VolumeOutput(
                name="VolumeOutput",
                output_fields=["primitiveVars", "T", "Cp", "Mach", "qcriterion", "VelocityRelative"]    # Output fields for post-processing
            ),
            fl.SurfaceOutput(
                name="SurfaceOutput",
                surfaces=volume_mesh["*"],  # Select all surfaces defined in volume mesh for output
                output_fields=["primitiveVars", "Cp", "Cf", "yPlus", "nodeForcesPerUnitArea"]   # Output fields for post-processing
            ),
        ],
        # Define models for the simulation, such as walls and freestream conditions
        models=[
            # Solver settings for Navier-Stokes and turbulence
            fl.Fluid(
                navier_stokes_solver=fl.NavierStokesSolver(
                    absolute_tolerance=1e-9,    # Tolerance below which the solver goes to the next physical step for unsteady simulation
                    linear_solver=fl.LinearSolver(max_iterations=35),   # Maximum number of linear solver iterations
                    limit_velocity=True,    # Enable limiter for velocity
                    limit_pressure_density=True # Enable limiter for pressure and density
                ),
                turbulence_model_solver=fl.SpalartAllmaras(
                    absolute_tolerance=1e-8,    # Tolerance below which the solver goes to the next physical step for unsteady simulation
                    linear_solver=fl.LinearSolver(max_iterations=25),   # Maximum number of linear solver iterations
                    DDES=True,  # Enable Delayed Detached Eddy Simulation
                    rotation_correction=True,   # Enable rotation correction
                    equation_evaluation_frequency=1 # Set the frequency at which the turbulence equation is updated
                ),
            ),
            fl.Rotation(
                volumes=rotation_zone,  # Apply rotation boundary condition previously defined cylinder
                spec=fl.AngularVelocity(600 * fl.u.rpm) # Angular velocity of 600 RPM
            ),
            fl.Freestream(
                surfaces=volume_mesh["farField/farField"],  # Apply freestream boundary condition on farField/farField
                name="Freestream"
            ),
            fl.Wall(
                surfaces=volume_mesh["innerRotating/blade"],    # Apply no-slip wall boundary condition to innerRotating/blade surfaces
                name="NoSlipWall"
            ),
        ],
    )

# Step 3: Run the simulation case with the specified parameters
project.run_case(params=params, name="Case of XV-15 Quick Start")
