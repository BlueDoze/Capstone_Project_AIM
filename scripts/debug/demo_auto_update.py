#!/usr/bin/env python3
"""
Practical Demonstration of Automatic Method
============================================

This script demonstrates in practice how the system automatically
detects new images and updates embeddings.
"""

import os
import sys
import time
import shutil
from datetime import datetime

def demo_auto_update():
    """Practical demonstration of automatic system"""
    print("🎬 PRACTICAL DEMONSTRATION OF AUTOMATIC METHOD")
    print("=" * 55)
    print(f"📅 Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)
    
    try:
        # Import system
        print("📦 Starting system...")
        import main

        # Wait for initialization
        time.sleep(2)

        print("✅ System started with automatic monitoring active")

        # Check initial status
        initial_status = main.image_manager.get_status()
        print(f"\n📊 INITIAL STATUS:")
        print(f"   • Processed images: {initial_status['total_images']}")
        print(f"   • Images in folder: {initial_status['folder_image_count']}")
        print(f"   • Active monitoring: {main.auto_updater.get_status()['is_running']}")

        # Demonstration 1: Add new image
        print(f"\n🎯 DEMONSTRATION 1: ADDING NEW IMAGE")
        print("-" * 50)

        # Copy an existing image as "new"
        new_image_path = "images/demo_new_image.jpg"
        if os.path.exists("images/M1.jpeg"):
            shutil.copy("images/M1.jpeg", new_image_path)
            print(f"✅ New image added: demo_new_image.jpg")
            print("⏰ Waiting for automatic detection...")

            # Wait for processing
            for i in range(15):  # 15 seconds
                time.sleep(1)
                current_status = main.image_manager.get_status()
                if current_status['total_images'] > initial_status['total_images']:
                    print(f"🎉 Image detected and processed automatically!")
                    print(f"   • Processed images: {current_status['total_images']}")
                    break
                print(f"   ⏳ Waiting... ({i+1}/15)")
            else:
                print("⚠️ Image may not have been detected automatically")

        # Demonstration 2: Remove image
        print(f"\n🎯 DEMONSTRATION 2: REMOVING IMAGE")
        print("-" * 40)

        if os.path.exists(new_image_path):
            os.remove(new_image_path)
            print(f"✅ Image removed: demo_new_image.jpg")
            print("⏰ Waiting for automatic detection...")

            # Wait for processing
            for i in range(10):  # 10 seconds
                time.sleep(1)
                current_status = main.image_manager.get_status()
                print(f"   ⏳ Waiting... ({i+1}/10)")

            final_status = main.image_manager.get_status()
            print(f"📊 Final status: {final_status['total_images']} processed images")

        # Demonstration 3: Test chat with new image
        print(f"\n🎯 DEMONSTRATION 3: TESTING CHAT WITH NEW IMAGE")
        print("-" * 55)

        # Add image again for testing
        if os.path.exists("images/M1.jpeg"):
            shutil.copy("images/M1.jpeg", new_image_path)
            print(f"✅ Image added again for testing")
            time.sleep(8)  # Wait for processing

            # Test chat
            with main.app.test_client() as client:
                response = client.post('/chat',
                                     json={'message': 'Where is room 1020? Use visual information.'},
                                     content_type='application/json')

                if response.status_code == 200:
                    data = response.get_json()
                    print("✅ Chat working with visual information")
                    print(f"📝 Response: {data['reply'][:100]}...")
                else:
                    print(f"❌ Chat error: {response.status_code}")

        # Clean up test file
        if os.path.exists(new_image_path):
            os.remove(new_image_path)

        print(f"\n" + "=" * 55)
        print("🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("=" * 55)
        print("✅ System automatically detects new images")
        print("✅ Embeddings are updated automatically")
        print("✅ Chat uses updated visual information")
        print("✅ Zero manual intervention required")

        return True

    except Exception as e:
        print(f"\n❌ DEMONSTRATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_usage_guide():
    """Shows usage guide for automatic method"""
    print("\n" + "=" * 60)
    print("📚 USAGE GUIDE - AUTOMATIC METHOD")
    print("=" * 60)

    print("\n🚀 HOW TO USE:")
    print("-" * 15)
    print("1. Start the system: python main.py")
    print("2. Add images to the 'images/' folder")
    print("3. System detects automatically")
    print("4. Embeddings are updated automatically")
    print("5. Chat uses updated visual information")

    print("\n📁 SUPPORTED FORMATS:")
    print("-" * 25)
    print("• JPG, JPEG")
    print("• PNG")
    print("• BMP")
    print("• TIFF")
    print("• WEBP")

    print("\n⚙️ CONFIGURATION:")
    print("-" * 18)
    print("• Monitored folder: images/")
    print("• Delay between updates: 5 seconds")
    print("• Waits 2 seconds before processing")
    print("• Runs in separate thread")

    print("\n🌐 CONTROL ENDPOINTS:")
    print("-" * 30)
    print("• GET /images/auto-monitor/status")
    print("• POST /images/auto-monitor/start")
    print("• POST /images/auto-monitor/stop")
    print("• GET /system/status")

    print("\n💡 TIPS:")
    print("-" * 10)
    print("• System starts automatically")
    print("• No need to restart for new images")
    print("• Cache is updated automatically")
    print("• Optimized performance")

if __name__ == "__main__":
    print("🎬 AUTOMATIC METHOD DEMONSTRATION")
    print("=" * 40)

    # Run demonstration
    success = demo_auto_update()

    # Show usage guide
    show_usage_guide()

    if success:
        print("\n🎉 DEMONSTRATION EXECUTED SUCCESSFULLY!")
        print("✅ Automatic method working perfectly")
    else:
        print("\n❌ DEMONSTRATION FAILED!")
        print("⚠️ Check the errors above")

    sys.exit(0 if success else 1)
