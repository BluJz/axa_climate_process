import folium
from folium.features import GeoJsonTooltip

def create_map(geo_df, geojson_data, columns=['id', 'precipitation'], legend_title='Precipitation levels'):
    # Create a Folium map object
    m = folium.Map(
        location=[
            geo_df["geometry"].centroid.y.mean(),
            geo_df["geometry"].centroid.x.mean(),
        ],
        zoom_start=6,
    )

    # Create a Choropleth layer (colors based on the attribute represented)
    choropleth = folium.Choropleth(
        geo_data=geojson_data,
        data=geo_df,
        columns=columns,
        key_on="feature.properties.id",
        fill_color="YlGnBu",  # Make sure this color scale is valid
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=legend_title,
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
            fields=["precipitation"],
            aliases=["Precipitation: "],
            localize=True,
            sticky=True,
        ),
    ).add_to(m)

    # Add the layer control
    folium.LayerControl().add_to(m)

    return m
