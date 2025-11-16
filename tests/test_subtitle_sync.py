import unittest
import os
import tempfile
from src.core.subtitle_sync import SubtitleSyncEngine

class TestSubtitleSync(unittest.TestCase):
    def setUp(self):
        self.sync_engine = SubtitleSyncEngine()
        self.test_dir = tempfile.mkdtemp()
    
    def test_find_pairs(self):
        # Criar arquivos de teste
        open(os.path.join(self.test_dir, "test_video.mp4"), 'w').close()
        open(os.path.join(self.test_dir, "test_video.srt"), 'w').close()
        open(os.path.join(self.test_dir, "other_video.avi"), 'w').close()
        
        pairs = self.sync_engine.find_video_subtitle_pairs(self.test_dir)
        self.assertEqual(len(pairs), 1)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

if __name__ == '__main__':
    unittest.main()