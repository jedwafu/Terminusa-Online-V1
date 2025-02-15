import unittest
from unittest.mock import Mock, patch
import sys
import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum, auto

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class NotificationType(Enum):
    """Notification preference types"""
    ACHIEVEMENTS = auto()
    FRIEND_REQUESTS = auto()
    PARTY_INVITES = auto()
    GUILD_INVITES = auto()
    TRADE_REQUESTS = auto()
    PRIVATE_MESSAGES = auto()
    SYSTEM_MESSAGES = auto()

class ChatFilter(Enum):
    """Chat filter levels"""
    NONE = auto()
    BASIC = auto()
    STRICT = auto()

@dataclass
class GameplaySettings:
    """Gameplay settings"""
    auto_loot: bool = True
    show_damage_numbers: bool = True
    show_floating_text: bool = True
    show_player_names: bool = True
    show_player_titles: bool = True
    show_player_levels: bool = True
    camera_shake: bool = True
    screen_effects: bool = True
    combat_animations: bool = True
    particle_effects: bool = True

@dataclass
class AudioSettings:
    """Audio settings"""
    master_volume: float = 1.0
    music_volume: float = 0.7
    sfx_volume: float = 0.8
    ambient_volume: float = 0.6
    ui_volume: float = 0.8
    voice_volume: float = 0.8
    mute_all: bool = False

@dataclass
class GraphicsSettings:
    """Graphics settings"""
    resolution: str = "1920x1080"
    fullscreen: bool = True
    vsync: bool = True
    frame_rate_limit: int = 60
    shadow_quality: str = "high"
    texture_quality: str = "high"
    effect_quality: str = "high"
    anti_aliasing: bool = True
    ambient_occlusion: bool = True
    bloom: bool = True
    motion_blur: bool = False

@dataclass
class InterfaceSettings:
    """Interface settings"""
    ui_scale: float = 1.0
    chat_opacity: float = 0.8
    minimap_size: float = 1.0
    show_tooltips: bool = True
    show_quest_tracker: bool = True
    show_party_frames: bool = True
    show_raid_frames: bool = True
    show_buffs: bool = True
    show_debuffs: bool = True
    compact_ui: bool = False

@dataclass
class UserSettings:
    """User settings container"""
    gameplay: GameplaySettings = GameplaySettings()
    audio: AudioSettings = AudioSettings()
    graphics: GraphicsSettings = GraphicsSettings()
    interface: InterfaceSettings = InterfaceSettings()
    notifications: Dict[NotificationType, bool] = None
    chat_filter: ChatFilter = ChatFilter.BASIC
    keybindings: Dict[str, str] = None

    def __post_init__(self):
        if self.notifications is None:
            self.notifications = {t: True for t in NotificationType}
        if self.keybindings is None:
            self.keybindings = self._default_keybindings()

    def _default_keybindings(self) -> Dict[str, str]:
        """Get default keybindings"""
        return {
            'inventory': 'i',
            'character': 'c',
            'map': 'm',
            'quest_log': 'l',
            'skills': 'k',
            'party': 'p',
            'guild': 'g',
            'friends': 'o',
            'chat': 'enter'
        }

class SettingsManager:
    """Manages user settings"""
    def __init__(self):
        self.settings: Dict[int, UserSettings] = {}
        self.defaults = UserSettings()

    def get_settings(self, user_id: int) -> UserSettings:
        """Get user settings"""
        if user_id not in self.settings:
            self.settings[user_id] = UserSettings()
        return self.settings[user_id]

    def update_settings(
        self,
        user_id: int,
        settings: Dict[str, Any]
    ) -> bool:
        """Update user settings"""
        if user_id not in self.settings:
            self.settings[user_id] = UserSettings()
        
        user_settings = self.settings[user_id]
        
        for category, values in settings.items():
            if hasattr(user_settings, category):
                category_settings = getattr(user_settings, category)
                if isinstance(category_settings, dict):
                    category_settings.update(values)
                else:
                    for key, value in values.items():
                        if hasattr(category_settings, key):
                            setattr(category_settings, key, value)
        
        return True

    def reset_settings(self, user_id: int, category: Optional[str] = None):
        """Reset settings to defaults"""
        if category:
            if user_id in self.settings:
                setattr(
                    self.settings[user_id],
                    category,
                    getattr(self.defaults, category)
                )
        else:
            self.settings[user_id] = UserSettings()

    def export_settings(self, user_id: int) -> Dict[str, Any]:
        """Export settings to dictionary"""
        if user_id not in self.settings:
            return asdict(self.defaults)
        return asdict(self.settings[user_id])

    def import_settings(self, user_id: int, data: Dict[str, Any]) -> bool:
        """Import settings from dictionary"""
        try:
            settings = UserSettings(
                gameplay=GameplaySettings(**data['gameplay']),
                audio=AudioSettings(**data['audio']),
                graphics=GraphicsSettings(**data['graphics']),
                interface=InterfaceSettings(**data['interface']),
                notifications=data['notifications'],
                chat_filter=ChatFilter[data['chat_filter'].upper()],
                keybindings=data['keybindings']
            )
            self.settings[user_id] = settings
            return True
        except Exception:
            return False

