"""
Allows to configuration ecoal (esterownik.pl) pumps as switches.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.ecoal_boiler/
"""
import logging
from typing import Optional

import voluptuous as vol

from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchDevice
from homeassistant.components.ecoal_boiler import DATA_ECOAL_BOILER
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['ecoal_boiler']

# Available ids
PUMP_IDNAMES = (
    "central_heating_pump",
    "domestic_hot_water_pump",
    "central_heating_pump2",
)

ENABLED_SCHEMA = {}
for pump_id in PUMP_IDNAMES:
    ENABLED_SCHEMA[vol.Optional(pump_id)] = cv.string
CONF_ENABLE = "enable"
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Optional(CONF_ENABLE): ENABLED_SCHEMA}
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up switches based on ecoal interface."""
    ecoal_contr = hass.data[DATA_ECOAL_BOILER]
    config_enable = config.get(CONF_ENABLE, {})
    # _LOGGER.debug("config_enable: %r", config_enable)
    switches = []
    for pump_id in PUMP_IDNAMES:     # pylint: disable=W0621
        name = config_enable.get(pump_id)
        if name:
            switches.append(EcoalSwitch(ecoal_contr, name, pump_id))
    add_entities(switches, True)


class EcoalSwitch(SwitchDevice):
    """Representation of Ecoal switch."""

    def __init__(self, ecoal_contr, name, state_attr):
        """
        Initialize switch.

        Sets HA switch to state as read from controller.
        """
        self._ecoal_contr = ecoal_contr
        self._name = name
        self._state_attr = state_attr
        # NOTE: Ecoalcotroller holds convention that same postfix is used 
        # to set attribute 
        #   set_<attr>()
        # as attribute name in status instance:
        #   status.<attr>
        self._contr_set_fun = getattr(self._ecoal_contr, "set_" + state_attr)
        # No value set, will be read from controller instead
        self._state = None

    @property
    def name(self) -> Optional[str]:
        """Return the name of the switch."""
        return self._name

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        status = self._ecoal_contr.get_cached_status()
        self._state = getattr(status, self._state_attr)

    def reread_update(self) -> None:
        """Fetch state of pump without using cache."""
        # Get status without using cache
        self._ecoal_contr.get_status()
        self.update()

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._state

    def turn_on(self, **kwargs) -> None:
        """Turn the device on."""
        self._contr_set_fun(1)
        # Reread state without using cache.
        self.reread_update()

    def turn_off(self, **kwargs) -> None:
        """Turn the device off."""
        self._contr_set_fun(0)
        # Reread state without using cache.
        self.reread_update()
