#!/usr/bin/env python3
"""
Generate PDFs with all cards from a TTS JSON file, respecting duplicates.
Reads the JSON file to determine how many copies of each card exist.
Generates three PDFs:
  1. Faces with backs - cards that have unique backs
  2. Faces without backs - cards with generic backs
  3. Backs - unique backs mirrored for double-sided printing
"""

import json
from pathlib import Path
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
from collections import Counter

def extract_card_ids_from_json(json_file: Path) -> list:
    """
    Extract all card instances from the TTS JSON file with full CardIDs.
    Returns a list of CardIDs (e.g., [801, 803, 803, 501, ...]).
    """
    with open(json_file) as f:
        data = json.load(f)

    card_ids = []

    def traverse(obj):
        """Recursively traverse to find all cards."""
        if isinstance(obj, dict):
            # Check for DeckIDs array (multiple cards in a deck)
            if 'DeckIDs' in obj:
                card_ids.extend(obj['DeckIDs'])

            # Check for single CardID
            elif 'CardID' in obj and 'CustomDeck' in obj:
                card_ids.append(obj['CardID'])

            # Recurse into all dict values
            for value in obj.values():
                traverse(value)

        elif isinstance(obj, list):
            # Recurse into all list items
            for item in obj:
                traverse(item)

    traverse(data)
    return card_ids


def extract_card_from_sprite_sheet(
    sprite_image: Image.Image,
    grid_width: int,
    grid_height: int,
    position: int,
    rotate_if_landscape: bool = True
) -> Image.Image:
    """
    Extract a single card from a sprite sheet at the given grid position.

    Args:
        sprite_image: PIL Image of the full sprite sheet
        grid_width: Number of cards horizontally
        grid_height: Number of cards vertically
        position: Card position (0-indexed, row-major order)
        rotate_if_landscape: If True, rotate card 90° if width > height

    Returns:
        PIL Image of the extracted card
    """
    sprite_width, sprite_height = sprite_image.size

    # Calculate individual card dimensions
    card_pixel_width = sprite_width // grid_width
    card_pixel_height = sprite_height // grid_height

    # Calculate card position in grid
    col = position % grid_width
    row = position // grid_width

    # Calculate pixel coordinates
    left = col * card_pixel_width
    top = row * card_pixel_height
    right = left + card_pixel_width
    bottom = top + card_pixel_height

    # Extract the card
    card = sprite_image.crop((left, top, right, bottom))

    # Rotate if landscape
    if rotate_if_landscape and card_pixel_width > card_pixel_height:
        card = card.rotate(90, expand=True)

    return card


def draw_card_with_marks(c, card_image, x, y, card_width_pts, card_height_pts):
    """
    Draw a card on the canvas with crop marks.

    Args:
        c: ReportLab canvas
        card_image: PIL Image of the card
        x, y: Position to draw the card
        card_width_pts, card_height_pts: Card dimensions in points
    """
    # Draw the card
    img_reader = ImageReader(card_image)
    c.drawImage(img_reader, x, y, width=card_width_pts, height=card_height_pts, preserveAspectRatio=True)

    # Draw crop marks
    mark_length = 0.15 * inch
    mark_offset = 0.05 * inch

    # Top-left
    c.line(x - mark_offset - mark_length, y + card_height_pts, x - mark_offset, y + card_height_pts)
    c.line(x, y + card_height_pts + mark_offset, x, y + card_height_pts + mark_offset + mark_length)

    # Top-right
    c.line(x + card_width_pts + mark_offset, y + card_height_pts, x + card_width_pts + mark_offset + mark_length, y + card_height_pts)
    c.line(x + card_width_pts, y + card_height_pts + mark_offset, x + card_width_pts, y + card_height_pts + mark_offset + mark_length)

    # Bottom-left
    c.line(x - mark_offset - mark_length, y, x - mark_offset, y)
    c.line(x, y - mark_offset, x, y - mark_offset - mark_length)

    # Bottom-right
    c.line(x + card_width_pts + mark_offset, y, x + card_width_pts + mark_offset + mark_length, y)
    c.line(x + card_width_pts, y - mark_offset, x + card_width_pts, y - mark_offset - mark_length)


