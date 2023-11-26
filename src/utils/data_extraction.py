import geopandas as gpd
import pandas as pd
from shapely.ops import nearest_points
import streamlit as st

def load_agri_data(path="../data/agreste.csv", drop_columns=['Unnamed: 0', 'n1', 'n2', 'n3', 'n4', 'n5', 'departement']):
    df_agri = pd.read_csv(path)
    df_agri.drop(columns=drop_columns, inplace=True)
    condition = (df_agri['dpt'] == '28') | (df_agri['dpt'] == '27')
    df_agri = df_agri[condition].copy()

    return df_agri


def load_meteo_data_date(path="../data/ERA5_data.parquet", specific_date='2020-01-01'):
    df_meteorological = pd.read_parquet(path)
    df_specific_date = df_meteorological[
        df_meteorological.index.get_level_values("date") == specific_date
    ]

    gdf_meteorological = gpd.GeoDataFrame(
        df_specific_date,
        geometry=gpd.points_from_xy(
            df_specific_date.index.get_level_values("longitude"),
            df_specific_date.index.get_level_values("latitude"),
        ),
    )

    gdf_meteorological["id"] = range(len(gdf_meteorological))

    return gdf_meteorological


@st.cache_data
def load_communes_geometry(path_gpd_communes="../data/communes-20220101-shp/", path_df_communes="../data/cog_ensemble_2021_csv/commune2021.csv", path_base_meteo="../data/ERA5_data.parquet"):
    # Extract a 'base' meteo dataframe to build the geometry of communes on it
    df_base_meteo = pd.read_parquet(path_base_meteo)
    base_date = "2020-01-01"
    df_base_meteo = df_base_meteo[
        df_base_meteo.index.get_level_values("date") == base_date
    ]
    gdf_base_meteorological = gpd.GeoDataFrame(
        df_base_meteo,
        geometry=gpd.points_from_xy(
            df_base_meteo.index.get_level_values("longitude"),
            df_base_meteo.index.get_level_values("latitude"),
        ),
    )


    gdf_communes = gpd.read_file(path_gpd_communes)
    gdf_communes.drop(columns=["nom", "wikipedia", "surf_ha"], inplace=True)

    df_communes = pd.read_csv(path_df_communes)
    df_communes.drop(
        columns=[
            "TYPECOM",
            "REG",
            "CTCD",
            "ARR",
            "TNCC",
            "NCC",
            "NCCENR",
            "LIBELLE",
            "CAN",
            "COMPARENT",
        ],
        inplace=True,
    )

    # Merge the GeoDataFrame with the DataFrame on the 'insee' and 'COM' columns
    merged_communes_gdf = gdf_communes.merge(df_communes, left_on="insee", right_on="COM")
    merged_communes_gdf.drop(columns=["COM"], inplace=True)

    condition = merged_communes_gdf["DEP"].isin(["27", "28"])
    gdf_communes = merged_communes_gdf[condition].copy()

    gdf_base_meteorological["id"] = range(len(gdf_base_meteorological))

    gdf_communes["nearest_id"] = None  # Add a column for storing the id of the nearest point
    # Calculate the centroids of the communes if they are not already points
    gdf_communes["centroid"] = gdf_communes.geometry.centroid

    # Find the nearest meteorological point for each commune centroid
    for index, commune in gdf_communes.iterrows():
        # Use unary_union to create a single geometry that includes all meteorological points
        # This speeds up the operation considerably
        nearest_geom = nearest_points(
            commune["centroid"], gdf_base_meteorological.unary_union
        )[1]

        # Get the nearest point's data
        nearest_data = gdf_base_meteorological.loc[
            gdf_base_meteorological["geometry"] == nearest_geom
        ]

        # Assign the id of the nearest point
        gdf_communes.at[index, "nearest_id"] = nearest_data["id"].values[0]

    gdf_communes.drop(columns=["centroid"], inplace=True)

    gdf_communes_meteo = gdf_communes.dissolve(by="nearest_id", as_index=False)

    return gdf_communes_meteo
