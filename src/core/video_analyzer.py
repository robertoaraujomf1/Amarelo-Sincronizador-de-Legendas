import cv2
import os
from moviepy.editor import VideoFileClip

class VideoAnalyzer:
    def __init__(self):
        self.supported_formats = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
    
    def analyze_video(self, video_path):
        """Analisa o vídeo e retorna informações importantes"""
        try:
            if not os.path.exists(video_path):
                return None
            
            # Usar moviepy para obter duração
            try:
                with VideoFileClip(video_path) as video:
                    duration = video.duration
                    fps = video.fps
                    size = video.size  # (width, height)
                
                return {
                    'duration': duration,
                    'fps': fps,
                    'width': size[0],
                    'height': size[1],
                    'file_size': os.path.getsize(video_path)
                }
            except:
                # Fallback usando OpenCV
                return self.analyze_with_opencv(video_path)
                
        except Exception as e:
            print(f"Erro ao analisar vídeo {video_path}: {str(e)}")
            return None
    
    def analyze_with_opencv(self, video_path):
        """Análise de fallback usando OpenCV"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return None
            
            # Obter FPS
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # Obter número total de frames
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Calcular duração
            duration = total_frames / fps if fps > 0 else 0
            
            # Obter resolução
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            cap.release()
            
            return {
                'duration': duration,
                'fps': fps,
                'width': width,
                'height': height,
                'file_size': os.path.getsize(video_path)
            }
        except:
            return None
    
    def get_video_scene_changes(self, video_path, threshold=0.3):
        """Detecta mudanças de cena no vídeo (para análise mais avançada)"""
        scene_changes = []
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return scene_changes
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            prev_frame = None
            
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if prev_frame is not None:
                    # Calcular diferença entre frames
                    diff = cv2.absdiff(prev_frame, frame)
                    non_zero_count = cv2.countNonZero(cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY))
                    total_pixels = frame.shape[0] * frame.shape[1]
                    
                    if non_zero_count / total_pixels > threshold:
                        scene_changes.append(frame_count / fps)
                
                prev_frame = frame.copy()
                frame_count += 1
            
            cap.release()
        except:
            pass
        
        return scene_changes