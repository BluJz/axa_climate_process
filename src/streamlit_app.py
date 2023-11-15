import streamlit as st
import pandas as pd
import geopandas as gpd
from streamlit_folium import st_folium
from shapely.ops import nearest_points
import folium
from folium.features import GeoJsonTooltip


APP_TITLE = "Agricultural Yields in Eure and Eure-et-Loire Report"
APP_SUB_TITLE = "AXA Climate Process Project"


def main():
    st.set_page_config(APP_TITLE)
    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)

    # Load data

    # df_agri = pd.read_csv("../data/agreste.csv")
    # drop_columns = ['Unnamed: 0', 'n1', 'n2', 'n3', 'n4', 'n5', 'departement']
    # df_agri.drop(columns=drop_columns, inplace=True)
    # condition = (df_agri['dpt'] == '28') | (df_agri['dpt'] == '27')
    # df_agri = df_agri[condition]

    df_meteorological = pd.read_parquet("../data/ERA5_data.parquet")
    # Let's say you want to plot the data for a specific date
    specific_date = "2020-01-01"  # for example
    df_specific_date = df_meteorological[
        df_meteorological.index.get_level_values("date") == specific_date
    ]
    gdf = gpd.GeoDataFrame(
        df_specific_date,
        geometry=gpd.points_from_xy(
            df_specific_date.index.get_level_values("longitude"),
            df_specific_date.index.get_level_values("latitude"),
        ),
    )

    gdf_communes = gpd.read_file("../data/communes-20220101-shp/")
    gdf_communes.drop(columns=["nom", "wikipedia", "surf_ha"], inplace=True)

    folder_path = "../data/cog_ensemble_2021_csv/"
    df_communes = pd.read_csv(folder_path + "commune2021.csv")
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

    # Assuming you have already read the shape file into a GeoDataFrame called 'gdf' and the CSV into a DataFrame called 'df_communes'

    # Convert the 'insee' and 'COM' columns to strings if they are not already
    gdf_communes["insee"] = gdf_communes["insee"].astype(str)
    df_communes["COM"] = df_communes["COM"].astype(str)

    # Merge the GeoDataFrame with the DataFrame on the 'insee' and 'COM' columns
    merged_gdf = gdf_communes.merge(df_communes, left_on="insee", right_on="COM")
    merged_gdf.drop(columns=["COM"], inplace=True)

    # The 'DEP' column from df_commune will now be in the merged_gdf, giving you the department for each commune
    list_interest_dpt = [
        "27",
        "28",
        "76",
        "60",
        "95",
        "78",
        "91",
        "75",
        "45",
        "41",
        "72",
        "61",
        "14",
    ]

    condition = merged_gdf["DEP"].isin(["27", "28"])
    merged_gdf = merged_gdf[condition].copy()

    gdf_meteorological = gpd.GeoDataFrame(
        df_specific_date,
        geometry=gpd.points_from_xy(
            df_specific_date.index.get_level_values("longitude"),
            df_specific_date.index.get_level_values("latitude"),
        ),
    )

    # Assuming 'gdf_communes' is your GeoDataFrame of communes with polygon geometries
    gdf_communes = merged_gdf
    # and 'gdf_meteorological' is your GeoDataFrame of meteorological points

    # Ensure both GeoDataFrames use the same CRS
    # gdf_communes = gdf_communes.to_crs(gdf_meteorological.crs)

    # Calculate the centroids of the communes if they are not already points
    gdf_communes["centroid"] = gdf_communes.geometry.centroid

    # Initialize a column for the nearest meteorological data
    for attribute in gdf_meteorological.columns.drop("geometry"):
        gdf_communes[attribute] = None

    # Find the nearest meteorological point for each commune centroid
    for index, commune in gdf_communes.iterrows():
        # Use unary_union to create a single geometry that includes all meteorological points
        # This speeds up the operation considerably
        nearest_geom = nearest_points(
            commune["centroid"], gdf_meteorological.unary_union
        )[1]

        # Get the nearest point's data
        nearest_data = gdf_meteorological.loc[
            gdf_meteorological["geometry"] == nearest_geom
        ]

        # Assign the data to the commune's row
        for attribute in gdf_meteorological.columns.drop("geometry"):
            gdf_communes.at[index, attribute] = nearest_data[attribute].values[0]

    # Drop the centroid column if you wish
    gdf_communes = gdf_communes.drop(columns=["centroid"])

    list_col = [
        "insee",
        "DEP",
        "precipitation",
        "r_min",
        "ssrd_mean",
        "Tmax",
        "Tavg",
        "Tmin",
        "ws10_mean",
    ]
    for column in list_col:
        gdf_communes[column] = gdf_communes[column].astype(float)

    gdf_meteorological["id"] = range(len(gdf_meteorological))

    gdf_communes[
        "nearest_id"
    ] = None  # Add a column for storing the id of the nearest point
    # Calculate the centroids of the communes if they are not already points
    gdf_communes["centroid"] = gdf_communes.geometry.centroid

    # Find the nearest meteorological point for each commune centroid
    for index, commune in gdf_communes.iterrows():
        # Use unary_union to create a single geometry that includes all meteorological points
        # This speeds up the operation considerably
        nearest_geom = nearest_points(
            commune["centroid"], gdf_meteorological.unary_union
        )[1]

        # Get the nearest point's data
        nearest_data = gdf_meteorological.loc[
            gdf_meteorological["geometry"] == nearest_geom
        ]

        # Assign the id of the nearest point
        gdf_communes.at[index, "nearest_id"] = nearest_data["id"].values[0]

    gdf_communes.drop(columns=["centroid"], inplace=True)

    gdf_dissolved = gdf_communes.dissolve(by="nearest_id", as_index=False)

    # Convert the GeoDataFrame to GeoJSON
    geojson_dissolved = gdf_dissolved.to_json()

    # Create a Folium map object
    m = folium.Map(
        location=[
            gdf_dissolved["geometry"].centroid.y.mean(),
            gdf_dissolved["geometry"].centroid.x.mean(),
        ],
        zoom_start=6,
    )

    # Create a Choropleth layer
    choropleth = folium.Choropleth(
        geo_data=geojson_dissolved,
        data=gdf_dissolved,
        columns=["nearest_id", "precipitation"],
        key_on="feature.properties.nearest_id",
        fill_color="YlGnBu",  # Make sure this color scale is valid
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Precipitation levels",
    ).add_to(m)

    # Create a GeoJson layer with tooltips
    geojson_layer = folium.GeoJson(
        geojson_dissolved,
        name="Communes",
        style_function=lambda feature: {
            "color": "black",
            "weight": 0.5,
            "fillOpacity": 0.1,
        },
        tooltip=GeoJsonTooltip(
            fields=["precipitation"],
            aliases=["Precipitation: "],
            localize=True,
            sticky=True,
        ),
    ).add_to(m)

    # Ensure tooltip appears on top by adding it after the choropleth
    geojson_layer.add_to(m)

    # Add the layer control
    folium.LayerControl().add_to(m)

    st_folium(m, width=725)

    st.subheader(f"End of code")


if __name__ == "__main__":
    main()
