"""Sensor platform for Teslemetry integration."""
from __future__ import annotations

from itertools import chain
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import cast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfLength,
    UnitOfPower,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.util.variance import ignore_variance
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .entity import (
    TeslemetryEnergyLiveEntity,
    TeslemetryVehicleEntity,
    TeslemetryWallConnectorEntity,
    TeslemetryEnergyInfoEntity,
)
from .models import TeslemetryEnergyData, TeslemetryVehicleData

ChargeStates = {
    "Starting": "starting",
    "Charging": "charging",
    "Stopped": "stopped",
    "Complete": "complete",
    "Disconnected": "disconnected",
    "NoPower": "no_power",
}

ShiftStates = {"P": "p", "D": "d", "R": "r", "N": "n"}


@dataclass(frozen=True, kw_only=True)
class TeslemetrySensorEntityDescription(SensorEntityDescription):
    """Describes Teslemetry Sensor entity."""

    value_fn: Callable[[StateType], StateType | datetime] = lambda x: x
    available_fn: Callable[[StateType], bool] = lambda _: True


VEHICLE_DESCRIPTIONS: tuple[TeslemetrySensorEntityDescription, ...] = (
    TeslemetrySensorEntityDescription(
        key="charge_state_charging_state",
        options=list(ChargeStates.values()),
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda value: ChargeStates[cast(str, value)],
    ),
    TeslemetrySensorEntityDescription(
        key="charge_state_usable_battery_level",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
    ),
    TeslemetrySensorEntityDescription(
        key="charge_state_charge_energy_added",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=1,
        value_fn=ignore_variance(lambda x: x, 0.2),
    ),
    TeslemetrySensorEntityDescription(
        key="charge_state_charger_power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
    ),
    TeslemetrySensorEntityDescription(
        key="charge_state_charger_voltage",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TeslemetrySensorEntityDescription(
        key="charge_state_charger_actual_current",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TeslemetrySensorEntityDescription(
        key="charge_state_charge_rate",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TeslemetrySensorEntityDescription(
        key="charge_state_minutes_to_full_charge",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda value: dt_util.now() + timedelta(minutes=cast(float, value)),
        available_fn=lambda value: value is not None and value > 0,
    ),
    TeslemetrySensorEntityDescription(
        key="charge_state_battery_range",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=1,
    ),
    TeslemetrySensorEntityDescription(
        key="drive_state_speed",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
    ),
    TeslemetrySensorEntityDescription(
        key="drive_state_power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TeslemetrySensorEntityDescription(
        key="drive_state_shift_state",
        options=list(ShiftStates.values()),
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda x: ShiftStates.get(x, "p"),
    ),
    TeslemetrySensorEntityDescription(
        key="vehicle_state_odometer",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TeslemetrySensorEntityDescription(
        key="vehicle_state_tpms_pressure_fl",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        # suggested_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TeslemetrySensorEntityDescription(
        key="vehicle_state_tpms_pressure_fr",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        # suggested_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TeslemetrySensorEntityDescription(
        key="vehicle_state_tpms_pressure_rl",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        # suggested_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TeslemetrySensorEntityDescription(
        key="vehicle_state_tpms_pressure_rr",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        # suggested_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TeslemetrySensorEntityDescription(
        key="climate_state_inside_temp",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        suggested_display_precision=1,
    ),
    TeslemetrySensorEntityDescription(
        key="climate_state_outside_temp",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        suggested_display_precision=1,
    ),
    TeslemetrySensorEntityDescription(
        key="climate_state_driver_temp_setting",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TeslemetrySensorEntityDescription(
        key="climate_state_passenger_temp_setting",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TeslemetrySensorEntityDescription(
        key="drive_state_active_route_traffic_minutes_delay",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
    ),
    TeslemetrySensorEntityDescription(
        key="drive_state_active_route_energy_at_arrival",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TeslemetrySensorEntityDescription(
        key="drive_state_active_route_miles_to_arrival",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
    ),
    TeslemetrySensorEntityDescription(
        key="drive_state_active_route_minutes_to_arrival",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=ignore_variance(
            lambda value: dt_util.now() + timedelta(minutes=cast(float, value)),
            timedelta(seconds=30),
        ),
    ),
)

ENERGY_LIVE_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="solar_power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_unit_of_measurement=UnitOfPower.KILO_WATT,
        suggested_display_precision=2,
        device_class=SensorDeviceClass.POWER,
    ),
    SensorEntityDescription(
        key="energy_left",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="total_pack_energy",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="percentage_charged",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="battery_power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_unit_of_measurement=UnitOfPower.KILO_WATT,
        suggested_display_precision=2,
        device_class=SensorDeviceClass.POWER,
    ),
    SensorEntityDescription(
        key="load_power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_unit_of_measurement=UnitOfPower.KILO_WATT,
        suggested_display_precision=2,
        device_class=SensorDeviceClass.POWER,
    ),
    SensorEntityDescription(
        key="grid_power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_unit_of_measurement=UnitOfPower.KILO_WATT,
        suggested_display_precision=2,
        device_class=SensorDeviceClass.POWER,
    ),
    SensorEntityDescription(
        key="grid_services_power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_unit_of_measurement=UnitOfPower.KILO_WATT,
        suggested_display_precision=2,
        device_class=SensorDeviceClass.POWER,
    ),
    SensorEntityDescription(
        key="generator_power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_unit_of_measurement=UnitOfPower.KILO_WATT,
        suggested_display_precision=2,
        device_class=SensorDeviceClass.POWER,
    ),
    SensorEntityDescription(key="island_status", device_class=SensorDeviceClass.ENUM),
)

WALL_CONNECTOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="wall_connector_state",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENUM,
    ),
    SensorEntityDescription(
        key="wall_connector_fault_state",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENUM,
    ),
    SensorEntityDescription(
        key="wall_connector_power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_unit_of_measurement=UnitOfPower.KILO_WATT,
        suggested_display_precision=2,
        device_class=SensorDeviceClass.POWER,
    ),
    SensorEntityDescription(
        key="vin",
    ),
)

ENERGY_INFO_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="vpp_backup_reserve_percent",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
    ),
    SensorEntityDescription(key="version"),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Teslemetry sensor platform from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        chain(
            (  # Add vehicles
                TeslemetryVehicleSensorEntity(vehicle, description)
                for vehicle in data.vehicles
                for description in VEHICLE_DESCRIPTIONS
            ),
            (  # Add energy site live
                TeslemetryEnergyLiveSensorEntity(energysite, description)
                for energysite in data.energysites
                for description in ENERGY_LIVE_DESCRIPTIONS
                if description.key in energysite.live_coordinator.data
            ),
            (  # Add wall connectors
                TeslemetryWallConnectorSensorEntity(energysite, din, description)
                for energysite in data.energysites
                for din in energysite.live_coordinator.data.get("wall_connectors", {})
                for description in WALL_CONNECTOR_DESCRIPTIONS
            ),
            (  # Add energy site info
                TeslemetryEnergyInfoSensorEntity(energysite, description)
                for energysite in data.energysites
                for description in ENERGY_INFO_DESCRIPTIONS
                if description.key in energysite.info_coordinator.data
            ),
        )
    )


class TeslemetrySensorEntity(SensorEntity):
    """Base class for all Teslemetry sensors."""


class TeslemetryVehicleSensorEntity(TeslemetryVehicleEntity, SensorEntity):
    """Base class for Teslemetry vehicle metric sensors."""

    entity_description: TeslemetrySensorEntityDescription

    def __init__(
        self,
        data: TeslemetryVehicleData,
        description: TeslemetrySensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(data, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        """Return if sensor entity is available."""
        return (
            super().available
            and self.is_not_none()
            and self.entity_description.available_fn(self.get())
        )

    @property
    def native_value(self) -> StateType | datetime:
        """Return the state of the sensor."""
        if (value := self.get()) is None:
            return None
        return self.entity_description.value_fn(value)


class TeslemetryEnergyLiveSensorEntity(TeslemetryEnergyLiveEntity, SensorEntity):
    """Base class for Teslemetry energy site metric sensors."""

    entity_description: TeslemetrySensorEntityDescription

    def __init__(
        self,
        data: TeslemetryEnergyData,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(data, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        """Return if sensor entity is available."""
        return super().available and self.has()

    @property
    def native_value(self) -> StateType | datetime:
        """Return the state of the sensor."""
        return self.get()


class TeslemetryWallConnectorSensorEntity(TeslemetryWallConnectorEntity, SensorEntity):
    """Base class for Teslemetry energy site metric sensors."""

    entity_description: TeslemetrySensorEntityDescription

    def __init__(
        self,
        data: TeslemetryEnergyData,
        din: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            data,
            din,
            description.key,
        )
        self.entity_description = description

    @property
    def available(self) -> bool:
        """Return if sensor entity is available."""
        return super().available and self.has()

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self._value

    @property
    def available(self) -> bool:
        """Return if sensor is available."""
        return self.coordinator.last_update_success


class TeslemetryEnergyInfoSensorEntity(TeslemetryEnergyInfoEntity, SensorEntity):
    """Base class for Teslemetry energy site metric sensors."""

    entity_description: TeslemetrySensorEntityDescription

    def __init__(
        self,
        data: TeslemetryEnergyData,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(data, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        """Return if sensor entity is available."""
        return super().available and self.has()

    @property
    def native_value(self) -> StateType | datetime:
        """Return the state of the sensor."""
        return self.get()
