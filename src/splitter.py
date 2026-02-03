"""
Video Splitter Module
=====================

Splits videos into 30-second or 60-second segments for WhatsApp status uploads.
"""

import ffmpeg
import os
import math
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class SplitResult:
    """Result of video splitting operation"""
    success: bool
    segments: List[str]
    total_segments: int
    segment_duration: int
    message: str


def get_video_duration(input_path: str) -> float:
    """Get video duration in seconds"""
    probe = ffmpeg.probe(input_path)
    return float(probe['format']['duration'])


def split_video(
    input_path: str,
    output_dir: str,
    segment_duration: int = 30,
    output_prefix: str = "segment"
) -> SplitResult:
    """
    Split a video into segments of specified duration.
    
    This function uses FFmpeg's segment muxer for efficient splitting
    without re-encoding (stream copy) when possible.
    
    Args:
        input_path: Path to input video file
        output_dir: Directory for output segments
        segment_duration: Duration of each segment in seconds (30 or 60)
        output_prefix: Prefix for output filenames
        
    Returns:
        SplitResult with list of segment paths and metadata
    """
    try:
        # Get video duration
        total_duration = get_video_duration(input_path)
        
        # Calculate number of segments
        num_segments = math.ceil(total_duration / segment_duration)
        
        if num_segments <= 1:
            # Video is shorter than segment duration, no need to split
            return SplitResult(
                success=True,
                segments=[input_path],
                total_segments=1,
                segment_duration=segment_duration,
                message="Video is shorter than segment duration. No splitting needed."
            )
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        segments = []
        
        for i in range(num_segments):
            start_time = i * segment_duration
            
            # Calculate actual duration for this segment
            remaining = total_duration - start_time
            actual_duration = min(segment_duration, remaining)
            
            # Skip very short final segments (less than 2 seconds)
            if actual_duration < 2 and i > 0:
                continue
            
            output_path = os.path.join(
                output_dir, 
                f"{output_prefix}_part{i+1:02d}.mp4"
            )
            
            try:
                # Use stream copy for fast splitting (no re-encoding)
                stream = ffmpeg.input(input_path, ss=start_time, t=actual_duration)
                
                output = ffmpeg.output(
                    stream,
                    output_path,
                    c='copy',              # Stream copy (fast, no quality loss)
                    movflags='+faststart', # Enable progressive download
                    avoid_negative_ts='make_zero'  # Fix timestamp issues
                )
                
                ffmpeg.run(output, overwrite_output=True, capture_stderr=True)
                segments.append(output_path)
                
            except ffmpeg.Error:
                # If stream copy fails, try with re-encoding
                stream = ffmpeg.input(input_path, ss=start_time, t=actual_duration)
                
                output = ffmpeg.output(
                    stream,
                    output_path,
                    c_v='libx264',
                    crf=18,  # High quality re-encode
                    preset='fast',
                    c_a='aac',
                    b_a='128k',
                    movflags='+faststart'
                )
                
                ffmpeg.run(output, overwrite_output=True, capture_stderr=True)
                segments.append(output_path)
        
        return SplitResult(
            success=True,
            segments=segments,
            total_segments=len(segments),
            segment_duration=segment_duration,
            message=f"Successfully split video into {len(segments)} segments of {segment_duration}s each."
        )
        
    except ffmpeg.Error as e:
        return SplitResult(
            success=False,
            segments=[],
            total_segments=0,
            segment_duration=segment_duration,
            message=f"Split failed: {e.stderr.decode() if e.stderr else str(e)}"
        )
    except Exception as e:
        return SplitResult(
            success=False,
            segments=[],
            total_segments=0,
            segment_duration=segment_duration,
            message=f"Split failed: {str(e)}"
        )


def split_and_compress(
    input_path: str,
    output_dir: str,
    segment_duration: int,
    compress_func,
    output_prefix: str = "compressed"
) -> Tuple[SplitResult, List]:
    """
    Split video and compress each segment.
    
    This is a combined operation that first splits the video,
    then compresses each segment individually.
    
    Args:
        input_path: Path to input video file
        output_dir: Directory for output
        segment_duration: Duration of each segment (30 or 60)
        compress_func: Compression function to apply to each segment
        output_prefix: Prefix for output filenames
        
    Returns:
        Tuple of (SplitResult, list of CompressionResults)
    """
    # First split the video
    split_dir = os.path.join(output_dir, "temp_splits")
    split_result = split_video(
        input_path, 
        split_dir, 
        segment_duration,
        "temp_segment"
    )
    
    if not split_result.success:
        return split_result, []
    
    # Compress each segment
    compression_results = []
    compressed_segments = []
    
    for i, segment_path in enumerate(split_result.segments):
        compressed_path = os.path.join(
            output_dir,
            f"{output_prefix}_part{i+1:02d}.mp4"
        )
        
        result = compress_func(segment_path, compressed_path)
        compression_results.append(result)
        
        if result.success:
            compressed_segments.append(compressed_path)
        
        # Clean up temporary segment
        if os.path.exists(segment_path):
            os.remove(segment_path)
    
    # Clean up temp directory
    if os.path.exists(split_dir):
        try:
            os.rmdir(split_dir)
        except:
            pass
    
    # Update split result with compressed segments
    final_result = SplitResult(
        success=all(r.success for r in compression_results),
        segments=compressed_segments,
        total_segments=len(compressed_segments),
        segment_duration=segment_duration,
        message=f"Split and compressed {len(compressed_segments)} segments."
    )
    
    return final_result, compression_results
