"""Constants for the EVE Online integration."""

DOMAIN = "eve_online"

# ESI OAuth2 endpoints
OAUTH_AUTH_URL="https://login.eveonline.com/v2/oauth/authorize"
OAUTH_TOKEN_URL="https://login.eveonline.com/v2/oauth/token"

# ESI API base URL
ESI_BASE = "https://esi.evetech.net/latest"

# Config entry keys
CONF_CHARACTER_ID = "character_id"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"  # placeholder

# Required ESI scopes
SCOPES = [
    "esi-skills.read_skills.v1",
    "esi-skills.read_skillqueue.v1",
    "esi-wallet.read_character_wallet.v1",
    "esi-markets.read_character_orders.v1",
    "esi-location.read_online.v1",
    "esi-location.read_location.v1",
    "esi-location.read_ship_type.v1",
]
