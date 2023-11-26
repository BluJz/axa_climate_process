import streamlit as st
import pandas as pd
import geopandas as gpd
from streamlit_folium import folium_static
from shapely.ops import nearest_points
import folium
from folium.features import GeoJsonTooltip
from utils.maps import create_map
from utils.data_extraction import load_communes_geometry, load_meteo_data_date


APP_TITLE = "Agricultural Yields in Eure and Eure-et-Loire Report"
APP_SUB_TITLE = "AXA Climate Process Project"


def extract():
    gdf_meteo = load_meteo_data_date()
    gdf_communes_geom = load_communes_geometry()

    gdf_precipitation = gdf_communes_geom.merge(
        gdf_meteo[['id', 'precipitation']],
        left_on='nearest_id',
        right_on='id',
        how='left'
        )
    geojson_map = gdf_precipitation.to_json()

    st.subheader(f"End of data extraction")

    return gdf_precipitation, geojson_map


def plot(gdf, geojson):
    st.subheader(f"Start of plot")
    m = create_map(gdf, geojson)

    folium_static(m, width=725)

    st.subheader(f"End of plot")


if __name__ == "__main__":
    st.set_page_config(APP_TITLE)
    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)
    
    gdf, geojson = extract()

    plot(gdf, geojson)
