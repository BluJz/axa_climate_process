import streamlit as st
import pandas as pd
import altair as alt
from streamlit_folium import folium_static
from utils.meteo import get_monthly_mean, convert_lat_long_to_communes, surface_dpt_average
from utils.data_extraction import load_meteo_data, load_communes_geometry, load_agri_data
from utils.maps import create_map

METEOROLOGICAL_COLUMNS = ['precipitation', 'r_min', 'ssrd_mean', 'Tmax', 'Tavg', 'Tmin', 'ws10_mean']

def plot_monthly(meteo_column, year, df_meteo, gdf_geom):
    df_meteo_year = get_monthly_mean(df_meteo, year=year)
    df_meteo_mean = get_monthly_mean(df_meteo, compare_year=year)

    gdf_meteo_year = convert_lat_long_to_communes(df_meteo_year, gdf_geom=gdf_geom)
    gdf_meteo_mean = convert_lat_long_to_communes(df_meteo_mean, gdf_geom=gdf_geom)

    df_meteo_year = surface_dpt_average(gdf_meteo_year)
    df_meteo_mean = surface_dpt_average(gdf_meteo_mean)

    df_meteo_year_27 = df_meteo_year.loc['27']
    df_meteo_year_28 = df_meteo_year.loc['28']
    df_meteo_mean_27 = df_meteo_mean.loc['27']
    df_meteo_mean_28 = df_meteo_mean.loc['28']
    # Add a new 'line_type' column to each DataFrame
    df_meteo_year_27['line_type'] = 'Dpt 27'
    df_meteo_year_28['line_type'] = 'Dpt 28'
    df_meteo_mean_27['line_type'] = 'Mean Dpt 27'
    df_meteo_mean_28['line_type'] = 'Mean Dpt 28'

    # Combine all DataFrames for plotting
    combined_df = pd.concat([df_meteo_year_27, df_meteo_year_28, df_meteo_mean_27, df_meteo_mean_28])

    # Create a combined chart
    combined_chart = alt.Chart(combined_df).mark_line().encode(
        x=alt.X('date:T', title='Date', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y(f'{meteo_column}:Q', title=meteo_column.capitalize()),
        color='line_type:N'
    )

    # Transparent selector across the chart
    selectors = alt.Chart(combined_df).mark_rule().encode(
        x='date:T',
        opacity=alt.value(0),
        tooltip=[alt.Tooltip('date:T', title='Date'), alt.Tooltip(f'{meteo_column}:Q', title=meteo_column.capitalize())]
    ).add_selection(
        alt.selection_single(fields=['date'], nearest=True, on='mouseover', empty='none')
    )

    # Combine the line chart with selectors
    chart = alt.layer(combined_chart, selectors).properties(
        width=700,
        height=400
    ).interactive()

    # Display the chart in Streamlit
    st.altair_chart(chart, use_container_width=True)

    return gdf_meteo_year, gdf_meteo_mean

def plot_agri_yield(year):
    st.header('Rendements agricoles')
    agri_df = load_agri_data()
    variable = 'Rendement'

    # Filter DataFrame based on selected variable
    filtered_df = agri_df[agri_df['variable'] == variable]
    filtered_df = filtered_df[filtered_df['year'] == year]
    # Get unique values of 'n6'
    n6_values = filtered_df['n6'].unique()

    # Plotting
    for n6_value in n6_values:
        st.subheader(f"Catégorie: '{n6_value}'")
        n6_filtered_df = filtered_df[filtered_df['n6'] == n6_value]

        for dpt_value in ['27', '28']:
            if dpt_value == '27':
                dpt = 'Eure'
            else:
                dpt = 'Eure-et-Loire'
            st.text(f"Pour le département de l'{dpt}")
                    
            dpt_filtered_df = n6_filtered_df[n6_filtered_df['dpt'] == dpt_value]

            for kpi in st.columns(1):
                kpi.metric(
                    label=str(year),
                    value=dpt_filtered_df.iloc[0]['value']
                )

def plot_map_snapshot(gdf, meteo_column):
    # Extract unique months and convert to a readable format
    unique_months = gdf['date'].dt.strftime('%B %Y').unique()
    # Create a select box for user to choose the month
    selected_month = st.selectbox("Sélectionnez le mois", unique_months)
    # Filter the DataFrame based on the user's selection
    # Convert 'selected_month' back to datetime for comparison
    selected_month_dt = pd.to_datetime(selected_month)
    filtered_gdf = gdf[gdf['date'].dt.month == selected_month_dt.month]
    geojson_map = filtered_gdf.drop(columns=['date']).to_json()
    
    m = create_map(filtered_gdf, geojson_map, meteo_column)

    folium_static(m, width=725)


def main():
    st.title('Dashboard snapshot sur une année')
    df_meteo = load_meteo_data()
    gdf_geom = load_communes_geometry()

    # User input for the year
    year = st.number_input("Sélectionnez l'année", min_value=2000, max_value=2021, value=2020)

    # Selector for the meteorological data column
    meteo_column = st.selectbox("Sélectionnez la variable météorologique à afficher", 
                                METEOROLOGICAL_COLUMNS)

    plot_agri_yield(year=year)
    
    gdf_meteo_year, gdf_meteo_mean = plot_monthly(meteo_column, year, df_meteo=df_meteo, gdf_geom=gdf_geom)

    plot_map_snapshot(gdf_meteo_year, meteo_column)

    



if __name__ == '__main__':
    main()
