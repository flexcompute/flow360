import flow360 as fl
from flow360 import u
from flow360 import log

log.set_logging_level("DEBUG")
fl.Env.uat.active()

project = fl.Project.from_cloud("prj-5f80e781-3195-4035-862a-a94ccd238995")

parent_case = fl.Case.from_cloud("case-be2bdbf6-bc83-4ef2-9a07-48c296a16eba")

param: fl.SimulationParams = parent_case.params

# fork with new angle of attack being 1.23 degrees
# param.operating_condition.reference_velocity_magnitude = 1.23 * u.m / u.s

# project.run_case(params=param, fork_from=parent_case, name="Forked case with new alpha")
project.run_case(params=param, name="Forked case with new alpha")
