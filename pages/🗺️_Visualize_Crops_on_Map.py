import streamlit as st
import pandas as pd
import pydeck as pdk
import os
from lat_long_finder import generate_lat_lon_csv

# Define the folder name
folder_name = "State Files"

# Check if the folder exists
if not os.path.exists(folder_name):
    # Create the folder
    os.makedirs(folder_name)
    print(f"Folder '{folder_name}' created.")
else:
    print(f"Folder '{folder_name}' already exists.")

df = pd.read_csv("crop_production.csv")

st.set_page_config("Map", page_icon="🗺️")
st.title("Crop Geographical Data")

# Sidebar filters
with st.sidebar:
    st.write("# Filter Data")
    state = st.selectbox("Select State: ", df["State_Name"].unique())
    crop_year = st.selectbox("Select Crop Year:", df["Crop_Year"].unique())
    crop = st.selectbox("Select Crop:", df["Crop"].unique())
    season = st.selectbox("Select Season:", df["Season"].unique())

lat_lon_file = f"State Files/lat_lon_{'_'.join(word for word in state.split())}.csv"

# If the file doesn't exist, then generate the latitude and longitude coordinates
# of the districts by calling the generate_lat_lon_csv from the lat_long_finder script
if not os.path.isfile(lat_lon_file):
    generate_lat_lon_csv(state)

lat_lon_df = pd.read_csv(lat_lon_file)
df = df[df["State_Name"] == state]

# Merge the dataframes on the District_Name key
df = pd.merge(df, lat_lon_df, on="District_Name")

# Filter dataframe based on user selections
filtered_df = df[
    (df["Crop_Year"] == crop_year) & (df["Crop"] == crop) & (df["Season"] == season)
]

st.write(filtered_df)

# Pydeck map visualization
view_state = pdk.ViewState(
    latitude=filtered_df["lat"].mean(),
    longitude=filtered_df["lon"].mean(),
    zoom=5,
    pitch=50,
)

# Pydeck Layer for showing cultivation area of each district
area_layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered_df,
    get_position=["lon", "lat"],
    get_radius="Area * 0.3",
    get_fill_color=[0, 0, 255, 100],
    pickable=True,
    auto_highlight=True,
)

# Pydeck Layer for showing production of each district
production_layer = pdk.Layer(
    "ColumnLayer",
    data=filtered_df,
    radius=3000,
    get_position=["lon", "lat"],
    get_elevation="Production * 5",
    get_fill_color=[255, 0, 0, 100],
    pickable=True,
    auto_highlight=True,
)


# Tooltip for pickable attribute
tooltip = {
    "html": "District: <b>{District_Name}</b>, Production: <b>{Production}</b>, Area: <b>{Area}</b>",
    "style": {
        "background": "grey",
        "color": "white",
        "font-family": '"Helvetica Neue", Arial',
        "z-index": "10000",
    },
}

# Render pydeck chart
st.pydeck_chart(
    pdk.Deck(
        layers=[area_layer, production_layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style=pdk.map_styles.CARTO_LIGHT,
    )
)