def generate_pdf(
    card_list: list,
    sprite_cache: dict,
    output_file: Path,
    card_width: float,
    card_height: float,
    card_spacing: float,
    is_backs: bool = False
):
    """
    Generate a single PDF from a card list.

    Args:
        card_list: List of card info dicts
        sprite_cache: Dict of cached sprite sheet images
        output_file: Output PDF path
        card_width, card_height: Card dimensions in inches
        card_spacing: Spacing between cards in inches
        is_backs: If True, mirror cards horizontally on each page for printing
    """
    total_cards = len(card_list)
    if total_cards == 0:
        print(f"  No cards for {output_file.name}, skipping")
        return

    cards_per_page = 9
    cards_per_row = 3
    cards_per_col = 3
    page_width, page_height = letter

    # Card dimensions
    card_width_pts = card_width * inch
    card_height_pts = card_height * inch
    card_spacing_pts = card_spacing * inch

    # Calculate total grid dimensions
    total_grid_width = (cards_per_row * card_width_pts) + ((cards_per_row - 1) * card_spacing_pts)
    total_grid_height = (cards_per_col * card_height_pts) + ((cards_per_col - 1) * card_spacing_pts)

    # Center the grid on the page
    start_x = (page_width - total_grid_width) / 2
    start_y = page_height - ((page_height - total_grid_height) / 2) - card_height_pts

    # Create PDF
    c = pdf_canvas.Canvas(str(output_file), pagesize=letter)
    total_pages = (total_cards + cards_per_page - 1) // cards_per_page

    print(f"\nGenerating {output_file.name} with {total_pages} pages...")

    for page_num in range(total_pages):
        start_idx = page_num * cards_per_page
        end_idx = min(start_idx + cards_per_page, total_cards)
        page_cards = card_list[start_idx:end_idx]

        # Draw cards on this page
        for idx, card_info in enumerate(page_cards):
            row = idx // cards_per_row
            col = idx % cards_per_row

            # For backs, mirror horizontally within each row
            if is_backs:
                col = (cards_per_row - 1) - col

            x = start_x + col * (card_width_pts + card_spacing_pts)
            y = start_y - row * (card_height_pts + card_spacing_pts)

            # Load sprite sheet (from cache if possible)
            sprite_path_str = str(card_info['sprite_path'])
            if sprite_path_str not in sprite_cache:
                try:
                    sprite_cache[sprite_path_str] = Image.open(card_info['sprite_path'])
                except Exception as e:
                    print(f"  Error loading sprite sheet {card_info['sprite_path']}: {e}")
                    continue

            sprite_image = sprite_cache[sprite_path_str]

            # Extract individual card from sprite sheet
            try:
                card_image = extract_card_from_sprite_sheet(
                    sprite_image,
                    card_info['grid_width'],
                    card_info['grid_height'],
                    card_info['position']
                )

                draw_card_with_marks(c, card_image, x, y, card_width_pts, card_height_pts)

            except Exception as e:
                print(f"  Error extracting card {card_info['card_id']} position {card_info['position']}: {e}")

        # Add page
        if page_num < total_pages - 1:
            c.showPage()

        if (page_num + 1) % 5 == 0:
            print(f"  Page {page_num + 1}/{total_pages} complete...")

    c.save()
    print(f"\n✓ Saved {output_file.name}: {total_pages} pages, {total_cards} cards")


