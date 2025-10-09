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
from homeassistant.const import CURRENCY_EURO
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = datetime.timedelta(minutes=15)  # Time between updating data from Elia

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""
    add_entities([EliaSensor()], update_before_add=True)  # True argument makes update() happen on startup
    _LOGGER.info("SDAC_Elia sensor was set up")


class EliaSensor(SensorEntity):
    """Representation of a Sensor."""

    _attr_name = "Elia SDAC current price"              # Name of sensor
    _attr_native_unit_of_measurement = CURRENCY_EURO    # Unit of state value
    _attr_state_class = SensorStateClass.MEASUREMENT

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        date_today = datetime.date.today()
        url = f"https://griddata.elia.be/eliabecontrols.prod/interface/Interconnections/daily/auctionresultsqh/{date_today}"
        try:
            response = requests.get(url, timeout=5)  # Get payload from Elia database
            response.raise_for_status()
            _LOGGER.info("Elia SDAC prices fetched")
            data = response.json()
        except Exception as err:
            _LOGGER.error("Error fetching data from Elia: %s", err)
            return

        prices = [{"time": i["dateTime"], "price": i["price"]} for i in data]   # filter data to store time and price
        current_price = self.get_current_price(prices)                          # get current electricty price
        self._attr_native_value = current_price                                 # Write current price to sensor state
        self._set_attributes(prices)                                            # Write all time-price pairs of today to sensor attributes

    def _set_attributes(self, prices: list[dict]) -> None:
        local_time = datetime.datetime.now()
        self._attr_extra_state_attributes = {
            "Last update:": local_time.replace(microsecond=0),
            "prices": prices,
            }
        _LOGGER.info(f"Elia SDAC prices updated at {local_time}")

    def get_current_price(self, prices: list[dict]) -> float | None:
        utc_time = datetime.datetime.now(datetime.timezone.utc)                                 # Get current UTC time
        rounded_quarter = utc_time.minute // 15 * 15                                            # determine last quarter minutes
        rounded_utc_time = utc_time.replace(microsecond=0, second=0, minute=rounded_quarter)    # change current minutes to last quarter
        target_time_str = rounded_utc_time.strftime("%Y-%m-%dT%H:%M:%SZ")                       # Create string to match standard
        current_price_dict = next((p for p in prices if p["time"] == target_time_str), None)    # Get time matching price dict
        if current_price_dict == None:
            _LOGGER.error("No time match found in prices from Elia")
            return None
        current_price = current_price_dict["price"]
        return current_price
