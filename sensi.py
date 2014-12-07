import requests
from settings import BASE_URL


def _get(endpoint):
    response = requests.get(BASE_URL+endpoint)
    return response.text


def get_duration():
    return _get("/duration")


def get_temperature():
    return _get("/temperature")


def get_desiredTemperature():
    return _get("/desiredTemperature")


def get_mode():
    return _get("/mode")

