import geopandas as gpd
import pandas as pd
from utils.data_extraction import load_meteo_data_date, load_meteo_data

METEOROLOGICAL_COLUMNS = ['precipitation', 'r_min', 'ssrd_mean', 'Tmax', 'Tavg', 'Tmin', 'ws10_mean']

def convert_lat_long_to_communes(df_meteo, gdf_geom):
    """Converts a df_meteo to the communes geometry (with dpt feature)

    Args:
        df_meteo (pd.DataFrame): must have latitude and longitude as index
        gdf_geom (gdp.GeoDataFrame): communes gdf with corresponding geometry

    Returns:
        gpd.GeoDataFrame: geodataframe with communes geometry and corresponding meteorological values
    """
    gdf_base_meteo = load_meteo_data_date()
    lat_lon_to_id = gdf_base_meteo.reset_index().drop_duplicates(subset=['latitude', 'longitude']).set_index(['latitude', 'longitude'])['id']

    df_meteo_with_id = df_meteo.copy()
    df_meteo_with_id['id'] = df_meteo_with_id.index.map(lat_lon_to_id)

    gdf_meteo = gpd.GeoDataFrame(
        df_meteo_with_id,
        geometry=gpd.points_from_xy(
            df_meteo_with_id.index.get_level_values("longitude"),
            df_meteo_with_id.index.get_level_values("latitude"),
        ),
    )

    # Merge the dataframes
    gdf_communes_meteo = gdf_geom.merge(gdf_meteo.drop(columns=['geometry']), 
                                              left_on='nearest_id', 
                                              right_on='id', 
                                              how='left')

    return gdf_communes_meteo

# Function to calculate weighted average for a group
def weighted_avg(group, cols, weight_col):
    weighted_avgs = {}
    total_weight = group[weight_col].sum()
    for col in cols:
        weighted_avgs[col] = (group[col] * group[weight_col]).sum() / total_weight
    return pd.Series(weighted_avgs)

def surface_dpt_average(gdf_meteo):
    """Gets weighted average for departments based on a gpd dataframe

    Args:
        gdf_meteo (gpd.GeoDataFrame): needs to have communes geometry, meteorological data and dates

    Returns:
        gpd.GeoDataFrame: dataframe with department as index, date as column and corresponding meteorological data
    """
    # Calculate the area of each polygon if not already present
    gdf_meteo['area'] = gdf_meteo.geometry.area

    # Function to calculate weighted average for a group
    def weighted_avg(group, cols, weight_col):
        weighted_avgs = {}
        total_weight = group[weight_col].sum()
        for col in cols:
            weighted_avgs[col] = (group[col] * group[weight_col]).sum() / total_weight
        return pd.Series(weighted_avgs)

    # Group by 'department' and 'date', then apply the weighted average function
    result = gdf_meteo.groupby(['DEP', 'date']).apply(weighted_avg, METEOROLOGICAL_COLUMNS, 'area')
    result.reset_index(level='date', inplace=True)
    return result

def get_monthly_mean(df_meteo, year=None, compare_year=2020):
    df_meteo_reset = df_meteo.reset_index(level='date')

    if year is not None:
        # Filter the data from September of the selected year to August of the next year
        start_date = pd.to_datetime(f"{year-1}-09-01")
        end_date = pd.to_datetime(f"{year}-08-31")
        filtered_df = df_meteo_reset[(df_meteo_reset['date'] >= start_date) & (df_meteo_reset['date'] <= end_date)]

        # Group by latitude, longitude, year, and month, then calculate the mean
        monthly_means = filtered_df.groupby([pd.Grouper(level='latitude'), 
                            pd.Grouper(level='longitude'), 
                            filtered_df['date'].dt.year.rename('year'), 
                            filtered_df['date'].dt.month.rename('month')]).mean()
        
        # Reset index to turn 'year' and 'month' back into columns
        monthly_means = monthly_means.reset_index()

        # Create a new 'date' column that is the first day of each month and year
        monthly_means['date'] = pd.to_datetime(monthly_means['year'].astype(str) + '-' + 
                                       monthly_means['month'].astype(str) + '-01')

    else:
        filtered_df = df_meteo_reset
        # Group by latitude, longitude, year, and month, then calculate the mean
        monthly_means = filtered_df.groupby([pd.Grouper(level='latitude'), 
                            pd.Grouper(level='longitude'), 
                            filtered_df['date'].dt.month.rename('month')]).mean()
        monthly_means['year'] = monthly_means.index.get_level_values('month').map(lambda x: compare_year if x <= 8 else compare_year-1)

        # Reset index to turn 'year' and 'month' back into columns
        monthly_means = monthly_means.reset_index()

        # Create a new 'date' column that is the first day of each month and year
        monthly_means['date'] = pd.to_datetime(monthly_means['year'].astype(str) + '-' + 
                                       monthly_means['month'].astype(str) + '-01')

    # Drop the 'year' and 'month' columns as they are now redundant with the 'date' column
    monthly_means.drop(['year', 'month'], axis=1, inplace=True)

    # Set 'latitude' and 'longitude' back as the index
    monthly_means.set_index(['latitude', 'longitude'], inplace=True)
    return monthly_means
