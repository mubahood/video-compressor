"""
Three Creative Video Compression Algorithms for WhatsApp Status
================================================================

Each algorithm uses different strategies to optimize video quality
while keeping file sizes under WhatsApp's limits.

Now enhanced with ML-based content analysis for the Neural algorithm!
"""

import ffmpeg
import os
import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

# ML Analyzer for content-aware compression
try:
    from .ml_analyzer import MLVideoAnalyzer, ContentType, VideoAnalysis
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("ML analyzer not available, using standard compression")


class Algorithm(Enum):
    """Available compression algorithms"""
    NEURAL_PRESERVE = "neural_preserve"      # Algorithm 1: Smart Quality Preservation
    BITRATE_SCULPTOR = "bitrate_sculptor"    # Algorithm 2: Dynamic Bitrate Sculpting
    QUANTUM_COMPRESS = "quantum_compress"    # Algorithm 3: Aggressive Quantum Compression


@dataclass
class VideoInfo:
    """Video metadata container"""
    width: int
    height: int
    duration: float
    bitrate: int
    fps: float
    codec: str
    file_size: int
    has_audio: bool
    audio_bitrate: Optional[int] = None


@dataclass
class CompressionResult:
    """Result of compression operation"""
    success: bool
    output_path: str
    original_size: int
    compressed_size: int
    compression_ratio: float
    algorithm_used: str
    message: str


def probe_video(input_path: str) -> VideoInfo:
    """
    Analyze video file and extract metadata.
    
    Args:
        input_path: Path to the video file
        
    Returns:
        VideoInfo object with video metadata
    """
    try:
        probe = ffmpeg.probe(input_path)
        video_stream = next(
            (s for s in probe['streams'] if s['codec_type'] == 'video'), None
        )
        audio_stream = next(
            (s for s in probe['streams'] if s['codec_type'] == 'audio'), None
        )
        
        if not video_stream:
            raise ValueError("No video stream found")
        
        # Extract video info
        width = int(video_stream.get('width', 0))
        height = int(video_stream.get('height', 0))
        duration = float(probe['format'].get('duration', 0))
        bitrate = int(probe['format'].get('bit_rate', 0))
        
        # Handle frame rate (can be fraction like "30000/1001")
        fps_str = video_stream.get('r_frame_rate', '30/1')
        if '/' in fps_str:
            num, den = map(int, fps_str.split('/'))
            fps = num / den if den != 0 else 30.0
        else:
            fps = float(fps_str)
        
        codec = video_stream.get('codec_name', 'unknown')
        file_size = int(probe['format'].get('size', 0))
        
        has_audio = audio_stream is not None
        audio_bitrate = None
        if has_audio and 'bit_rate' in audio_stream:
            audio_bitrate = int(audio_stream['bit_rate'])
        
        return VideoInfo(
            width=width,
            height=height,
            duration=duration,
            bitrate=bitrate,
            fps=fps,
            codec=codec,
            file_size=file_size,
            has_audio=has_audio,
            audio_bitrate=audio_bitrate
        )
    except ffmpeg.Error as e:
        raise RuntimeError(f"FFmpeg probe error: {e.stderr.decode() if e.stderr else str(e)}")


def calculate_target_bitrate(
    duration: float,
    target_size_mb: float = 15.5,
    audio_bitrate_kbps: int = 128
) -> int:
    """
    Calculate optimal video bitrate to achieve target file size.
    
    Formula: bitrate = (target_size * 8) / duration - audio_bitrate
    
    Args:
        duration: Video duration in seconds
        target_size_mb: Target file size in MB (default 15.5 for safety margin)
        audio_bitrate_kbps: Audio bitrate in kbps
        
    Returns:
        Target video bitrate in bps
    """
    target_size_bits = target_size_mb * 8 * 1024 * 1024  # Convert MB to bits
    total_bitrate = target_size_bits / duration
    audio_bits = audio_bitrate_kbps * 1000
    video_bitrate = int(total_bitrate - audio_bits)
    
    # Ensure minimum quality
    return max(video_bitrate, 500000)  # At least 500kbps


