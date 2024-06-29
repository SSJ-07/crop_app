import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pydeck as pdk
import os
from lat_long_finder import generate_lat_lon_csv
import pickle
import joblib

st.set_page_config("ML Model", page_icon= "🤖")


df = pd.read_csv("crop_production.csv")
model = joblib.load("model2.pkl")
label_encoders = joblib.load("label_encoders2.pkl")


st.title("Crop Yield Prediction")

# district = st.selectbox("District name", ["AHMEDNAGAR", "PUNE", ])
maharashtra_districts = df[df["State_Name"] == "Maharashtra"]["District_Name"].unique()
district = st.selectbox("District name", maharashtra_districts)
crops = df["Crop"].unique()
seasons = df["Season"].unique()
crop = st.selectbox("Crop", crops)
season = st.selectbox("Season", seasons)
area = st.number_input("Area in hectares", min_value=0.0)

input_data = pd.DataFrame(
    {
        "District_Name": [district],
        "Season": [season],
        "Crop": [crop],
        "Area": [area],
    }
)

# Debug: Check input data before encoding
st.write("Input Data before encoding:", input_data)

# Preprocessing the input data
for column in ["District_Name", "Season", "Crop"]:
    if column in label_encoders:
        le = label_encoders[column]
        input_data[column] = le.transform(input_data[column])

    # input_data[column] = label_encoders.transform(input_data[column])

# Debug: Check input data after encoding
st.write("Input Data after encoding:", input_data)

if st.button("Predict"):
    predictions = model.predict(input_data)
    st.write(f"Predicted Production: {predictions[0]} kilotons")
