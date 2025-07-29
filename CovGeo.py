import requests
import streamlit as st
import pandas as pd

st.title("Ayush Goyal")
st.markdown("<h1><b>Place To Coordinates Converter</b></h1>", unsafe_allow_html=True)
def get_lat_lon(place_name, api_key):
    url = "https://api.opencagedata.com/geocode/v1/json"
    params = {
        'q': place_name,
        'key': api_key,
        'limit': 1,
        'no_annotations': 1
    }
    response = requests.get(url, params=params)
    data = response.json()

    if data['results']:
        location = data['results'][0]['geometry']
        return location['lat'], location['lng']
    else:
        return None

# Example usage
api_key = "8366f68deede4707aceeda298dbec08c"
inp = st.text_input('Any Place Name', key='blabla', placeholder='Taj Mahal, Lake View, etc...')
coordinates = get_lat_lon(inp, api_key)

if coordinates:
    lat = coordinates[0]
    lon = coordinates[1]
    st.markdown(f"<b>Latitude: {lat}, Longitude: {lon}</b>", unsafe_allow_html=True)
    df = pd.DataFrame({'lat':[lat], 'lon':[lon]})
    st.map(df)

st.markdown("~ Project Done By <b>Ayush Goyal</b>", unsafe_allow_html=True)
