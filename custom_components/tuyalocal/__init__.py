"""The Tuya local integration."""
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import logging

from homeassistant.const import CONF_HOST

from .switch import PLATFORM_SCHEMA
from .const import (DOMAIN, CONF_DEVICE_ID, CONF_LOCAL_KEY, CONF_UPDATE_INTERVAL,DEFAULT_UPDATE_INTERVAL)


_LOGGER = logging.getLogger(__name__)



async def async_setup(hass, config):
    switch_config = config.get(SWITCH_DOMAIN)

    if switch_config is not None:
        conf = next((item for item in switch_config if item['platform']==DOMAIN),None)
        if conf is not None:
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN, context={"source": SOURCE_IMPORT}, data=conf
                )
            )
    return True    

async def async_setup_entry(hass, config_entry):
    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(config_entry, SWITCH_DOMAIN)
    )

    return True

    
async def async_unload_entry(hass, entry):
    """Unloading the Tuya platforms."""
    return  await hass.config_entries.async_forward_entry_unload(
        entry, SWITCH_DOMAIN
    )
