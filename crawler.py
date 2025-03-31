import os
import time
import json
from urllib.parse import urlparse, unquote
from playwright.sync_api import sync_playwright
import requests

# Configuration
BASE_URL = "https://pikwizard.com/s/photo/pictures/"
DOWNLOAD_DIR = "pikwizard_images"
METADATA_FILE = os.path.join(DOWNLOAD_DIR, "metadata.json")
MAX_IMAGES = 1000
SCROLL_DELAY = 2
HEADLESS = False
REQUEST_TIMEOUT = 30

def clean_filename(url):
    """Create a safe filename from URL"""
    parsed = urlparse(url)
    filename = unquote(os.path.basename(parsed.path))
    filename = filename.split('?')[0]
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    if '.' not in filename[-6:]:
        filename += '.jpg'
    return filename

def download_image(img_url, referer, download_dir):
    """Download image with retry logic"""
    filename = clean_filename(img_url)
    save_path = os.path.join(download_dir, filename)
    
    if os.path.exists(save_path):
        return None
    
    for attempt in range(3):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': referer
            }
            
            response = requests.get(img_url, headers=headers, stream=True, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return save_path
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {img_url}: {e}")
            time.sleep((attempt + 1) * 2)
    
    print(f"Failed to download after 3 attempts: {img_url}")
    return None

def crawl_images():
    """Main function to crawl and download images"""
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
    
    metadata = {}
    alt_texts = set()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        try:
            print(f"🌍 Navigating to {BASE_URL}...")
            page.goto(BASE_URL, timeout=60000)
            time.sleep(3)
            
            print(f"🔍 Scrolling to collect {MAX_IMAGES} images...")
            collected_urls = set()
            scroll_attempts = 0
            last_height = page.evaluate("document.body.scrollHeight")
            
            while len(collected_urls) < MAX_IMAGES and scroll_attempts < 20:
                page.evaluate("window.scrollBy(0, window.innerHeight * 0.8)")
                time.sleep(SCROLL_DELAY)
                
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    scroll_attempts += 1
                    print(f"⏳ No new content (attempt {scroll_attempts}/20)")
                    time.sleep(SCROLL_DELAY * 2)
                else:
                    scroll_attempts = 0
                    last_height = new_height
                
                img_elements = page.query_selector_all('img[src*="ftcdn.net"]')
                for img in img_elements:
                    img_url = img.get_attribute('src')
                    if img_url and img_url not in collected_urls:
                        collected_urls.add(img_url)
                        alt_text = img.get_attribute('alt') or ''
                        alt_texts.add(alt_text)
                        if len(collected_urls) >= MAX_IMAGES:
                            break
                
                print(f"📸 Total images found: {len(collected_urls)}")
            
            print(f"\n⬇️ Downloading {len(collected_urls)} images...")
            for idx, img_url in enumerate(collected_urls, 1):
                local_path = download_image(img_url, BASE_URL, DOWNLOAD_DIR)
                if not local_path:
                    continue
                
                alt_text = next((img.get_attribute('alt') for img in img_elements 
                               if img.get_attribute('src') == img_url), '')
                
                metadata[os.path.basename(local_path)] = {
                    'source_url': img_url,
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'alt_text': alt_text,
                    'analyzed': False  # Flag to indicate if analysis has been done
                }
                
                print(f"✅ Downloaded {idx}/{len(collected_urls)}: {os.path.basename(local_path)}")
                time.sleep(0.5)
            
            # Save metadata
            with open(METADATA_FILE, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"\n🎉 Successfully downloaded {len(metadata)} images")
            print(f"💾 Metadata saved to {METADATA_FILE}")
            
        except Exception as e:
            print(f"🔥 Error: {e}")
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    print("🚀 Starting PikWizard Image Crawler")
    print("Features:")
    print("- Scrapes images from PikWizard")
    print("- Saves images to local directory")
    print("- Stores metadata including alt texts")
    
    start_time = time.time()
    crawl_images()
    
    total_time = (time.time() - start_time) / 60
    print(f"\n⏱️ Total execution time: {total_time:.2f} minutes")
    print("✅ Crawling completed successfully!")