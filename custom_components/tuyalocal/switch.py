"""
Simple platform to control **SOME** Tuya switch devices.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.tuya/
"""
import voluptuous as vol
from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchEntity
from homeassistant.const import (CONF_NAME, CONF_HOST, CONF_ID, CONF_SWITCHES, CONF_FRIENDLY_NAME, CONF_ICON)
import homeassistant.helpers.config_validation as cv
from time import time
from threading import Lock
import logging
from homeassistant.config_entries import SOURCE_IMPORT

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['pytuya==7.0.4']

from .const import CONF_DEVICE_ID, CONF_LOCAL_KEY, CONF_UPDATE_INTERVAL

from .const import DEFAULT_ID, DEFAULT_UPDATE_INTERVAL, DOMAIN

ATTR_CURRENT = 'current'
ATTR_CURRENT_CONSUMPTION = 'current_consumption'
ATTR_VOLTAGE = 'voltage'

SWITCH_SCHEMA = vol.Schema({
    vol.Optional(CONF_ID, default=DEFAULT_ID): cv.string,
    vol.Optional(CONF_FRIENDLY_NAME): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_ICON): cv.icon,
    vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): cv.positive_int,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_LOCAL_KEY): cv.string,
    vol.Optional(CONF_ID, default=DEFAULT_ID): cv.string,
    vol.Optional(CONF_SWITCHES, default={}):
        vol.Schema({cv.slug: SWITCH_SCHEMA}),
})


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    _LOGGER.debug("async_setup_platform")

async def async_setup_entry(hass, config_entry, async_add_devices):
    config = config_entry.data
    from . import pytuya

    devices = config.get(CONF_SWITCHES)
    switch_id = config.get(CONF_ID)
    if switch_id==None or switch_id =='' :
        switch_id = DEFAULT_ID
    switches = []

    _device = await hass.async_add_executor_job(
        pytuya.OutletDevice, 
        config.get(CONF_DEVICE_ID),
        config.get(CONF_HOST),
        config.get(CONF_LOCAL_KEY)
    )


    outlet_device = TuyaCache(
        _device, config.get(CONF_UPDATE_INTERVAL)
    )

    for object_id, device_config in devices.items():
        switches.append(
                TuyaDevice(
                    outlet_device,
                    device_config.get(CONF_FRIENDLY_NAME, object_id),
                    device_config.get(CONF_ICON),
                    device_config.get(CONF_ID)
                )
        )

    name = config.get(CONF_NAME)
    if name:
        switches.append(
                TuyaDevice(
                    outlet_device,
                    name,
                    config.get(CONF_ICON),
                    switch_id
                )
        )
    else:
        switches.append(
                TuyaDevice(
                    outlet_device,
                    config.get(CONF_DEVICE_ID),
                    config.get(CONF_ICON),
                    switch_id
                )
        )

    async_add_devices(switches)



class TuyaCache:
    """Cache wrapper for pytuya.OutletDevice"""

    def __init__(self, device, scan_interval=20):
        """Initialize the cache."""
        self._cached_status = ''
        self._cached_status_time = 0
        self._device = device
        self._lock = Lock()
        self._scan_interval = scan_interval
        _LOGGER.debug("fetch device status every %d seconds", scan_interval)

    def __get_status(self):
        for i in range(3):
            try:
                status = self._device.status()
                return status
            except ConnectionError:
                if i+1 == 3:
                    raise ConnectionError("Failed to update status.")

    def set_status(self, state, switchid):
        """Change the Tuya switch status and clear the cache."""
        self._cached_status = ''
        self._cached_status_time = 0
        return self._device.set_status(state, switchid)

    def status(self):
        """Get state of Tuya switch and cache the results."""
        self._lock.acquire()
        try:
            now = time()
            if not self._cached_status or now - self._cached_status_time > self._scan_interval:
                self._cached_status = self.__get_status()
                self._cached_status_time = time()
            return self._cached_status
        finally:
            self._lock.release()

class TuyaDevice(SwitchEntity):
    """Representation of a Tuya switch."""

    def __init__(self, device, name, icon, switchid):
        """Initialize the Tuya switch."""
        self._device = device
        self._name = name
        self._state = False
        self._icon = icon
        self._switchid = switchid
        self._status = self._device.status()

    @property
    def name(self):
        """Get name of Tuya switch."""
        return self._name

    @property
    def is_on(self):
        """Check if Tuya switch is on."""
        return self._state

    @property
    def device_state_attributes(self):
        attrs = {}
        try:
            attrs[ATTR_CURRENT] = "{}".format(self._status['dps']['104'])
            attrs[ATTR_CURRENT_CONSUMPTION] = "{}".format(self._status['dps']['105']/10)
            attrs[ATTR_VOLTAGE] = "{}".format(self._status['dps']['106']/10)
        except KeyError:
            pass
        return attrs

    @property
    def icon(self):
        """Return the icon."""
        return self._icon

    def turn_on(self, **kwargs):
        """Turn Tuya switch on."""
        self._device.set_status(True, self._switchid)

    def turn_off(self, **kwargs):
        """Turn Tuya switch off."""
        self._device.set_status(False, self._switchid)

    def update(self):
        """Get state of Tuya switch."""
        status = self._device.status()
        self._status= status
        self._state = status['dps'][self._switchid]

