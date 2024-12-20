import flow360 as fl
from flow360.examples import OM6wing

# Step 1: Create a new project from a predefined mesh file in the Airplane example
# Download the predefined nesh file
OM6wing.get_files()
# This initializes a project with the specified geometry and assigns it a name.
project = fl.Project.from_file(OM6wing.mesh_filename, name="OM6wing Quick Start from Python")

# Access the volume mesh of the project
volume_mesh = project.volume_mesh

# Step 2: Define simulation parameters within a specific unit system
with fl.SI_unit_system:
    # Set up the main simulation parameters
    params = fl.SimulationParams(
        # Reference geometry parameters for the simulation (e.g., center of pressure)
        reference_geometry=fl.ReferenceGeometry(
            area=1.15315084119231,  # Reference area
            moment_center=[0.0, 0.0, 0.0],  # Reference moment center
            moment_length=[1.47602, 0.801672958512342, 1.47602] # Reference moment length
        ),
        # Operating conditions
        operating_condition=fl.operating_condition_from_mach_reynolds(
            reynolds=14.6e6,    # Reynolds number of 14.6e+06
            mach=0.84,  # Mach number of 0.84
            project_length_unit=fl.u.m, # Length/Grid unit for nondimensionalization
            alpha=3.06 * fl.u.deg   # Angle of attack of 3.06 degrees
        ),
        # Time-stepping configuration: specifying steady-state with a maximum step limit
        time_stepping=fl.Steady(
            max_steps=500,  # Maximum step limit
            CFL=fl.RampCFL(
                initial=5,  # Initial CFL value
                final=200,  # Final CFL value
                ramp_steps=40   # Number of steps before reaching final value starting from initial
            )
        ),
        # Define models for the simulation, such as walls and freestream conditions
        models=[
            fl.Fluid(), # Solver settings can be defined here, in this case they are default
            fl.Wall(
                name="Wall",
                surfaces=[volume_mesh["Wing"]]  # Apply no-slip wall boundary condition to Wing surfaces
            ),
            fl.SlipWall(
                ame="SlipWall",
                surfaces=[volume_mesh["Symmetry"]]  # Apply slip wall boundary condition on Symmetry
            ),
            fl.Freestream(
                name="Freestream",
                surfaces=[volume_mesh["Farfield"]]  # Apply freestream boundary condition on Farfield
            ),
        ],
        # Define output parameters for the simulation
        outputs=[
            fl.SurfaceOutput(
                output_fields=["primitiveVars", "Cp", "Cf"],    # Output fields for post-processing
                surfaces=[volume_mesh["Wing"]]  # Select Wing surfaces for output
            ),
            fl.VolumeOutput(
                output_fields=["primitiveVars", "Mach"] # Output fields for post-processing
            ),
        ],
    )

# Step 3: Run the simulation case with the specified parameters
project.run_case(params, name="Case of OM6Wing Quick Start")