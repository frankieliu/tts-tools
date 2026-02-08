#!/usr/bin/env python3
"""
Comprehensive Tabletop Simulator object analysis for Tend game
Analyzes structure, categorizes objects, and provides spatial organization
"""

import json
from collections import defaultdict
from typing import Dict, List, Any

def extract_color_from_name(name: str) -> str:
    """Extract color from object name/nickname"""
    colors = ['Red', 'Blue', 'Green', 'Yellow', 'Orange', 'Purple', 'Pink',
              'White', 'Black', 'Brown', 'Grey', 'Gray', 'Teal', 'Cyan']
    name_upper = name.upper()
    for color in colors:
        if color.upper() in name_upper:
            return color
    return "No Color"

def get_zone_from_position(pos: Dict) -> str:
    """Determine game zone based on position"""
    x, z = pos['x'], pos['z']

    # Define zones based on typical TTS layout
    if abs(x) < 10 and abs(z) < 10:
        return "Center Play Area"
    elif x < -30:
        return "Left Player Area"
    elif x > 30:
        return "Right Player Area"
    elif z < -10:
        return "Bottom Player Area"
    elif z > 10:
        return "Top Player Area"
    elif x < 0:
        return "Left Side"
    else:
        return "Right Side"

def categorize_by_purpose(obj: Dict, parent_type: str = None) -> str:
    """Enhanced categorization with better heuristics"""
    name = obj.get('Nickname', '').lower()
    obj_type = obj.get('Name', '')
    description = obj.get('Description', '').lower()
    pos = obj.get('Transform', {})
    x = pos.get('posX', 0)

    # Special handling for nested objects
    if parent_type:
        if 'cargo' in parent_type.lower():
            return "Cargo Sheets"
        elif 'scratch' in parent_type.lower():
            return "Scratch Off Cards"

    # Type-based categorization
    if obj_type == 'Custom_Board':
        return "Player Boards"
    elif obj_type == 'Custom_Tile':
        return "Tiles/Tokens"
    elif obj_type == 'Infinite_Bag':
        return "Token Sources (Infinite Bags)"
    elif obj_type == 'Custom_Dice':
        return "Dice"
    elif obj_type == 'ScriptingTrigger':
        return "Game Automation/Scripting"
    elif obj_type == 'HandTrigger':
        return "Hand Zones"
    elif obj_type == 'Custom_Assetbundle':
        return "3D Decorative Assets"
    elif obj_type == 'Custom_PDF':
        return "Rulebook"
    elif obj_type in ['Deck', 'DeckCustom']:
        return "Card Decks"
    elif obj_type in ['Card', 'CardCustom']:
        # Cards placed on table vs in decks
        if parent_type:
            return "Cards (in deck)"
        else:
            return "Cards (on table)"
    elif obj_type == 'Custom_Model_Bag':
        return "Storage Bags"
    elif 'piece' in obj_type.lower():
        return "Special Game Pieces"
    elif obj_type == 'Custom_Model':
        return "3D Models"
    else:
        return "Other Components"

def process_object(obj: Dict, parent_info: Dict = None) -> Dict:
    """Process a single object and return its record"""
    guid = obj.get('GUID', 'N/A')
    name = obj.get('Name', 'Unknown')
    nickname = obj.get('Nickname', '')
    description = obj.get('Description', '')

    # Extract position
    transform = obj.get('Transform', {})
    position = {
        'x': transform.get('posX', 0),
        'y': transform.get('posY', 0),
        'z': transform.get('posZ', 0)
    }

    zone = get_zone_from_position(position)

    # Create object record
    obj_record = {
        'guid': guid,
        'type': name,
        'nickname': nickname,
        'description': description,
        'position': position,
        'zone': zone,
        'locked': obj.get('Locked', False),
        'parent': parent_info
    }

    return obj_record

