"""
Config flow for EVE Online integration - manual OAuth2 callback URL paste.
"""
import asyncio, logging, secrets, hashlib, base64
from urllib.parse import urlencode, urlparse, parse_qs

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_CHARACTER_ID, CONF_CLIENT_ID, CONF_CLIENT_SECRET,     CONF_REFRESH_TOKEN, SCOPES, OAUTH_AUTH_URL, OAUTH_TOKEN_URL

_LOGGER = logging.getLogger(__name__)


class EVEOnlineConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._client_id = None
        self._client_secret = None
        self._code_verifier = None
        self._state = None
        self._auth_url = None

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            self._client_id = user_input[CONF_CLIENT_ID].strip()
            self._client_secret = user_input[CONF_CLIENT_SECRET].strip()
            if not self._client_id or not self._client_secret:
                errors["base"] = "empty_credentials"
            else:
                self._code_verifier = base64.urlsafe_b64encode(
                    secrets.token_bytes(32)
                ).decode().rstrip("=")
                code_challenge = base64.urlsafe_b64encode(
                    hashlib.sha256(self._code_verifier.encode()).digest()
                ).decode().rstrip("=")
                self._state = secrets.token_urlsafe(16)
                params = {
                    "response_type": "code",
                    "client_id": self._client_id,
                    "redirect_uri": "http://localhost/callback",
                    "scope": " ".join(SCOPES),
                    "state": self._state,
                    "code_challenge": code_challenge,
                    "code_challenge_method": "S256",
                }
                self._auth_url = OAUTH_AUTH_URL + "?" + urlencode(params)
                return await self.async_step_callback()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_CLIENT_ID): str,
                vol.Required(CONF_CLIENT_SECRET): str,
            }),
            errors=errors,
        )

    async def async_step_callback(self, user_input=None):
        errors = {}
        if user_input is not None:
            callback_url = user_input.get("callback_url", "").strip()
            if not callback_url:
                errors["base"] = "no_callback_url"
            else:
                parsed = urlparse(callback_url)
                params = parse_qs(parsed.query)
                auth_code = params.get("code", [None])[0]
                returned_state = params.get("state", [None])[0]
                error = params.get("error", [None])[0]

                if error:
                    errors["base"] = "auth_failed"
                elif not auth_code:
                    errors["base"] = "no_code"
                elif returned_state != self._state:
                    errors["base"] = "state_mismatch"
                else:
                    return await self._exchange_token(auth_code)

        return self.async_show_form(
            step_id="callback",
            data_schema=vol.Schema({
                vol.Required("callback_url"): str,
            }),
            errors=errors,
            description_placeholders={"auth_url": self._auth_url or ""},
        )

    async def _exchange_token(self, auth_code):
        errors = {}
        session = async_get_clientsession(self.hass)
        try:
            async with session.post(
                OAUTH_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": auth_code,
                    "code_verifier": self._code_verifier,
                    "redirect_uri": "http://localhost/callback",
                },
                auth=aiohttp.BasicAuth(self._client_id, self._client_secret),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    _LOGGER.error("Token exchange failed: %s", text)
                    errors["base"] = "token_failed"
                else:
                    token_data = await resp.json()
                    access_token = token_data.get("access_token")
                    refresh_token = token_data.get("refresh_token")
                    if not access_token or not refresh_token:
                        errors["base"] = "token_missing"
                    else:
                        async with session.get(
                            "https://login.eveonline.com/oauth/verify",
                            headers={"Authorization": f"Bearer {access_token}"},
                        ) as vrfy:
                            if vrfy.status != 200:
                                _LOGGER.error("Verify failed: %s", await vrfy.text())
                                errors["base"] = "verify_failed"
                            else:
                                char_data = await vrfy.json()
                                char_id = char_data.get("CharacterID")
                                char_name = char_data.get("CharacterName")
                                if not char_id or not char_name:
                                    errors["base"] = "no_character"
                                else:
                                    await self.async_set_unique_id(str(char_id))
                                    self._abort_if_unique_id_configured()
                                    return self.async_create_entry(
                                        title=f"EVE Online - {char_name}",
                                        data={
                                            CONF_CLIENT_ID: self._client_id,
                                            CONF_CLIENT_SECRET: self._client_secret,
                                            CONF_CHARACTER_ID: char_id,
                                            CONF_REFRESH_TOKEN: refresh_token,
                                            "access_token": access_token,
                                            "character_name": char_name,
                                        },
                                    )
        except aiohttp.ClientError as err:
            _LOGGER.exception("Network error: %s", err)
            errors["base"] = "network"
        except Exception as err:
            _LOGGER.exception("Unexpected error: %s", err)
            errors["base"] = "unknown"
        return self.async_show_form(
            step_id="callback",
            data_schema=vol.Schema({vol.Required("callback_url"): str}),
            errors=errors,
            description_placeholders={"auth_url": self._auth_url or ""},
        )