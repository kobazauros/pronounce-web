import pandas as pd
import streamlit as st

# Set page configuration (optional)
st.set_page_config(page_title="Streamlit Table Example", layout="wide")

st.title('Sample Formant Analysis')

df = pd.read_csv('analysis_vowels/final_thesis_data.csv') 
st.dataframe(df, use_container_width=True)
