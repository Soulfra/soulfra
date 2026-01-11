#!/usr/bin/env python3
"""
Platform Connectors - Convert Soul Packs to Platform-Specific Files

The "Ventrilo for Souls" connector modules.

Each connector takes a Soul Pack (dict) and generates
platform-specific output files:

- RobloxConnector → .lua ModuleScript
- MinecraftConnector → .json player data (NBT compatible)
- UnityConnector → .json asset bundle
- VoiceConnector → .json persona config
- WebConnector → .html profile

Usage:
    from platform_connectors import RobloxConnector

    connector = RobloxConnector()
    lua_code = connector.generate(soul_pack)
    connector.save_to_file(lua_code, 'output/player_soul.lua')
"""

from .roblox_connector import RobloxConnector
from .minecraft_connector import MinecraftConnector

__all__ = ['RobloxConnector', 'MinecraftConnector']
