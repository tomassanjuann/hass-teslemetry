"""Teslemetry parent entity class."""

import asyncio
from typing import Any
from tesla_fleet_api import VehicleSpecific, EnergySpecific
from tesla_fleet_api.exceptions import TeslaFleetError

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.exceptions import ServiceValidationError, HomeAssistantError

from .const import DOMAIN, LOGGER, MODELS, TeslemetryState
from .coordinator import (
    TeslemetryEnergySiteLiveCoordinator,
    TeslemetryVehicleDataCoordinator,
    TeslemetryEnergySiteInfoCoordinator,
)
from .models import TeslemetryEnergyData, TeslemetryVehicleData

FUTURE = 32503680000000


class TeslemetryEntity(
    CoordinatorEntity[
        TeslemetryVehicleDataCoordinator
        | TeslemetryEnergySiteLiveCoordinator
        | TeslemetryEnergySiteInfoCoordinator
    ]
):
    """Parent class for all Teslemetry entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TeslemetryVehicleDataCoordinator
        | TeslemetryEnergySiteLiveCoordinator
        | TeslemetryEnergySiteInfoCoordinator,
        api: VehicleSpecific | EnergySpecific,
        key: str,
    ) -> None:
        """Initialize common aspects of a Teslemetry entity."""
        super().__init__(coordinator)
        self.api = api
        self.key = key
        self._attr_translation_key = self.key
        self._async_update_attrs()

    @property
    def available(self) -> bool:
        """Return if sensor is available."""
        return self.coordinator.last_update_success and self._attr_available

    @property
    def _value(self) -> int:
        """Return a specific value from coordinator data."""
        return self.coordinator.data.get(self.key)

    def get(self, key: str, default: Any | None = None) -> Any:
        """Return a specific value from coordinator data."""
        return self.coordinator.data.get(key, default)

    def exactly(self, value: Any, key: str | None = None) -> bool | None:
        """Return if a key exactly matches the valug but retain None."""
        key = key or self.key
        if value is None:
            return self.get(key, False) is None
        current = self.get(key)
        if current is None:
            return None
        return current == value

    def has(self, key: str | None = None) -> bool:
        """Return True if a specific value is in coordinator data."""
        return (key or self.key) in self.coordinator.data

    def raise_for_scope(self):
        """Raise an error if a scope is not available."""
        if not self.scoped:
            raise ServiceValidationError(
                f"Missing required scope: {' or '.join(self.entity_description.scopes)}"
            )

    async def handle_command(self, command) -> dict[str, Any]:
        """Handle a command."""
        try:
            result = await command
            LOGGER.debug("Command result: %s", result)
        except TeslaFleetError as e:
            LOGGER.debug("Command error: %s", e.message)
            raise ServiceValidationError(
                f"Teslemetry command failed, {e.message}"
            ) from e
        return result

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._async_update_attrs()
        self.async_write_ha_state()


class TeslemetryVehicleEntity(TeslemetryEntity):
    """Parent class for Teslemetry Vehicle entities."""

    _last_update: int = 0

    def __init__(
        self,
        data: TeslemetryVehicleData,
        key: str,
        timestamp_key: str | None = None,
        streaming_key: str | None = None,
    ) -> None:
        """Initialize common aspects of a Teslemetry entity."""
        self.timestamp_key = timestamp_key
        self.streaming_key = streaming_key
        self.stream = data.stream

        self._attr_unique_id = f"{data.vin}-{key}"
        self._wakelock = data.wakelock

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, data.vin)},
            manufacturer="Tesla",
            configuration_url="https://teslemetry.com/console",
            name=data.display_name,
            model=MODELS.get(data.vin[3]),
            serial_number=data.vin,
        )
        super().__init__(data.coordinator, data.api, key)

    async def async_added_to_hass(self) -> asyncio.Coroutine[Any, Any, None]:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        if self.streaming_key:
            self.async_on_remove(
                self.stream.async_add_listener(self._handle_stream_update)
            )

    async def _handle_stream_update(self, data: dict[str, Any]) -> None:
        """Handle updated data from the stream."""
        if (
            data["vin"] != self.api.vin
            or (value := data["data"].get(self.streaming_key)) is None
        ):
            return
        if data["timestamp"] < self._last_update:
            LOGGER.warning("A streaming update was older than a polled update")
        self._last_update = data["timestamp"]
        self._async_value_from_stream(value)
        self.async_write_ha_state()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.timestamp_key is None:
            LOGGER.debug("Updating %s, there is no timestamp key", self.name)
            self._async_update_attrs()
            self.async_write_ha_state()
            return

        timestamp = self.get(self.timestamp_key)
        if timestamp is None:
            LOGGER.debug("Updating %s, there is no timestamp value", self.name)
            self._async_update_attrs()
            self.async_write_ha_state()
            return
        if timestamp > self._last_update:
            LOGGER.debug("Updating %s, timestamp is newer", self.name)
            self._last_update = timestamp
            self._async_update_attrs()
            self.async_write_ha_state()
            return
        LOGGER.debug("Skipping update of %s, timestamp is not newer", self.name)

    async def wake_up_if_asleep(self) -> None:
        """Wake up the vehicle if its asleep."""
        async with self._wakelock:
            times = 0
            while self.coordinator.data["state"] != TeslemetryState.ONLINE:
                try:
                    if times == 0:
                        cmd = await self.api.wake_up()
                    else:
                        cmd = await self.api.vehicle()
                    state = cmd["response"]["state"]
                except TeslaFleetError as e:
                    raise HomeAssistantError(str(e)) from e
                except TypeError as e:
                    raise HomeAssistantError("Invalid response from Teslemetry") from e
                self.coordinator.data["state"] = state
                if state != TeslemetryState.ONLINE:
                    times += 1
                    if times >= 4:  # Give up after 30 seconds total
                        raise HomeAssistantError("Could not wake up vehicle")
                    await asyncio.sleep(times * 5)

    async def handle_command(self, command) -> dict[str, Any]:
        """Handle a vehicle command."""
        result = await super().handle_command(command)
        if not (message := result.get("response", {}).get("result")):
            message = message or "Bad response from Tesla"
            LOGGER.debug("Command failure: %s", message)
            raise ServiceValidationError(message)
        return result


class TeslemetryEnergyLiveEntity(TeslemetryEntity):
    """Parent class for Teslemetry Energy Site Live entities."""

    def __init__(
        self,
        data: TeslemetryEnergyData,
        key: str,
    ) -> None:
        """Initialize common aspects of a Teslemetry entity."""
        self._attr_unique_id = f"{data.id}-{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(data.id))},
            manufacturer="Tesla",
            configuration_url="https://teslemetry.com/console",
            name=self.coordinator.data.get("site_name", "Energy Site"),
        )

        super().__init__(data.live_coordinator, data.api, key)


class TeslemetryEnergyInfoEntity(TeslemetryEntity):
    """Parent class for Teslemetry Energy Site Info Entities."""

    def __init__(
        self,
        data: TeslemetryEnergyData,
        key: str,
    ) -> None:
        """Initialize common aspects of a Teslemetry entity."""
        self._attr_unique_id = f"{data.id}-{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(data.id))},
            manufacturer="Tesla",
            configuration_url="https://teslemetry.com/console",
            name=self.coordinator.data.get("site_name", "Energy Site"),
        )

        super().__init__(data.info_coordinator, data.api, key)


class TeslemetryWallConnectorEntity(
    TeslemetryEntity, CoordinatorEntity[TeslemetryEnergySiteLiveCoordinator]
):
    """Parent class for Teslemetry Wall Connector Entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        data: TeslemetryEnergyData,
        din: str,
        key: str,
    ) -> None:
        """Initialize common aspects of a Teslemetry entity."""
        self.din = din
        self._attr_unique_id = f"{data.id}-{din}-{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, din)},
            manufacturer="Tesla",
            configuration_url="https://teslemetry.com/console",
            name="Wall Connector",
            via_device=(DOMAIN, str(data.id)),
            serial_number=din.split("-")[-1],
        )

        super().__init__(data.live_coordinator, data.api, key)

    @property
    def _value(self) -> int:
        """Return a specific wall connector value from coordinator data."""
        return (
            self.coordinator.data.get("wall_connectors", {})
            .get(self.din, {})
            .get(self.key)
        )
