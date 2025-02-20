#!/usr/bin/env python3
"""Data management script for Terminusa Online"""

import os
import sys
import argparse
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Data directories
DATA_DIRS = {
    'backups': project_root / 'backups',
    'logs': project_root / 'logs',
    'data': project_root / 'data',
    'stats': project_root / 'stats'
}

# Data subdirectories
DATA_SUBDIRS = [
    'market',
    'combat',
    'social',
    'ai'
]

def setup_directories():
    """Create required data directories"""
    print("Setting up data directories...")
    
    for name, path in DATA_DIRS.items():
        path.mkdir(exist_ok=True)
        print(f"Created {name} directory: {path}")
    
    data_dir = DATA_DIRS['data']
    for subdir in DATA_SUBDIRS:
        (data_dir / subdir).mkdir(exist_ok=True)
        print(f"Created data subdirectory: {subdir}")

def cleanup_old_data(args):
    """Clean up old data files"""
    print("Cleaning up old data files...")
    
    # Calculate cutoff date
    cutoff = datetime.now() - timedelta(days=args.days)
    print(f"Removing files older than: {cutoff.date()}")
    
    total_removed = 0
    total_size = 0
    
    # Clean each directory
    for name, path in DATA_DIRS.items():
        if not path.exists():
            continue
        
        print(f"\nChecking {name} directory...")
        
        # Handle subdirectories for data
        if name == 'data':
            for subdir in DATA_SUBDIRS:
                subpath = path / subdir
                if not subpath.exists():
                    continue
                
                removed, size = cleanup_directory(subpath, cutoff, args.dry_run)
                total_removed += removed
                total_size += size
        else:
            removed, size = cleanup_directory(path, cutoff, args.dry_run)
            total_removed += removed
            total_size += size
    
    print(f"\nTotal files removed: {total_removed}")
    print(f"Total space freed: {format_size(total_size)}")

def cleanup_directory(path: Path, cutoff: datetime, dry_run: bool) -> tuple[int, int]:
    """Clean up files in a directory older than cutoff date"""
    removed = 0
    total_size = 0
    
    for item in path.glob('*'):
        if item.is_file():
            mtime = datetime.fromtimestamp(item.stat().st_mtime)
            if mtime < cutoff:
                size = item.stat().st_size
                if dry_run:
                    print(f"Would remove: {item} ({format_size(size)})")
                else:
                    print(f"Removing: {item} ({format_size(size)})")
                    item.unlink()
                removed += 1
                total_size += size
    
    return removed, total_size

def format_size(size: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"

def analyze_data(args):
    """Analyze data usage and patterns"""
    print("Data Analysis Report")
    print("=" * 50)
    
    total_files = 0
    total_size = 0
    data_types: Dict[str, Dict[str, Any]] = {}
    
    # Analyze each directory
    for name, path in DATA_DIRS.items():
        if not path.exists():
            continue
        
        print(f"\n{name.title()} Directory:")
        print("-" * 30)
        
        # Handle subdirectories for data
        if name == 'data':
            for subdir in DATA_SUBDIRS:
                subpath = path / subdir
                if not subpath.exists():
                    continue
                
                files, size, types = analyze_directory(subpath)
                total_files += files
                total_size += size
                data_types.update(types)
                
                print(f"{subdir}:")
                print(f"  Files: {files}")
                print(f"  Size: {format_size(size)}")
        else:
            files, size, types = analyze_directory(path)
            total_files += files
            total_size += size
            data_types.update(types)
            
            print(f"Files: {files}")
            print(f"Size: {format_size(size)}")
    
    print("\nFile Type Analysis:")
    print("-" * 30)
    for ext, info in sorted(data_types.items()):
        print(f"{ext:8}: {info['count']:5} files, {format_size(info['size'])}")
    
    print(f"\nTotal Files: {total_files}")
    print(f"Total Size: {format_size(total_size)}")

def analyze_directory(path: Path) -> tuple[int, int, Dict[str, Dict[str, Any]]]:
    """Analyze files in a directory"""
    files = 0
    total_size = 0
    types: Dict[str, Dict[str, Any]] = {}
    
    for item in path.glob('*'):
        if item.is_file():
            files += 1
            size = item.stat().st_size
            total_size += size
            
            ext = item.suffix.lower() or 'none'
            if ext not in types:
                types[ext] = {'count': 0, 'size': 0}
            types[ext]['count'] += 1
            types[ext]['size'] += size
    
    return files, total_size, types

def export_data_info(args):
    """Export data directory information"""
    info = {
        'timestamp': datetime.utcnow().isoformat(),
        'directories': {}
    }
    
    # Analyze each directory
    for name, path in DATA_DIRS.items():
        if not path.exists():
            continue
        
        dir_info = {
            'path': str(path),
            'total_files': 0,
            'total_size': 0,
            'file_types': {},
            'subdirectories': {}
        }
        
        # Handle subdirectories for data
        if name == 'data':
            for subdir in DATA_SUBDIRS:
                subpath = path / subdir
                if not subpath.exists():
                    continue
                
                files, size, types = analyze_directory(subpath)
                dir_info['subdirectories'][subdir] = {
                    'files': files,
                    'size': size,
                    'types': {ext: dict(info) for ext, info in types.items()}
                }
                dir_info['total_files'] += files
                dir_info['total_size'] += size
                
                # Merge file types
                for ext, type_info in types.items():
                    if ext not in dir_info['file_types']:
                        dir_info['file_types'][ext] = {'count': 0, 'size': 0}
                    dir_info['file_types'][ext]['count'] += type_info['count']
                    dir_info['file_types'][ext]['size'] += type_info['size']
        else:
            files, size, types = analyze_directory(path)
            dir_info['total_files'] = files
            dir_info['total_size'] = size
            dir_info['file_types'] = {ext: dict(info) for ext, info in types.items()}
        
        info['directories'][name] = dir_info
    
    # Save to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    stats_dir = DATA_DIRS['stats']
    stats_file = stats_dir / f'data_info_{timestamp}.json'
    
    with open(stats_file, 'w') as f:
        json.dump(info, f, indent=2)
    
    print(f"Data information exported to: {stats_file}")

def main():
    parser = argparse.ArgumentParser(description="Terminusa Online Data Management")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup',
                                       help='Setup data directories')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup',
                                         help='Clean up old data files')
    cleanup_parser.add_argument('--days', type=int, default=30,
                              help='Remove files older than N days')
    cleanup_parser.add_argument('--dry-run', action='store_true',
                              help='Show what would be removed')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze',
                                         help='Analyze data usage')
    
    # Export command
    export_parser = subparsers.add_parser('export',
                                        help='Export data information')
    
    args = parser.parse_args()
    
    if args.command == 'setup':
        setup_directories()
    elif args.command == 'cleanup':
        cleanup_old_data(args)
    elif args.command == 'analyze':
        analyze_data(args)
    elif args.command == 'export':
        export_data_info(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
