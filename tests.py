from unittest import TestCase
from datetime import datetime, timedelta
import sensi
import worker

class Test(TestCase):
    def test_get_duration(self):
        response = sensi.get_duration()

        self.assertTrue(response)

    def test_get_mode(self):
        response = sensi.get_mode()

        self.assertTrue(response)

    def test_get_desiredTemperature(self):
        response = sensi.get_desiredTemperature()

        self.assertTrue(response)

    def test_get_temperature(self):
        response = sensi.get_temperature()

        self.assertTrue(response)

    def test_parse_sensi_time_format(self):
        result = worker.parse_sensi_time_format("10:12:00")

        self.assertTrue(isinstance(result, timedelta))