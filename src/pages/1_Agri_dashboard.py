import streamlit as st
import pandas as pd
import altair as alt
from utils.data_extraction import load_agri_data

def main():
    st.title('Dashboard rendements agricoles')
    agri_df = load_agri_data()

    # Select the variable to plot
    variable = st.selectbox("Sélectionnez la variable d'intérêt: ", agri_df['variable'].unique(), index=2)

    # Filter DataFrame based on selected variable
    filtered_df = agri_df[agri_df['variable'] == variable]

    # Get unique values of 'n6'
    n6_values = filtered_df['n6'].unique()

    # Plotting
    for n6 in n6_values:
        st.subheader(f"{variable} pour la catégorie '{n6}'")
        chart = plot_for_n6(filtered_df, n6)
        st.altair_chart(chart, use_container_width=True)

    # Add a numeric input for the user to select a number from 1 to 10
    x = st.slider("Sélectionnez le nombre de moins bonnes valeurs à afficher: ", 1, 10, 1)

    # Display the X lowest values of the selected variable
    st.subheader(f"Années avec les {x} moins bonnes valeurs pour la variable sélectionnée: '{variable}'")
    display_lowest_values(agri_df, variable, x)

def plot_for_n6(df, n6_value):
    # Filter for the specific 'n6'
    df_n6 = df[df['n6'] == n6_value]

    # Map 'dpt' values to names
    df_n6['dpt'] = df_n6['dpt'].map({'27': 'Eure', '28': 'Eure-et-Loire'})

    # Define a selection that chooses the nearest point along the x-axis
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['year'], empty='none')

    # Base chart with line marks
    line = alt.Chart(df_n6).mark_line().encode(
        x=alt.X('year:O', axis=alt.Axis(title='Année', labelAngle=-45)),
        y=alt.Y('value:Q', axis=alt.Axis(title='Valeur')),
        color=alt.Color('dpt:N', legend=alt.Legend(title='Département'))
    )

    # Transparent selectors across the chart to track x-value of the cursor
    selectors = alt.Chart(df_n6).mark_point().encode(
        x='year:O',
        opacity=alt.value(0)
    ).add_selection(
        nearest
    )

    # Text layer to show values
    text = line.mark_text(align='left', dx=5, dy=-5).encode(
        text=alt.condition(nearest, 'value:Q', alt.value(' '))
    )

    # Rule to mark the x position of the cursor
    rules = alt.Chart(df_n6).mark_rule(color='gray').encode(
        x='year:O'
    ).transform_filter(
        nearest
    )

    # Combine the layers
    chart = alt.layer(
        line, selectors, rules, text
    ).properties(
        width=600, height=400
    ).interactive()

    return chart

def display_lowest_values(df, variable, x):
    # Filter the DataFrame based on the selected variable
    filtered_df = df[df['variable'] == variable]

    for n6_value in df['n6'].unique():
        st.subheader(f"Catégorie: '{n6_value}'")
        n6_filtered_df = filtered_df[filtered_df['n6'] == n6_value]

        for dpt_value in df['dpt'].unique():
            if dpt_value == '27':
                dpt = 'Eure'
            else:
                dpt = 'Eure-et-Loire'
            st.text(f"Pour le département de l'{dpt}")
                    
            dpt_filtered_df = n6_filtered_df[n6_filtered_df['dpt'] == dpt_value]
            # Sort by 'value' and select the first X rows
            lowest_values_df = dpt_filtered_df.sort_values(by='value').head(x)
            lowest_values_df.reset_index(inplace=True)

            count = 1
            for kpi in st.columns(x):
                kpi.metric(
                    label=str(lowest_values_df.at[count-1,'year']),
                    value=lowest_values_df.at[count-1,'value']
                )
                count+=1


if __name__ == "__main__":
    main()

