"""
Photo Compression Algorithms for WhatsApp Status
=================================================
Three intelligent algorithms optimized for WhatsApp's image processing.
Ensures photos remain crisp and clear after WhatsApp re-compression.

WhatsApp Status Image Behavior:
- Compresses images to ~1280px on longest side
- Uses aggressive JPEG compression (~70-80% quality)
- Strips EXIF metadata
- May apply sharpening artifacts

Our Strategy:
- Pre-compress to WhatsApp's target specs
- Use optimal quality that won't be degraded further
- Apply subtle sharpening to counteract WhatsApp's compression
- Optimize colors and contrast
"""

import os
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import io

# Try to import advanced features
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class PhotoAlgorithm(Enum):
    """Available photo compression algorithms"""
    CLARITY_MAX = "clarity_max"       # Maximum quality preservation
    BALANCED_PRO = "balanced_pro"     # Balanced size/quality
    QUICK_SHARE = "quick_share"       # Fast, small files


@dataclass
class PhotoCompressionResult:
    """Result of photo compression"""
    success: bool
    output_path: str
    original_size: int
    compressed_size: int
    compression_ratio: float
    algorithm_used: str
    output_format: str
    new_dimensions: Tuple[int, int]
    message: str


@dataclass
class PhotoInfo:
    """Information about a photo"""
    width: int
    height: int
    format: str
    mode: str
    file_size: int
    has_transparency: bool
    is_animated: bool


def analyze_photo(file_path: str) -> Optional[PhotoInfo]:
    """Analyze photo and return its properties"""
    try:
        file_size = os.path.getsize(file_path)
        
        with Image.open(file_path) as img:
            is_animated = getattr(img, 'n_frames', 1) > 1
            has_transparency = img.mode in ('RGBA', 'LA', 'P') and 'transparency' in img.info
            
            return PhotoInfo(
                width=img.width,
                height=img.height,
                format=img.format or 'UNKNOWN',
                mode=img.mode,
                file_size=file_size,
                has_transparency=has_transparency,
                is_animated=is_animated
            )
    except Exception as e:
        print(f"Error analyzing photo: {e}")
        return None


def get_optimal_dimensions(
    width: int, 
    height: int, 
    max_dimension: int = 1280
) -> Tuple[int, int]:
    """Calculate optimal dimensions while maintaining aspect ratio"""
    if width <= max_dimension and height <= max_dimension:
        return width, height
    
    if width > height:
        new_width = max_dimension
        new_height = int(height * (max_dimension / width))
    else:
        new_height = max_dimension
        new_width = int(width * (max_dimension / height))
    
    # Ensure dimensions are even (better for some encoders)
    new_width = new_width if new_width % 2 == 0 else new_width + 1
    new_height = new_height if new_height % 2 == 0 else new_height + 1
    
    return new_width, new_height


def apply_smart_sharpen(img: Image.Image, strength: float = 0.3) -> Image.Image:
    """Apply intelligent sharpening that counteracts WhatsApp compression"""
    # Use unsharp mask for natural sharpening
    # This helps preserve detail after WhatsApp re-compresses
    return img.filter(ImageFilter.UnsharpMask(
        radius=1.0,
        percent=int(50 + strength * 100),  # 50-150%
        threshold=2
    ))


def enhance_for_whatsapp(img: Image.Image, level: str = 'balanced') -> Image.Image:
    """
    Apply enhancements optimized for WhatsApp viewing.
    WhatsApp tends to slightly desaturate and reduce contrast.
    """
    if level == 'none':
        return img
    
    # Subtle contrast boost (WhatsApp flattens contrast slightly)
    contrast_factor = {'light': 1.02, 'balanced': 1.05, 'strong': 1.08}.get(level, 1.05)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(contrast_factor)
    
    # Subtle saturation boost (counteract WhatsApp desaturation)
    saturation_factor = {'light': 1.02, 'balanced': 1.05, 'strong': 1.10}.get(level, 1.05)
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(saturation_factor)
    
    return img


