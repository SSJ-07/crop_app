import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

st.set_page_config(page_title="Graphs 2", page_icon=":bar_chart:")
df = pd.read_csv("crop_production.csv")

st.title("Exploratory Data Analysis")
st.write(df.head())

# Containers
st.header("Summary Statistics")
with st.container():
    st.write(df.describe())

st.header("Correlation Matrix")
with st.container():
    corr = df.corr(numeric_only=True)
    fig, ax = plt.subplots()
    sns.heatmap(corr, annot=True, ax=ax, cmap="coolwarm")
    st.pyplot(fig)

st.header("Crop Distribution")
with st.container():
    fig, ax = plt.subplots()
    df["Crop"].value_counts().plot(kind="bar", ax=ax)
    ax.set_title("Crop Distribution")
    ax.set_xlabel("Crops")
    ax.set_ylabel("Count")
    st.pyplot(fig)

st.header("Production by Season")
with st.container():
    filtered_df = df[df['Season'] != 'Whole Year']
    fig, ax = plt.subplots()
    sns.boxplot(x='Season', y='Production', data=filtered_df, ax=ax)
    ax.set_title("Production by Season")
    st.pyplot(fig)

st.header("Yield Analysis")
with st.container():
    df['Yield'] = df['Production'] / df['Area']
    fig, ax = plt.subplots()
    sns.histplot(df['Yield'], kde=True, ax=ax)
    ax.set_title("Yield Distribution")
    ax.set_xlabel("Yield (Production per unit area)")
    st.pyplot(fig)

st.header("Production by Crop Type")
with st.container():
    fig, ax = plt.subplots()
    crop_prod = df.groupby('Crop')['Production'].sum().reset_index()
    sns.barplot(x='Production', y='Crop', data=crop_prod, ax=ax)
    ax.set_title("Production by Crop Type")
    st.pyplot(fig)

st.header("Pair Plots by Crop and Season")
with st.container():
    selected_crop = st.selectbox("Select Crop for Pair Plot", df['Crop'].unique())
    selected_season = st.selectbox("Select Season for Pair Plot", df['Season'].unique())
    filtered_df = df[(df['Crop'] == selected_crop) & (df['Season'] == selected_season)]
    
    if not filtered_df.empty:
        fig = sns.pairplot(filtered_df)
        st.pyplot(fig)
    else:
        st.write("No data available for the selected crop and season.")

st.header("Production vs Area")
with st.container():
    crop_selected = st.selectbox("Select Crop for Scatter Plot", df["Crop"].unique())
    filtered_df = df[df["Crop"] == crop_selected]
    fig, ax = plt.subplots()
    sns.scatterplot(x="Area", y="Production", data=filtered_df, hue="Season", ax=ax)
    ax.set_title(f"Production vs Area for {crop_selected}")
    st.pyplot(fig)
