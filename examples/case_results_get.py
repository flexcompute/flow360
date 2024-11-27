#import flow360.v1 as fl
from matplotlib.pyplot import show
import os
os.environ["FLOW360_BETA_FEATURES"] = "1"

from flow360 import *

Env.preprod.active()

my_case = Case.from_cloud("case-6ac0d1f1-7302-40f3-ac74-16b995f90633")
# res = my_case.results.nonlinear_residuals
# res.as_dataframe().plot(x="physical_step", logy=True)
# show()

monitor_result = my_case.results.monitors
monitor_names = monitor_result.monitor_names
print(monitor_names)
df_inside2 = monitor_result.get_monitor_by_name("inside2").as_dataframe()

# get the point of interest
df = df_inside2[['physical_step','inside2_Point30_p']]

# get unique value for each physical step
change_indices = df.index[df['physical_step'].diff().fillna(1) != 0][1:] - 1

result = df.loc[change_indices, ['physical_step','inside2_Point30_p']]

result.plot(x="physical_step")



