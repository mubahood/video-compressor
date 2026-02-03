"""
ML-Based Video Content Analyzer
================================
Uses computer vision and machine learning to analyze video content
and provide optimal compression parameters.

Features:
- Face detection for quality prioritization
- Scene complexity analysis
- Motion estimation
- Content classification (talking head, action, nature, etc.)

Note: This module requires opencv-python-headless and numpy.
If not available, a fallback analyzer is used.
"""

# Try to import ML dependencies - they're optional
try:
    import cv2
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    cv2 = None
    np = None

from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum
import os


class ContentType(Enum):
    """Detected video content type"""
    TALKING_HEAD = "talking_head"    # Person talking to camera (prioritize face quality)
    GROUP_PEOPLE = "group_people"    # Multiple people
    ACTION = "action"                # High motion content
    NATURE = "nature"                # Nature/landscape (prioritize detail)
    SCREEN_CONTENT = "screen"        # Screen recording/text
    GENERAL = "general"              # General content


@dataclass
class FrameAnalysis:
    """Analysis result for a single frame"""
    face_count: int
    face_area_ratio: float      # Percentage of frame covered by faces
    edge_density: float         # Amount of detail/edges
    brightness: float           # Average brightness
    contrast: float             # Image contrast
    colorfulness: float         # Color variety
    blur_score: float           # Blur detection


@dataclass
class VideoAnalysis:
    """Complete video analysis result"""
    content_type: ContentType
    avg_face_count: float
    max_face_count: int
    face_coverage: float        # Average face area ratio
    complexity_score: float     # 0-1, higher = more complex
    motion_score: float         # 0-1, higher = more motion
    brightness_score: float     # 0-1
    recommended_crf: int
    recommended_bitrate_mult: float
    face_regions: List[Tuple[int, int, int, int]]  # Detected face regions for ROI
    analysis_confidence: float


