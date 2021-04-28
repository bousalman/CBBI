from typing import List

import numpy as np
import pandas as pd


def mark_highs_lows(df: pd.DataFrame, col: str, begin_with_high: bool, window_size: float, ignore_last_rows: int) -> pd.DataFrame:
    """
    Marks highs and lows (peaks) of the column values inside the given DataFrame.
    Marked points are indicated by the value '1' inside their corresponding, newly added, 'High' and 'Low' columns.

    Args:
        df: DataFrame from which the column values are selected and to which marked points columns are added.
        col: Column name of which values are selected inside the given DataFrame.
        begin_with_high: Indicates whether the first peak is high or low.
        window_size: Window size for the algorithm to consider.
                     Too low value will mark too many peaks, whereas, too high value will mark too little peaks.

    Returns:
        Modified input DataFrame with columns, indicating the marked points, added.
    """
    col_high = col + 'High'
    col_low = col + 'Low'

    assert col in df.columns, 'The column name (col) could not be found inside the given DataFrame (df)'
    assert col_high not in df.columns, 'The DataFrame (df) already contains the "High" column - bugprone'
    assert col_low not in df.columns, 'The DataFrame (df) already contains the "Low" column - bugprone'
    assert window_size > 0, 'Value of the window_size argument must be at least 1'

    df[col_high] = 0
    df[col_low] = 0

    searching_high = begin_with_high
    current_index = df.index[0]

    while True:
        window = df.loc[current_index:current_index + window_size, col]
        window_index = window.idxmax() if searching_high else window.idxmin()

        if window.shape[0] <= 1:
            break

        if window_index == current_index:
            df.loc[window_index, col_high if searching_high else col_low] = 1
            searching_high = not searching_high
            window_index = window_index + 1

        current_index = window_index

    df.loc[df.shape[0] - ignore_last_rows:, (col_high, col_low)] = 0
    return df


def mark_days_since(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    for col in cols:
        indexes = df.loc[df[col] == 1].index
        df[f'DaysSince{col}'] = df.index.to_series().apply(lambda v: min([v - index if index <= v else np.nan for index in indexes]))

    return df


def fix_block_halving_data(df: pd.DataFrame) -> pd.DataFrame:
    current_block_production = 50
    df['Halving'] = 0

    while True:
        current_block_production_min = 0.95 * current_block_production
        current_block_production_max = 1.05 * current_block_production

        df.loc[(current_block_production_min < df['BlockGeneration']) &
               (df['BlockGeneration'] < current_block_production_max), 'BlockGeneration'] = current_block_production

        block_halving_index = np.min(df[df['BlockGeneration'] < current_block_production].index)

        if np.isnan(block_halving_index):
            break

        df.loc[block_halving_index, 'Halving'] = 1
        current_block_production /= 2

    return df


def fix_current_day_data(df: pd.DataFrame) -> pd.DataFrame:
    row = df.iloc[-1].copy()

    target_total_blocks = 24 * 6
    target_scale = target_total_blocks / row['TotalBlocks']

    for col_name in ['TotalBlocks', 'TotalGeneration', 'TotalGenerationUSD']:
        row[col_name] *= target_scale

    df.iloc[-1] = row
    return df


def format_percentage(val: float, suffix: str = ' %') -> str:
    """
    Formats a percentage value (0.0 - 1.0) in a standardized way.
    Returned value has a constant width and a trailing '%' sign.

    Args:
        val: Percentage value to be formatted.
        suffix: String to be appended to the result.

    Returns:
        Formatted percentage value with a constant width and trailing '%' sign.

    Examples:
        >>> print(format_percentage(0.359))
        str(' 36 %')

        >>> print(format_percentage(1.1))
        str('110 %')
    """

    return f'{round(val * 100): >3d}{suffix}'


def get_color(val: float) -> str:
    """
    Maps a percentage value (0.0 - 1.0) to its corresponding color.
    The color is used to indicate whether the value is low (0.0) or high (1.0).
    Returned value is a valid termcolor-package color string.

    Args:
        val: Percentage value to be mapped into a color.

    Returns:
        Valid termcolor-package color string.
    """

    config = [
        'red',
        .3,
        'yellow',
        .65,
        'green',
        .85,
        'cyan',
        .97,
        'magenta',
    ]

    bin_index = np.digitize([round(val, 2)], config[1::2])[0]
    return config[::2][bin_index]
