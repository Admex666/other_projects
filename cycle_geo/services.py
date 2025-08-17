def slope_and_elevation(city, country):
    import requests
    from geopy.geocoders import Nominatim
    import numpy as np
    import time

    geolocator = Nominatim(user_agent="geoapi")
    location = geolocator.geocode(f"{city}, {country}")
    if location is None:
        print(f"Nem található a város: {city}, {country}")
        return np.nan, np.nan, np.nan, np.nan

    lat_center, lon_center = location.latitude, location.longitude
    print(f"Latitude: {lat_center}, Longitude: {lon_center}")

    # Magasság a középponton
    url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat_center},{lon_center}"
    response = requests.get(url).json()
    elevation = response['results'][0]['elevation']
    print(f'Elevation: {elevation}')

    # Város körüli rácspontok 5 km sugarú körben
    radius = 5  # km
    latitudes = np.linspace(lat_center - radius/110.574, lat_center + radius/110.574, num=3)
    longitudes = np.linspace(lon_center - radius/111.320, lon_center + radius/111.320, num=3)

    # Koordináták generálása
    coordinates = [(lat, lon) for lat in latitudes for lon in longitudes]

    def get_elevation(lat, lon):
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
        try:
            time.sleep(0.33)
            response = requests.get(url)
            data = response.json()
            if "results" in data and len(data["results"]) > 0:
                return data["results"][0]["elevation"]
            else:
                return np.nan
        except:
            return np.nan

    elevations = [get_elevation(lat, lon) for lat, lon in coordinates]

    # Számítsd ki a magasságkülönbségeket
    elevation_diff = np.diff(elevations)
    average_slope = np.nan
    if len(elevation_diff) > 0:
        average_slope = np.mean(np.abs(elevation_diff))
    
    print(f"Average Slope: {average_slope} meters")

    return lat_center, lon_center, average_slope, elevation

# Population
def population(country):
    import requests

    api_url = f'https://api.api-ninjas.com/v1/population?country={country}'
    response = requests.get(api_url, headers={'X-Api-Key': 'OnFySqSsla3cRc2nFaPGsQ==e3Jphlk1JxsiUO6u'})
    if response.status_code == requests.codes.ok:
        try:
            pop = response.json()['historical_population'][0]['population']
            print(f'{pop/1_000_000} million')
            return pop
        except:
            return None
    else:
        print("Error:", response.status_code, response.text)
        return None
    
def temperature(lat, lon):
	import openmeteo_requests
	import pandas as pd
	import requests_cache
	from retry_requests import retry

	try:
		# Setup the Open-Meteo API client with cache and retry on error
		cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
		retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
		openmeteo = openmeteo_requests.Client(session = retry_session)

		# Make sure all required weather variables are listed here
		# The order of variables in hourly or daily is important to assign them correctly below
		url = "https://archive-api.open-meteo.com/v1/archive"
		params = {
			"latitude": lat,
			"longitude": lon,
			"start_date": "2024-08-13",
			"end_date": "2025-08-13",
			"hourly": "temperature_2m",
		}
		responses = openmeteo.weather_api(url, params=params)

		# Process first location. Add a for-loop for multiple locations or weather models
		response = responses[0]

		# Process hourly data. The order of variables needs to be the same as requested.
		hourly = response.Hourly()
		hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()

		hourly_data = {"date": pd.date_range(
			start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
			end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
			freq = pd.Timedelta(seconds = hourly.Interval()),
			inclusive = "left"
		)}

		hourly_data["temperature_2m"] = hourly_temperature_2m

		hourly_dataframe = pd.DataFrame(data = hourly_data)
		#print("\nHourly data\n", hourly_dataframe)

		q1 = hourly_dataframe['temperature_2m'].quantile(0.25)
		median = hourly_dataframe['temperature_2m'].quantile(0.50)
		q3 = hourly_dataframe['temperature_2m'].quantile(0.75)

		print(f'25th perc temperature: {q1:.1f}')
		print(f'Average temperature: {median:.1f}')
		print(f'75th perc temperature: {q3:.1f}')

		return q1, median, q3
	except:
		return None, None, None