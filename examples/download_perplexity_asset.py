#!/usr/bin/env python3
"""
Example: Download a file asset from Perplexity

This script connects to an existing Perplexity chat that has
a downloadable file (e.g., HTML report from code interpreter)
and downloads it to the specified directory.

Usage:
    python download_perplexity_asset.py

Requirements:
    - Browser daemon must be running
    - Perplexity must have a chat with a generated file open
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from chat_automation.perplexity import PerplexityAutomation


async def main():
    """Download asset from Perplexity"""
    print("="*60)
    print("Perplexity File Downloader")
    print("="*60)

    # Create automation instance
    auto = PerplexityAutomation()

    try:
        # Connect to existing browser
        print("\nConnecting to browser daemon...")
        await auto.connect_to_existing_browser()
        print(f"✓ Connected to: {auto.page.url}")

        # Check if on Perplexity
        if "perplexity" not in auto.page.url.lower():
            print("⚠️ Not on Perplexity page!")
            print("Please navigate to a Perplexity chat with files first")
            return 1

        # Download the asset
        print("\nLooking for downloadable assets...")
        result = await auto.download_asset()

        if result:
            print("\n" + "="*60)
            print("✓ DOWNLOAD SUCCESSFUL")
            print("="*60)
            print(f"Filename: {result['filename']}")
            print(f"Saved to: {result['path']}")
            print(f"Source: {result['url'][:80]}...")
            return 0
        else:
            print("\n✗ Download failed")
            print("   Make sure there's a file available on the current page")
            return 1

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
