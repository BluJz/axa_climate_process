import folium
from folium.features import GeoJsonTooltip

DICT_THRESHOLDS = {
    'precipitation': [0., 1., 2., 3., 4., 5.],
    'r_min': [0., 20., 40., 60., 80., 100.],
    'ssrd_mean': [0., 70., 140., 210., 280., 350.],
    'Tmax': [0., 8., 16., 24., 32., 40.],
    'Tavg': [0., 8., 16., 24., 32., 40.],
    'Tmin': [0., 8., 16., 24., 32., 40.],
    'ws10_mean': [0., 2., 4., 6., 8., 10.]
}

def create_map(geo_df, geojson_data, meteo_column):
    # Create a Folium map object
    m = folium.Map(
        location=[
            geo_df["geometry"].centroid.y.mean(),
            geo_df["geometry"].centroid.x.mean(),
        ],
        zoom_start=6,
    )

    # Define the threshold scale
    threshold_scale = DICT_THRESHOLDS[meteo_column]
    geo_df['capped_value'] = geo_df[meteo_column].apply(lambda x: max(min(x, threshold_scale[-1]), threshold_scale[0]))
    columns = ['id', 'capped_value']

    # Create a Choropleth layer (colors based on the attribute represented)
    choropleth = folium.Choropleth(
        geo_data=geojson_data,
        data=geo_df,
        columns=columns,
        key_on="feature.properties.id",
        fill_color="YlGnBu",  # Make sure this color scale is valid
        threshold_scale=threshold_scale,
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=meteo_column,
    ).add_to(m)

    # Create a GeoJson layer with tooltips
    geojson_layer = folium.GeoJson(
        geojson_data,
        name="Communes",
        style_function=lambda feature: {
            "color": "black",
            "weight": 0.5,
            "fillOpacity": 0.1,
        },
        tooltip=GeoJsonTooltip(
            fields=[meteo_column],
            aliases=[meteo_column + ": "],
            localize=True,
            sticky=True,
        ),
    ).add_to(m)

    # Add the layer control
    folium.LayerControl().add_to(m)

    return m
