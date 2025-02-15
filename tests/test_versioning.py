import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum, auto
import semver
import json

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class VersionType(Enum):
    """Version types"""
    MAJOR = auto()
    MINOR = auto()
    PATCH = auto()

@dataclass
class Version:
    """Version information"""
    version: str
    release_date: datetime
    changes: List[Dict[str, str]]
    breaking_changes: List[str]
    min_client_version: str
    supported_clients: List[str]
    metadata: Optional[Dict[str, Any]] = None

class VersioningSystem:
    """System for version control and compatibility"""
    def __init__(self, version_file: str = 'versions.json'):
        self.version_file = version_file
        self.versions: Dict[str, Version] = {}
        self.current_version = None
        self.load_versions()

    def load_versions(self):
        """Load version history"""
        if os.path.exists(self.version_file):
            with open(self.version_file, 'r') as f:
                data = json.load(f)
                for version_data in data['versions']:
                    version = Version(
                        version=version_data['version'],
                        release_date=datetime.fromisoformat(
                            version_data['release_date']
                        ),
                        changes=version_data['changes'],
                        breaking_changes=version_data['breaking_changes'],
                        min_client_version=version_data['min_client_version'],
                        supported_clients=version_data['supported_clients'],
                        metadata=version_data.get('metadata')
                    )
                    self.versions[version.version] = version
                
                self.current_version = data['current_version']

    def save_versions(self):
        """Save version history"""
        data = {
            'current_version': self.current_version,
            'versions': [
                {
                    'version': v.version,
                    'release_date': v.release_date.isoformat(),
                    'changes': v.changes,
                    'breaking_changes': v.breaking_changes,
                    'min_client_version': v.min_client_version,
                    'supported_clients': v.supported_clients,
                    'metadata': v.metadata
                }
                for v in self.versions.values()
            ]
        }
        
        with open(self.version_file, 'w') as f:
            json.dump(data, f, indent=2)

    def create_version(
        self,
        version_type: VersionType,
        changes: List[Dict[str, str]],
        breaking_changes: List[str],
        min_client_version: str,
        supported_clients: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Version:
        """Create a new version"""
        if not self.current_version:
            new_version = "1.0.0"
        else:
            ver = semver.VersionInfo.parse(self.current_version)
            if version_type == VersionType.MAJOR:
                new_version = str(ver.bump_major())
            elif version_type == VersionType.MINOR:
                new_version = str(ver.bump_minor())
            else:
                new_version = str(ver.bump_patch())
        
        version = Version(
            version=new_version,
            release_date=datetime.utcnow(),
            changes=changes,
            breaking_changes=breaking_changes,
            min_client_version=min_client_version,
            supported_clients=supported_clients,
            metadata=metadata
        )
        
        self.versions[new_version] = version
        self.current_version = new_version
        self.save_versions()
        
        return version

    def get_version(self, version: str) -> Optional[Version]:
        """Get version information"""
        return self.versions.get(version)

    def get_current_version(self) -> Optional[Version]:
        """Get current version"""
        if self.current_version:
            return self.versions.get(self.current_version)
        return None

    def check_compatibility(
        self,
        client_version: str
    ) -> Tuple[bool, Optional[str]]:
        """Check client compatibility"""
        if not self.current_version:
            return True, None
        
        current = self.versions[self.current_version]
        
        # Check minimum version
        if semver.VersionInfo.parse(client_version) < \
           semver.VersionInfo.parse(current.min_client_version):
            return False, "Client version too old"
        
        # Check supported versions
        if client_version not in current.supported_clients:
            return False, "Client version not supported"
        
        return True, None

    def get_changelog(
        self,
        from_version: Optional[str] = None,
        to_version: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get changelog between versions"""
        if not from_version:
            from_version = min(self.versions.keys())
        if not to_version:
            to_version = self.current_version
        
        changelog = []
        for version in sorted(
            self.versions.keys(),
            key=lambda v: semver.VersionInfo.parse(v)
        ):
            if semver.VersionInfo.parse(version) > semver.VersionInfo.parse(from_version) and \
               semver.VersionInfo.parse(version) <= semver.VersionInfo.parse(to_version):
                v = self.versions[version]
                changelog.append({
                    'version': v.version,
                    'release_date': v.release_date,
                    'changes': v.changes,
                    'breaking_changes': v.breaking_changes
                })
        
        return changelog

class TestVersioning(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.version_file = 'test_versions.json'
        self.versioning = VersioningSystem(self.version_file)

    def tearDown(self):
        """Clean up after each test"""
        if os.path.exists(self.version_file):
            os.remove(self.version_file)

    def test_version_creation(self):
        """Test version creation"""
        # Create initial version
        version = self.versioning.create_version(
            VersionType.MAJOR,
            [{'feature': 'Initial release'}],
            [],
            '1.0.0',
            ['1.0.0']
        )
        
        # Verify version
        self.assertEqual(version.version, '1.0.0')
        self.assertEqual(self.versioning.current_version, '1.0.0')
        
        # Create minor version
        version = self.versioning.create_version(
            VersionType.MINOR,
            [{'feature': 'New feature'}],
            [],
            '1.0.0',
            ['1.0.0', '1.1.0']
        )
        
        self.assertEqual(version.version, '1.1.0')

    def test_version_loading(self):
        """Test version loading"""
        # Create versions
        self.versioning.create_version(
            VersionType.MAJOR,
            [{'feature': 'Initial release'}],
            [],
            '1.0.0',
            ['1.0.0']
        )
        
        # Create new versioning system
        new_versioning = VersioningSystem(self.version_file)
        
        # Verify loaded versions
        self.assertEqual(
            new_versioning.current_version,
            '1.0.0'
        )
        self.assertIn('1.0.0', new_versioning.versions)

    def test_compatibility_checking(self):
        """Test compatibility checking"""
        # Create version with requirements
        self.versioning.create_version(
            VersionType.MAJOR,
            [{'feature': 'Initial release'}],
            [],
            '1.0.0',
            ['1.0.0', '1.1.0']
        )
        
        # Check compatible version
        compatible, message = self.versioning.check_compatibility('1.0.0')
        self.assertTrue(compatible)
        
        # Check incompatible version
        compatible, message = self.versioning.check_compatibility('0.9.0')
        self.assertFalse(compatible)
        self.assertEqual(message, "Client version too old")

    def test_changelog_generation(self):
        """Test changelog generation"""
        # Create multiple versions
        versions = [
            (VersionType.MAJOR, [{'feature': 'Initial release'}]),
            (VersionType.MINOR, [{'feature': 'New feature'}]),
            (VersionType.PATCH, [{'fix': 'Bug fix'}])
        ]
        
        for type, changes in versions:
            self.versioning.create_version(
                type,
                changes,
                [],
                '1.0.0',
                ['1.0.0']
            )
        
        # Get full changelog
        changelog = self.versioning.get_changelog()
        self.assertEqual(len(changelog), 3)
        
        # Get partial changelog
        changelog = self.versioning.get_changelog('1.0.0', '1.1.0')
        self.assertEqual(len(changelog), 1)

    def test_breaking_changes(self):
        """Test breaking changes tracking"""
        breaking_changes = [
            "API endpoint removed",
            "Database schema changed"
        ]
        
        # Create version with breaking changes
        version = self.versioning.create_version(
            VersionType.MAJOR,
            [{'feature': 'Major update'}],
            breaking_changes,
            '2.0.0',
            ['2.0.0']
        )
        
        # Verify breaking changes
        self.assertEqual(version.breaking_changes, breaking_changes)
        
        # Check changelog
        changelog = self.versioning.get_changelog()
        self.assertEqual(
            changelog[0]['breaking_changes'],
            breaking_changes
        )

    def test_version_metadata(self):
        """Test version metadata"""
        metadata = {
            'build_number': '12345',
            'commit_hash': 'abc123',
            'build_date': datetime.utcnow().isoformat()
        }
        
        # Create version with metadata
        version = self.versioning.create_version(
            VersionType.MAJOR,
            [{'feature': 'Initial release'}],
            [],
            '1.0.0',
            ['1.0.0'],
            metadata
        )
        
        # Verify metadata
        self.assertEqual(version.metadata, metadata)
        
        # Load and verify
        new_versioning = VersioningSystem(self.version_file)
        loaded_version = new_versioning.get_version('1.0.0')
        self.assertEqual(loaded_version.metadata, metadata)

    def test_version_sequence(self):
        """Test version sequence validation"""
        # Create version sequence
        versions = [
            (VersionType.MAJOR, '1.0.0'),
            (VersionType.MINOR, '1.1.0'),
            (VersionType.PATCH, '1.1.1')
        ]
        
        for type, expected_version in versions:
            version = self.versioning.create_version(
                type,
                [{'change': 'Update'}],
                [],
                '1.0.0',
                ['1.0.0']
            )
            self.assertEqual(version.version, expected_version)

if __name__ == '__main__':
    unittest.main()
