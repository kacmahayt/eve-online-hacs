# EVE Online for Home Assistant

[![HACS Default](https://img.shields.io/badge/HACS-Default-blue.svg)](https://hacs.xyz)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.1+-blueviolet)](https://home-assistant.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Monitor your EVE Online character directly from Home Assistant. Track wallet, skills, skill queue, market orders, online status, ship, and location.

## Features

- **Character** — name, corporation, security status
- **Portrait** — character portrait with name
- **Wallet** — current ISK balance
- **Skills** — total skill points + unallocated SP
- **Skill Queue** — queue length, time remaining, training status
- **Market Orders** — active buy/sell orders
- **Corporation** — corporation name, ticker, member count
- **Online Status** — online/offline + last login/logout
- **Ship** — current ship name & type
- **System** — current solar system location
- **Jump Fatigue** — remaining fatigue time

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** → **Custom Repositories**
3. Add `https://github.com/kacmahayt/eve-online-hacs` as type **Integration**
4. Click **Install**
5. Restart Home Assistant

### Manual

1. Copy `custom_components/eve_online/` to your HA `custom_components/` directory
2. Restart Home Assistant

## Setup

### 1. Create an EVE Online application

1. Go to https://developers.eveonline.com/ and log in
2. Click **CREATE APPLICATION**
3. Fill in:
   - **Name**: `EVE Online Home Assistant` (or any name)
   - **Description**: Brief description
   - **Connection Type**: `Authentication & API Access`
   - **Callback URL**: `http://localhost/callback`
4. Select these **Scopes**:
   - `esi-skills.read_skills.v1`
   - `esi-skills.read_skillqueue.v1`
   - `esi-wallet.read_character_wallet.v1`
   - `esi-markets.read_character_orders.v1`
   - `esi-location.read_online.v1`
   - `esi-location.read_location.v1`
   - `esi-location.read_ship_type.v1`
5. Save and copy your **Client ID** and **Client Secret**

### 2. Add Integration

1. Go to **Settings → Devices & Services**
2. Click **+ Add Integration**
3. Search for **EVE Online**
4. Enter your **Client ID** and **Client Secret**
5. Click **Submit**
6. Click the authorization link, log in with your EVE account
7. After authorization, your browser will redirect to a page that fails to load (normal!)
8. **Copy the entire URL** from the browser address bar
9. Paste it into Home Assistant and click **Submit**

## Sensors

| Entity | Example Value | Description |
|--------|--------------|-------------|
| `sensor.eve_online_eve_character` | YourCharacter | Character name |
| `sensor.eve_online_eve_portrait` | YourCharacter | Character portrait + name |
| `sensor.eve_online_eve_wallet` | 1000000000.00 | ISK balance |
| `sensor.eve_online_eve_total_sp` | 50000000 | Total skill points |
| `sensor.eve_online_eve_skill_queue` | 3 | Skills in queue |
| `sensor.eve_online_eve_market_orders` | 0 | Active market orders |
| `sensor.eve_online_eve_corporation` | YourCorp | Corporation name |
| `sensor.eve_online_eve_security_status` | 5.0 | Security status |
| `sensor.eve_online_eve_online_status` | False | Online/Offline |
| `sensor.eve_online_eve_ship` | YourShip | Current ship |
| `sensor.eve_online_eve_system` | YourSystem | Current solar system |
| `sensor.eve_online_eve_jump_fatigue` | None | Jump clone fatigue |

## Lovelace Example

Add a glance card with entities to your dashboard:

```yaml
type: entities
title: EVE Online
entities:
  - sensor.eve_online_eve_portrait
  - sensor.eve_online_eve_character
  - sensor.eve_online_eve_wallet
  - sensor.eve_online_eve_total_sp
  - sensor.eve_online_eve_skill_queue
  - sensor.eve_online_eve_corporation
  - sensor.eve_online_eve_security_status
  - sensor.eve_online_eve_online_status
  - sensor.eve_online_eve_ship
  - sensor.eve_online_eve_system
```

## Support

- [Create an issue](https://github.com/kacmahayt/eve-online-hacs/issues)
- CCP Games: [EVE Online Developer Portal](https://developers.eveonline.com/)

## Donate

If you find this integration useful and want to show appreciation, send ISK to **KaCMaHayT** in EVE Online. o7

---

*EVE Online and the EVE logo are the registered trademarks of CCP hf.*