def analyze_objects(json_data: Dict) -> Dict:
    """Main analysis function"""
    objects = json_data.get('ObjectStates', [])

    # Storage for analysis
    by_type = defaultdict(list)
    by_purpose = defaultdict(list)
    by_color = defaultdict(list)
    by_zone = defaultdict(list)
    all_objects = []

    top_level_count = len(objects)
    nested_count = 0

    print(f"Processing {top_level_count} top-level objects...")

    for obj in objects:
        # Process the parent object
        obj_record = process_object(obj)

        # Categorize
        obj_type = obj_record['type']
        purpose = categorize_by_purpose(obj)
        color = extract_color_from_name(obj_record['nickname']) if obj_record['nickname'] else "No Color"
        zone = obj_record['zone']

        # Store in categories
        by_type[obj_type].append(obj_record)
        by_purpose[purpose].append(obj_record)
        by_color[color].append(obj_record)
        by_zone[zone].append(obj_record)
        all_objects.append(obj_record)

        # Process nested objects (in decks, bags, etc.)
        if 'ContainedObjects' in obj:
            parent_name = f"{obj_record['type']}"
            if obj_record['nickname']:
                parent_name += f" [{obj_record['nickname']}]"
            parent_type = obj_record['nickname'] or obj_record['type']

            contained = obj['ContainedObjects']
            print(f"  Found {len(contained)} objects in {parent_name}")
            nested_count += len(contained)

            for nested_obj in contained:
                nested_record = process_object(nested_obj, parent_info=parent_name)

                # Categorize nested object
                nested_type = nested_record['type']
                nested_purpose = categorize_by_purpose(nested_obj, parent_type)
                nested_color = extract_color_from_name(nested_record['nickname']) if nested_record['nickname'] else "No Color"
                nested_zone = nested_record['zone']

                # Store in categories
                by_type[nested_type].append(nested_record)
                by_purpose[nested_purpose].append(nested_record)
                by_color[nested_color].append(nested_record)
                by_zone[nested_zone].append(nested_record)
                all_objects.append(nested_record)

    total_count = top_level_count + nested_count
    print(f"Total objects: {total_count} ({top_level_count} top-level + {nested_count} nested)")

    return {
        'total_count': total_count,
        'top_level_count': top_level_count,
        'nested_count': nested_count,
        'by_type': dict(by_type),
        'by_purpose': dict(by_purpose),
        'by_color': dict(by_color),
        'by_zone': dict(by_zone),
        'all_objects': all_objects,
        'game_info': {
            'name': json_data.get('SaveName', 'Unknown'),
            'date': json_data.get('Date', 'Unknown'),
            'complexity': json_data.get('GameComplexity', 'Unknown'),
            'player_counts': json_data.get('PlayerCounts', [])
        }
    }

