#!/usr/bin/env python3
"""
Test client for Color Extraction NIM
"""

import asyncio
import aiohttp
import json
import time

async def test_color_extraction():
    """Test the color extraction NIM service"""
    
    # Test image URLs
    test_images = [
        "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800",  # Landscape
        "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800",  # Forest
        "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=800",  # Beach
    ]
    
    base_url = "http://localhost:8080"
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        async with session.get(f"{base_url}/health") as response:
            health_data = await response.json()
            print(f"Health Status: {health_data}")
        
        print("\n" + "="*50)
        
        # Test color extraction for each image
        for i, image_url in enumerate(test_images, 1):
            print(f"\n🎨 Testing image {i}: {image_url}")
            
            payload = {
                "image_url": image_url,
                "num_colors": 5,
                "min_percentage": 0.05
            }
            
            start_time = time.time()
            
            try:
                async with session.post(
                    f"{base_url}/extract-colors",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        processing_time = time.time() - start_time
                        
                        print(f"✅ Success! Processing time: {processing_time:.2f}s")
                        print(f"Algorithm used: {result['algorithm_used']}")
                        print(f"Image dimensions: {result['image_dimensions']}")
                        print(f"Colors found: {result['total_colors_found']}")
                        
                        print("\n🎨 Extracted Colors:")
                        for j, color in enumerate(result['colors'], 1):
                            print(f"  {j}. {color['hex_code']} - {color['percentage']:.1%} ({color['color_name']})")
                    else:
                        error_data = await response.json()
                        print(f"❌ Error {response.status}: {error_data}")
                        
            except asyncio.TimeoutError:
                print("❌ Request timed out")
            except Exception as e:
                print(f"❌ Error: {str(e)}")
            
            print("-" * 30)

if __name__ == "__main__":
    print("🚀 Starting Color Extraction NIM Test Client")
    print("Make sure the NIM service is running on http://localhost:8080")
    print("="*50)
    
    asyncio.run(test_color_extraction())