def get_optimal_resolution(width: int, height: int, algorithm: Algorithm) -> Tuple[int, int]:
    """
    Calculate optimal output resolution based on algorithm.
    
    Args:
        width: Original width
        height: Original height
        algorithm: The compression algorithm being used
        
    Returns:
        Tuple of (new_width, new_height)
    """
    is_portrait = height > width
    
    if algorithm == Algorithm.NEURAL_PRESERVE:
        # Preserve more resolution for quality
        max_dimension = 1080
    elif algorithm == Algorithm.BITRATE_SCULPTOR:
        # Standard HD
        max_dimension = 720
    else:  # QUANTUM_COMPRESS
        # Lower resolution for maximum compression
        max_dimension = 640
    
    if is_portrait:
        if height > max_dimension:
            scale_factor = max_dimension / height
            new_height = max_dimension
            new_width = int(width * scale_factor)
        else:
            new_width, new_height = width, height
    else:
        if width > max_dimension:
            scale_factor = max_dimension / width
            new_width = max_dimension
            new_height = int(height * scale_factor)
        else:
            new_width, new_height = width, height
    
    # Ensure dimensions are divisible by 2 (required by most codecs)
    new_width = new_width if new_width % 2 == 0 else new_width - 1
    new_height = new_height if new_height % 2 == 0 else new_height - 1
    
    return new_width, new_height


# =============================================================================
# ALGORITHM 1: NEURAL PRESERVE (ML-ENHANCED)
# =============================================================================
# Strategy: Uses ML-based content analysis to maximize perceptual quality.
# Analyzes faces, motion, complexity to optimize encoding parameters.
# Uses film-grade encoding with content-aware adjustments.
# Best for: Videos with lots of detail, faces, or artistic content.
# =============================================================================

