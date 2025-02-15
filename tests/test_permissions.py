import unittest
from unittest.mock import Mock, patch
import sys
import os
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum, auto

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Permission(Enum):
    """Permission types"""
    # User Management
    CREATE_USER = auto()
    DELETE_USER = auto()
    MODIFY_USER = auto()
    VIEW_USER = auto()
    
    # Guild Management
    CREATE_GUILD = auto()
    DELETE_GUILD = auto()
    MODIFY_GUILD = auto()
    INVITE_MEMBER = auto()
    KICK_MEMBER = auto()
    
    # Party Management
    CREATE_PARTY = auto()
    INVITE_TO_PARTY = auto()
    KICK_FROM_PARTY = auto()
    
    # Game Actions
    ENTER_GATE = auto()
    USE_MARKETPLACE = auto()
    TRADE_ITEMS = auto()
    USE_CHAT = auto()
    
    # Admin Actions
    VIEW_LOGS = auto()
    MODIFY_SETTINGS = auto()
    BAN_USER = auto()
    MUTE_USER = auto()
    VIEW_METRICS = auto()
    MANAGE_MAINTENANCE = auto()

class Role(Enum):
    """User roles"""
    GUEST = auto()
    PLAYER = auto()
    MODERATOR = auto()
    ADMIN = auto()
    SYSTEM = auto()

@dataclass
class PermissionContext:
    """Permission context data"""
    user_id: int
    target_id: Optional[int] = None
    guild_id: Optional[int] = None
    party_id: Optional[int] = None
    item_id: Optional[int] = None

class PermissionSystem:
    """Manages access control and permissions"""
    def __init__(self):
        self.role_permissions: Dict[Role, Set[Permission]] = {
            Role.GUEST: {
                Permission.VIEW_USER
            },
            Role.PLAYER: {
                Permission.VIEW_USER,
                Permission.CREATE_PARTY,
                Permission.INVITE_TO_PARTY,
                Permission.ENTER_GATE,
                Permission.USE_MARKETPLACE,
                Permission.TRADE_ITEMS,
                Permission.USE_CHAT
            },
            Role.MODERATOR: {
                Permission.VIEW_USER,
                Permission.MODIFY_USER,
                Permission.KICK_MEMBER,
                Permission.KICK_FROM_PARTY,
                Permission.MUTE_USER,
                Permission.VIEW_LOGS
            },
            Role.ADMIN: {
                Permission.CREATE_USER,
                Permission.DELETE_USER,
                Permission.MODIFY_USER,
                Permission.VIEW_USER,
                Permission.DELETE_GUILD,
                Permission.MODIFY_GUILD,
                Permission.BAN_USER,
                Permission.MUTE_USER,
                Permission.VIEW_LOGS,
                Permission.MODIFY_SETTINGS,
                Permission.VIEW_METRICS,
                Permission.MANAGE_MAINTENANCE
            },
            Role.SYSTEM: set(Permission)  # All permissions
        }
        
        self.user_roles: Dict[int, Role] = {}
        self.guild_roles: Dict[int, Dict[int, Role]] = {}  # guild_id -> user_id -> role
        self.custom_permissions: Dict[int, Set[Permission]] = {}

    def assign_role(self, user_id: int, role: Role):
        """Assign role to user"""
        self.user_roles[user_id] = role

    def assign_guild_role(self, guild_id: int, user_id: int, role: Role):
        """Assign guild role to user"""
        if guild_id not in self.guild_roles:
            self.guild_roles[guild_id] = {}
        self.guild_roles[guild_id][user_id] = role

    def grant_permission(self, user_id: int, permission: Permission):
        """Grant custom permission to user"""
        if user_id not in self.custom_permissions:
            self.custom_permissions[user_id] = set()
        self.custom_permissions[user_id].add(permission)

    def revoke_permission(self, user_id: int, permission: Permission):
        """Revoke custom permission from user"""
        if user_id in self.custom_permissions:
            self.custom_permissions[user_id].discard(permission)

    def has_permission(
        self,
        permission: Permission,
        context: PermissionContext
    ) -> bool:
        """Check if user has permission"""
        user_id = context.user_id
        
        # Check system role
        if self.user_roles.get(user_id) == Role.SYSTEM:
            return True
        
        # Check custom permissions
        if user_id in self.custom_permissions:
            if permission in self.custom_permissions[user_id]:
                return True
        
        # Check role permissions
        role = self.user_roles.get(user_id, Role.GUEST)
        if permission in self.role_permissions[role]:
            return True
        
        # Check guild permissions
        if context.guild_id is not None:
            guild_roles = self.guild_roles.get(context.guild_id, {})
            guild_role = guild_roles.get(user_id)
            if guild_role and permission in self.role_permissions[guild_role]:
                return True
        
        return False

    def get_user_permissions(self, user_id: int) -> Set[Permission]:
        """Get all permissions for user"""
        permissions = set()
        
        # Role permissions
        role = self.user_roles.get(user_id, Role.GUEST)
        permissions.update(self.role_permissions[role])
        
        # Custom permissions
        if user_id in self.custom_permissions:
            permissions.update(self.custom_permissions[user_id])
        
        return permissions