class TestSettings(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.settings_manager = SettingsManager()
        self.test_user_id = 1

    def test_default_settings(self):
        """Test default settings retrieval"""
        settings = self.settings_manager.get_settings(self.test_user_id)
        
        # Verify default values
        self.assertTrue(settings.gameplay.auto_loot)
        self.assertEqual(settings.audio.master_volume, 1.0)
        self.assertEqual(settings.graphics.resolution, "1920x1080")
        self.assertEqual(settings.interface.ui_scale, 1.0)

    def test_update_settings(self):
        """Test settings update"""
        updates = {
            'gameplay': {
                'auto_loot': False,
                'show_damage_numbers': False
            },
            'audio': {
                'master_volume': 0.5
            }
        }
        
        success = self.settings_manager.update_settings(
            self.test_user_id,
            updates
        )
        
        self.assertTrue(success)
        
        settings = self.settings_manager.get_settings(self.test_user_id)
        self.assertFalse(settings.gameplay.auto_loot)
        self.assertEqual(settings.audio.master_volume, 0.5)

    def test_reset_settings(self):
        """Test settings reset"""
        # Change some settings
        self.settings_manager.update_settings(
            self.test_user_id,
            {
                'gameplay': {'auto_loot': False},
                'audio': {'master_volume': 0.5}
            }
        )
        
        # Reset gameplay settings
        self.settings_manager.reset_settings(
            self.test_user_id,
            'gameplay'
        )
        
        settings = self.settings_manager.get_settings(self.test_user_id)
        self.assertTrue(settings.gameplay.auto_loot)  # Reset to default
        self.assertEqual(settings.audio.master_volume, 0.5)  # Unchanged

    def test_notification_settings(self):
        """Test notification settings"""
        # Update notification preferences
        updates = {
            'notifications': {
                NotificationType.FRIEND_REQUESTS: False,
                NotificationType.PARTY_INVITES: False
            }
        }
        
        self.settings_manager.update_settings(
            self.test_user_id,
            updates
        )
        
        settings = self.settings_manager.get_settings(self.test_user_id)
        self.assertFalse(settings.notifications[NotificationType.FRIEND_REQUESTS])
        self.assertTrue(settings.notifications[NotificationType.GUILD_INVITES])

    def test_keybinding_settings(self):
        """Test keybinding settings"""
        # Update keybindings
        updates = {
            'keybindings': {
                'inventory': 'b',
                'character': 'v'
            }
        }
        
        self.settings_manager.update_settings(
            self.test_user_id,
            updates
        )
        
        settings = self.settings_manager.get_settings(self.test_user_id)
        self.assertEqual(settings.keybindings['inventory'], 'b')
        self.assertEqual(settings.keybindings['character'], 'v')

    def test_export_import(self):
        """Test settings export and import"""
        # Modify settings
        self.settings_manager.update_settings(
            self.test_user_id,
            {
                'gameplay': {'auto_loot': False},
                'audio': {'master_volume': 0.5}
            }
        )
        
        # Export settings
        exported = self.settings_manager.export_settings(self.test_user_id)
        
        # Reset settings
        self.settings_manager.reset_settings(self.test_user_id)
        
        # Import settings
        success = self.settings_manager.import_settings(
            self.test_user_id,
            exported
        )
        
        self.assertTrue(success)
        
        # Verify imported settings
        settings = self.settings_manager.get_settings(self.test_user_id)
        self.assertFalse(settings.gameplay.auto_loot)
        self.assertEqual(settings.audio.master_volume, 0.5)

    def test_chat_filter_settings(self):
        """Test chat filter settings"""
        # Update chat filter
        updates = {
            'chat_filter': ChatFilter.STRICT
        }
        
        self.settings_manager.update_settings(
            self.test_user_id,
            {'chat_filter': ChatFilter.STRICT}
        )
        
        settings = self.settings_manager.get_settings(self.test_user_id)
        self.assertEqual(settings.chat_filter, ChatFilter.STRICT)

    def test_graphics_settings(self):
        """Test graphics settings"""
        # Update graphics settings
        updates = {
            'graphics': {
                'resolution': '2560x1440',
                'fullscreen': False,
                'vsync': False,
                'frame_rate_limit': 144
            }
        }
        
        self.settings_manager.update_settings(
            self.test_user_id,
            updates
        )
        
        settings = self.settings_manager.get_settings(self.test_user_id)
        self.assertEqual(settings.graphics.resolution, '2560x1440')
        self.assertEqual(settings.graphics.frame_rate_limit, 144)

    def test_interface_settings(self):
        """Test interface settings"""
        # Update interface settings
        updates = {
            'interface': {
                'ui_scale': 1.2,
                'chat_opacity': 0.5,
                'minimap_size': 1.5,
                'compact_ui': True
            }
        }
        
        self.settings_manager.update_settings(
            self.test_user_id,
            updates
        )
        
        settings = self.settings_manager.get_settings(self.test_user_id)
        self.assertEqual(settings.interface.ui_scale, 1.2)
        self.assertTrue(settings.interface.compact_ui)

    def test_invalid_settings(self):
        """Test handling of invalid settings"""
        # Try to update with invalid category
        updates = {
            'invalid_category': {
                'some_setting': True
            }
        }
        
        success = self.settings_manager.update_settings(
            self.test_user_id,
            updates
        )
        
        self.assertTrue(success)  # Should ignore invalid category
        
        # Try to update with invalid setting
        updates = {
            'gameplay': {
                'invalid_setting': True
            }
        }
        
        success = self.settings_manager.update_settings(
            self.test_user_id,
            updates
        )
        
        self.assertTrue(success)  # Should ignore invalid setting

if __name__ == '__main__':
    unittest.main()
