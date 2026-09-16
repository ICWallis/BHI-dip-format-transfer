# %%
# Example of how to use the WCL to GLOG conversion function for sinusoids.


# %%
# Import required libraries and functions
import pandas as pd
import bhi_dip_format_transfer as dt


# %%
# Import the WCL sinusoid file that will be converted to GLOG format
dips_filename = r"TestData_sinusoids_WCL_format.csv"

WCL = pd.read_csv(
    dips_filename, 
    na_values=['', ' ', '-999.25'], # Handle standard nan values
    skiprows=[1], # Skip the second row which contains units
    )

WCL.head()

# Units are currently handled manually in this method. They are first stripped
# from the import file and then manually defined and added to the WCL export file. 

# The function assumes the following header names are present in the WCL file:
# 'Depth', 'Feature Depth', 'Azimuth', 'Dip', 'Type', 'Visible Azimuth Ranges', 'Aperture'
# 'Notes' is optional; if missing, a blank NOTES column is created in the output.
#
# If your WCL file uses different header names, pass them in as col_* kwargs
# instead of renaming your dataframe, e.g.:
#   GLOG = dt.wcl_to_glog_sinusoids(WCL, col_dip='Dip_Apparent')
# Every column has a matching col_* kwarg (col_depth, col_feature_depth,
# col_azimuth, col_dip, col_type, col_visible_azimuth_ranges, col_aperture,
# col_notes) - see the function docstring for the full list.


# %%
# Example usage for the appended function (original workflow above is unchanged).
GLOG = dt.wcl_to_glog_sinusoids(WCL)
GLOG.head()

# Output has standard header names for GLOG format: 
# 'DEPTH', 'DEPTH_PLANE', 'AZIMUTH', 'DIP', 'AZI_END', 
# 'AZI_START', 'CATEGORY', 'NOTES', 'Aperture'

# Aperture is not handled in GLOG in the same way as WCL and may need to be
# removed before importing the data into GLOG.


# %%
# Add the correct units into the top of the dataframe. 
# The units in this case are [m, deg, deg, mm, deg, ''] for the columns 
# 'DEPTH', 'DEPTH_PLANE', 'AZIMUTH', 'DIP', 'AZI_END', 'AZI_START', 'CATEGORY', 'NOTES', 'Aperture'
# They may be different in your case.

GLOG.loc[-1] = [
    'm', 
    'm', 
    'deg', 
    'deg', 
    'deg', 
    'deg', 
    '',  
    '', 
    'mm'
    ]

GLOG.index = GLOG.index + 1  # shifting index
GLOG = GLOG.sort_index()  # sorting by index

GLOG.to_csv(r"Example_WCLtoGLOG_sinusoids__results.csv", index=False)

GLOG.head()


# %%