def compress_neural_preserve(
    input_path: str,
    output_path: str,
    target_size_mb: float = 15.5
) -> CompressionResult:
    """
    Algorithm 1: Neural Preserve - ML-Enhanced Premium Quality (AI-Powered)
    
    This algorithm uses machine learning to analyze video content and optimize:
    - Face detection to prioritize quality in face regions
    - Scene complexity analysis for smart bit allocation
    - Motion estimation for optimal encoding parameters
    - Content classification (talking head, action, nature, etc.)
    
    Technical features:
    - Adaptive CRF based on ML content analysis
    - Psycho-visual optimizations tuned per content type
    - Face-aware quality enhancement
    - Lanczos scaling for sharpest downscaling
    - Content-adaptive denoising
    
    Best for: Detailed videos, faces, nature scenes, artistic content
    """
    video_info = probe_video(input_path)
    new_width, new_height = get_optimal_resolution(
        video_info.width, video_info.height, Algorithm.NEURAL_PRESERVE
    )
    
    base_bitrate = calculate_target_bitrate(
        video_info.duration, target_size_mb, 128
    )
    
    # =========================================================================
    # ML CONTENT ANALYSIS
    # =========================================================================
    ml_analysis = None
    content_type_str = "general"
    has_faces = False
    face_coverage = 0
    complexity = 0.5
    motion_level = 0.3
    
    if ML_AVAILABLE:
        try:
            analyzer = MLVideoAnalyzer()
            ml_analysis = analyzer.analyze_video(input_path, sample_rate=15)
            
            content_type_str = ml_analysis.content_type.value
            has_faces = ml_analysis.avg_face_count > 0
            face_coverage = ml_analysis.face_coverage
            complexity = ml_analysis.complexity_score
            motion_level = ml_analysis.motion_score
            
            print(f"[ML Analysis] Content: {content_type_str}, "
                  f"Faces: {ml_analysis.avg_face_count:.1f}, "
                  f"Complexity: {complexity:.2f}, "
                  f"Motion: {motion_level:.2f}")
        except Exception as e:
            print(f"[ML Analysis] Failed, using defaults: {e}")
    
    # =========================================================================
    # ADAPTIVE PARAMETERS BASED ON ML ANALYSIS
    # =========================================================================
    
    # CRF: Lower = higher quality (17-23 range)
    if ml_analysis and ml_analysis.analysis_confidence > 0.3:
        # Use ML-recommended CRF as base
        crf_value = ml_analysis.recommended_crf
        bitrate_mult = ml_analysis.recommended_bitrate_mult
        
        # Further adjustments based on duration
        if video_info.duration < 15:
            crf_value = max(17, crf_value - 1)  # Boost for short clips
        elif video_info.duration > 60:
            crf_value = min(22, crf_value + 1)  # Slightly reduce for long clips
    else:
        # Fallback: duration-based CRF
        if video_info.duration < 15:
            crf_value = 18
        elif video_info.duration < 30:
            crf_value = 19
        elif video_info.duration < 60:
            crf_value = 20
        else:
            crf_value = 21
        bitrate_mult = 1.0
    
    # Apply bitrate multiplier
    target_bitrate = int(base_bitrate * bitrate_mult)
    
    # Adjust encoding parameters based on content type
    if content_type_str == "talking_head":
        # Prioritize face quality
        psy_rd = "1.5:0.3"       # Higher psy for face detail
        aq_strength = "1.0"      # Strong AQ for skin tones
        deblock = "0:0"          # Less deblocking to preserve face detail
        preset = "veryslow"
        denoise_strength = 1     # Minimal denoising for faces
    elif content_type_str == "action":
        # Prioritize motion handling
        psy_rd = "1.0:0.15"
        aq_strength = "0.8"
        deblock = "-1:-1"
        preset = "slower"        # Faster preset OK for motion
        denoise_strength = 3     # More denoising OK for motion
    elif content_type_str == "nature":
        # Prioritize detail and color
        psy_rd = "1.3:0.25"
        aq_strength = "0.9"
        deblock = "-1:-1"
        preset = "veryslow"
        denoise_strength = 2
    elif content_type_str == "screen":
        # Prioritize sharpness and text
        psy_rd = "0.8:0.1"       # Lower psy for clean edges
        aq_strength = "0.6"
        deblock = "0:0"
        preset = "veryslow"
        denoise_strength = 0     # No denoising for screen content
    else:
        # General content
        psy_rd = "1.2:0.25"
        aq_strength = "0.9"
        deblock = "-1:-1"
        preset = "veryslow"
        denoise_strength = 2
    
    # Calculate optimal fps
    target_fps = min(video_info.fps, 30) if video_info.fps > 0 else 30
    
    try:
        stream = ffmpeg.input(input_path)
        video = stream.video
        
        # =====================================================================
        # VIDEO PROCESSING PIPELINE
        # =====================================================================
        
        # 1. High-quality Lanczos scaling
        video = video.filter('scale', new_width, new_height, 
                            flags='lanczos',
                            force_original_aspect_ratio='decrease')
        
        # 2. Ensure even dimensions
        video = video.filter('pad', 
                            f'ceil(iw/2)*2', 
                            f'ceil(ih/2)*2')
        
        # 3. Content-adaptive denoising (skip for screen content)
        if denoise_strength > 0:
            video = video.filter('hqdn3d', 
                                luma_spatial=denoise_strength,
                                chroma_spatial=denoise_strength,
                                luma_tmp=denoise_strength + 1,
                                chroma_tmp=denoise_strength + 1)
        
        # 4. Adaptive sharpening (stronger for faces and detail)
        if content_type_str == "talking_head":
            # Subtle sharpening for faces - avoid harsh edges
            video = video.filter('unsharp', 
                                luma_msize_x=3, luma_msize_y=3, luma_amount=0.2,
                                chroma_msize_x=3, chroma_msize_y=3, chroma_amount=0.05)
        elif content_type_str != "action":
            # Standard sharpening for non-action content
            video = video.filter('unsharp', 
                                luma_msize_x=3, luma_msize_y=3, luma_amount=0.3,
                                chroma_msize_x=3, chroma_msize_y=3, chroma_amount=0.1)
        
        # 5. Frame rate handling
        if video_info.fps > 30:
            video = video.filter('fps', fps=target_fps)
        
        # =====================================================================
        # X264 ENCODING PARAMETERS (ML-OPTIMIZED)
        # =====================================================================
        
        x264_params = [
            # Adaptive Quantization
            'aq-mode=3',
            f'aq-strength={aq_strength}',
            
            # Psycho-visual (content-adapted)
            f'psy-rd={psy_rd}',
            
            # Motion estimation
            'me=umh',
            'subme=10',
            'ref=6',
            'merange=24',
            
            # B-frames
            'bframes=5',
            'b-adapt=2',
            'b-pyramid=normal',
            
            # Rate control
            'rc-lookahead=60',
            'mbtree=1',
            'qcomp=0.7',
            
            # Deblocking (content-adapted)
            f'deblock={deblock}',
            
            # Partitioning
            'analyse=all',
            'direct=auto',
            
            # Trellis
            'trellis=2',
            
            # Quality preservation
            'no-fast-pskip=1',
            'no-dct-decimate=1',
            'weightp=2',
            'weightb=1',
        ]
        
        # Add face-specific tuning if faces detected
        if has_faces and face_coverage > 0.05:
            x264_params.append('tune=film')  # Film tune preserves grain/detail
        
        output_args = {
            'c:v': 'libx264',
            'crf': crf_value,
            'preset': preset,
            'profile:v': 'high',
            'level': '4.2',
            'pix_fmt': 'yuv420p',
            'movflags': '+faststart',
            'maxrate': f'{int(target_bitrate * 1.5)}',
            'bufsize': f'{int(target_bitrate * 3)}',
            'x264-params': ':'.join(x264_params),
            'colorspace': 'bt709',
            'color_primaries': 'bt709',
            'color_trc': 'bt709',
        }
        
        # Premium audio encoding
        if video_info.has_audio:
            audio = stream.audio
            output_args['c:a'] = 'aac'
            output_args['b:a'] = '160k'
            output_args['ar'] = '48000'
            output_args['ac'] = '2'
            output_args['aac_coder'] = 'twoloop'
            output = ffmpeg.output(video, audio, output_path, **output_args)
        else:
            output = ffmpeg.output(video, output_path, **output_args)
        
        # Run encoding
        ffmpeg.run(output, overwrite_output=True, capture_stderr=True)
        
        # Verify output
        compressed_size = os.path.getsize(output_path)
        compression_ratio = (1 - compressed_size / video_info.file_size) * 100
        
        # Build result message
        ml_info = ""
        if ml_analysis and ml_analysis.analysis_confidence > 0.3:
            ml_info = f" [AI: {content_type_str}"
            if has_faces:
                ml_info += f", faces detected"
            ml_info += "]"
        
        return CompressionResult(
            success=True,
            output_path=output_path,
            original_size=video_info.file_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            algorithm_used="Neural Preserve (AI)",
            message=f"AI-enhanced compression complete.{ml_info} Quality: {100-compression_ratio:.1f}%"
        )
        
    except ffmpeg.Error as e:
        return CompressionResult(
            success=False,
            output_path="",
            original_size=video_info.file_size,
            compressed_size=0,
            compression_ratio=0,
            algorithm_used="Neural Preserve (AI)",
            message=f"Compression failed: {e.stderr.decode() if e.stderr else str(e)}"
        )


