import os
import json
import time
import re
import numpy as np
from PIL import Image
import torch
from ultralytics import YOLO
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer

# Configuration
DOWNLOAD_DIR = "pikwizard_images"
METADATA_FILE = os.path.join(DOWNLOAD_DIR, "metadata.json")

# Initialize models
device = "cuda" if torch.cuda.is_available() else "cpu"

# Image captioning model
caption_model = VisionEncoderDecoderModel.from_pretrained("nlpconnect/vit-gpt2-image-captioning").to(device)
caption_feature_extractor = ViTImageProcessor.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
caption_tokenizer = AutoTokenizer.from_pretrained("nlpconnect/vit-gpt2-image-captioning")

# Object detection model (fallback)
det_model = YOLO('yolov8n.pt')

def is_gibberish(text):
    """Check if generated caption is nonsensical"""
    text = text.lower()
    if len(text.split()) > 20:  # Too long
        return True
    if len(set(text.split())) < 3:  # Too repetitive
        return True
    if re.search(r'\b(\w+)\b.*\b\1\b.*\b\1\b', text):  # Repeated words
        return True
    return False

def generate_object_caption(detections):
    """Generate caption from detected objects"""
    if not detections:
        return "An image"
    
    objects = [d['class'] for d in detections if d['confidence'] > 0.3]
    if not objects:
        return "An image"
    
    objects = list(set(objects))  # Remove duplicates
    if len(objects) == 1:
        return f"An image of {objects[0]}"
    elif len(objects) == 2:
        return f"An image of {objects[0]} and {objects[1]}"
    else:
        return f"An image containing {', '.join(objects[:-1])}, and {objects[-1]}"

def generate_detection(pil_img):
    """Generate object detections with bounding boxes"""
    img = np.array(pil_img)
    results = det_model(img)
    detections = []
    for result in results:
        for box, conf, cls_id in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
            detections.append({
                'class': det_model.names[int(cls_id)],
                'confidence': float(conf),
                'bbox': [float(x) for x in box]
            })
    return detections

def generate_caption(pil_img):
    """Generate caption with fallback to object detection"""
    try:
        # First try neural caption
        pixel_values = caption_feature_extractor(
            images=pil_img, 
            return_tensors="pt"
        ).pixel_values.to(device)
        
        output_ids = caption_model.generate(
            pixel_values,
            max_length=40,
            num_beams=3,
            temperature=0.9,
            top_p=0.9,
            repetition_penalty=2.0,
            early_stopping=True
        )
        
        caption = caption_tokenizer.decode(output_ids[0], skip_special_tokens=True)
        caption = re.sub(r'[^a-zA-Z0-9,.!?\'" ]+', '', caption).capitalize()
        
        # If caption is generic or gibberish, use object detection
        if caption.lower() == "an image" or is_gibberish(caption):
            detections = generate_detection(pil_img)
            caption = generate_object_caption(detections)
            return caption, detections
        else:
            return caption, None
            
    except Exception as e:
        print(f"Caption generation error: {str(e)}")
        # Fallback to object detection
        detections = generate_detection(pil_img)
        caption = generate_object_caption(detections)
        return caption, detections

def analyze_image(image_path):
    """Generate natural language description with fallback to object detection"""
    try:
        pil_img = Image.open(image_path).convert("RGB")
        caption, detections = generate_caption(pil_img)
        
        return {
            'caption': caption,
            'detections': detections if detections else None,
            'model': 'vit-gpt2-image-captioning' if not detections else 'vit-gpt2-image-captioning with YOLO fallback'
        }
    except Exception as e:
        return {'error': str(e)}

def analyze_images():
    """Analyze all downloaded images"""
    if not os.path.exists(METADATA_FILE):
        print("Error: No metadata file found. Please run the crawler first.")
        return
    
    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)
    
    print(f"\n🔍 Analyzing {len(metadata)} images...")
    
    processed_count = 0
    start_time = time.time()
    
    for filename, data in metadata.items():
        if data.get('analyzed', False):
            continue
            
        image_path = os.path.join(DOWNLOAD_DIR, filename)
        if not os.path.exists(image_path):
            continue
        
        try:
            # Analyze the image
            analysis = analyze_image(image_path)
            
            if 'error' in analysis:
                print(f"⚠️ Failed to process {filename}: {analysis['error']}")
                continue
                
            data['analysis'] = analysis
            data['analyzed'] = True
            processed_count += 1
            
            print(f"✅ Processed {processed_count}: {analysis['caption']}")
            if analysis.get('detections'):
                print(f"   Detected objects: {', '.join(d['class'] for d in analysis['detections'])}")
            
            # Save progress periodically
            if processed_count % 10 == 0:
                with open(METADATA_FILE, 'w') as f:
                    json.dump(metadata, f, indent=2)
                    
        except Exception as e:
            print(f"⚠️ Unexpected error processing {filename}: {str(e)}")
            continue
    
    # Final save
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    total_time = (time.time() - start_time) / 60
    print(f"\n🎉 Successfully analyzed {processed_count} images")
    print(f"⏱️ Analysis time: {total_time:.2f} minutes")
    print(f"💾 Updated metadata saved to {METADATA_FILE}")

if __name__ == "__main__":
    print("🚀 Starting Image Analyzer")
    print("Features:")
    print("- Uses vit-gpt2-image-captioning for primary caption generation")
    print("- Falls back to YOLO object detection when needed")
    print("- Updates metadata with analysis results")
    
    analyze_images()
    print("✅ Analysis completed successfully!")