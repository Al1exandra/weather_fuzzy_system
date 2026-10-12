from datetime import datetime
import requests
import pandas as pd

def get_current_weather(city, api_key):

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
            "q": city,
            "appid": api_key,
            "units": "metric",
            "lang": "ru"
        }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        weather_info = {
            'city': city,
            'timestamp': datetime.now(),
            'temperature': data['main']['temp'],
            'feels_like': data['main']['feels_like'],
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'wind_speed': data['wind']['speed'],
            'description': data['weather'][0]['description']   
        }
        return weather_info
    except requests.RequestException as error:
        print("\nОшибка подключения для города", city)
        return None 
    
def get_historical_weather(city, latitude, longitude):

    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": "2021-01-01",
        "end_date": "2025-12-31",
        "daily": "temperature_2m_mean",
        "timezone": "Europe/Moscow"
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame({
            "date": data["daily"]["time"],
            "temperature": data["daily"]["temperature_2m_mean"]
        })

        filename = city.replace(" ", "_") + "_history.csv"
        df.to_csv(filename, index=False, encoding="utf-8-sig")

        return df

    except requests.RequestException as error:
        print("Ошибка получения истории для города", city)
        return None
    
def get_seasonal_norms(df):

    df["date"] = pd.to_datetime(df["date"])

    # определяем сезон по номеру месяца
    def get_season(month):
        if month in [12, 1, 2]:
            return "Зима"
        elif month in [3, 4, 5]:
            return "Весна"
        elif month in [6, 7, 8]:
            return "Лето"
        else:
            return "Осень"

    df["season"] = df["date"].dt.month.apply(get_season)

    seasonal_norms = df.groupby("season")["temperature"].mean()

    return seasonal_norms

def numeric_to_linguistic(value, var_name, city_name, season):

    if var_name == "temperature":

        if city_name == "Kazan":

            if season == "winter":
                if value < -25:
                    return "экстремально холодно"
                elif value < -15:
                    return "холодно"
                elif value < -5:
                    return "умеренно холодно"
                elif value < 0:
                    return "близко к нулю"
                else:
                    return "тепло для зимы"

            elif season == "summer":
                if value < 15:
                    return "холодно для лета"
                elif value < 20:
                    return "прохладно"
                elif value < 25:
                    return "комфортно"
                elif value < 30:
                    return "тепло"
                else:
                    return "жарко"
                
            elif season == "spring":
                if value < 0:
                    return "холодно"
                elif value < 10:
                    return "прохладно"
                elif value < 20:
                    return "комфортно"
                else:
                    return "тепло"

            elif season == "autumn":
                if value < 0:
                    return "холодно"
                elif value < 10:
                    return "прохладно"
                elif value < 20:
                    return "комфортно"
                else:
                    return "тепло"

# Формирование рекомендаций по погоде

def get_recommendation(quality, difference):
    recommendations = []

    if quality < 4:
        recommendations.append("Неблагоприятные погодные условия")

    if difference >= 5:
        recommendations.append("Необычно тепло для этого сезона")
    elif difference <= -5:
        recommendations.append("Необычно холодно для этого сезона")

    if quality >= 7 and abs(difference) < 5:
        recommendations.append("Погодные условия близки к норме")

    if len(recommendations) == 0:
        recommendations.append("Существенных отклонений не выявлено")

    return recommendations