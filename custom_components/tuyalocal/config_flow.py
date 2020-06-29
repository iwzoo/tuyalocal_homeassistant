"""Config flow for Tuya Local"""
import logging
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import (CONF_NAME, CONF_HOST, CONF_ID, CONF_SWITCHES, CONF_FRIENDLY_NAME, CONF_ICON)
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from copy import deepcopy

from .const import CONF_UPDATE_INTERVAL, CONF_DEVICE_ID, CONF_LOCAL_KEY
from .const import DEFAULT_UPDATE_INTERVAL, DEFAULT_ID, DOMAIN

import traceback

_LOGGER = logging.getLogger(__name__)

CONF_ADD_SWITCHES = 'need_add_switches'

SWITCH_SCHEMA = vol.Schema({
    vol.Optional(CONF_ID, default=''): str,
    vol.Optional(CONF_FRIENDLY_NAME, default=''): str,
    # vol.Optional(CONF_ADD_SWITCHES, default=False): bool
})

DATA_SCHEMA_USER = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_DEVICE_ID): str,
        vol.Required(CONF_LOCAL_KEY): str,
        vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.Coerce(int),
        vol.Optional(CONF_ADD_SWITCHES, default=False): bool
    }
)

RESULT_SUCCESS = 'success'
RESULT_CONN_REFUSED = 'conn_refused'
RESULT_ERROR_ALEADY_EXISTS = 'conn_error_exists'

SETUP_DEVICE = 'setup_device'


class LocalTuyaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a local tuya config flow"""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize flow."""
        self._name = None
        self._icon = None
        self._update_interval = DEFAULT_UPDATE_INTERVAL
        self._host = None
        self._device_id = None
        self._local_key = None
        self._id = DEFAULT_ID
        self._switches = {}
        self._is_import = False

    def _get_entry(self):
        switches = {}
        for switch_id, switch_config in self._switches.items():
            config = deepcopy(switch_config)
            del config[CONF_ADD_SWITCHES]
            switches[switch_id] = config
        data = {
            CONF_UPDATE_INTERVAL: self._update_interval,
            CONF_HOST: self._host,
            CONF_DEVICE_ID: self._device_id,
            CONF_LOCAL_KEY: self._local_key,
            CONF_SWITCHES: switches
        }        

        return self.async_create_entry(
            title="tuya@" + self._host,
            data=data,
            description="update status every " + str(self._update_interval) + " seconds"
        )

    def _try_connect(self):
        """Try to connect and check auth."""
        from . import pytuya
        try:
            device = pytuya.OutletDevice(self._device_id, self._host, self._local_key)
            result = device.status()
        except Exception as ex:
            return RESULT_CONN_REFUSED
        return RESULT_SUCCESS

    async def async_step_import(self, user_input=None):
        """Handle configuration by yaml file"""
        _LOGGER.debug("import tuya configuration")
        self._is_import = True
        return await self.async_step_user(user_input)
    
    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user"""
        # if self._async_current_entries():
        #     _LOGGER.debug("an entry exists")
        #     return self.async_abort(reason="single_intance_allowed")
        _LOGGER.debug("async_step_user")

        errors = {}

        if user_input is not None:
            _LOGGER.debug("got user input")
            self._host = str(user_input[CONF_HOST])
            self._device_id = str(user_input[CONF_DEVICE_ID])
            self._local_key = str(user_input[CONF_LOCAL_KEY])
            self._update_interval = user_input[CONF_UPDATE_INTERVAL]

        
            exists = await self.async_set_unique_id(self._device_id)            
            if exists is not None:
                if self._is_import:
                    return self.async_abort(reason=RESULT_ERROR_ALEADY_EXISTS)
                errors["base"] = RESULT_ERROR_ALEADY_EXISTS
                return self.async_show_form(
                    step_id="user", data_schema=DATA_SCHEMA_USER, errors=errors
                )
            
            for entry in self._async_current_entries():
                if entry.version !=  1:
                    continue
                if entry.data[CONF_DEVICE_ID] == self._device_id:
                    return self.async_abort(reason=RESULT_ERROR_ALEADY_EXISTS)
                
            result = await self.hass.async_add_executor_job(self._try_connect)

            if result == RESULT_SUCCESS:
                if self._is_import:
                    return self._get_entry()
                if bool(user_input[CONF_ADD_SWITCHES]) == False:
                    return self._get_entry()
                return self.async_show_form(
                    step_id="add_switch", data_schema=SWITCH_SCHEMA, errors=errors
                )
            if self._is_import:
                _LOGGER.error(
                    "Error importing from configuration.yaml: connection refused"
                )
                return self.async_abort(reason=result)
            errors["base"] = result
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA_USER, errors=errors
        )
    async def async_step_add_switch(self, user_input=None):
        errors = {}
        if user_input is not None:
            _LOGGER.debug(user_input)
            switch_id = user_input[CONF_ID]
            switch_fn = user_input[CONF_FRIENDLY_NAME]
            if switch_id.strip()=='':
                # just create the device
                return self._get_entry()
            else:
                self._switches["switch" + str( len(self._switches) + 1 )] = user_input
                add_more = False #bool(user_input[CONF_ADD_SWITCHES])
                if add_more == True:
                    return self.async_show_form(
                        step_id="add_switch", data_schema=SWITCH_SCHEMA, errors=errors
                    )
                else:
                    return self._get_entry()

        return self.async_show_form(
            step_id="add_switch", data_schema=SWITCH_SCHEMA, errors=errors
        )