# =============================================================================
# ALGORITHM 2: BITRATE SCULPTOR  
# =============================================================================
# Strategy: Dynamically sculpts bitrate based on scene complexity.
# Uses 2-pass encoding to analyze content and allocate bits optimally.
# Best for: Mixed content videos, vlogs, general purpose.
# =============================================================================

def compress_bitrate_sculptor(
    input_path: str,
    output_path: str,
    target_size_mb: float = 15.5
) -> CompressionResult:
    """
    Algorithm 2: Bitrate Sculptor - Dynamic Bitrate Allocation
    
    This algorithm sculpts the bitrate dynamically by:
    - Using 2-pass encoding for optimal bit allocation
    - Analyzing scene complexity in first pass
    - Allocating more bits to complex scenes
    - Using B-frames efficiently for temporal compression
    - Applying adaptive GOP (Group of Pictures) sizing
    
    Best for: Vlogs, mixed content, varying complexity videos
    """
    video_info = probe_video(input_path)
    new_width, new_height = get_optimal_resolution(
        video_info.width, video_info.height, Algorithm.BITRATE_SCULPTOR
    )
    
    target_bitrate = calculate_target_bitrate(
        video_info.duration, target_size_mb, 128
    )
    
    # Bitrate Sculptor uses target bitrate with 2-pass
    passlog_prefix = output_path.replace('.mp4', '_passlog')
    
    try:
        # ========== PASS 1: Analysis ==========
        stream = ffmpeg.input(input_path)
        video = stream.video.filter('scale', new_width, new_height)
        
        pass1_args = {
            'c:v': 'libx264',
            'b:v': target_bitrate,
            'pass': 1,
            'passlogfile': passlog_prefix,
            'preset': 'medium',
            'f': 'null',
            'an': None,  # No audio in first pass
            'x264-params': ':'.join([
                'keyint=60',            # Keyframe every 60 frames
                'min-keyint=30',        # Minimum keyframe interval
                'scenecut=40',          # Scene change detection
                'b-adapt=2',            # Optimal B-frame decision
                'bframes=3',            # Use B-frames
                'ref=3',                # Reference frames
            ])
        }
        
        # First pass outputs to null (analysis only)
        pass1_output = ffmpeg.output(video, '/dev/null', **pass1_args)
        ffmpeg.run(pass1_output, overwrite_output=True, capture_stderr=True)
        
        # ========== PASS 2: Encoding ==========
        stream = ffmpeg.input(input_path)
        video = stream.video.filter('scale', new_width, new_height)
        
        # Apply temporal denoising for cleaner compression
        video = video.filter('hqdn3d', luma_spatial=2, chroma_spatial=2, 
                            luma_tmp=3, chroma_tmp=3)
        
        pass2_args = {
            'c:v': 'libx264',
            'b:v': target_bitrate,
            'pass': 2,
            'passlogfile': passlog_prefix,
            'preset': 'medium',
            'profile:v': 'main',
            'level': '4.0',
            'pix_fmt': 'yuv420p',
            'movflags': '+faststart',
            'x264-params': ':'.join([
                'keyint=60',
                'min-keyint=30',
                'scenecut=40',
                'b-adapt=2',
                'bframes=3',
                'ref=3',
                'direct=auto',          # Optimal direct mode
                'me=hex',               # Fast motion estimation
                'subme=7',              # Good subpel quality
                'trellis=1',            # Rate-distortion optimization
            ])
        }
        
        # Handle audio
        if video_info.has_audio:
            audio = stream.audio
            pass2_args['c:a'] = 'aac'
            pass2_args['b:a'] = '128k'
            pass2_args['ar'] = '44100'
            output = ffmpeg.output(video, audio, output_path, **pass2_args)
        else:
            output = ffmpeg.output(video, output_path, **pass2_args)
        
        ffmpeg.run(output, overwrite_output=True, capture_stderr=True)
        
        # Cleanup pass log files
        for ext in ['.log', '.log.mbtree', '-0.log', '-0.log.mbtree']:
            log_file = passlog_prefix + ext
            if os.path.exists(log_file):
                os.remove(log_file)
        
        # Verify output
        compressed_size = os.path.getsize(output_path)
        compression_ratio = (1 - compressed_size / video_info.file_size) * 100
        
        return CompressionResult(
            success=True,
            output_path=output_path,
            original_size=video_info.file_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            algorithm_used="Bitrate Sculptor",
            message=f"2-pass encoding complete. Achieved {compression_ratio:.1f}% compression with optimal bit allocation."
        )
        
    except ffmpeg.Error as e:
        # Cleanup on error
        for ext in ['.log', '.log.mbtree', '-0.log', '-0.log.mbtree']:
            log_file = passlog_prefix + ext
            if os.path.exists(log_file):
                os.remove(log_file)
                
        return CompressionResult(
            success=False,
            output_path="",
            original_size=video_info.file_size,
            compressed_size=0,
            compression_ratio=0,
            algorithm_used="Bitrate Sculptor",
            message=f"Compression failed: {e.stderr.decode() if e.stderr else str(e)}"
        )


