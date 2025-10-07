"""Platform for sensor integration."""
from __future__ import annotations
import datetime
import requests
import logging

#from .const import ELIA_URL
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)
# Time between updating data from Elia
SCAN_INTERVAL = datetime.timedelta(minutes=15)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""
    add_entities([EliaSensor()], True)  # True argument makes update() happen on startup (according to chatGPT)
    _LOGGER.info("ExampleSensor set up")


class EliaSensor(SensorEntity):
    """Representation of a Sensor."""

    _attr_name = "Elia SDAC prices"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._attr_native_value = 24
        _LOGGER.info("Value of ExampleSensor set to 24")

        date_today = datetime.date.today()
        url = f"https://griddata.elia.be/eliabecontrols.prod/interface/Interconnections/daily/auctionresultsqh/{date_today}"
        try:
            response = requests.get(url, timeout=5)        # Get payload from database
            response.raise_for_status()
            _LOGGER.info("Elia SDAC prices fetched")
            data = response.json()
        except Exception as err:
            _LOGGER.error("Error fetching data from Elia: %s", err)
            return
        
        prices = [{"time": i["dateTime"], "price": i["price"]} for i in data]
        self._attr_extra_state_attributes = {"prices": prices}
        