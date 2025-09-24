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

# Sidebar filters with default values
with st.sidebar:
    st.write("# Filter Data")
    
    # Get unique values
    states = df["State_Name"].unique()
    years = df["Crop_Year"].unique()
    crops = df["Crop"].unique()
    seasons = df["Season"].unique()
    
    # Set default to Maharashtra (which has coordinate data)
    maharashtra_index = 0
    if "Maharashtra" in states:
        maharashtra_index = list(states).index("Maharashtra")
    
    # Set default to 2004 (which has data)
    year_2004_index = 0
    if 2004 in years:
        year_2004_index = list(years).index(2004)
    
    # Set default to Rice (which has data)
    rice_index = 0
    if "Rice" in crops:
        rice_index = list(crops).index("Rice")
    
    # Set default to Kharif (which has data)
    kharif_index = 0
    if "Kharif" in seasons:
        kharif_index = list(seasons).index("Kharif")
    
    state = st.selectbox("Select State: ", states, index=maharashtra_index)
    crop_year = st.selectbox("Select Crop Year:", years, index=year_2004_index)
    crop = st.selectbox("Select Crop:", crops, index=rice_index)
    season = st.selectbox("Select Season:", seasons, index=kharif_index)

lat_lon_file = f"State Files/lat_lon_{'_'.join(word for word in state.split())}.csv"

# If the file doesn't exist, then generate the latitude and longitude coordinates
# of the districts by calling the generate_lat_lon_csv from the lat_long_finder script
if not os.path.isfile(lat_lon_file):
    generate_lat_lon_csv(state)

lat_lon_df = pd.read_csv(lat_lon_file)
df = df[df["State_Name"] == state]

# Check if coordinates are missing and provide fallback
if lat_lon_df["lat"].isna().all() or lat_lon_df["lon"].isna().all():
    st.warning(f"⚠️ Coordinates not available. Using approximate coordinates for {state} districts.")
    
    # Fallback coordinates for different states
    state_coords = {
        'Maharashtra': {
            'AHMEDNAGAR': [19.0952, 74.7496],
            'AKOLA': [20.7006, 77.0086],
            'AMRAVATI': [20.9374, 77.7796],
            'AURANGABAD': [19.8762, 75.3433],
            'BEED': [18.9894, 75.7564],
            'BHANDARA': [21.1702, 79.6539],
            'BULDHANA': [20.5313, 76.1829],
            'CHANDRAPUR': [19.9615, 79.2961],
            'DHULE': [20.9013, 74.7774],
            'GADCHIROLI': [20.1806, 80.0039],
            'GONDIA': [21.4602, 80.1920],
            'HINGOLI': [19.7146, 77.1424],
            'JALGAON': [21.0077, 75.5626],
            'JALNA': [19.8410, 75.8864],
            'KOLHAPUR': [16.7050, 74.2433],
            'LATUR': [18.4088, 76.5604],
            'MUMBAI': [19.0760, 72.8777],
            'NAGPUR': [21.1458, 79.0882],
            'NANDED': [19.1383, 77.3210],
            'NANDURBAR': [21.3707, 74.2409],
            'NASHIK': [19.9975, 73.7898],
            'OSMANABAD': [18.1814, 76.0419],
            'PALGHAR': [19.6969, 72.7654],
            'PARBHANI': [19.2460, 76.4408],
            'PUNE': [18.5204, 73.8567],
            'RAIGAD': [18.5158, 73.1829],
            'RATNAGIRI': [16.9944, 73.3002],
            'SANGLI': [16.8524, 74.5815],
            'SATARA': [17.6805, 74.0183],
            'SINDHUDURG': [16.3615, 73.4004],
            'SOLAPUR': [17.6599, 75.9064],
            'THANE': [19.2183, 72.9781],
            'WARDHA': [20.7453, 78.6022],
            'WASHIM': [20.1110, 77.1330],
            'YAVATMAL': [20.4009, 78.1339]
        },
        'Andaman and Nicobar Islands': {
            'NICOBARS': [7.1395, 93.7947],
            'NORTH AND MIDDLE ANDAMAN': [12.9044, 92.9396],
            'SOUTH ANDAMANS': [11.7401, 92.6586]
        }
    }
    
    # Update the lat_lon_df with fallback coordinates
    if state in state_coords:
        for idx, row in lat_lon_df.iterrows():
            district = row['District_Name']
            if district in state_coords[state]:
                lat_lon_df.at[idx, 'lat'] = state_coords[state][district][0]
                lat_lon_df.at[idx, 'lon'] = state_coords[state][district][1]
    else:
        st.error(f"❌ No coordinate data available for {state}. Please select Maharashtra or Andaman and Nicobar Islands.")
        st.stop()

# Merge the dataframes on the District_Name key
df = pd.merge(df, lat_lon_df, on="District_Name")

# Filter dataframe based on user selections
filtered_df = df[
    (df["Crop_Year"] == crop_year) & (df["Crop"] == crop) & (df["Season"] == season)
]

# Remove rows with missing coordinates
filtered_df = filtered_df.dropna(subset=['lat', 'lon'])

if filtered_df.empty:
    st.error("❌ No data available for the selected filters.")
    st.info("💡 Try different filter combinations.")
else:
    st.write("**Filtered Data:**")
    st.write(filtered_df[['District_Name', 'Area', 'Production', 'lat', 'lon']])

    # Pydeck map visualization
    st.write("**🗺️ Interactive Map:**")
    
    view_state = pdk.ViewState(
        latitude=filtered_df["lat"].mean(),
        longitude=filtered_df["lon"].mean(),
        zoom=6,
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
        "html": "District: <b>{District_Name}</b><br/>Production: <b>{Production}</b><br/>Area: <b>{Area}</b>",
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
    
    st.info("💡 **Map Legend:** Blue circles show cultivation area, Red columns show production volume. Click on markers for details.")
