import streamlit as st
import pandas as pd
from lat_long_finder import generate_lat_lon_csv
import joblib

st.set_page_config("ML Model", page_icon="🤖")


df = pd.read_csv("crop_production.csv")
model = joblib.load("model2.pkl")
label_encoders = joblib.load("label_encoders2.pkl")


st.title("Maharashtra Crop Yield Prediction")

# district = st.selectbox("District name", ["AHMEDNAGAR", "PUNE", ])
maharashtra_districts = df[df["State_Name"] == "Maharashtra"]["District_Name"].unique()
district = st.selectbox("District name", maharashtra_districts)
crops = df["Crop"].unique()
seasons = df["Season"].unique()
crop = st.selectbox("Crop", crops)
season = st.selectbox("Season", seasons)
area = st.number_input("Area in Hectares", min_value=1.0)

input_data = pd.DataFrame(
    {
        "District_Name": [district],
        "Season": [season],
        "Crop": [crop],
        "Area": [area],
    }
)

# Debug: Check input data before encoding
# st.write("Input Data before encoding:", input_data)

# Preprocessing the input data
for column in ["District_Name", "Season", "Crop"]:
    if column in label_encoders:
        le = label_encoders[column]
        try:
            input_data[column] = le.transform(input_data[column])
            n = 0
        except ValueError:
            st.write("Crop not grown in this district")
            n = 1

    # input_data[column] = label_encoders.transform(input_data[column])

# Debug: Check input data after encoding
# st.write("Input Data after encoding:", input_data)
if n != 1:

    if st.button("Predict Yield in Kilotons"):
        predictions = model.predict(input_data)
        st.write(f"Predicted Production: {predictions[0]:.2f} kilotons")


# MSP caluclator
msp_values = {
    "Arecanut": None,
    "Other Kharif pulses": None,
    "Rice": 2300,
    "Banana": None,
    "Cashewnut": None,
    "Coconut": None,
    "Dry ginger": None,
    "Sugarcane": 340,
    "Sweet potato": None,
    "Tapioca": None,
    "Black pepper": None,
    "Dry chillies": None,
    "other oilseeds": None,
    "Turmeric": None,
    "Maize": 2225,
    "Moong(Green Gram)": 8682,
    "Urad": 7400,
    "Arhar/Tur": 7550,
    "Groundnut": 6783,
    "Sunflower": 7280,
    "Bajra": 2500,
    "Castor seed": None,
    "Cotton(lint)": 7121,
    "Horse-gram": None,
    "Jowar": 3371,
    "Korra": None,
    "Ragi": 4290,
    "Tobacco": None,
    "Gram": 5335,
    "Wheat": 2125,
    "Masoor": 6000,
    "Sesamum": 7307,
    "Linseed": None,
    "Safflower": 5215,
    "Onion": None,
    "other misc. pulses": None,
    "Samai": None,
    "Small millets": None,
    "Coriander": None,
    "Potato": None,
    "Other Rabi pulses": None,
    "Soyabean": 4892,
    "Beans & Mutter(Vegetable)": None,
    "Bhindi": None,
    "Brinjal": None,
    "Citrus Fruit": None,
    "Cucumber": None,
    "Grapes": None,
    "Mango": None,
    "Orange": None,
    "other fibres": None,
    "Other Fresh Fruits": None,
    "Other Vegetables": None,
    "Papaya": None,
    "Pome Fruit": None,
    "Tomato": None,
    "Rapeseed & Mustard": 5450,
    "Mesta": None,
    "Cowpea(Lobia)": None,
    "Lemon": None,
    "Pome Granet": None,
    "Sapota": None,
    "Cabbage": None,
    "Peas (vegetable)": None,
    "Niger seed": 6930,
    "Bottle Gourd": None,
    "Sannhamp": None,
    "Varagu": None,
    "Garlic": None,
    "Ginger": None,
    "Oilseeds total": None,
    "Pulses total": None,
    "Jute": 4450,
    "Peas & beans (Pulses)": None,
    "Blackgram": None,
    "Paddy": 1868,
    "Pineapple": None,
    "Barley": 1600,
    "Khesari": None,
    "Guar seed": None,
    "Moth": None,
    "Other Cereals & Millets": None,
    "Cond-spcs other": None,
    "Turnip": None,
    "Carrot": None,
    "Redish": None,
    "Arcanut (Processed)": None,
    "Atcanut (Raw)": None,
    "Cashewnut Processed": None,
    "Cashewnut Raw": None,
    "Cardamom": None,
    "Rubber": None,
    "Bitter Gourd": None,
    "Drum Stick": None,
    "Jack Fruit": None,
    "Snak Guard": None,
    "Pump Kin": None,
    "Tea": None,
    "Coffee": None,
    "Cauliflower": None,
    "Other Citrus Fruit": None,
    "Water Melon": None,
    "Total foodgrain": None,
    "Kapas": None,
    "Colocosia": None,
    "Lentil": None,
    "Bean": None,
    "Jobster": None,
    "Perilla": None,
    "Rajmash Kholar": None,
    "Ricebean (nagadal)": None,
    "Ash Gourd": None,
    "Beet Root": None,
    "Lab-Lab": None,
    "Ribed Guard": None,
    "Yam": None,
    "Apple": None,
    "Peach": None,
    "Pear": None,
    "Plums": None,
    "Litchi": None,
    "Ber": None,
    "Other Dry Fruit": None,
    "Jute & mesta": None,
}

if st.button("Predict Revenue"):
    if crop in msp_values and msp_values[crop] is not None:
        predicted_production = model.predict(input_data)
        msp = msp_values[crop] * predicted_production * 10000
        st.write(f"Predicted Revenue: ₹{msp[0]:.2f}")
    elif crop in msp_values and msp_values[crop] is None:
        st.markdown("MSP value for the selected crop is not available.")
        # st.popover
        # st.progress
        # with st.spinner
