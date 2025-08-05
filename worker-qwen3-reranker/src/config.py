import os
from typing import Optional

class RerankerConfig:
    def __init__(self):
        # Model configuration
        self.model_name = os.environ.get("MODEL_NAME", "Qwen/Qwen3-Reranker-0.6B")
        self.max_length = int(os.environ.get("MAX_LENGTH", "8192"))
        self.device = os.environ.get("DEVICE", "cuda" if self._check_cuda() else "cpu")
        
        # RunPod configuration
        self.runpod_max_concurrency = int(os.environ.get("RUNPOD_MAX_CONCURRENCY", "10"))
        
        # Performance settings
        self.use_flash_attention = os.environ.get("USE_FLASH_ATTENTION", "false").lower() == "true"
        self.torch_dtype = os.environ.get("TORCH_DTYPE", "float16")
        
    def _check_cuda(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
            
    def get_torch_dtype(self):
        import torch
        if self.torch_dtype == "float16":
            return torch.float16
        elif self.torch_dtype == "bfloat16":
            return torch.bfloat16
        else:
            return torch.float32