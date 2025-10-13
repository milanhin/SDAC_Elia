"""Platform for sensor integration."""
from __future__ import annotations
import datetime
import requests
import logging

#from .const import ELIA_URL
from typing import Any
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
SCAN_INTERVAL = datetime.timedelta(minutes=1)  # Time between calling update() function

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

    _attr_name = "Elia SDAC current price"                      # Name of sensor
    _attr_native_unit_of_measurement = f"{CURRENCY_EURO}/MWh"   # Unit of state value
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self):
        super().__init__()
        self._last_update_time: datetime.datetime | None = None  # Time of last updated state of sensor
        self._last_fetch_time: datetime.datetime | None = None   # Time of last data fetch from Elia
        self._last_fetch_date: datetime.date | None = None       # Date of last data fetch from Elia
        self._SDAC_data: Any = None                              # JSON object with SDAC price data from Elia
        self._prices: list[dict] = []                            # Filtered data with time and price pairs
        self._current_price: float | None = None                 # Current SDAC price
    
    @property
    def native_value(self) -> float | None: # type: ignore[override]
        """Return the current SDAC price so it gets stored in the sensor as value"""
        return self._current_price
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]: # type: ignore
        """Store all SDAC prices of the day."""
        return {
            "Last update:": self._last_fetch_time,
            "prices": self._prices,
            }

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        
        time_now = datetime.datetime.now()
        date_today = datetime.date.today()
        if self._last_fetch_date != date_today:
            try:
                self._SDAC_data = self._fetch_data()
            except Exception as err:
                _LOGGER.error("Error fetching data from Elia: %s", err)
                return
            
            _LOGGER.info("SDAC prices fetched from Elia")
            self._prices = [{"time": i["dateTime"], "price": i["price"]} for i in self._SDAC_data]  # filter data to store time and price
            self._last_fetch_time = time_now
            self._last_fetch_date = date_today

        self._current_price = self.get_current_price()
        _LOGGER.info("SDAC_Elia sensor value updated")

    def get_current_price(self) -> float | None:
        utc_time = datetime.datetime.now(datetime.timezone.utc)                                     # Get current UTC time
        rounded_quarter = utc_time.minute // 15 * 15                                                # determine last quarter minutes
        rounded_utc_time = utc_time.replace(microsecond=0, second=0, minute=rounded_quarter)        # change current minutes to last quarter
        target_time_str = rounded_utc_time.strftime("%Y-%m-%dT%H:%M:%SZ")                           # Create string to match standard
        current_price_dict = next((p for p in self._prices if p["time"] == target_time_str), None)  # Get time matching price dict
        if current_price_dict == None:
            _LOGGER.error("No time match found in prices from Elia")
            return None
        current_price = current_price_dict["price"]
        return current_price

    def _fetch_data(self) -> Any:
        time_now = datetime.datetime.now()
        date_today = time_now.date()
        url = f"https://griddata.elia.be/eliabecontrols.prod/interface/Interconnections/daily/auctionresultsqh/{date_today}"
        response = requests.get(url, timeout=5)  # Get payload from Elia database
        response.raise_for_status()
        _LOGGER.info("Elia SDAC prices fetched")
        data = response.json()
        return data