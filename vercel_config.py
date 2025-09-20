# Vercel-specific configuration
import os

# Check if we're running on Vercel
IS_VERCEL = os.getenv('VERCEL') == '1'

# OCR configuration for different environments
OCR_CONFIG = {
    'local': {
        'use_tesseract': True,
        'fallback_to_basic': False
    },
    'vercel': {
        'use_tesseract': False,
        'fallback_to_basic': True,
        'use_cloud_vision': False  # Could be enabled with Google Cloud Vision API
    }
}

def get_ocr_config():
    """Get OCR configuration based on environment"""
    return OCR_CONFIG['vercel'] if IS_VERCEL else OCR_CONFIG['local']
