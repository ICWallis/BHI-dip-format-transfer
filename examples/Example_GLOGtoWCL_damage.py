# %%
# Example of how to use the GLOG to WCL conversion function 
# for damage (sticks and boxes).


# %%
# Import required libraries and functions
import pandas as pd
import numpy as np
import bhi_dip_format_transfer as dt


# %%
# Import the GLOG damage file that will be converted to WCL format
geolog_test_file = r"TestData_damage_GLOG_format.csv"

GLOG = pd.read_csv(
    geolog_test_file,
    na_values=['', ' ', '-999.25'], # handles expected nan values
    skiprows=[1], # skips the second row which contains units
    )

# The function assumes the following header names are present in the GLOG file:
# 'DEPTH', 'AZIMUTH', 'TILT', 'HEIGHT', 'AWIDTH', 'CATEGORY', 'NOTES'
#
# If your GLOG file uses different header names, pass them in as col_* kwargs
# instead of renaming your dataframe, e.g.:
#   WCL = dt.glog_to_wcl_sticks(GLOG, col_height='HEIGHT_M')
# Every required column has a matching col_* kwarg (col_depth, col_azimuth,
# col_tilt, col_height, col_awidth, col_category, col_notes) - see the
# function docstring for the full list.


#%%
# Undertake the conversion from GLOG to WCL format
WCL = dt.glog_to_wcl_sticks(GLOG)
WCL.head()

# Output has standard header names for WCL format: 
# 'Depth', 'Azimuth', 'Tilt', 'Length', 'Opening', 'Type', 'NOTES'
# 'NOTES' is not handled in WCL and must be manually removed before import. 


# %%
# Add the correct units into the top of the dataframe. 
# The units in this case are [m, deg, deg, m, deg, '', '',] for the columns 
# ['Depth', 'Azimuth', 'Tilt', 'Length', 'Opening', 'Type', 'NOTES']
# They may be different in your case.

WCL.loc[-1] = [
    'm',
    'deg',
    'deg',
    'm',
    'deg',
    '',
    '',
    ]

WCL.index = WCL.index + 1  # shifting index
WCL = WCL.sort_index()  # sorting by index

# Export to a new CSV file
WCL.to_csv(r"Example_GLOGtoWCL_damage__results.csv", index=False)

WCL.head()

# %%