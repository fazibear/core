"""Config flow for file integration."""

import os
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_FILE_PATH,
    CONF_FILENAME,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_VALUE_TEMPLATE,
    Platform,
)
from homeassistant.helpers.selector import (
    BooleanSelector,
    BooleanSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TemplateSelector,
    TemplateSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import CONF_TIMESTAMP, DEFAULT_NAME, DOMAIN

BOOLEAN_SELECTOR = BooleanSelector(BooleanSelectorConfig())
PLATFORM_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=["notify", "sensor"],
        mode=SelectSelectorMode.DROPDOWN,
    )
)
TEMPLATE_SELECTOR = TemplateSelector(TemplateSelectorConfig())
TEXT_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT))

FILE_SENSOR_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME): TEXT_SELECTOR,
        vol.Required(CONF_FILE_PATH): TEXT_SELECTOR,
        vol.Optional(CONF_VALUE_TEMPLATE): TEMPLATE_SELECTOR,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): TEXT_SELECTOR,
    }
)

FILE_NOTIFY_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME): TEXT_SELECTOR,
        vol.Required(CONF_FILENAME): TEXT_SELECTOR,
        vol.Optional(CONF_TIMESTAMP, default=False): BOOLEAN_SELECTOR,
    }
)


class FileConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a file config flow."""

    VERSION = 1

    async def validate_file_path(self, file_path: str) -> bool:
        """Ensure the file path is valid."""
        return await self.hass.async_add_executor_job(
            self.hass.config.is_allowed_path, file_path
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["notify", "sensor"],
        )

    async def async_step_notify(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle file notifier config flow."""
        errors: dict[str, str] = {}
        if user_input:
            user_input[CONF_PLATFORM] = "notify"
            self._async_abort_entries_match(
                {key: user_input[key] for key in (CONF_PLATFORM, CONF_FILENAME)}
            )
            filepath: str = os.path.join(
                self.hass.config.config_dir, user_input[CONF_FILENAME]
            )
            if not await self.validate_file_path(filepath):
                errors[CONF_FILENAME] = "not_allowed"
            else:
                name: str = user_input.get(CONF_NAME, DEFAULT_NAME)
                title = f"{name} [{user_input[CONF_FILENAME]}]"
                return self.async_create_entry(data=user_input, title=title)

        return self.async_show_form(
            step_id="notify", data_schema=FILE_NOTIFY_SCHEMA, errors=errors
        )

    async def async_step_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle file sensor config flow."""
        errors: dict[str, str] = {}
        if user_input:
            user_input[CONF_PLATFORM] = "sensor"
            self._async_abort_entries_match(
                {key: user_input[key] for key in (CONF_PLATFORM, CONF_FILE_PATH)}
            )
            if not await self.validate_file_path(user_input[CONF_FILENAME]):
                errors[CONF_FILE_PATH] = "not_allowed"
            else:
                name: str = user_input.get(CONF_NAME, DEFAULT_NAME)
                title = f"{name} [{user_input[CONF_FILE_PATH]}]"
                return self.async_create_entry(data=user_input, title=title)

        return self.async_show_form(
            step_id="sensor", data_schema=FILE_SENSOR_SCHEMA, errors=errors
        )

    async def async_step_import(
        self, import_data: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Import `file`` config from configuration.yaml."""
        assert import_data is not None
        self._async_abort_entries_match(import_data)
        platform = import_data[CONF_PLATFORM]
        name: str = import_data.get(CONF_NAME, DEFAULT_NAME)
        file_name: str
        if platform == Platform.NOTIFY:
            file_name = import_data[CONF_FILENAME]
        else:
            file_name = import_data[CONF_FILE_PATH]
        title = f"{name} [{file_name}]"
        return self.async_create_entry(title=title, data=import_data)
