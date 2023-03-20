import pandas as pd
import streamlit as st
import pydeck as pdk
import altair as alt
import numpy as np

# Read the CSV file
CSV_FILE = "LA_crime_data.csv"
df = pd.read_csv(CSV_FILE)

# Convert date columns to datetime
df['DATE OCC'] = pd.to_datetime(df['DATE OCC'])

# Fill missing values with a default value
df = df.fillna("")

def display_map(df):
    view_state = pdk.ViewState(
        latitude=df['LAT'].mean(),
        longitude=df['LON'].mean(),
        zoom=9,
        pitch=0
    )

    # Replace NaN values with empty strings for JSON compatibility
    json_data = df.to_json(orient="records")
    data = pd.read_json(json_data)

    # Create a dictionary to map crime types to colors
    unique_crime_types = df['Crm Cd Desc'].unique()
    colors = np.random.randint(0, 256, size=(len(unique_crime_types), 3)).tolist()
    crime_type_color_map = dict(zip(unique_crime_types, colors))

    # Add a 'color' column to the DataFrame with the corresponding color for each crime type
    data['color'] = data['Crm Cd Desc'].map(crime_type_color_map)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=data,
        get_position=["LON", "LAT"],
        get_radius=100,
        get_fill_color="color",
        pickable=True
    )

    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))


st.set_page_config(layout="wide")
st.title("LA Crime Data Visualization")
st.caption("Original data from [data.gov](https://catalog.data.gov/dataset/crime-data-from-2020-to-present)")
st.sidebar.header("Filters")

# Filter by year
years = list(df['DATE OCC'].dt.year.unique())
selected_year = st.sidebar.selectbox("Select a year", years)
filtered_df = df[df['DATE OCC'].dt.year == selected_year]

# Filter by crime type
selected_crime_types = st.sidebar.multiselect("Select crime types", df['Crm Cd Desc'].unique())
if selected_crime_types:
    filtered_df = filtered_df[filtered_df['Crm Cd Desc'].isin(selected_crime_types)]

# Filter by area
selected_areas = st.sidebar.multiselect("Select areas", df['AREA NAME'].unique())
if selected_areas:
    filtered_df = filtered_df[filtered_df['AREA NAME'].isin(selected_areas)]

# Filter by victim demographics
min_age, max_age = int(df['Vict Age'].min()), int(df['Vict Age'].max())
selected_age_range = st.sidebar.slider("Victim age range", min_age, max_age, (min_age, max_age))
filtered_df = filtered_df[(filtered_df['Vict Age'] >= selected_age_range[0]) & (filtered_df['Vict Age'] <= selected_age_range[1])]

selected_sex = st.sidebar.multiselect("Victim sex", df['Vict Sex'].unique())
if selected_sex:
    filtered_df = filtered_df[filtered_df['Vict Sex'].isin(selected_sex)]

# Display the map
display_map(filtered_df)

st.header("Crime Summary Statistics")
st.write(f"Total crimes: {len(filtered_df)}")

most_common_crime_type = filtered_df['Crm Cd Desc'].mode()
if not most_common_crime_type.empty:
    st.write(f"Most common crime type: {most_common_crime_type[0]}")
else:
    st.write("Most common crime type: N/A")

most_affected_area = filtered_df['AREA NAME'].mode()
if not most_affected_area.empty:
    st.write(f"Most affected area: {most_affected_area[0]}")
else:
    st.write("Most affected area: N/A")

# Crime type comparison chart
crime_type_counts = filtered_df['Crm Cd Desc'].value_counts().nlargest(20)  # Select the top 20 crimes
crime_type_chart_data = pd.DataFrame({"Crime Type": crime_type_counts.index, "Count": crime_type_counts.values})
crime_type_chart = alt.Chart(crime_type_chart_data).mark_bar().encode(
    x=alt.X("Count:Q", title="Count"),
    y=alt.Y("Crime Type:N", title="Crime Type", sort="-x"),
    tooltip=["Crime Type", "Count"],
).properties(
    title="Top 20 Crime Types",
    height=400,
    width=600,
)
st.altair_chart(crime_type_chart, use_container_width=True)

# Affected areas comparison chart
area_chart = alt.Chart(filtered_df).mark_bar().encode(
    x=alt.X('AREA NAME', sort='-y', axis=alt.Axis(title='Area')),
    y=alt.Y('count()', axis=alt.Axis(title='Number of Crimes'))
).properties(title="Affected Areas Comparison", width=600)
st.altair_chart(area_chart, use_container_width=True)


with st.expander("Crime Data Table"):
    start_index = st.number_input("Start index", min_value=0, max_value=len(filtered_df)-1, value=0, step=1)
    end_index = st.number_input("End index", min_value=1, max_value=len(filtered_df), value=min(1000, len(filtered_df)), step=1)
    st.write(filtered_df.iloc[start_index:end_index])



