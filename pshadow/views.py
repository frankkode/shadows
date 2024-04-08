from django.shortcuts import render
import geopandas as gpd
from keplergl import KeplerGl
import pandas as pd
from statsmodels.tsa.api import VAR
import numpy as np
import math
import pytz
from suncalc import get_position
from shapely.geometry import Polygon
import pybdshadow
import warnings
warnings.filterwarnings('ignore')

def dashboard(request):
    # Add your logic to render the dashboard HTML page
    return render(request, 'dashboard.html')

def layer1_view(request):
    geo_df_1 = gpd.read_file('/Users/masabosimplicefrank/wong-shadow/parking/pshadow/primary_parking_space.geojson')
    return render(request, 'layer1.html', {'geojson_data': geo_df_1.to_json()})

def layer2_view(request):
    map_1 = KeplerGl(height=600)
    geo_df = gpd.read_file('parking/pshadow/ucam_parking_synth_roof.geojson')
    geo_df['floor'] = 1
    geo_df['height'] = 1
    geo_df['x'] = geo_df['geometry'].apply(lambda g: g.centroid.x)
    geo_df['y'] = geo_df['geometry'].apply(lambda g: g.centroid.y)
    map_1.add_data(data=geo_df, name='geo_data')
    return render(request, 'layer2.html', {'map_instance': map_1})











warnings.filterwarnings('ignore')

def layer3_view(request):
    # Load GeoDataFrame with rooftop geometries
    geo_df = gpd.read_file('parking/pshadow/ucam_parking_synth_roof.geojson')

    # Define the date and city
    date_str = '2023-06-15 16:00:00'
    city = 'Europe/Madrid'
    timezone = pytz.timezone(city)
    date = pd.to_datetime(date_str).tz_localize('UTC').tz_convert(timezone)

    # Compute shadows and sunlight for all rooftops
    geo_projected_df = all_sunshadeshadow_sunlight(date, geo_df)

    # Define the date range for analysis
    date_str = '2022-07-15 07:00:00'
    timezone = pytz.timezone(city)
    date = pd.to_datetime(date_str).tz_localize('UTC').tz_convert(timezone)
    end_date = date + pd.DateOffset(hours=10)
    date_range = pd.date_range(start=date, end=end_date, freq='H')

    # Create a DataFrame with date and time values
    df = pd.DataFrame({'datetime': date_range})
    df['datetime'] = df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S %Z%z')

    # Save the DataFrame to a CSV file
    df.to_csv('data.csv', index=False)

    # Load the parking space GeoDataFrame
    geo_df_2 = gpd.read_file('/Users/masabosimplicefrank/wong-shadow/ucam_parking_all_spaces.geojson')
    geo_df_2 = geo_df_2.set_crs(epsg=4326)

    # Loop through each hour and compute coverage rates
    for i in range(len(date_range)):
        current_date = date_range[i]
        shadows = all_sunshadeshadow_sunlight(current_date, geo_df)

        # Calculate coverage rates...
        shadows_crs = "EPSG:4326"  # Change this to the appropriate CRS if it's different
        shadows.crs = shadows_crs

        coverage_rates = []

        for index, parking_space in geo_df_2.iterrows():
            parking_space_gdf = gpd.GeoDataFrame(geometry=[parking_space.geometry])
            parking_space_gdf = parking_space_gdf.set_crs(crs=shadows_crs)
            parking_space_gdf = parking_space_gdf.to_crs(epsg=shadows.crs.to_epsg())

            intersection = gpd.overlay(parking_space_gdf, shadows, how='intersection')
            intersection.crs = shadows.crs

            intersection_area = intersection.geometry.area.sum()
            parking_space_area = parking_space_gdf.geometry.area.sum()

            coverage_rate = intersection_area / parking_space_area

            coverage_rates.append(coverage_rate)

        geo_df_2[f'coverage_rate_{current_date.strftime("%H:%M:%S")}'] = coverage_rates

        # Save GeoDataFrame to a GeoJSON file
        geo_df_2.to_file(f"media/geo_df_3.geojson", driver="GeoJSON")

    return render(request, 'layer3.html')


def layer4_view(request):
    Farcas_data = pd.read_excel("Farcas_data.xlsx")
    Farcas_data = Farcas_data.rename(columns={'Temperature°C': 'Farcas_cabin_temp'})
    his_temp = pd.read_excel("historical_weather_data_MU.xlsx")
    target_data_1 = Farcas_data[(Farcas_data['DateTime'] >= '2023-06-15 00:00:00') & (Farcas_data['DateTime'] <= '2023-06-15 23:00:00')]
    target_data_1['DateTime'] = pd.to_datetime(target_data_1['DateTime'])
    target_data_1.set_index('DateTime', inplace=True)
    target_data_1.index = target_data_1.index.floor('H')
    target_data_1 = target_data_1.drop(columns=['index', 'No.'])
    target_data_2 = his_temp[(his_temp['DateTime'] >= '2023-06-15 00:00:00') & (his_temp['DateTime'] <= '2023-06-15 23:00:00')]
    target_data_2['DateTime'] = pd.to_datetime(target_data_2['DateTime'])
    target_data_2.set_index('DateTime', inplace=True)
    target_data_2 = target_data_2.drop(columns=['index', 'App_temper (°C)','Rain (mm)','Windspeed (km/h)'])
    target_data = pd.merge(target_data_1, target_data_2, on='DateTime', how='inner')
    all_data = target_data[['Farcas_cabin_temp', 'Temperature (°C)']]
    target_data_differenced = all_data.diff().dropna()
    model_fitted = VAR(target_data_differenced).fit(5)
    forecast_steps = 24
    forecast_input = target_data_differenced.values[-5:]
    fc = model_fitted.forecast(y=forecast_input, steps=forecast_steps)
    forecast_index = pd.date_range(start=target_data.index[-1] + pd.Timedelta(hours=1), periods=forecast_steps, freq='H')
    target_data_forecast = pd.DataFrame(fc, index=forecast_index, columns=[f'{col}_1d' for col in all_data.columns])
    def invert_transformation(train_data, forecast_data):
        forecast_result = forecast_data.copy()
        columns = train_data.columns
        for col in columns:
            forecast_result[f'{col}_1d'] = train_data[col].iloc[-1] + forecast_result[f'{col}_1d'].cumsum()
        return forecast_result
    target_data_results = invert_transformation(all_data, target_data_forecast)
    target_data_results.to_csv("Temp_data.csv", index=False)
    return render(request, 'layer4.html')

def layer5_view(request):
    geo_df = gpd.read_file("geo_df_5.geojson")
    occupied_lots = geo_df[geo_df['occupied']]
    unoccupied_lots = geo_df[~geo_df['occupied']]
    temperature_data = pd.read_csv("Temp_data.csv")

    context = {
        'occupied_lots': occupied_lots,
        'unoccupied_lots': unoccupied_lots,
        'temperature_data': temperature_data,
    }

    return render(request, 'layer5.html', context)
