import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Crop Data Analysis", page_icon=":bar_chart:")
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
selected_crop = st.selectbox("Select Crop for Distribution", df["Crop"].unique())
with st.container():
    filtered_df = df[df["Crop"] == selected_crop]
    fig, ax = plt.subplots()
    sns.countplot(
        data=filtered_df,
        x="State_Name",
        order=filtered_df["State_Name"].value_counts().index,
        ax=ax,
    )
    ax.set_title(f"Distribution of {selected_crop} across States")
    ax.set_xlabel("States")
    ax.set_ylabel("Count")
    plt.setp(ax.get_xticklabels(), rotation=45)
    st.pyplot(fig)

st.header("Production by Season")
selected_crop_season = st.selectbox(
    "Select Crop for Production by Season", df["Crop"].unique()
)
with st.container():
    filtered_df = df[
        (df["Crop"] == selected_crop_season) & (df["Season"] != "Whole Year")
    ]
    fig, ax = plt.subplots()
    sns.boxplot(x="Season", y="Production", data=filtered_df, ax=ax)
    ax.set_title(f"Production by Season for {selected_crop_season}")
    st.pyplot(fig)


# st.header("Production by Crop Type")
# with st.container():
#     fig, ax = plt.subplots()
#     crop_prod = df.groupby("Crop")["Production"].sum().reset_index()
#     sns.barplot(x="Production", y="Crop", data=crop_prod, ax=ax)
#     ax.set_title("Production by Crop Type")
#     st.pyplot(fig)

st.header("Pair Plots by Crop and Season")
with st.container():
    selected_crop = st.selectbox("Select Crop for Pair Plot", df["Crop"].unique())
    selected_season = st.selectbox("Select Season for Pair Plot", df["Season"].unique())
    filtered_df = df[(df["Crop"] == selected_crop) & (df["Season"] == selected_season)]

    if not filtered_df.empty:
        fig = sns.pairplot(filtered_df)
        st.pyplot(fig)
    else:
        st.write("No data available for the selected crop and season.")

st.header("Production vs Area")
with st.container():
    crop_selected = st.selectbox("Select Crop for Scatter Plot", df["Crop"].unique())
    filtered_df = df[(df["Crop"] == crop_selected)]
    filtered_df = df[(df["Season"] != "Whole Year")]
    fig, ax = plt.subplots()
    sns.scatterplot(x="Area", y="Production", data=filtered_df, hue="Season", ax=ax)
    ax.set_title(f"Production vs Area for {crop_selected}")
    st.pyplot(fig)

st.header("Yield Analysis")
selected_crop_yield = st.selectbox(
    "Select Crop for Yield Analysis", df["Crop"].unique()
)
with st.container():
    filtered_df = df[df["Crop"] == selected_crop_yield].copy()
    filtered_df["Yield"] = filtered_df["Production"] / filtered_df["Area"]
    fig, ax = plt.subplots()
    sns.histplot(filtered_df["Yield"], kde=True, ax=ax)
    ax.set_title(f"Yield Distribution for {selected_crop_yield}")
    ax.set_xlabel("Yield (Production per unit area)")
    st.pyplot(fig)