class TestPermissions(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.permissions = PermissionSystem()
        
        # Test users
        self.admin_id = 1
        self.mod_id = 2
        self.player_id = 3
        self.guest_id = 4
        
        # Assign roles
        self.permissions.assign_role(self.admin_id, Role.ADMIN)
        self.permissions.assign_role(self.mod_id, Role.MODERATOR)
        self.permissions.assign_role(self.player_id, Role.PLAYER)
        self.permissions.assign_role(self.guest_id, Role.GUEST)

    def test_basic_permissions(self):
        """Test basic permission checks"""
        # Admin permissions
        context = PermissionContext(user_id=self.admin_id)
        self.assertTrue(
            self.permissions.has_permission(
                Permission.BAN_USER,
                context
            )
        )
        
        # Moderator permissions
        context = PermissionContext(user_id=self.mod_id)
        self.assertTrue(
            self.permissions.has_permission(
                Permission.MUTE_USER,
                context
            )
        )
        
        # Player permissions
        context = PermissionContext(user_id=self.player_id)
        self.assertTrue(
            self.permissions.has_permission(
                Permission.USE_CHAT,
                context
            )
        )
        
        # Guest permissions
        context = PermissionContext(user_id=self.guest_id)
        self.assertTrue(
            self.permissions.has_permission(
                Permission.VIEW_USER,
                context
            )
        )

    def test_permission_denial(self):
        """Test permission denial"""
        context = PermissionContext(user_id=self.player_id)
        
        # Player shouldn't have admin permissions
        self.assertFalse(
            self.permissions.has_permission(
                Permission.BAN_USER,
                context
            )
        )
        
        # Guest shouldn't have player permissions
        context = PermissionContext(user_id=self.guest_id)
        self.assertFalse(
            self.permissions.has_permission(
                Permission.USE_MARKETPLACE,
                context
            )
        )

    def test_custom_permissions(self):
        """Test custom permission assignment"""
        # Grant custom permission
        self.permissions.grant_permission(
            self.player_id,
            Permission.VIEW_LOGS
        )
        
        context = PermissionContext(user_id=self.player_id)
        self.assertTrue(
            self.permissions.has_permission(
                Permission.VIEW_LOGS,
                context
            )
        )
        
        # Revoke permission
        self.permissions.revoke_permission(
            self.player_id,
            Permission.VIEW_LOGS
        )
        
        self.assertFalse(
            self.permissions.has_permission(
                Permission.VIEW_LOGS,
                context
            )
        )

    def test_guild_permissions(self):
        """Test guild-specific permissions"""
        guild_id = 1
        
        # Assign guild role
        self.permissions.assign_guild_role(
            guild_id,
            self.player_id,
            Role.MODERATOR
        )
        
        context = PermissionContext(
            user_id=self.player_id,
            guild_id=guild_id
        )
        
        # Should have moderator permissions in guild
        self.assertTrue(
            self.permissions.has_permission(
                Permission.KICK_MEMBER,
                context
            )
        )
        
        # Should not have moderator permissions outside guild
        context = PermissionContext(user_id=self.player_id)
        self.assertFalse(
            self.permissions.has_permission(
                Permission.KICK_MEMBER,
                context
            )
        )

    def test_system_role(self):
        """Test system role permissions"""
        system_id = 999
        self.permissions.assign_role(system_id, Role.SYSTEM)
        
        context = PermissionContext(user_id=system_id)
        
        # Should have all permissions
        for permission in Permission:
            self.assertTrue(
                self.permissions.has_permission(
                    permission,
                    context
                )
            )

    def test_permission_listing(self):
        """Test permission listing"""
        # Get admin permissions
        admin_perms = self.permissions.get_user_permissions(self.admin_id)
        self.assertIn(Permission.BAN_USER, admin_perms)
        self.assertIn(Permission.MODIFY_SETTINGS, admin_perms)
        
        # Get player permissions
        player_perms = self.permissions.get_user_permissions(self.player_id)
        self.assertIn(Permission.USE_CHAT, player_perms)
        self.assertNotIn(Permission.BAN_USER, player_perms)

    def test_context_based_permissions(self):
        """Test context-based permission checks"""
        # Test party context
        context = PermissionContext(
            user_id=self.player_id,
            party_id=1
        )
        self.assertTrue(
            self.permissions.has_permission(
                Permission.INVITE_TO_PARTY,
                context
            )
        )
        
        # Test item context
        context = PermissionContext(
            user_id=self.player_id,
            item_id=1
        )
        self.assertTrue(
            self.permissions.has_permission(
                Permission.TRADE_ITEMS,
                context
            )
        )

    def test_role_hierarchy(self):
        """Test role hierarchy"""
        # Admin should have moderator permissions
        context = PermissionContext(user_id=self.admin_id)
        mod_perms = self.permissions.get_user_permissions(self.mod_id)
        
        for permission in mod_perms:
            self.assertTrue(
                self.permissions.has_permission(
                    permission,
                    context
                )
            )
        
        # Moderator should have player permissions
        context = PermissionContext(user_id=self.mod_id)
        player_perms = self.permissions.get_user_permissions(self.player_id)
        
        for permission in player_perms:
            self.assertTrue(
                self.permissions.has_permission(
                    permission,
                    context
                )
            )

    def test_permission_inheritance(self):
        """Test permission inheritance"""
        # Create new role with inherited permissions
        custom_role_perms = self.permissions.role_permissions[Role.PLAYER].copy()
        custom_role_perms.add(Permission.VIEW_LOGS)
        
        # Assign to user
        user_id = 100
        self.permissions.assign_role(user_id, Role.PLAYER)
        self.permissions.grant_permission(user_id, Permission.VIEW_LOGS)
        
        # Check permissions
        perms = self.permissions.get_user_permissions(user_id)
        self.assertEqual(perms, custom_role_perms)

    def test_multiple_contexts(self):
        """Test permissions across multiple contexts"""
        guild_id = 1
        party_id = 1
        
        # Set up complex context
        context = PermissionContext(
            user_id=self.player_id,
            guild_id=guild_id,
            party_id=party_id
        )
        
        # Assign guild role
        self.permissions.assign_guild_role(
            guild_id,
            self.player_id,
            Role.MODERATOR
        )
        
        # Should have combined permissions
        self.assertTrue(
            self.permissions.has_permission(
                Permission.KICK_MEMBER,  # Guild permission
                context
            )
        )
        self.assertTrue(
            self.permissions.has_permission(
                Permission.USE_CHAT,  # Player permission
                context
            )
        )

if __name__ == '__main__':
    unittest.main()
