import numpy as np
import matplotlib.pyplot as plt
import skfuzzy as fuzz
import skfuzzy.control as ctrl
import openmeteo_requests
import os
from dotenv import load_dotenv
from datetime import datetime
from func import get_current_weather, get_historical_weather, get_seasonal_norms, numeric_to_linguistic, get_recommendation

# Этап 1. Получение текущих данных из OpenWeatherMap API
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

cities = ["Kazan", "Moscow", "Saint Petersburg"]
current_data = {}
for city in cities:
    data = get_current_weather(city, API_KEY)
    if data:
        current_data[city] = data
        print(f"{city}: {data['temperature']}°C, {data['description']}")

# Этап 2. Получение исторических данных (Open-Meteo API)
city_coordinates = {"Kazan": (55.7961, 49.1064), "Moscow": (55.7558, 37.6173),"Saint Petersburg": (59.9343, 30.3351)}

historical_data = {}

for city, coordinates in city_coordinates.items():
    df = get_historical_weather(city, coordinates[0], coordinates[1])

    if df is not None:
        historical_data[city] = df
        print("\nИсторические данные:", city)
        print("Количество записей:", len(df))
        print(df.head())

# Этап 3. Расчет климатических норм по сезонам
seasonal_data = {}

for city, df in historical_data.items():

    norms = get_seasonal_norms(df)
    seasonal_data[city] = norms

    print("\nСезонные нормы температуры:", city)
    print(norms.round(1))

# Этап 4. Преобразование чисел в лингвистические переменные

print("\nЛингвистические характеристики температуры")

print("\nКазань:")
print("Зимой:", "-10°C - ", numeric_to_linguistic(-10, "temperature", "Kazan", "winter"))
print("Летом:", "30°C - ", numeric_to_linguistic(30, "temperature", "Kazan", "summer"))
print("Весной:", "6°C - ", numeric_to_linguistic(6, "temperature", "Kazan", "spring"))
print("Осенью:", "22°C - ", numeric_to_linguistic(22, "temperature", "Kazan", "autumn"))

# Этап 5. Реализация нечеткой системы с учетом сезонов

temperature = ctrl.Antecedent(np.arange(-40, 46, 1), "temperature")
humidity = ctrl.Antecedent(np.arange(0, 101, 1), "humidity")
wind_speed = ctrl.Antecedent(np.arange(0, 31, 1), "wind_speed")

comfort = ctrl.Consequent(np.arange(0, 11, 1), "comfort")

# температура
temperature["cold"] = fuzz.trapmf(temperature.universe, [-40, -40, 0, 10])
temperature["normal"] = fuzz.trimf(temperature.universe, [5, 20, 30])
temperature["hot"] = fuzz.trapmf(temperature.universe, [25, 35, 45, 45])

# влажность
humidity["low"] = fuzz.trapmf(humidity.universe, [0, 0, 30, 45])
humidity["normal"] = fuzz.trimf(humidity.universe, [30, 50, 70])
humidity["high"] = fuzz.trapmf(humidity.universe, [55, 75, 100, 100])

# скорость ветра
wind_speed["low"] = fuzz.trapmf(wind_speed.universe, [0, 0, 2, 5])
wind_speed["medium"] = fuzz.trimf(wind_speed.universe, [2, 6, 12])
wind_speed["high"] = fuzz.trapmf(wind_speed.universe, [8, 15, 30, 30])

# комфорт
comfort["bad"] = fuzz.trapmf(comfort.universe, [0, 0, 2, 4])
comfort["average"] = fuzz.trimf(comfort.universe, [2, 5, 8])
comfort["good"] = fuzz.trapmf(comfort.universe, [6, 8, 10, 10])

# Правила нечёткого вывода Мамдани

rule1 = ctrl.Rule(temperature["normal"] & humidity["normal"] & wind_speed["low"], comfort["good"])

rule2 = ctrl.Rule(temperature["cold"] | temperature["hot"], comfort["bad"])

rule3 = ctrl.Rule(humidity["high"] & wind_speed["high"], comfort["bad"])

