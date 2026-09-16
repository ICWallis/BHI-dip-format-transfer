import pandas as pd
import numpy as np
import math

def glog_to_wcl_sinusoids(glog: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Convert sinusoid dip picks from Geolog (GLOG) convention to WellCAD (WCL) convention.

    This function handles both complete and partial sinusoid dip picks, ensuring
    proper conversion of depth and azimuth information from GLOG to WCL format.
    The output dataframe is structured to align with WellCAD's expected column
    conventions. Input column names can be customized via keyword arguments if 
    they differ from the defaults.

    Args:
        glog (pd.DataFrame): Input Geolog dataframe. Required columns are:
            - DEPTH_PLANE
            - DEPTH
            - AZI_START
            - AZI_END
            - AZIMUTH
            - DIP
            - CATEGORY
            - NOTES

    Kwargs:
        round_decimals (int, optional): Number of decimals used when rounding
            AZI_START and AZI_END before building the visible azimuth range.
            Defaults to 1.    
        aperture_value (int | float, optional): Constant value assigned to the
            output Aperture column. Defaults to 0.
        empty_azi_range_value (str, optional): Replacement value for rows where
            both AZI_START and AZI_END are missing (rendered as "nan-nan").
            Defaults to a single blank space " ".
        azi_range_separator (str, optional): Separator used to combine AZI_START
            and AZI_END into the WCL visible azimuth range. Defaults to "-".
        col_depth_plane (str, optional): Column name holding GLOG DEPTH_PLANE.
            Defaults to "DEPTH_PLANE".
        col_depth (str, optional): Column name holding GLOG DEPTH. Defaults to
            "DEPTH".
        col_azi_start (str, optional): Column name holding GLOG AZI_START.
            Defaults to "AZI_START".
        col_azi_end (str, optional): Column name holding GLOG AZI_END. Defaults
            to "AZI_END".
        col_azimuth (str, optional): Column name holding GLOG AZIMUTH. Defaults
            to "AZIMUTH".
        col_dip (str, optional): Column name holding GLOG DIP. Defaults to "DIP".
        col_category (str, optional): Column name holding GLOG CATEGORY.
            Defaults to "CATEGORY".
        col_notes (str, optional): Column name holding GLOG NOTES. Defaults to
            "NOTES".

    Returns:
        pd.DataFrame: WCL-formatted dataframe with columns:
            Depth, Azimuth, Dip, Aperture, Visible Azimuth Ranges, Type, NOTES.

    Conventions:
        - Unit rows are intentionally not handled here. Add/remove units outside
          this function as needed by import/export workflows.
        - WCL Depth is derived from Geolog DEPTH_PLANE, with missing DEPTH_PLANE
          infilled from DEPTH.
        - Partial sinusoids (start/end azimuth provided):
          DEPTH_PLANE maps to WCL Depth and DEPTH maps to WCL Feature Depth.
        - Complete sinusoids (no start/end azimuth):
          DEPTH_PLANE is typically empty; DEPTH is used as both WCL Depth and
          WCL Feature Depth after infill.
        - Only WCL Depth is produced here because WCL computes feature depth
          based on CALA during interpretation.
    """
    round_decimals = kwargs.get('round_decimals', 1)
    aperture_value = kwargs.get('aperture_value', 0)
    empty_azi_range_value = kwargs.get('empty_azi_range_value', ' ')
    azi_range_separator = kwargs.get('azi_range_separator', '-')

    col_depth_plane = kwargs.get('col_depth_plane', 'DEPTH_PLANE')
    col_depth = kwargs.get('col_depth', 'DEPTH')
    col_azi_start = kwargs.get('col_azi_start', 'AZI_START')
    col_azi_end = kwargs.get('col_azi_end', 'AZI_END')
    col_azimuth = kwargs.get('col_azimuth', 'AZIMUTH')
    col_dip = kwargs.get('col_dip', 'DIP')
    col_category = kwargs.get('col_category', 'CATEGORY')
    col_notes = kwargs.get('col_notes', 'NOTES')

    # Normalize input column names to the canonical names used below, so
    # callers can pass GLOG files with varying header conventions.
    glog_processed = glog.rename(columns={
        col_depth_plane: 'DEPTH_PLANE',
        col_depth: 'DEPTH',
        col_azi_start: 'AZI_START',
        col_azi_end: 'AZI_END',
        col_azimuth: 'AZIMUTH',
        col_dip: 'DIP',
        col_category: 'CATEGORY',
        col_notes: 'NOTES',
    }).copy()

    # Infill DEPTH_PLANE for complete sinusoids where only DEPTH is available.
    glog_processed = glog_processed.fillna({'DEPTH_PLANE': glog_processed['DEPTH']})

    # Build WCL visible azimuth range from rounded start/end values.
    glog_processed['AZI_START'] = glog_processed['AZI_START'].round(round_decimals)
    glog_processed['AZI_END'] = glog_processed['AZI_END'].round(round_decimals)
    glog_processed['AZI_RANGE'] = (
        glog_processed['AZI_START'].astype(str)
        + azi_range_separator
        + glog_processed['AZI_END'].astype(str)
    )
    glog_processed['AZI_RANGE'] = glog_processed['AZI_RANGE'].replace(
        'nan' + azi_range_separator + 'nan',
        empty_azi_range_value,
    )

    # Aperture is kept as a constant placeholder for this transfer format.
    glog_processed['APERTURE'] = aperture_value

    wcl = glog_processed[[
        'DEPTH_PLANE',
        'AZIMUTH',
        'DIP',
        'APERTURE',
        'AZI_RANGE',
        'CATEGORY',
        'NOTES',
    ]].copy()

    wcl.rename(columns={
        'DEPTH_PLANE': 'Depth',
        'AZIMUTH': 'Azimuth',
        'DIP': 'Dip',
        'APERTURE': 'Aperture',
        'AZI_RANGE': 'Visible Azimuth Ranges',
        'CATEGORY': 'Type',
    }, inplace=True)

    return wcl


def process_azimuth_range(row):
    if isinstance(row, str):
        parts = row.strip().split('-')
        if len(parts) == 2:
            # Standard format: start-end
            return pd.Series({
                'Azi Range Start': float(parts[0]), 
                'Azi Range End': float(parts[1]),
                # 'Azi Range Start__second': np.nan, 
                # 'Azi Range End__second': np.nan
            })
        elif len(parts) == 4:
            # Extended format: start1-end1-start2-end2
            print(f"Warning: Two visible azimuth ranges: {row}")
            return pd.Series({
                'Azi Range Start': float(parts[0]), 
                'Azi Range End': float(parts[1]),
                # 'Azi Range Start__second': float(parts[2]), 
                # 'Azi Range End__second': float(parts[3])
            })
        else:
            # Handle unexpected format
            print(f"Warning: Unexpected format in row: {row}")
            return pd.Series({
                'Azi Range Start': np.nan, 
                'Azi Range End': np.nan,
                # 'Azi Range Start__second': np.nan, 
                # 'Azi Range End__second': np.nan
            })
    else:
        return pd.Series({
            'Azi Range Start': np.nan, 
            'Azi Range End': np.nan,
            # 'Azi Range Start__second': np.nan, 
            # 'Azi Range End__second': np.nan
        })

def wcl_to_glog_sinusoids(wcl: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Convert sinusoid dip picks from WellCAD (WCL) convention to Geolog (GLOG) convention.

    This function ensures that the sinusoid dip picks are correctly transformed 
    from the WellCAD convention to the Geolog convention, maintaining the 
    integrity of depth, azimuth, and dip information. The output dataframe is 
    structured to align with GeoLOG's expected column conventions. If column 
    names in the input dataframe differ from the defaults, they can be specified 
    via keyword arguments.

    Args:
        wcl (pd.DataFrame): Input WellCAD dataframe. Required columns are:
            - Depth
            - Feature Depth
            - Azimuth
            - Dip
            - Type
            - Visible Azimuth Ranges
            - Aperture

    Kwargs:
        empty_visible_range_value (str, optional): Value treated as empty in
            the input Visible Azimuth Ranges column before parsing. Defaults
            to a single blank space " ".
        nan_fill_value (int | float, optional): Value used to replace NaN in
            the final GLOG output. Defaults to -999.25.
        col_depth (str, optional): Column name holding WCL Depth. Defaults to
            "Depth".
        col_feature_depth (str, optional): Column name holding WCL Feature
            Depth. Defaults to "Feature Depth".
        col_azimuth (str, optional): Column name holding WCL Azimuth. Defaults
            to "Azimuth".
        col_dip (str, optional): Column name holding WCL Dip. Defaults to "Dip".
        col_type (str, optional): Column name holding WCL Type. Defaults to
            "Type".
        col_visible_azimuth_ranges (str, optional): Column name holding WCL
            Visible Azimuth Ranges. Defaults to "Visible Azimuth Ranges".
        col_aperture (str, optional): Column name holding WCL Aperture.
            Defaults to "Aperture".
        col_notes (str, optional): Column name holding WCL Notes. This column
            is optional in the input; if absent, NOTES is created and filled
            with NaN. Defaults to "Notes".

    Returns:
        pd.DataFrame: GLOG-formatted dataframe with columns:
            DEPTH, DEPTH_PLANE, AZIMUTH, DIP, AZI_END, AZI_START,
            CATEGORY, NOTES, Aperture.

    Conventions:
        - Unit rows are intentionally not handled here. Add/remove units
          outside this function as needed by import/export workflows.
        - Visible Azimuth Ranges values are parsed into Azi Range Start and
          Azi Range End using the same parsing behavior as the script-level
          process_azimuth_range helper.
        - If Azi Range Start is missing, the sinusoid is treated as complete:
          DEPTH is assigned from Depth and DEPTH_PLANE is left as missing.
        - If Azi Range Start is present, the sinusoid is treated as partial:
          DEPTH is assigned from Feature Depth and DEPTH_PLANE from Depth.
        - If NOTES does not exist, it is created and filled with NaN before
          renaming/subselection.
        - Final NaN values are replaced with the configured nan_fill_value.
        - Aperture is included from the WCL input but is not handled in GLOG.
          in the same way as WCL. This may need to be deleted before importing
          the data into GLOG. 
    """
    empty_visible_range_value = kwargs.get('empty_visible_range_value', ' ')
    nan_fill_value = kwargs.get('nan_fill_value', -999.25)

    col_depth = kwargs.get('col_depth', 'Depth')
    col_feature_depth = kwargs.get('col_feature_depth', 'Feature Depth')
    col_azimuth = kwargs.get('col_azimuth', 'Azimuth')
    col_dip = kwargs.get('col_dip', 'Dip')
    col_type = kwargs.get('col_type', 'Type')
    col_visible_azimuth_ranges = kwargs.get('col_visible_azimuth_ranges', 'Visible Azimuth Ranges')
    col_aperture = kwargs.get('col_aperture', 'Aperture')
    col_notes = kwargs.get('col_notes', 'Notes')

    # Normalize input column names to the canonical names used below, so
    # callers can pass WCL files with varying header conventions.
    wcl_processed = wcl.rename(columns={
        col_depth: 'Depth',
        col_feature_depth: 'Feature Depth',
        col_azimuth: 'Azimuth',
        col_dip: 'Dip',
        col_type: 'Type',
        col_visible_azimuth_ranges: 'Visible Azimuth Ranges',
        col_aperture: 'Aperture',
        col_notes: 'Notes',
    }).copy()
    wcl_processed['Visible Azimuth Ranges'] = wcl_processed[
        'Visible Azimuth Ranges'
    ].replace(empty_visible_range_value, pd.NA)

    wcl_processed[[
        'Azi Range Start',
        'Azi Range End',
    ]] = wcl_processed['Visible Azimuth Ranges'].apply(process_azimuth_range)

    wcl_processed['GLG_Depth'] = np.nan
    wcl_processed['GLG_Depth_Plane'] = np.nan

    # Keep row-wise logic aligned with the original transformation block.
    for index, row in wcl_processed.iterrows():
        if pd.isna(row['Azi Range Start']):
            wcl_processed.at[index, 'GLG_Depth'] = row['Depth']
            wcl_processed.at[index, 'GLG_Depth_Plane'] = None
        else:
            wcl_processed.at[index, 'GLG_Depth'] = row['Feature Depth']
            wcl_processed.at[index, 'GLG_Depth_Plane'] = row['Depth']

    if 'Notes' not in wcl_processed.columns:
        wcl_processed['Notes'] = np.nan

    wcl_processed.rename(columns={
        'GLG_Depth': 'DEPTH',
        'GLG_Depth_Plane': 'DEPTH_PLANE',
        'Azimuth': 'AZIMUTH',
        'Dip': 'DIP',
        'Type': 'CATEGORY',
        'Notes': 'NOTES',
        'Azi Range Start': 'AZI_START',
        'Azi Range End': 'AZI_END',
    }, inplace=True)

    glog = wcl_processed[[
        'DEPTH',
        'DEPTH_PLANE',
        'AZIMUTH',
        'DIP',
        'AZI_END',
        'AZI_START',
        'CATEGORY',
        'NOTES',
        'Aperture',
    ]].copy()

    glog.fillna(nan_fill_value, inplace=True)

    return glog


def glog_to_wcl_sticks(glog: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Convert stick (damage) picks from Geolog (GLOG) convention to WellCAD (WCL) convention.

    The function assumes that the input dataframe follows the GLOG column conventions.
    If the column names in the input dataframe differ from the defaults, 
    they can be specified via keyword arguments.

    Args:
        glog (pd.DataFrame): Input Geolog dataframe. Required columns are:
            - DEPTH
            - AZIMUTH
            - TILT
            - HEIGHT
            - AWIDTH
            - CATEGORY
            - NOTES

    Kwargs:
        tilt_fill_value (int | float, optional): Value used to replace missing
            tilt values after the GLOG to WCL sign conversion. Defaults to 0.
        tilt_zero_threshold (int | float, optional): Tilt values below this
            threshold are snapped to zero, which removes near-vertical noise
            introduced by the sign conversion. Defaults to 0.1.
        opening_fill_value (int | float, optional): Value used to replace
            missing AWIDTH (WCL Opening) values. Defaults to 0.
        col_depth (str, optional): Column name holding GLOG DEPTH. Defaults to
            "DEPTH".
        col_azimuth (str, optional): Column name holding GLOG AZIMUTH. Defaults
            to "AZIMUTH".
        col_tilt (str, optional): Column name holding GLOG TILT. Defaults to
            "TILT".
        col_height (str, optional): Column name holding GLOG HEIGHT. Defaults
            to "HEIGHT".
        col_awidth (str, optional): Column name holding GLOG AWIDTH. Defaults
            to "AWIDTH".
        col_category (str, optional): Column name holding GLOG CATEGORY.
            Defaults to "CATEGORY".
        col_notes (str, optional): Column name holding GLOG NOTES. Defaults to
            "NOTES".

    Returns:
        pd.DataFrame: WCL-formatted dataframe with columns:
            Depth, Azimuth, Tilt, Length, Opening, Type, NOTES.

    Conventions:
        - Unit rows are intentionally not handled here. Add/remove units outside
          this function as needed by import/export workflows.
        - GLOG and WCL measure tilt in opposite directions relative to the
          borehole axis, so GLOG TILT is negated to produce WCL Tilt.
        - The tilt threshold test is a simple "less than" comparison, so any
          tilt that remains negative after the sign conversion is also snapped
          to zero.
        - GLOG HEIGHT maps to WCL Length and GLOG AWIDTH maps to WCL Opening.
    """
    tilt_fill_value = kwargs.get('tilt_fill_value', 0)
    tilt_zero_threshold = kwargs.get('tilt_zero_threshold', 0.1)
    opening_fill_value = kwargs.get('opening_fill_value', 0)

    col_depth = kwargs.get('col_depth', 'DEPTH')
    col_azimuth = kwargs.get('col_azimuth', 'AZIMUTH')
    col_tilt = kwargs.get('col_tilt', 'TILT')
    col_height = kwargs.get('col_height', 'HEIGHT')
    col_awidth = kwargs.get('col_awidth', 'AWIDTH')
    col_category = kwargs.get('col_category', 'CATEGORY')
    col_notes = kwargs.get('col_notes', 'NOTES')

    # Normalize input column names to the canonical names used below, so
    # callers can pass GLOG files with varying header conventions.
    glog_processed = glog.rename(columns={
        col_depth: 'DEPTH',
        col_azimuth: 'AZIMUTH',
        col_tilt: 'TILT',
        col_height: 'HEIGHT',
        col_awidth: 'AWIDTH',
        col_category: 'CATEGORY',
        col_notes: 'NOTES',
    }).copy()

    # Convert GLOG tilt to WCL tilt convention (opposite direction relative to
    # the borehole axis) and infill missing values.
    glog_processed['WCL_TILT_DEG'] = glog_processed['TILT'] * -1
    glog_processed['WCL_TILT_DEG'] = glog_processed['WCL_TILT_DEG'].fillna(tilt_fill_value)

    # Snap small (and any residual negative) tilt values to zero.
    glog_processed['WCL_TILT_DEG'] = np.where(
        glog_processed['WCL_TILT_DEG'] < tilt_zero_threshold,
        0,
        glog_processed['WCL_TILT_DEG'],
    )

    # WCL Opening is not permitted to be empty.
    glog_processed['AWIDTH'] = glog_processed['AWIDTH'].fillna(opening_fill_value)

    wcl = glog_processed[[
        'DEPTH', # Depth
        'AZIMUTH', # Azimuth
        'WCL_TILT_DEG', # Tilt
        'HEIGHT', # Length
        'AWIDTH', # Opening
        'CATEGORY', # Type
        'NOTES', # Notes
    ]].copy()

    # Rename the columns to match the WCL format (names in the row comments)
    wcl.rename(columns={
        'DEPTH': 'Depth',
        'AZIMUTH': 'Azimuth',
        'WCL_TILT_DEG': 'Tilt',
        'HEIGHT': 'Length',
        'AWIDTH': 'Opening',
        'CATEGORY': 'Type',
    }, inplace=True)

    return wcl


def crack_tip_positions(
    radius_m: float,    # Cylinder radius in meters
    z_center_m: float,  # Axial (depth) position of crack center (meters)
    theta_deg: float,   # Circumferential angle of crack center (degrees CW from origin)
    omega_deg: float,   # Tilt of crack CW from long axis (degrees, can be negative)
    L_axial_m: float    # Total crack length projected onto the cylinder's long axis (meters)
):
    """
    Returns the axial position (m) and circumferential angle (degrees CW from origin)
    of the two tips of an inclined tensile crack on a cylinder surface.

    Sign convention for omega (tilt, CW from long axis):
      +omega : as z increases, theta increases (clockwise shift)
      -omega : as z increases, theta decreases (counter-clockwise shift)

    Tips are labelled by their axial position:
      'high_z_tip' : tip at z_center + dz  (always higher axial position)
      'low_z_tip'  : tip at z_center - dz  (always lower axial position)

    The circumferential shift of each tip follows naturally from the sign of omega.
    """

    # ── Input validation ───────────────────────────────────────────────────────
    if radius_m <= 0:
        raise ValueError(f"radius_m must be positive, got {radius_m}")
    if L_axial_m <= 0:
        raise ValueError(f"L_axial_m must be positive, got {L_axial_m}")
    if not (-90.0 < omega_deg < 90.0):
        raise ValueError(
            f"omega_deg must be between -90 and +90 (exclusive), got {omega_deg}. "
            "A crack at ±90° would be purely circumferential with no axial projection."
        )
        # NOTE: the last validation may be an issue where some software 
        # conventions allow omega to be ±180°. Check data examples to confirm 
        # the expected range of omega.

    # ── Geometry ───────────────────────────────────────────────────────────────
    C         = 2.0 * math.pi * radius_m        # Circumference (m)
    dz        = L_axial_m / 2.0                 # Half axial extent (m)
    omega_rad = math.radians(omega_deg)
    ds        = dz * math.tan(omega_rad)        # Half circumferential extent (m)
                                                # sign of ds matches sign of omega
    d_theta   = (ds / C) * 360.0                # Convert to degrees

    # ── Tip positions ──────────────────────────────────────────────────────────
    # High-z tip: move +dz axially, +d_theta circumferentially
    # (d_theta is negative when alpha is negative, so this is self-consistent)
    z_high      = z_center_m + dz
    theta_high  = (theta_deg + d_theta) % 360.0

    # Low-z tip: move -dz axially, -d_theta circumferentially
    z_low       = z_center_m - dz
    theta_low   = (theta_deg - d_theta) % 360.0

    return {
        "high_z_tip": {"z_m": z_high, "theta_deg": theta_high},
        "low_z_tip":  {"z_m": z_low,  "theta_deg": theta_low},
        "d_theta_deg": d_theta,           # signed circumferential half-offset
        "dz_m": dz,                       # axial half-offset (always positive)
    }


def apply_crack_tip_calculation(row):
    # Test for cases where endpoints are not calculated (e.g., missing Tilt or Length)
    if pd.isna(row['Tilt']) or pd.isna(row['Length']):
        return pd.Series({
            'high_z_tip_z_m': np.nan,
            'high_z_tip_theta_deg': np.nan,
            'low_z_tip_z_m': np.nan,
            'low_z_tip_theta_deg': np.nan,
            'd_theta_deg': np.nan,
            'dz_m': np.nan,
        })
    else:
        # Otherwise calculate the tip positions
        result = crack_tip_positions(
            radius_m=row['Radius'],
            z_center_m=row['Depth'],
            theta_deg=row['Azimuth'],
            omega_deg=row['Tilt'],
            L_axial_m=row['Length'],
        )
        return pd.Series({
            'high_z_tip_z_m': result['high_z_tip']['z_m'],
            'high_z_tip_theta_deg': result['high_z_tip']['theta_deg'],
            'low_z_tip_z_m': result['low_z_tip']['z_m'],
            'low_z_tip_theta_deg': result['low_z_tip']['theta_deg'],
            'd_theta_deg': result['d_theta_deg'],
            'dz_m': result['dz_m'],
        })


def wcl_to_glog_sticks(wcl: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Convert stick (damage) picks from WellCAD (WCL) convention to Geolog (GLOG) convention.

    The function assumes that the input dataframe follows the WCL column conventions.
    If the column names in the input dataframe differ from the defaults, they can
    be specified via keyword arguments.

    Args:
        wcl (pd.DataFrame): Input WellCAD dataframe. Required columns are:
            - Depth
            - Azimuth
            - Tilt
            - Length
            - Opening
            - Type
            - Notes
            - Radius: crack-tip cylinder radius in meters at each feature's
              Depth (e.g. interpolated from a caliper log before calling this
              function; not computed here).

    Kwargs:
        nan_fill_value (int | float, optional): Value used to replace all
            remaining NaN values before export, matching the GLOG convention
            for missing data. Defaults to -999.25.
        col_depth (str, optional): Column name holding WCL Depth. Defaults to
            "Depth".
        col_azimuth (str, optional): Column name holding WCL Azimuth. Defaults
            to "Azimuth".
        col_tilt (str, optional): Column name holding WCL Tilt. Defaults to
            "Tilt".
        col_length (str, optional): Column name holding WCL Length. Defaults
            to "Length".
        col_opening (str, optional): Column name holding WCL Opening. Defaults
            to "Opening".
        col_type (str, optional): Column name holding WCL Type. Defaults to
            "Type".
        col_notes (str, optional): Column name holding WCL Notes. Defaults to
            "Notes".
        col_radius (str, optional): Column name holding WCL Radius. Defaults
            to "Radius".

    Returns:
        pd.DataFrame: GLOG-formatted dataframe with columns:
            DEPTH, AZIMUTH, AZI_END, AZI_START, TILT, HEIGHT, AWIDTH, CATEGORY, NOTES.

    Conventions:
        - Unit rows are intentionally not handled here. Add/remove units outside
          this function as needed by import/export workflows.
        - WCL Tilt values of exactly 0 are treated as missing (no tilt was
          measured) and are set to NaN before the crack-tip endpoint
          calculation, since a tilt of 0 would otherwise be interpreted as a
          genuine horizontal crack.
        - Crack-tip endpoints are calculated per row via
          apply_crack_tip_calculation()/crack_tip_positions(), using WCL
          Radius, Depth, Azimuth, Tilt and Length. The high-z tip angle
          becomes GLOG AZI_END and the low-z tip angle becomes GLOG AZI_START.
        - GLOG TILT is the negative of WCL Tilt (GLOG and WCL measure tilt in
          opposite directions relative to the borehole axis).
        - WCL Opening values of exactly 0 are treated as missing and are set
          to NaN, matching the GLOG convention that 0 is not a valid opening
          width.
        - All remaining NaN values (including rows where Tilt or Length were
          missing, so no crack-tip endpoints could be calculated) are replaced
          with nan_fill_value to match the GLOG convention for missing data
          (-999.25 by default).
    """
    nan_fill_value = kwargs.get('nan_fill_value', -999.25)

    col_depth = kwargs.get('col_depth', 'Depth')
    col_azimuth = kwargs.get('col_azimuth', 'Azimuth')
    col_tilt = kwargs.get('col_tilt', 'Tilt')
    col_length = kwargs.get('col_length', 'Length')
    col_opening = kwargs.get('col_opening', 'Opening')
    col_type = kwargs.get('col_type', 'Type')
    col_notes = kwargs.get('col_notes', 'Notes')
    col_radius = kwargs.get('col_radius', 'Radius')

    # Normalize input column names to the canonical names used below, so
    # callers can pass WCL files with varying header conventions.
    wcl_processed = wcl.rename(columns={
        col_depth: 'Depth',
        col_azimuth: 'Azimuth',
        col_tilt: 'Tilt',
        col_length: 'Length',
        col_opening: 'Opening',
        col_type: 'Type',
        col_notes: 'Notes',
        col_radius: 'Radius',
    }).copy()

    # Set WCL.Tilt values of 0 to NaN
    wcl_processed['Tilt'] = wcl_processed['Tilt'].replace(0, np.nan)

    tip_columns = [
        'high_z_tip_z_m',
        'high_z_tip_theta_deg',
        'low_z_tip_z_m',
        'low_z_tip_theta_deg',
        'd_theta_deg',
        'dz_m',
    ]

    wcl_processed[tip_columns] = wcl_processed.apply(apply_crack_tip_calculation, axis=1, result_type='expand')

    # Make a new tilt column for GLOG convention (opposite sign of WCL tilt)
    wcl_processed['GLOG Tilt'] = wcl_processed['Tilt'] * -1

    # Make 0 values in WCL.Opening column NaN
    wcl_processed['Opening'] = wcl_processed['Opening'].replace(0, np.nan)

    # Replace NaN values with the GLOG missing-data placeholder
    wcl_processed.fillna(nan_fill_value, inplace=True)

    wcl_processed.rename(columns={
        'Depth': 'DEPTH',
        'Azimuth': 'AZIMUTH',
        'high_z_tip_theta_deg': 'AZI_END',
        'low_z_tip_theta_deg': 'AZI_START',
        'GLOG Tilt': 'TILT',
        'Length': 'HEIGHT',
        'Opening': 'AWIDTH',
        'Type': 'CATEGORY',
        'Notes': 'NOTES',
    }, inplace=True)

    glog = wcl_processed[[
        'DEPTH',
        'AZIMUTH',
        'AZI_END',
        'AZI_START',
        'TILT',
        'HEIGHT',
        'AWIDTH',
        'CATEGORY',
        'NOTES',
    ]].copy()

    return glog