class MLVideoAnalyzer:
    """
    ML-based video analyzer for content-aware compression.
    Uses OpenCV's DNN face detector and various CV algorithms.
    
    Falls back to basic analysis if OpenCV is not available.
    """
    
    def __init__(self):
        """Initialize the analyzer with face detection model"""
        self.face_cascade = None
        self.face_net = None
        self.ml_available = ML_AVAILABLE
        
        if self.ml_available:
            self._init_face_detector()
    
    def _init_face_detector(self):
        """Initialize face detection - try DNN first, fall back to Haar cascade"""
        if not self.ml_available:
            return
            
        # Try to use OpenCV's DNN face detector (more accurate)
        try:
            # Check for pre-trained model files
            model_path = os.path.join(os.path.dirname(__file__), 'models')
            prototxt = os.path.join(model_path, 'deploy.prototxt')
            weights = os.path.join(model_path, 'res10_300x300_ssd_iter_140000.caffemodel')
            
            if os.path.exists(prototxt) and os.path.exists(weights):
                self.face_net = cv2.dnn.readNetFromCaffe(prototxt, weights)
                print("Using DNN face detector")
                return
        except Exception:
            pass
        
        # Fall back to Haar cascade (always available)
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            if self.face_cascade.empty():
                raise ValueError("Failed to load cascade")
        except Exception as e:
            print(f"Warning: Face detection unavailable: {e}")
    
    def detect_faces(self, frame) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in a frame.
        
        Returns:
            List of (x, y, w, h) tuples for each detected face
        """
        if not self.ml_available or frame is None:
            return []
        
        faces = []
        
        # Try DNN detector first
        if self.face_net is not None:
            try:
                h, w = frame.shape[:2]
                blob = cv2.dnn.blobFromImage(
                    cv2.resize(frame, (300, 300)), 1.0, (300, 300),
                    (104.0, 177.0, 123.0), swapRB=False, crop=False
                )
                self.face_net.setInput(blob)
                detections = self.face_net.forward()
                
                for i in range(detections.shape[2]):
                    confidence = detections[0, 0, i, 2]
                    if confidence > 0.5:  # Confidence threshold
                        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                        x1, y1, x2, y2 = box.astype(int)
                        faces.append((x1, y1, x2 - x1, y2 - y1))
                return faces
            except Exception:
                pass
        
        # Fall back to Haar cascade
        if self.face_cascade is not None:
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                detected = self.face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                )
                faces = [(x, y, w, h) for (x, y, w, h) in detected]
            except Exception:
                pass
        
        return faces
    
    def analyze_frame(self, frame) -> FrameAnalysis:
        """
        Analyze a single frame for various quality metrics.
        """
        if not self.ml_available or frame is None:
            return FrameAnalysis(0, 0, 0, 0.5, 0.5, 0.5, 0.5)
        
        h, w = frame.shape[:2]
        frame_area = h * w
        
        # Face detection
        faces = self.detect_faces(frame)
        face_count = len(faces)
        face_area = sum(fw * fh for (_, _, fw, fh) in faces)
        face_area_ratio = face_area / frame_area if frame_area > 0 else 0
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Edge density (detail level)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / frame_area
        
        # Brightness
        brightness = np.mean(gray) / 255.0
        
        # Contrast (standard deviation of brightness)
        contrast = np.std(gray) / 128.0  # Normalized
        
        # Colorfulness metric (Hasler and Süsstrunk)
        if len(frame.shape) == 3:
            b, g, r = cv2.split(frame.astype(float))
            rg = np.abs(r - g)
            yb = np.abs(0.5 * (r + g) - b)
            colorfulness = (np.mean(rg) + np.mean(yb)) / 255.0
        else:
            colorfulness = 0
        
        # Blur detection using Laplacian variance
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_score = min(laplacian_var / 500.0, 1.0)  # Normalized, higher = sharper
        
        return FrameAnalysis(
            face_count=face_count,
            face_area_ratio=face_area_ratio,
            edge_density=edge_density,
            brightness=brightness,
            contrast=contrast,
            colorfulness=colorfulness,
            blur_score=blur_score
        )
    
    def calculate_motion(self, frame1, frame2) -> float:
        """
        Calculate motion between two frames using optical flow.
        """
        if not self.ml_available or frame1 is None or frame2 is None:
            return 0.0
        
        try:
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            
            # Resize for faster processing
            scale = 0.25
            gray1 = cv2.resize(gray1, None, fx=scale, fy=scale)
            gray2 = cv2.resize(gray2, None, fx=scale, fy=scale)
            
            # Calculate optical flow
            flow = cv2.calcOpticalFlowFarneback(
                gray1, gray2, None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )
            
            # Calculate magnitude
            mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            motion_score = np.mean(mag) / 20.0  # Normalized
            return min(motion_score, 1.0)
        except Exception:
            return 0.0
    
    def analyze_video(self, video_path: str, sample_rate: int = 10) -> VideoAnalysis:
        """
        Analyze entire video by sampling frames.
        
        Args:
            video_path: Path to video file
            sample_rate: Analyze every Nth frame
            
        Returns:
            VideoAnalysis with recommendations
        """
        # If ML not available, return default analysis
        if not self.ml_available:
            return self._default_analysis()
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return self._default_analysis()
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        
        frame_analyses = []
        motion_scores = []
        prev_frame = None
        all_faces = []
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Sample frames
            if frame_idx % sample_rate == 0:
                analysis = self.analyze_frame(frame)
                frame_analyses.append(analysis)
                
                # Detect faces for ROI
                faces = self.detect_faces(frame)
                all_faces.extend(faces)
                
                # Calculate motion
                if prev_frame is not None:
                    motion = self.calculate_motion(prev_frame, frame)
                    motion_scores.append(motion)
                
                prev_frame = frame.copy()
            
            frame_idx += 1
        
        cap.release()
        
        if not frame_analyses:
            return self._default_analysis()
        
        # Aggregate analysis
        avg_face_count = np.mean([a.face_count for a in frame_analyses])
        max_face_count = max(a.face_count for a in frame_analyses)
        face_coverage = np.mean([a.face_area_ratio for a in frame_analyses])
        avg_edge_density = np.mean([a.edge_density for a in frame_analyses])
        avg_brightness = np.mean([a.brightness for a in frame_analyses])
        avg_colorfulness = np.mean([a.colorfulness for a in frame_analyses])
        avg_motion = np.mean(motion_scores) if motion_scores else 0.0
        
        # Calculate complexity score
        complexity_score = (
            avg_edge_density * 0.4 +
            avg_colorfulness * 0.3 +
            (1 - avg_motion) * 0.3  # Less motion = can use more detail
        )
        complexity_score = min(max(complexity_score, 0), 1)
        
        # Determine content type
        content_type = self._classify_content(
            avg_face_count, max_face_count, face_coverage,
            avg_motion, avg_edge_density, avg_brightness
        )
        
        # Get recommendations based on analysis
        recommended_crf, bitrate_mult = self._get_recommendations(
            content_type, complexity_score, face_coverage, avg_motion
        )
        
        # Consolidate face regions (most common areas)
        face_regions = self._consolidate_face_regions(all_faces)
        
        return VideoAnalysis(
            content_type=content_type,
            avg_face_count=avg_face_count,
            max_face_count=max_face_count,
            face_coverage=face_coverage,
            complexity_score=complexity_score,
            motion_score=avg_motion,
            brightness_score=avg_brightness,
            recommended_crf=recommended_crf,
            recommended_bitrate_mult=bitrate_mult,
            face_regions=face_regions,
            analysis_confidence=min(len(frame_analyses) / 10, 1.0)
        )
    
    def _classify_content(
        self,
        avg_faces: float,
        max_faces: int,
        face_coverage: float,
        motion: float,
        edge_density: float,
        brightness: float
    ) -> ContentType:
        """Classify video content type based on analysis"""
        
        # Talking head: 1 face, high face coverage, low motion
        if avg_faces >= 0.8 and face_coverage > 0.05 and motion < 0.3:
            return ContentType.TALKING_HEAD
        
        # Group of people: multiple faces
        if max_faces >= 2 and avg_faces >= 1.5:
            return ContentType.GROUP_PEOPLE
        
        # Action: high motion
        if motion > 0.5:
            return ContentType.ACTION
        
        # Screen content: high edge density, low colorfulness
        if edge_density > 0.15 and brightness > 0.6:
            return ContentType.SCREEN_CONTENT
        
        # Nature: high colorfulness, medium complexity
        if edge_density > 0.05 and motion < 0.4:
            return ContentType.NATURE
        
        return ContentType.GENERAL
    
    def _get_recommendations(
        self,
        content_type: ContentType,
        complexity: float,
        face_coverage: float,
        motion: float
    ) -> Tuple[int, float]:
        """
        Get encoding recommendations based on content analysis.
        
        Returns:
            Tuple of (recommended_crf, bitrate_multiplier)
        """
        # Base CRF based on content type
        crf_map = {
            ContentType.TALKING_HEAD: 18,   # Highest quality for faces
            ContentType.GROUP_PEOPLE: 19,   # High quality for people
            ContentType.ACTION: 21,         # Slightly lower for motion
            ContentType.NATURE: 19,         # High quality for detail
            ContentType.SCREEN_CONTENT: 20, # Good quality for text
            ContentType.GENERAL: 20,
        }
        
        base_crf = crf_map.get(content_type, 20)
        
        # Adjust CRF based on complexity
        # Higher complexity = lower CRF (more bits needed)
        crf_adjustment = int((0.5 - complexity) * 4)  # -2 to +2
        recommended_crf = max(17, min(23, base_crf + crf_adjustment))
        
        # Bitrate multiplier
        # Higher face coverage = higher multiplier (prioritize faces)
        bitrate_mult = 1.0
        if face_coverage > 0.1:
            bitrate_mult += 0.2
        if content_type == ContentType.TALKING_HEAD:
            bitrate_mult += 0.1
        if motion > 0.5:
            bitrate_mult += 0.15  # Action needs more bits
        
        return recommended_crf, min(bitrate_mult, 1.5)
    
    def _consolidate_face_regions(
        self,
        faces: List[Tuple[int, int, int, int]],
        max_regions: int = 3
    ) -> List[Tuple[int, int, int, int]]:
        """Consolidate face detections into main regions for ROI encoding"""
        if not faces:
            return []
        
        # Simple clustering by position
        # For now, return the largest faces
        faces_sorted = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        return faces_sorted[:max_regions]
    
    def _default_analysis(self) -> VideoAnalysis:
        """Return default analysis when video cannot be analyzed"""
        return VideoAnalysis(
            content_type=ContentType.GENERAL,
            avg_face_count=0,
            max_face_count=0,
            face_coverage=0,
            complexity_score=0.5,
            motion_score=0.3,
            brightness_score=0.5,
            recommended_crf=20,
            recommended_bitrate_mult=1.0,
            face_regions=[],
            analysis_confidence=0
        )


def get_ml_recommendations(video_path: str) -> dict:
    """
    Convenience function to get ML-based compression recommendations.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Dictionary with recommendations
    """
    analyzer = MLVideoAnalyzer()
    analysis = analyzer.analyze_video(video_path)
    
    return {
        'content_type': analysis.content_type.value,
        'recommended_crf': analysis.recommended_crf,
        'bitrate_multiplier': analysis.recommended_bitrate_mult,
        'face_coverage': analysis.face_coverage,
        'complexity': analysis.complexity_score,
        'motion': analysis.motion_score,
        'has_faces': analysis.avg_face_count > 0,
        'face_regions': analysis.face_regions,
        'confidence': analysis.analysis_confidence
    }