def generate_deck_pdf(
    json_file: Path,
    metadata_file: Path,
    output_dir: Path,
    cards_per_page: int = 9,
    card_width: float = 2.5,
    card_height: float = 3.5,
    card_spacing: float = 0.0
):
    """
    Generate three PDFs: faces with backs, faces without backs, and backs.

    Args:
        json_file: Path to TTS deserialized JSON file
        metadata_file: Path to sprite_metadata.json
        output_dir: Output directory for PDFs
        cards_per_page: Number of cards per page (default 9 for 3x3)
        card_width: Card width in inches (default 2.5)
        card_height: Card height in inches (default 3.5)
        card_spacing: Spacing between cards in inches (default 0.0)
    """
    # Extract all card IDs from JSON
    print("Extracting card IDs from JSON...")
    card_ids = extract_card_ids_from_json(json_file)

    # Load sprite metadata
    with open(metadata_file) as f:
        metadata = json.load(f)
    sprite_sheets = metadata['sprite_sheets']

    # Build card lists
    cards_with_backs = []
    cards_without_backs = []
    backs_list = []
    sprite_cache = {}  # Cache loaded sprite sheets

    print(f"\nFound {len(card_ids)} card instances")
    print("\nProcessing cards by deck...")

    # Group cards by deck for reporting
    card_counter = Counter(card_ids)

    for card_id, count in sorted(card_counter.items()):
        deck_id = card_id // 100
        position = card_id % 100
        deck_id_str = str(deck_id)

        if deck_id_str not in sprite_sheets:
            print(f"  WARNING: Deck {deck_id} (CardID {card_id}): Not found in sprite metadata")
            continue

        sprite_info = sprite_sheets[deck_id_str]
        local_image = Path(sprite_info['local_image'])

        if not local_image.exists():
            print(f"  WARNING: Deck {deck_id}: Image not found: {local_image}")
            continue

        has_unique_back = sprite_info.get('unique_back', False)

        # Prepare card info
        card_info = {
            'card_id': card_id,
            'deck_id': deck_id,
            'position': position,
            'sprite_path': local_image,
            'grid_width': sprite_info['grid_width'],
            'grid_height': sprite_info['grid_height']
        }

        # Add to appropriate list
        for _ in range(count):
            if has_unique_back:
                cards_with_backs.append(card_info.copy())

                # Also add to backs list
                back_image = Path(sprite_info.get('local_back_image', ''))
                if back_image and back_image.exists():
                    back_info = card_info.copy()
                    back_info['sprite_path'] = back_image
                    backs_list.append(back_info)
            else:
                cards_without_backs.append(card_info.copy())

        back_indicator = " (unique back)" if has_unique_back else ""
        print(f"  Deck {deck_id}, Position {position}: {count} copies{back_indicator}")

    print(f"\n=== Summary ===")
    print(f"  Cards with unique backs: {len(cards_with_backs)}")
    print(f"  Cards without unique backs: {len(cards_without_backs)}")
    print(f"  Unique backs: {len(backs_list)}")

    # Generate PDFs
    if cards_with_backs:
        generate_pdf(
            cards_with_backs,
            sprite_cache,
            output_dir / 'complete_deck_faces_with_backs.pdf',
            card_width,
            card_height,
            card_spacing,
            is_backs=False
        )

    if cards_without_backs:
        generate_pdf(
            cards_without_backs,
            sprite_cache,
            output_dir / 'complete_deck_faces_no_backs.pdf',
            card_width,
            card_height,
            card_spacing,
            is_backs=False
        )

    if backs_list:
        generate_pdf(
            backs_list,
            sprite_cache,
            output_dir / 'complete_deck_backs.pdf',
            card_width,
            card_height,
            card_spacing,
            is_backs=True  # Enable horizontal mirroring
        )


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate complete deck PDFs from TTS JSON file')
    parser.add_argument('json_file', help='Path to TTS deserialized JSON file')
    parser.add_argument('-m', '--metadata', default='sprite_metadata.json', help='Path to sprite_metadata.json')
    parser.add_argument('-o', '--output', default='complete_deck.pdf', help='Output PDF file (directory will be used)')
    parser.add_argument('--card-width', type=float, default=2.5, help='Card width in inches (default: 2.5)')
    parser.add_argument('--card-height', type=float, default=3.5, help='Card height in inches (default: 3.5)')
    parser.add_argument('--card-spacing', type=float, default=0.0, help='Spacing between cards in inches (default: 0.0)')

    args = parser.parse_args()

    json_file = Path(args.json_file)
    metadata_file = Path(args.metadata)
    output_file = Path(args.output)
    output_dir = output_file.parent

    generate_deck_pdf(
        json_file,
        metadata_file,
        output_dir,
        card_width=args.card_width,
        card_height=args.card_height,
        card_spacing=args.card_spacing
    )
