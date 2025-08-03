"""
Model persistence utilities for RunPod network volumes.
Copies models from container to persistent disk on first run.
"""

import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PERSISTENT_VOLUME = "/runpod-volume"
CONTAINER_MODEL_PATH = "/models"

def ensure_models_on_persistent_disk():
    """
    Check if models exist on persistent disk, if not copy them from container.
    This runs on container startup to ensure models are available.
    """
    # Define model paths
    models = [
        "Qwen3-Embedding-0.6B",
        "Qwen3-Reranker-0.6B"
    ]
    
    persistent_models_dir = Path(PERSISTENT_VOLUME) / "models"
    persistent_models_dir.mkdir(exist_ok=True)
    
    for model in models:
        persistent_model_path = persistent_models_dir / model
        container_model_path = Path(CONTAINER_MODEL_PATH) / model
        
        if not persistent_model_path.exists():
            logger.info(f"Model {model} not found on persistent disk. Copying from container...")
            
            if container_model_path.exists():
                # Copy model to persistent disk
                shutil.copytree(
                    container_model_path,
                    persistent_model_path,
                    dirs_exist_ok=True
                )
                logger.info(f"Successfully copied {model} to persistent disk")
            else:
                logger.warning(f"Model {model} not found in container at {container_model_path}")
        else:
            logger.info(f"Model {model} already exists on persistent disk")
    
    # Update HF_HOME to use persistent models
    os.environ["HF_HOME"] = str(persistent_models_dir)
    os.environ["TRANSFORMERS_CACHE"] = str(persistent_models_dir)
    
    return persistent_models_dir

def get_model_path(model_name: str) -> Path:
    """Get the path to a model, preferring persistent disk."""
    persistent_models_dir = Path(PERSISTENT_VOLUME) / "models"
    model_path = persistent_models_dir / model_name.split("/")[-1]
    
    if model_path.exists():
        return model_path
    
    # Fallback to container path
    container_path = Path(CONTAINER_MODEL_PATH) / model_name.split("/")[-1]
    if container_path.exists():
        return container_path
    
    # Return the expected persistent path (model will be downloaded if needed)
    return model_path

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ensure_models_on_persistent_disk()