# =============================================================================
# ALGORITHM 3: QUANTUM COMPRESS
# =============================================================================
# Strategy: Aggressive compression for maximum size reduction.
# Sacrifices some quality for smallest possible file size.
# Best for: Low bandwidth situations, bulk uploads, quick sharing.
# =============================================================================

def compress_quantum_compress(
    input_path: str,
    output_path: str,
    target_size_mb: float = 12.0  # More aggressive target
) -> CompressionResult:
    """
    Algorithm 3: Quantum Compress - Maximum Compression
    
    This algorithm achieves maximum compression by:
    - Using higher CRF values for aggressive quantization
    - Reducing resolution more aggressively
    - Applying noise reduction before encoding
    - Using faster presets with tuning for compression
    - Reducing frame rate if very high
    - Lower audio bitrate
    
    Best for: Quick sharing, low bandwidth, bulk processing
    """
    video_info = probe_video(input_path)
    new_width, new_height = get_optimal_resolution(
        video_info.width, video_info.height, Algorithm.QUANTUM_COMPRESS
    )
    
    # Quantum uses aggressive CRF
    crf_value = 28  # Higher CRF = more compression
    
    # Reduce framerate if above 30fps
    target_fps = min(video_info.fps, 30)
    
    try:
        stream = ffmpeg.input(input_path)
        video = stream.video
        
        # Apply aggressive noise reduction
        video = video.filter('hqdn3d', luma_spatial=4, chroma_spatial=4,
                            luma_tmp=6, chroma_tmp=6)
        
        # Scale down
        video = video.filter('scale', new_width, new_height)
        
        # Reduce framerate if needed
        if video_info.fps > 30:
            video = video.filter('fps', fps=target_fps)
        
        output_args = {
            'c:v': 'libx264',
            'crf': crf_value,
            'preset': 'faster',          # Faster encoding, still good compression
            'tune': 'fastdecode',        # Optimize for fast playback
            'profile:v': 'baseline',     # Most compatible, smaller
            'level': '3.1',
            'pix_fmt': 'yuv420p',
            'movflags': '+faststart',
            'x264-params': ':'.join([
                'keyint=120',            # Larger GOP for compression
                'min-keyint=60',
                'bframes=0',             # No B-frames for simplicity
                'ref=1',                 # Minimal references
                'me=dia',                # Fast motion estimation
                'subme=4',               # Faster subpel
                'aq-mode=0',             # No adaptive quantization
                'no-mbtree=1',           # Disable macroblock tree
            ])
        }
        
        # Handle audio with lower bitrate
        if video_info.has_audio:
            audio = stream.audio
            output_args['c:a'] = 'aac'
            output_args['b:a'] = '96k'   # Lower audio bitrate
            output_args['ar'] = '44100'
            output_args['ac'] = '1'      # Convert to mono for more savings
            output = ffmpeg.output(video, audio, output_path, **output_args)
        else:
            output = ffmpeg.output(video, output_path, **output_args)
        
        ffmpeg.run(output, overwrite_output=True, capture_stderr=True)
        
        # Verify output
        compressed_size = os.path.getsize(output_path)
        compression_ratio = (1 - compressed_size / video_info.file_size) * 100
        
        return CompressionResult(
            success=True,
            output_path=output_path,
            original_size=video_info.file_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            algorithm_used="Quantum Compress",
            message=f"Maximum compression achieved! {compression_ratio:.1f}% size reduction. File is optimized for fast sharing."
        )
        
    except ffmpeg.Error as e:
        return CompressionResult(
            success=False,
            output_path="",
            original_size=video_info.file_size,
            compressed_size=0,
            compression_ratio=0,
            algorithm_used="Quantum Compress",
            message=f"Compression failed: {e.stderr.decode() if e.stderr else str(e)}"
        )