def detect_image_type(img: Image.Image) -> str:
    """
    Detect the type of image content for optimal processing.
    Returns: 'photo', 'graphic', 'text', 'screenshot'
    """
    if not NUMPY_AVAILABLE:
        return 'photo'  # Default to photo processing
    
    try:
        # Convert to numpy for analysis
        if img.mode != 'RGB':
            img_rgb = img.convert('RGB')
        else:
            img_rgb = img
        
        arr = np.array(img_rgb)
        
        # Calculate color statistics
        unique_colors = len(np.unique(arr.reshape(-1, 3), axis=0))
        total_pixels = arr.shape[0] * arr.shape[1]
        color_ratio = unique_colors / total_pixels
        
        # Calculate edge density (indicates text/graphics)
        gray = np.mean(arr, axis=2)
        edges = np.abs(np.diff(gray, axis=0)).mean() + np.abs(np.diff(gray, axis=1)).mean()
        
        # Classify based on characteristics
        if color_ratio < 0.01 and edges > 20:
            return 'screenshot'  # Few colors, sharp edges
        elif color_ratio < 0.05:
            return 'graphic'     # Limited color palette
        elif edges > 30:
            return 'text'        # High edge density
        else:
            return 'photo'       # Natural photograph
    except:
        return 'photo'


# =============================================================================
# ALGORITHM 1: CLARITY MAX
# =============================================================================
# Strategy: Maximum quality preservation with intelligent enhancement.
# Uses high quality JPEG with subtle sharpening to counteract WhatsApp.
# Best for: Important photos, portraits, detailed images
# =============================================================================

def compress_clarity_max(
    input_path: str,
    output_path: str,
    target_format: str = 'jpg'
) -> PhotoCompressionResult:
    """
    Algorithm 1: Clarity Max - Maximum Quality Preservation
    
    Features:
    - High quality output (92% JPEG quality)
    - Smart sharpening to counteract WhatsApp compression
    - Color/contrast enhancement for WhatsApp viewing
    - Optimal dimensions (1280px max)
    - Progressive JPEG for better perceived loading
    - Chroma subsampling 4:4:4 for best color
    """
    photo_info = analyze_photo(input_path)
    if not photo_info:
        return PhotoCompressionResult(
            success=False, output_path="", original_size=0,
            compressed_size=0, compression_ratio=0,
            algorithm_used="Clarity Max", output_format="",
            new_dimensions=(0, 0), message="Could not analyze photo"
        )
    
    try:
        with Image.open(input_path) as img:
            # Handle animated images
            if photo_info.is_animated:
                return _process_animated_gif(input_path, output_path, 'clarity_max')
            
            # Convert to RGB if needed (for JPEG output)
            if img.mode in ('RGBA', 'P'):
                # Preserve transparency info for later
                has_alpha = img.mode == 'RGBA' or 'transparency' in img.info
                if has_alpha and target_format.lower() in ('png', 'webp'):
                    pass  # Keep alpha
                else:
                    # Create white background for JPEG
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Detect image type for optimized processing
            img_type = detect_image_type(img)
            
            # Calculate optimal dimensions
            new_width, new_height = get_optimal_dimensions(
                img.width, img.height, 
                max_dimension=1280
            )
            
            # High-quality resize using Lanczos
            if (new_width, new_height) != (img.width, img.height):
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Apply smart sharpening (stronger for photos, lighter for graphics)
            sharpen_strength = 0.4 if img_type == 'photo' else 0.2
            img = apply_smart_sharpen(img, sharpen_strength)
            
            # Apply WhatsApp-optimized enhancements
            if img_type in ('photo', 'graphic'):
                img = enhance_for_whatsapp(img, 'balanced')
            
            # Determine output format
            if target_format.lower() in ('jpg', 'jpeg'):
                output_path = output_path.rsplit('.', 1)[0] + '.jpg'
                img.save(
                    output_path,
                    'JPEG',
                    quality=92,
                    optimize=True,
                    progressive=True,
                    subsampling=0  # 4:4:4 - best color quality
                )
            elif target_format.lower() == 'png':
                output_path = output_path.rsplit('.', 1)[0] + '.png'
                img.save(output_path, 'PNG', optimize=True)
            else:  # WebP
                output_path = output_path.rsplit('.', 1)[0] + '.webp'
                img.save(output_path, 'WEBP', quality=92, method=6)
            
            compressed_size = os.path.getsize(output_path)
            compression_ratio = (1 - compressed_size / photo_info.file_size) * 100
            
            return PhotoCompressionResult(
                success=True,
                output_path=output_path,
                original_size=photo_info.file_size,
                compressed_size=compressed_size,
                compression_ratio=compression_ratio,
                algorithm_used="Clarity Max",
                output_format=target_format.upper(),
                new_dimensions=(new_width, new_height),
                message=f"Premium quality compression. Detected: {img_type}"
            )
            
    except Exception as e:
        return PhotoCompressionResult(
            success=False, output_path="", original_size=photo_info.file_size,
            compressed_size=0, compression_ratio=0,
            algorithm_used="Clarity Max", output_format="",
            new_dimensions=(0, 0), message=f"Compression failed: {str(e)}"
        )


