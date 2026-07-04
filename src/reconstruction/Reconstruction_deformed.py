import pandas as pd
import cv2
import numpy as np
from scipy.signal import savgol_filter

# ==============================================================================
#                              AUXILIARY FUNCTIONS
# ==============================================================================


def transform_coordinates(
    input_csv: str, output_csv: str, scale_x: float, scale_y: float
):
    """
    Transforms the coordinates from the input CSV file and saves them to the output CSV file.
    """
    df = pd.read_csv(input_csv)
    df["frame"] = pd.to_numeric(df["frame"], errors="coerce")
    df["x"] = pd.to_numeric(df["x"], errors="coerce")
    df["y"] = pd.to_numeric(df["y"], errors="coerce")
    transformed_points = []

    for _, row in df.iterrows():
        if pd.isna(row["frame"]):
            continue

        x_old, y_old = row["x"], row["y"]
        if pd.isna(x_old) or pd.isna(y_old):
            transformed_points.append([int(row["frame"]), np.nan, np.nan])
            continue

        x_new = int(x_old * scale_x)
        y_new = int(y_old * scale_y) + 65
        transformed_points.append([int(row["frame"]), x_new, y_new])

    transformed_df = pd.DataFrame(transformed_points, columns=["frame", "x", "y"])
    transformed_df.to_csv(output_csv, index=False)

    print(f"Transformed coordinates have been saved to: {output_csv}")


def Savitzky_Golay_filter(df, window_length=60, polyorder=2):
    """
    Apply Savitzky-Golay filter to smooth the x and y coordinates in the DataFrame.
    """
    df = df.copy()

    if df.empty or len(df) < 3:
        return df

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

    for axis in ["x", "y"]:
        df[axis] = pd.to_numeric(df[axis], errors="coerce").round()

    return df


# ==============================================================================
#                           RECONSTRUCTION FUNCTIONS
# ==============================================================================


def process_reconstruction_deformed(
    input_csv: str, output_csv: str, template_path: str
):
    """
    Process the reconstruction by transforming coordinates and applying smoothing.
    """
    df = pd.read_csv(input_csv)
    template = cv2.imread(template_path)
    h, w = template.shape[:2]

    old_width, old_height = 106, 1829
    new_width, new_height = w, h - 65

    scale_x = new_width / old_width
    scale_y = new_height / old_height

    transform_coordinates(input_csv, output_csv, scale_x, scale_y)

    df = pd.read_csv(output_csv)
    df_smooted = Savitzky_Golay_filter(df)
    df_smooted.to_csv(output_csv, index=False)
