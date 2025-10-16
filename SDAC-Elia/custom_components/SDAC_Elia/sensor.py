"""Platform for sensor integration."""
from __future__ import annotations
import datetime
import requests
import logging

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
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import SDAC_EliaCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""
    sdac_coordinator = SDAC_EliaCoordinator(hass=hass, config_entry=None)
    await sdac_coordinator.async_refresh()  # Call _async_update_data() on setup
    async_add_entities(
        [
            EliaSensor(sdac_coordinator),
            EcopowerPriceSensor(sdac_coordinator),
            EcopowerInjectionSensor(sdac_coordinator)
        ]
    )
    _LOGGER.info("SDAC_Elia platform was set up")


class EliaSensor(CoordinatorEntity, SensorEntity): # pyright: ignore[reportIncompatibleVariableOverride]
    """Representation of a Sensor."""

    _attr_name = "Elia SDAC current price"                      # Name of sensor
    _attr_native_unit_of_measurement = f"{CURRENCY_EURO}/MWh"   # Unit of state value
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: SDAC_EliaCoordinator) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator
    
    @property
    def native_value(self) -> float | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return the current SDAC price so it gets stored in the sensor as value"""
        return self.coordinator.current_price
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]: # pyright: ignore[reportIncompatibleVariableOverride]
        """Store all SDAC prices of the day."""
        return {
            "Last update:": self.coordinator.last_fetch_time,
            "prices": self.coordinator.prices,
            }


class EcopowerPriceSensor(CoordinatorEntity, SensorEntity): # pyright: ignore[reportIncompatibleVariableOverride]
    """Sensor to show current energy price for Ecopower clients"""
    _attr_name = "Ecopower elektricity price"                   # Name of sensor
    _attr_native_unit_of_measurement = f"{CURRENCY_EURO}/MWh"   # Unit of state value
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: SDAC_EliaCoordinator) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator
    
    @property
    def native_value(self) -> float | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return Ecopower electricity price so it gets stored in the sensor as value"""
        return self.coordinator.ecopower_price


class EcopowerInjectionSensor(CoordinatorEntity, SensorEntity): # pyright: ignore[reportIncompatibleVariableOverride]
    """Sensor to show current injection price for Ecopower clients"""
    _attr_name = "Ecopower injection price"                     # Name of sensor
    _attr_native_unit_of_measurement = f"{CURRENCY_EURO}/MWh"   # Unit of state value
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: SDAC_EliaCoordinator) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator
    
    @property
    def native_value(self) -> float | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return Ecopower injection price so it gets stored in the sensor as value"""
        return self.coordinator.ecopower_injection_price