# =============================================================================
# ALGORITHM 2: BALANCED PRO
# =============================================================================
# Strategy: Optimal balance between quality and file size.
# Smart compression that adapts to image content.
# Best for: General use, sharing multiple photos
# =============================================================================

def compress_balanced_pro(
    input_path: str,
    output_path: str,
    target_format: str = 'jpg'
) -> PhotoCompressionResult:
    """
    Algorithm 2: Balanced Pro - Smart Quality/Size Balance
    
    Features:
    - Adaptive quality based on image content
    - 1080px max dimension for smaller files
    - Moderate sharpening
    - Chroma subsampling 4:2:2 for balance
    - Content-aware enhancement
    """
    photo_info = analyze_photo(input_path)
    if not photo_info:
        return PhotoCompressionResult(
            success=False, output_path="", original_size=0,
            compressed_size=0, compression_ratio=0,
            algorithm_used="Balanced Pro", output_format="",
            new_dimensions=(0, 0), message="Could not analyze photo"
        )
    
    try:
        with Image.open(input_path) as img:
            # Handle animated images
            if photo_info.is_animated:
                return _process_animated_gif(input_path, output_path, 'balanced_pro')
            
            # Convert to RGB
            if img.mode in ('RGBA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Detect image type
            img_type = detect_image_type(img)
            
            # Calculate optimal dimensions (smaller for balanced)
            new_width, new_height = get_optimal_dimensions(
                img.width, img.height,
                max_dimension=1080
            )
            
            # Resize
            if (new_width, new_height) != (img.width, img.height):
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Moderate sharpening
            img = apply_smart_sharpen(img, 0.25)
            
            # Light enhancement
            img = enhance_for_whatsapp(img, 'light')
            
            # Adaptive quality based on content
            if img_type == 'screenshot':
                quality = 88  # Screenshots need higher quality for text
            elif img_type == 'graphic':
                quality = 85
            else:
                quality = 82  # Photos can handle more compression
            
            # Save
            if target_format.lower() in ('jpg', 'jpeg'):
                output_path = output_path.rsplit('.', 1)[0] + '.jpg'
                img.save(
                    output_path,
                    'JPEG',
                    quality=quality,
                    optimize=True,
                    progressive=True,
                    subsampling=1  # 4:2:2
                )
            else:
                output_path = output_path.rsplit('.', 1)[0] + '.webp'
                img.save(output_path, 'WEBP', quality=quality, method=4)
            
            compressed_size = os.path.getsize(output_path)
            compression_ratio = (1 - compressed_size / photo_info.file_size) * 100
            
            return PhotoCompressionResult(
                success=True,
                output_path=output_path,
                original_size=photo_info.file_size,
                compressed_size=compressed_size,
                compression_ratio=compression_ratio,
                algorithm_used="Balanced Pro",
                output_format=target_format.upper(),
                new_dimensions=(new_width, new_height),
                message=f"Balanced compression. Quality: {quality}%, Type: {img_type}"
            )
            
    except Exception as e:
        return PhotoCompressionResult(
            success=False, output_path="", original_size=photo_info.file_size,
            compressed_size=0, compression_ratio=0,
            algorithm_used="Balanced Pro", output_format="",
            new_dimensions=(0, 0), message=f"Compression failed: {str(e)}"
        )


# =============================================================================
# ALGORITHM 3: QUICK SHARE
# =============================================================================
# Strategy: Maximum compression for fast sharing.
# Smallest file sizes while maintaining acceptable quality.
# Best for: Bulk sharing, low bandwidth, quick uploads
# =============================================================================

def compress_quick_share(
    input_path: str,
    output_path: str,
    target_format: str = 'jpg'
) -> PhotoCompressionResult:
    """
    Algorithm 3: Quick Share - Maximum Compression
    
    Features:
    - Aggressive compression (70% quality)
    - 720px max dimension
    - 4:2:0 chroma subsampling
    - Fast processing
    - Smallest file sizes
    """
    photo_info = analyze_photo(input_path)
    if not photo_info:
        return PhotoCompressionResult(
            success=False, output_path="", original_size=0,
            compressed_size=0, compression_ratio=0,
            algorithm_used="Quick Share", output_format="",
            new_dimensions=(0, 0), message="Could not analyze photo"
        )
    
    try:
        with Image.open(input_path) as img:
            # Handle animated images
            if photo_info.is_animated:
                return _process_animated_gif(input_path, output_path, 'quick_share')
            
            # Convert to RGB
            if img.mode != 'RGB':
                if img.mode in ('RGBA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                else:
                    img = img.convert('RGB')
            
            # Smaller dimensions for quick share
            new_width, new_height = get_optimal_dimensions(
                img.width, img.height,
                max_dimension=720
            )
            
            # Fast resize
            if (new_width, new_height) != (img.width, img.height):
                img = img.resize((new_width, new_height), Image.Resampling.BILINEAR)
            
            # Minimal sharpening
            img = apply_smart_sharpen(img, 0.15)
            
            # Save with aggressive compression
            output_path = output_path.rsplit('.', 1)[0] + '.jpg'
            img.save(
                output_path,
                'JPEG',
                quality=70,
                optimize=True,
                progressive=True,
                subsampling=2  # 4:2:0 - maximum compression
            )
            
            compressed_size = os.path.getsize(output_path)
            compression_ratio = (1 - compressed_size / photo_info.file_size) * 100
            
            return PhotoCompressionResult(
                success=True,
                output_path=output_path,
                original_size=photo_info.file_size,
                compressed_size=compressed_size,
                compression_ratio=compression_ratio,
                algorithm_used="Quick Share",
                output_format="JPG",
                new_dimensions=(new_width, new_height),
                message=f"Fast compression complete. Reduced by {compression_ratio:.1f}%"
            )
            
    except Exception as e:
        return PhotoCompressionResult(
            success=False, output_path="", original_size=photo_info.file_size,
            compressed_size=0, compression_ratio=0,
            algorithm_used="Quick Share", output_format="",
            new_dimensions=(0, 0), message=f"Compression failed: {str(e)}"
        )


# =============================================================================
# GIF PROCESSING
# =============================================================================

def _process_animated_gif(
    input_path: str,
    output_path: str,
    algorithm: str
) -> PhotoCompressionResult:
    """
    Process animated GIFs with optimization.
    Reduces colors, optimizes frames, and resizes.
    """
    photo_info = analyze_photo(input_path)
    
    try:
        with Image.open(input_path) as img:
            frames = []
            durations = []
            
            # Settings based on algorithm
            if algorithm == 'clarity_max':
                max_dim = 480
                colors = 256
            elif algorithm == 'balanced_pro':
                max_dim = 360
                colors = 192
            else:  # quick_share
                max_dim = 280
                colors = 128
            
            # Calculate new dimensions
            new_width, new_height = get_optimal_dimensions(
                img.width, img.height,
                max_dimension=max_dim
            )
            
            # Process each frame
            try:
                while True:
                    frame = img.copy()
                    
                    # Resize frame
                    frame = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Reduce colors
                    frame = frame.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
                    
                    frames.append(frame)
                    durations.append(img.info.get('duration', 100))
                    
                    img.seek(img.tell() + 1)
            except EOFError:
                pass
            
            # Save optimized GIF
            output_path = output_path.rsplit('.', 1)[0] + '.gif'
            
            if frames:
                frames[0].save(
                    output_path,
                    save_all=True,
                    append_images=frames[1:] if len(frames) > 1 else [],
                    duration=durations,
                    loop=0,
                    optimize=True
                )
            
            compressed_size = os.path.getsize(output_path)
            compression_ratio = (1 - compressed_size / photo_info.file_size) * 100
            
            algo_name = {
                'clarity_max': 'Clarity Max',
                'balanced_pro': 'Balanced Pro',
                'quick_share': 'Quick Share'
            }.get(algorithm, 'Unknown')
            
            return PhotoCompressionResult(
                success=True,
                output_path=output_path,
                original_size=photo_info.file_size,
                compressed_size=compressed_size,
                compression_ratio=compression_ratio,
                algorithm_used=algo_name,
                output_format="GIF",
                new_dimensions=(new_width, new_height),
                message=f"Animated GIF optimized. {len(frames)} frames, {colors} colors"
            )
            
    except Exception as e:
        return PhotoCompressionResult(
            success=False, output_path="", original_size=photo_info.file_size or 0,
            compressed_size=0, compression_ratio=0,
            algorithm_used="GIF Optimizer", output_format="",
            new_dimensions=(0, 0), message=f"GIF processing failed: {str(e)}"
        )


# =============================================================================
# MAIN COMPRESSION FUNCTION
# =============================================================================

def compress_photo(
    input_path: str,
    output_path: str,
    algorithm: PhotoAlgorithm = PhotoAlgorithm.BALANCED_PRO,
    target_format: str = 'jpg'
) -> PhotoCompressionResult:
    """
    Main photo compression function.
    
    Args:
        input_path: Path to source image
        output_path: Path for compressed output
        algorithm: Compression algorithm to use
        target_format: Output format (jpg, png, webp, gif)
    
    Returns:
        PhotoCompressionResult with compression details
    """
    if algorithm == PhotoAlgorithm.CLARITY_MAX:
        return compress_clarity_max(input_path, output_path, target_format)
    elif algorithm == PhotoAlgorithm.BALANCED_PRO:
        return compress_balanced_pro(input_path, output_path, target_format)
    elif algorithm == PhotoAlgorithm.QUICK_SHARE:
        return compress_quick_share(input_path, output_path, target_format)
    else:
        return compress_balanced_pro(input_path, output_path, target_format)


# =============================================================================
# VIDEO TO GIF CONVERSION
# =============================================================================

def video_to_gif(
    input_path: str,
    output_path: str,
    max_duration: float = 6.0,
    fps: int = 12,
    max_width: int = 360
) -> PhotoCompressionResult:
    """
    Convert a video clip to an optimized GIF.
    
    WhatsApp supports GIFs up to 6 seconds.
    """
    try:
        import subprocess
        
        # Get video info
        probe_cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', input_path
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception("Could not probe video")
        
        import json
        info = json.loads(result.stdout)
        
        original_size = int(info['format'].get('size', 0))
        duration = float(info['format'].get('duration', 0))
        
        # Limit duration
        use_duration = min(duration, max_duration)
        
        output_path = output_path.rsplit('.', 1)[0] + '.gif'
        
        # Two-pass GIF creation for better quality
        palette_path = output_path + '_palette.png'
        
        # Generate palette
        palette_cmd = [
            'ffmpeg', '-y', '-t', str(use_duration), '-i', input_path,
            '-vf', f'fps={fps},scale={max_width}:-1:flags=lanczos,palettegen=stats_mode=diff',
            palette_path
        ]
        subprocess.run(palette_cmd, capture_output=True)
        
        # Generate GIF using palette
        gif_cmd = [
            'ffmpeg', '-y', '-t', str(use_duration), '-i', input_path,
            '-i', palette_path,
            '-lavfi', f'fps={fps},scale={max_width}:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5',
            output_path
        ]
        subprocess.run(gif_cmd, capture_output=True)
        
        # Cleanup palette
        if os.path.exists(palette_path):
            os.remove(palette_path)
        
        if not os.path.exists(output_path):
            raise Exception("GIF creation failed")
        
        compressed_size = os.path.getsize(output_path)
        
        return PhotoCompressionResult(
            success=True,
            output_path=output_path,
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=(1 - compressed_size / original_size) * 100 if original_size > 0 else 0,
            algorithm_used="Video to GIF",
            output_format="GIF",
            new_dimensions=(max_width, 0),
            message=f"Converted {use_duration:.1f}s video to GIF at {fps}fps"
        )
        
    except Exception as e:
        return PhotoCompressionResult(
            success=False, output_path="", original_size=0,
            compressed_size=0, compression_ratio=0,
            algorithm_used="Video to GIF", output_format="",
            new_dimensions=(0, 0), message=f"Conversion failed: {str(e)}"
        )