def format_report(analysis: Dict) -> str:
    """Format analysis results as a comprehensive report"""
    report = []
    report.append("=" * 80)
    report.append("TABLETOP SIMULATOR OBJECT ANALYSIS")
    report.append(f"Game: {analysis['game_info']['name']}")
    report.append(f"Date: {analysis['game_info']['date']}")
    report.append(f"Complexity: {analysis['game_info']['complexity']}")
    report.append(f"Players: {analysis['game_info']['player_counts'][0]}-{analysis['game_info']['player_counts'][1]}")
    report.append("=" * 80)
    report.append("")

    # Summary statistics
    report.append("SUMMARY STATISTICS")
    report.append("-" * 80)
    report.append(f"Total Objects: {analysis['total_count']}")
    report.append(f"  Top-level Objects: {analysis['top_level_count']}")
    report.append(f"  Nested Objects (in decks/bags): {analysis['nested_count']}")
    report.append(f"Unique Object Types: {len(analysis['by_type'])}")
    report.append(f"Functional Categories: {len(analysis['by_purpose'])}")
    report.append("")

    # By Type
    report.append("DISTRIBUTION BY OBJECT TYPE")
    report.append("-" * 80)
    by_type_sorted = sorted(analysis['by_type'].items(), key=lambda x: len(x[1]), reverse=True)
    for obj_type, objs in by_type_sorted:
        top_level = len([o for o in objs if not o['parent']])
        nested = len([o for o in objs if o['parent']])
        if nested > 0:
            report.append(f"{obj_type:30s} : {len(objs):4d} objects ({top_level} top-level, {nested} nested)")
        else:
            report.append(f"{obj_type:30s} : {len(objs):4d} objects")
    report.append("")

    # By Purpose
    report.append("DISTRIBUTION BY FUNCTIONAL PURPOSE")
    report.append("-" * 80)
    by_purpose_sorted = sorted(analysis['by_purpose'].items(), key=lambda x: len(x[1]), reverse=True)
    for purpose, objs in by_purpose_sorted:
        report.append(f"{purpose:35s} : {len(objs):4d} objects")
    report.append("")

    # By Zone
    report.append("SPATIAL DISTRIBUTION (GAME ZONES)")
    report.append("-" * 80)
    by_zone_sorted = sorted(analysis['by_zone'].items(), key=lambda x: len(x[1]), reverse=True)
    for zone, objs in by_zone_sorted:
        report.append(f"{zone:30s} : {len(objs):4d} objects")
    report.append("")

    # By Color
    report.append("DISTRIBUTION BY COLOR")
    report.append("-" * 80)
    by_color_sorted = sorted(analysis['by_color'].items(), key=lambda x: len(x[1]), reverse=True)
    color_found = False
    for color, objs in by_color_sorted:
        if color != "No Color":
            color_found = True
            report.append(f"{color:30s} : {len(objs):4d} objects")
    if not color_found:
        report.append("No color-coded objects found.")
    else:
        no_color_count = len(analysis['by_color'].get('No Color', []))
        report.append(f"{'(No Color Association)':30s} : {no_color_count:4d} objects")
    report.append("")

    # Detailed listings by purpose
    report.append("=" * 80)
    report.append("DETAILED CATEGORIZATION BY FUNCTIONAL PURPOSE")
    report.append("=" * 80)
    report.append("")

    for purpose, objs in by_purpose_sorted:
        report.append("-" * 80)
        report.append(f"{purpose.upper()}")
        report.append(f"Count: {len(objs)} objects")
        report.append("-" * 80)

        # Separate top-level and nested
        top_level = [o for o in objs if not o['parent']]
        nested = [o for o in objs if o['parent']]

        if top_level:
            report.append(f"\nTop-level objects: {len(top_level)}")
            for obj in top_level:
                nickname = obj['nickname'] if obj['nickname'] else "(no nickname)"
                report.append(f"  [{obj['guid']}] {obj['type']}")
                if nickname != "(no nickname)":
                    report.append(f"    Name: {nickname}")
                report.append(f"    Position: ({obj['position']['x']:.1f}, {obj['position']['y']:.1f}, {obj['position']['z']:.1f})")
                report.append(f"    Zone: {obj['zone']}")
                if obj['description']:
                    desc = obj['description'][:80] + "..." if len(obj['description']) > 80 else obj['description']
                    report.append(f"    Description: {desc}")
                report.append("")

        if nested:
            report.append(f"Nested objects: {len(nested)}")
            # Group by parent
            by_parent = defaultdict(list)
            for obj in nested:
                by_parent[obj['parent']].append(obj)

            for parent, parent_objs in by_parent.items():
                report.append(f"\n  In {parent}: {len(parent_objs)} objects")
                for obj in parent_objs[:10]:  # Show first 10 from each parent
                    nickname = obj['nickname'] if obj['nickname'] else "(no nickname)"
                    report.append(f"    [{obj['guid']}] {obj['type']}: {nickname}")
                if len(parent_objs) > 10:
                    report.append(f"    ... and {len(parent_objs) - 10} more")

        report.append("")

    # Type reference
    report.append("=" * 80)
    report.append("OBJECT TYPE REFERENCE")
    report.append("=" * 80)
    report.append("")

    for obj_type, objs in by_type_sorted:
        report.append("-" * 80)
        report.append(f"{obj_type}: {len(objs)} total")

        top_level = [o for o in objs if not o['parent']]
        nested = [o for o in objs if o['parent']]

        if top_level:
            report.append(f"  {len(top_level)} top-level instances")
        if nested:
            report.append(f"  {len(nested)} nested instances (in decks/bags)")

        # Show sample
        sample = objs[0]
        report.append(f"  Example: GUID {sample['guid']}")
        if sample['nickname']:
            report.append(f"    Name: {sample['nickname']}")
        report.append(f"    Position: ({sample['position']['x']:.1f}, {sample['position']['y']:.1f}, {sample['position']['z']:.1f})")
        report.append("")

    return "\n".join(report)

def main():
    """Main execution"""
    input_file = '/Users/frankliu/Library/CloudStorage/Box-Box/Work/bg/tend/Mods/Workshop/3356045383.json'
    output_file = '/Users/frankliu/Library/CloudStorage/Box-Box/Work/bg/tend/Mods/Workshop/tts_analysis_report.txt'

    print(f"Loading JSON file: {input_file}")
    print(f"File size: 3.1MB, 103,431 lines")
    print()

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Game: {data.get('SaveName', 'Unknown')}")
    print(f"Date: {data.get('Date', 'Unknown')}")
    print()

    print("Analyzing objects...")
    analysis = analyze_objects(data)

    print("\nGenerating report...")
    report = format_report(analysis)

    print(f"Saving report to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Total objects analyzed: {analysis['total_count']}")
    print(f"  Top-level: {analysis['top_level_count']}")
    print(f"  Nested: {analysis['nested_count']}")
    print(f"Object types found: {len(analysis['by_type'])}")
    print(f"Functional categories: {len(analysis['by_purpose'])}")
    print(f"Spatial zones: {len(analysis['by_zone'])}")
    print(f"\nReport saved to: {output_file}")

if __name__ == '__main__':
    main()
