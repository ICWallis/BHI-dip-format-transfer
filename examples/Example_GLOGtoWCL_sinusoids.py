# %%
# Example of how to use the GLOG to WCL conversion function for sinusoids.


# %%
# Import required libraries and functions
import pandas as pd
import bhi_dip_format_transfer as dt


# %%
# Import the GLOG sinusoid file that will be converted to WCL format
geolog_test_file = r"TestData_sinusoids_GLOG_format.csv"

GLOG = pd.read_csv(
    geolog_test_file,
    na_values=['', ' ', '-999.25'], # handles expected NaN values
    skiprows=[1], # skip unit row, comment out if not present in your file
    )
GLOG.head()

# Units are currently handled manually in this method. They are first stripped
# from the import file and then manually defined and added to the WCL export file. 

# The function assumes the following header names are present in the GLOG file:
# 'DEPTH_PLANE', 'DEPTH', 'AZIMUTH', 'DIP',
# 'AZI_START', 'AZI_END', 'CATEGORY', 'NOTES'
#
# If your GLOG file uses different header names, pass them in as col_* kwargs
# instead of renaming your dataframe. For example, if your dip column is
# called 'DIP_APP' instead of 'DIP':
#   WCL = dt.glog_to_wcl_sinusoids(GLOG, col_dip='DIP_APP')
# Every required column has a matching col_* kwarg (col_depth_plane, col_depth,
# col_azi_start, col_azi_end, col_azimuth, col_dip, col_category, col_notes) -
# see the function docstring for the full list.


#%%
# Undertake the conversion from GLOG to WCL format
WCL = dt.glog_to_wcl_sinusoids(GLOG)
WCL.head()

# Output has standard header names for WCL format: 
# 'Depth', 'Azimuth', 'Dip', 'Aperture', 'Visible Azimuth Ranges', 'Type', 
# 'NOTES' is not handled in WCL and must be manually removed before import. 


# %%
# Add the correct units into the top of the dataframe. 
# The units in this case are [m, deg, deg, mm, deg, ''] for the columns 
# ['Depth', 'Azimuth', 'Dip', 'Aperture', 'Visible Azimuth Ranges', 'Type', 'NOTES']
# They may be different in your case.

WCL.loc[-1] = [
    'm', 
    'deg', 
    'deg', 
    'mm', 
    'deg', 
    '', 
    ''
    ]

WCL.index = WCL.index + 1  # shifting index
WCL = WCL.sort_index()  # sorting by index

# Export to a new CSV file called dips.csv
WCL.to_csv(r"Example_GLOGtoWCL_sinusoids__results.csv", index=False)

WCL.head()


#%% 