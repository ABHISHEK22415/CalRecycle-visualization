import streamlit as st
import geopandas as gpd
from urllib.parse import quote
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static

from waste_predictor import WastePredictor

st.set_page_config(layout="wide")

waste_predictor = WastePredictor()

data = waste_predictor.load_data()

business_groups = data['Business Group'].unique()
jurisdictions = data['Jurisdiction(s)'].unique()

# Add dynamic and animated heading to the Streamlit app
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
st.markdown(
    """
    <style>
        @keyframes slide-in {
            0% {
                transform: translateX(-100%);
            }
            100% {
                transform: translateX(0);
            }
        }
        .dynamic-heading {
            animation: slide-in 2s ease;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Display the dynamic and animated heading
st.markdown(
    """
    <h1 class="dynamic-heading">Welcome to CalRecycle Data Analysis Tool</h1>
    """,
    unsafe_allow_html=True
)

# Map
# Read GeoJSON data
url = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries/USA/CA/'
counties = [
    'Los Angeles', 'Alameda', 'Alpine',
    'Amador', 'Butte', 'Calaveras',
    'Colusa', 'Contra Costa',
    'Del Norte', 'El Dorado', 'Fresno',
    'Glenn', 'Humboldt', 'Imperial',
    'Inyo', 'Kern', 'Kings',
    'Lake', 'Lassen', 'Madera',
    'Marin', 'Mariposa', 'Mendocino',
    'Merced', 'Modoc', 'Mono',
    'Monterey', 'Napa', 'Nevada',
    'Orange', 'Placer', 'Plumas',
    'Riverside', 'Sacramento',
    'San Benito', 'San Diego',
    'San Francisco', 'San Joaquin',
]
geojson_data = {}
for county in counties:
    county_geojson = gpd.read_file(url + quote(f'{county}.geo.json'))
    geojson_data[county] = county_geojson

# Create a Folium map
m = folium.Map(location=[37.7749, -122.4194], zoom_start=6)

st.markdown(
    """
    <h2 class="dynamic-heading">Explore And Compare Waste Disposal By County And Business Type</h2>
    """,
    unsafe_allow_html=True
)

# Create a multi-select box where users can select counties to highlight
selected_counties = st.multiselect('Select counties', counties + ['All'])
map_bg = st.multiselect('Select a business group', business_groups)

f_data = pd.DataFrame()
g_data = []

# Highlight the selected counties
for county in selected_counties:
    if county == 'All':
        for county in counties:
            g_data.append(geojson_data[county])
            for bg in map_bg:
                tons_disposed = \
                    data[(data['Jurisdiction(s)'] == county + " (Countywide)") & (data['Business Group'] == bg)][
                        'Tons Disposed']
                print(tons_disposed)
                item = {
                    'County': county,
                    'Tons Disposed': float(tons_disposed.iloc[1] if len(tons_disposed) > 1 else tons_disposed.iloc[1])
                }
                # print(item)
                f_data = pd.concat([f_data, pd.DataFrame([item])], ignore_index=True)
    else:
        g_data.append(geojson_data[county])
        for bg in map_bg:
            tons_disposed = \
            data[(data['Jurisdiction(s)'] == county + " (Countywide)") & (data['Business Group'] == bg)][
                'Tons Disposed']
            print(tons_disposed)
            item = {
                'County': county,
                'Tons Disposed': float(tons_disposed)
            }
            # print(item)
            f_data = pd.concat([f_data, pd.DataFrame([item])], ignore_index=True)

if len(selected_counties) > 0 and len(map_bg) > 0:
    # Concatenate all GeoDataFrames into a single one
    g_data_combined = pd.concat(g_data)
    bins = list(f_data["Tons Disposed"].quantile([0, 0.33, 0.66, 1]))
    folium.Choropleth(
        geo_data=g_data_combined.__geo_interface__,
        name="choropleth",
        data=f_data,
        columns=["County", "Tons Disposed"],
        key_on="feature.properties.name",
        fill_color="BuPu",
        fill_opacity=0.9,
        line_opacity=0.8,
        bins=bins,
        legend_name="Waste Disposed (Tons)",
    ).add_to(m)

# Render the map in Streamlit
folium_static(m, width=1270, height=600)

st.markdown(
    """
    <h2 class="dynamic-heading">Analysis Of Waste Disposal By County</h2>
    """,
    unsafe_allow_html=True
)

# Embed the Flourish visualization in Streamlit without the Flourish credit marker
flourish_iframe = "<iframe src='https://flo.uri.sh/visualisation/14069038/embed' title='Interactive or visual content' class='flourish-embed-iframe' frameborder='0' scrolling='no' style='width:100%;height:600px;' sandbox='allow-same-origin allow-forms allow-scripts allow-downloads allow-popups allow-popups-to-escape-sandbox allow-top-navigation-by-user-activation'></iframe>"

# Embed the Flourish visualization in Streamlit
st.markdown(flourish_iframe, unsafe_allow_html=True)

st.markdown(
    """
    <h2 class="dynamic-heading">Predict Waste Generation And Distribution For Your Business</h2>
    """,
    unsafe_allow_html=True
)

# Intelligence

with st.form(key='my_form'):
    selected_bg = st.selectbox('Select a business group', business_groups)
    selected_j = st.selectbox('Select a jurisdiction', jurisdictions)
    num_employees = st.number_input('Number of employees', min_value=0, max_value=1000000, value=10)
    generate_button = st.form_submit_button(label='Predict Waste Distribution')

if generate_button:
    print(selected_bg, selected_j, num_employees)

    user_data = pd.DataFrame({
        'Business Group': [selected_bg],
        'Jurisdiction(s)': [selected_j],
        'Employee Count': [num_employees]
    })
    predictions = waste_predictor.predict(user_data)
    labels = [f'{k} ({v:.2f})' for k, v in predictions.items()]  # modify labels to include weight
    sizes = predictions.values()

    col1, col2 = st.columns(2)  # Create two columns

    with col1:
        st.subheader(
            f'Predicted Waste Distribution For Your Business'
        )

        fig1, ax1 = plt.subplots()
        ax1.pie(
            sizes,
            labels=labels,
            autopct='%1.1f%%',
            startangle=90
        )
        ax1.axis('equal')

        st.pyplot(fig1)

    # Filter the dataset based on the selected business group and jurisdiction
    filtered_data = data[(data['Business Group'] == selected_bg) & (data['Jurisdiction(s)'] == selected_j)]

    # Assuming your dataset has a column for each waste category with weights
    dataset_values = [filtered_data[k].sum() for k in predictions.keys()]
    labels_dataset = [f'{k} ({v:.2f})' for k, v in zip(predictions.keys(), dataset_values)]

    with col2:
        st.subheader(
            f'Observed Waste Distribution For {selected_bg} Business Type In {selected_j}'
        )

        fig2, ax2 = plt.subplots()
        ax2.pie(
            dataset_values,
            labels=labels_dataset,
            autopct='%1.1f%%',
            startangle=90
        )
        ax2.axis('equal')

        st.pyplot(fig2)