rule4 = ctrl.Rule(temperature["normal"] & wind_speed["medium"], comfort["average"])

rule5 = ctrl.Rule(humidity["normal"] & wind_speed["low"],comfort["good"])

# создаём систему управления
weather_control = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5])

# анализ текущей погоды в городах

print("\nНечёткий анализ текущей погоды")

for city, weather in current_data.items():
        
        simulation = ctrl.ControlSystemSimulation(weather_control)

        simulation.input["temperature"] = weather["temperature"]
        simulation.input["humidity"] = weather["humidity"]
        simulation.input["wind_speed"] = weather["wind_speed"]

        simulation.compute()

        quality = simulation.output["comfort"]

        print("\nГород:", city)
        print("Температура:", weather["temperature"], "°C")
        print("Влажность:", weather["humidity"], "%")
        print("Скорость ветра:", weather["wind_speed"], "м/с")
        print("Описание:", weather["description"])
        print("Оценка погоды:", round(quality, 2), "из 10")

# Этап 6. Сравнение с сезонными нормами

month = datetime.now().month

if month in [12, 1, 2]:
    current_season = "Зима"
elif month in [3, 4, 5]:
    current_season = "Весна"
elif month in [6, 7, 8]:
    current_season = "Лето"
else:
    current_season = "Осень"

print("\nСравнение температуры с сезонными нормами")
print("Текущий сезон:", current_season)

for city, weather in current_data.items():
    if weather is not None and city in seasonal_data:
        norms = seasonal_data[city]

        if current_season in norms.index:
            normal_temperature = norms[current_season]
            current_temperature = weather["temperature"]

            difference = current_temperature - normal_temperature

            print("\nГород:", city)
            print("Текущая температура:", current_temperature, "°C")
            print("Сезонная норма:", round(normal_temperature, 1), "°C")
            print("Отклонение:", round(difference, 1), "°C")

# Этап 7. Формирование рекомендаций

            simulation = ctrl.ControlSystemSimulation(weather_control)
            simulation.input["temperature"] = current_temperature
            simulation.input["humidity"] = weather["humidity"]
            simulation.input["wind_speed"] = weather["wind_speed"]
            simulation.compute()

            quality = simulation.output["comfort"]

            recommendations = get_recommendation(quality, difference)

            print("Оценка погоды:", round(quality, 2), "из 10")
            print("Рекомендации:")
            for recommendation in recommendations:
                print("-", recommendation)

# Этап 8. Визуализация результатов

cities_names = []
current_temperatures = []
normal_temperatures = []

for city, weather in current_data.items():

    if weather is not None and city in seasonal_data:
        if current_season in seasonal_data[city].index:
            cities_names.append(city)
            current_temperatures.append(weather["temperature"])
            normal_temperatures.append(
                seasonal_data[city][current_season]
            )

# cтроим график
positions = np.arange(len(cities_names))
width = 0.35

plt.figure(figsize=(10, 6))

plt.bar(
    positions - width / 2,
    current_temperatures,
    width,
    label="Текущая температура"
)

plt.bar(
    positions + width / 2,
    normal_temperatures,
    width,
    label="Сезонная норма"
)

plt.xticks(positions, cities_names)
plt.xlabel("Город")
plt.ylabel("Температура, °C")
plt.title("Сравнение текущей температуры с сезонной нормой")
plt.legend()
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.show()

# график оценок нечёткой системы

quality_cities = []
quality_values = []

for city, weather in current_data.items():

    if weather is not None:
        simulation = ctrl.ControlSystemSimulation(weather_control)

        simulation.input["temperature"] = weather["temperature"]
        simulation.input["humidity"] = weather["humidity"]
        simulation.input["wind_speed"] = weather["wind_speed"]

        simulation.compute()

        quality_cities.append(city)
        quality_values.append(
            simulation.output["comfort"]
        )

plt.figure(figsize=(8, 5))

plt.bar(quality_cities, quality_values)

plt.xlabel("Город")
plt.ylabel("Оценка погоды")
plt.title("Результаты нечёткого анализа погоды")
plt.ylim(0, 10)
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.show()
