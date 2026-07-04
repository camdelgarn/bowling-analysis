from collections import deque
import numpy as np
import pandas as pd
from scipy.signal import medfilt
from scipy.signal import savgol_filter

# ==============================================================================
#                              AUXILIARY FUNCTIONS
# ==============================================================================


def remove_low_y_coordinates(df):
    """
    Remove low y-coordinates from the DataFrame.
    Returns:
    pd.DataFrame
        The DataFrame with low y-coordinates removed.
    """
    df_cleaned = df.copy()
    df_cleaned["y"] = pd.to_numeric(df_cleaned["y"], errors="coerce")
    mask = (df_cleaned["y"] > 1750) | (df_cleaned["y"] < 30)
    df_cleaned.loc[mask, ["x", "y"]] = np.nan

    return df_cleaned


def remove_low_y_coordinates_v2(df):
    """
    Remove low y-coordinates from the DataFrame.
    Returns:
    pd.DataFrame
        The DataFrame with low y-coordinates removed.
    """
    df_cleaned = df.copy()
    df_cleaned["y"] = pd.to_numeric(df_cleaned["y"], errors="coerce")
    low_y_count = 0
    last_five_y = deque(maxlen=4)

    for index, row in df.iterrows():
        last_five_y.append(row["y"])

        if len(last_five_y) == 4 and all(y < 110 for y in last_five_y):
            low_y_count += 1

        if low_y_count >= 4:
            df_cleaned.loc[index, ["x", "y"]] = np.nan

    return df_cleaned


def rolling_median_mad(values, window_size):
    """
    Calculate the rolling median and median absolute deviation (MAD) for a given window size.
    Returns:
    tuple
        Two numpy arrays containing the rolling median and MAD values.
    """
    median_values = []
    mad_values = []

    window = deque(maxlen=window_size)

    for value in values:
        window.append(value)
        if len(window) == window_size:
            median = np.median(window)
            mad = np.median(np.abs(np.array(window) - median))
            median_values.append(median)
            mad_values.append(mad)
        else:
            median_values.append(np.nan)
            mad_values.append(np.nan)

    return np.array(median_values), np.array(mad_values)


def remove_outliers_with_rolling(
    df: pd.DataFrame, threshold: float = 2.5, window_size: int = 2
) -> pd.DataFrame:
    """
    Remove outliers from the DataFrame using a rolling median and MAD method.
    Returns:
    pd.DataFrame
        The DataFrame with outliers removed.
    """
    df_clean = df.copy()
    initial_nan_mask = df_clean[["x", "y"]].isna().any(axis=1)

    x_median, x_mad = rolling_median_mad(df_clean["x"].values, window_size)
    y_median, y_mad = rolling_median_mad(df_clean["y"].values, window_size)

    distances = np.sqrt(
        (df_clean["x"].values - x_median) ** 2 + (df_clean["y"].values - y_median) ** 2
    )

    if np.nanmedian(np.abs(distances - np.nanmedian(distances))) == 0:
        return df_clean

    modified_z = (
        0.6745
        * (distances - np.nanmedian(distances))
        / np.nanmedian(np.abs(distances - np.nanmedian(distances)))
    )
    mask_outliers = np.abs(modified_z) < threshold
    new_outlier_mask = ~mask_outliers & ~initial_nan_mask
    df_clean.loc[new_outlier_mask, ["x", "y"]] = np.nan

    return df_clean


def median_filter(df, kernel_size=3):
    """
    Apply a median filter to the x and y coordinates in the DataFrame.
    Returns:
    pd.DataFrame
        The DataFrame with median filtering applied.
    """
    df = df.copy()
    if df.empty:
        return df

    df["x"] = pd.to_numeric(df["x"], errors="coerce")
    df["y"] = pd.to_numeric(df["y"], errors="coerce")

    if len(df) >= kernel_size:
        df["x"] = medfilt(df["x"], kernel_size=kernel_size)
        df["y"] = medfilt(df["y"], kernel_size=kernel_size)

    # Keep frame alignment; invalid points are marked as missing and later interpolated.
    df.loc[(df["x"] <= 0) | (df["y"] <= 0), ["x", "y"]] = np.nan
    return df


def Savitzky_Golay_filter(df, window_length=45, polyorder=3):
    """
    Apply a Savitzky-Golay filter to the x and y coordinates in the DataFrame.
    Returns:
    pd.DataFrame
        The DataFrame with Savitzky-Golay filtering applied.
    """
    df = df.copy()
    if df.empty or len(df) < 3:
        return df

    # Ensure a valid odd window length not larger than the data length.
    wl = min(window_length, len(df) if len(df) % 2 == 1 else len(df) - 1)
    if wl <= polyorder:
        wl = polyorder + 1
        if wl % 2 == 0:
            wl += 1
    if wl > len(df):
        return df

    for axis in ["x", "y"]:
        df[axis] = pd.to_numeric(df[axis], errors="coerce")
        if df[axis].notna().sum() <= polyorder:
            continue

        filled_axis = df[axis].interpolate(method="linear").bfill().ffill()
        if filled_axis.isna().any():
            continue

        df[axis] = savgol_filter(
            filled_axis.to_numpy(), window_length=wl, polyorder=polyorder
        )
    # df['x'] = df['x'].round().astype(int)
    # df['y'] = df['y'].round().astype(int)

    return df


def interpolate_missing_coordinates(df):
    """
    Interpolate missing coordinates in the DataFrame.
    Returns:
    pd.DataFrame
        The DataFrame with missing coordinates interpolated.
    """
    if df.empty or "frame" not in df.columns:
        return pd.DataFrame(columns=["frame", "x", "y"])

    df = df.copy()
    df["frame"] = pd.to_numeric(df["frame"], errors="coerce")
    df = df.dropna(subset=["frame"])
    if df.empty:
        return pd.DataFrame(columns=["frame", "x", "y"])

    df["frame"] = df["frame"].astype(int)
    df = df.set_index("frame")

    min_frame = int(df.index.min())
    max_frame = int(df.index.max())
    if min_frame > max_frame:
        return pd.DataFrame(columns=["frame", "x", "y"])

    full_index = range(min_frame, max_frame + 1)
    df_full = df.reindex(full_index)

    df_full["x"] = df_full["x"].interpolate(method="linear")
    df_full["y"] = df_full["y"].interpolate(method="linear")

    df_full["x"] = df_full["x"].bfill().ffill()
    df_full["y"] = df_full["y"].bfill().ffill()

    # If the series is still empty (all NaN), return unsmoothed to keep pipeline alive.
    if df_full[["x", "y"]].isna().all().all():
        return df_full.reset_index().rename(columns={"index": "frame"})

    df_full = df_full.reset_index().rename(columns={"index": "frame"})
    df_full = Savitzky_Golay_filter(df_full)

    return df_full


# ==============================================================================
#                             PROCESSING FUNCTIONS
# ==============================================================================


def process_data_transformed(input_csv: str, output_csv: str):
    """
    Process the input CSV file and save the cleaned data to the output CSV file.
    """
    df_coords = pd.read_csv(input_csv)
    df_final = remove_low_y_coordinates_v2(df_coords)
    df_final = remove_low_y_coordinates(df_final)
    df_filtered = remove_outliers_with_rolling(df_final)
    df_smoothed = median_filter(df_filtered)
    df_interpolated = interpolate_missing_coordinates(df_smoothed)
    df_interpolated.to_csv(output_csv, index=False)

    print("Cleaned data saved to: ", output_csv)