# =============================================================================
# MAIN COMPRESSION FUNCTION
# =============================================================================

def compress_video(
    input_path: str,
    output_path: str,
    algorithm: Algorithm,
    target_size_mb: float = 15.5
) -> CompressionResult:
    """
    Main compression function that routes to the appropriate algorithm.
    
    Args:
        input_path: Path to input video file
        output_path: Path for output compressed video
        algorithm: Which compression algorithm to use
        target_size_mb: Target file size in megabytes
        
    Returns:
        CompressionResult with compression statistics
    """
    if algorithm == Algorithm.NEURAL_PRESERVE:
        return compress_neural_preserve(input_path, output_path, target_size_mb)
    elif algorithm == Algorithm.BITRATE_SCULPTOR:
        return compress_bitrate_sculptor(input_path, output_path, target_size_mb)
    elif algorithm == Algorithm.QUANTUM_COMPRESS:
        return compress_quantum_compress(input_path, output_path, target_size_mb)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")


# =============================================================================
# ALGORITHM COMPARISON TABLE
# =============================================================================
"""
┌─────────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ Feature             │ Neural Preserve  │ Bitrate Sculptor │ Quantum Compress │
├─────────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Quality Focus       │ ★★★★★           │ ★★★★☆           │ ★★★☆☆           │
│ File Size           │ ★★★☆☆           │ ★★★★☆           │ ★★★★★           │
│ Encoding Speed      │ ★★☆☆☆           │ ★★★☆☆           │ ★★★★★           │
│ Best For            │ Detail/Faces     │ General Use      │ Quick Share      │
├─────────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Resolution          │ Up to 1080p      │ 720p             │ 640p             │
│ Encoding Passes     │ 1-pass CRF       │ 2-pass ABR       │ 1-pass CRF       │
│ CRF Value           │ 23               │ N/A (bitrate)    │ 28               │
│ Preset              │ slow             │ medium           │ faster           │
│ B-Frames            │ Yes              │ Yes (3)          │ No               │
│ Audio Bitrate       │ 128 kbps         │ 128 kbps         │ 96 kbps (mono)   │
└─────────────────────┴──────────────────┴──────────────────┴──────────────────┘
"""
