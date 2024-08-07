import streamlit as st


st.set_page_config("Home", page_icon=":home:")
# st.title("Welcome")
# st.subheader("Test code")


# make changes to the EDA
# Add all the districts, seasons(remember the blanks), crops to the ML model
#

# Stream response with regional language
# Try catch block for ML model error
# dont use hexagon layer

# Use interactive plots
# add units at x and y labels
# Check out the map themes, change colour for column and area layer
# make the prediction yield and msp buttons the same
# use markdown to make highlight some part for example the prediction
# try connecting streamlit app to a google sheet/another file/ air table, if u change the MSP in the file locally and push it
# proper documentation - technical and product both
# make a flowing chatbot
# government policies for them


def app():
    st.title("Welcome to the Crop Yield Analysis and Prediction App")

    # Project Description
    st.header("Project Overview")
    st.write(
        """
        This application provides various features to explore and analyze crop production data.
        It leverages machine learning models to predict crop yield and calculate the Minimum Support Price (MSP) for various crops.
    """
    )

    # Features Section
    st.header("Features")
    st.write(
        """
        - **Exploratory Data Analysis (EDA)**: Gain insights into crop production data with interactive visualizations.
        - **Geographical Data Visualization (Map)**: Visualize crop data geographically using interactive maps.
        - **Machine Learning Model (ML Model)**: Predict crop yield and calculate MSP based on selected inputs.
    """
    )

    # Demo Use Cases Section
    st.header("Demo Use Cases")
    st.write(
        """
        1. **Understanding Crop Distribution**: Select a crop to see its distribution across different states.
        2. **Analyzing Production by Season**: Choose a crop to analyze its production across different seasons.
        3. **Yield Analysis**: Select a crop to view its yield distribution across various states.
        4. **Predicting Crop Yield**: Use the ML model to predict the yield for a selected crop based on input parameters.
        5. **Calculating MSP**: Predict the MSP for a crop by multiplying its yield with the predefined MSP value.
    """
    )

    # Instructions Section
    st.header("How to Use the App")
    st.write(
        """
        1. **Navigate**: Use the sidebar to navigate between different sections of the app.
        2. **Select Inputs**: Provide necessary inputs like crop type, season, and area to generate predictions and visualizations.
        3. **Explore**: Interact with the visualizations to gain insights into crop production data.
        4. **Predict**: Use the ML model to predict crop yield and calculate MSP.
    """
    )

    # Footer
    st.write("---")
    st.write(
        "Developed by Sumedh Jadhav. For more information, contact sumedh.sa.jadhav@gmail.com."
    )


# Run the app function to display the content
if __name__ == "__main__":
    app()
