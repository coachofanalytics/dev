#!/usr/bin/env python3
"""
Image Optimization Script for CODA Analytics
Optimizes large images to reduce slug size
"""

import os
import sys
from PIL import Image
from pathlib import Path

def optimize_image(image_path, quality=85, max_width=1920):
    """
    Optimize an image file
    
    Args:
        image_path: Path to the image file
        quality: JPEG quality (1-100)
        max_width: Maximum width for resizing
    """
    try:
        # Open the image
        with Image.open(image_path) as img:
            # Get original size
            original_size = os.path.getsize(image_path)
            
            # Convert to RGB if necessary (for JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create a white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Save optimized image
            img.save(image_path, 'JPEG', quality=quality, optimize=True)
            
            # Get new size
            new_size = os.path.getsize(image_path)
            reduction = original_size - new_size
            reduction_percent = (reduction / original_size) * 100
            
            print(f"✅ Optimized: {image_path}")
            print(f"   Original: {original_size:,} bytes")
            print(f"   New: {new_size:,} bytes")
            print(f"   Reduction: {reduction:,} bytes ({reduction_percent:.1f}%)")
            
            return reduction
            
    except Exception as e:
        print(f"❌ Error optimizing {image_path}: {e}")
        return 0

def main():
    """Main optimization function"""
    print("🎯 CODA Analytics Image Optimization")
    print("=" * 50)
    
    # Define the app directory
    app_dir = Path(__file__).parent.parent
    
    # Large images to optimize
    large_images = [
        "main/static/main/image/marketing.jpg",
        "main/static/main/image/fieldprojectmanagement.png", 
        "main/static/main/image/interviews.png",
        "static/management/img/background/company-agenda.png",
        "static/main/img/service-1.jpg",
        "static/main/img/service-2.jpg", 
        "static/main/img/service-3.jpg"
    ]
    
    total_reduction = 0
    optimized_count = 0
    
    for image_path in large_images:
        full_path = app_dir / image_path
        if full_path.exists():
            reduction = optimize_image(str(full_path))
            total_reduction += reduction
            optimized_count += 1
        else:
            print(f"⚠️  Not found: {image_path}")
    
    print("\n" + "=" * 50)
    print(f"🎉 Optimization Complete!")
    print(f"   Images optimized: {optimized_count}")
    print(f"   Total reduction: {total_reduction:,} bytes ({total_reduction/1024/1024:.1f} MB)")
    
    return total_reduction

if __name__ == "__main__":
    main()
