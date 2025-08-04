#!/usr/bin/env python3
"""
Startup script to manage model persistence on RunPod volume
"""
import os
import shutil
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RunPod volume path
VOLUME_PATH = "/runpod-volume"
VOLUME_MODELS_PATH = os.path.join(VOLUME_PATH, "models")

# Container model paths
CONTAINER_MODELS_PATH = "/models"

# Model directories to check/copy
MODELS = [
    "Qwen3-Embedding-0.6B",
    "Qwen3-Reranker-0.6B"
]

def ensure_volume_mounted():
    """Check if RunPod volume is mounted"""
    if not os.path.exists(VOLUME_PATH):
        logger.warning(f"RunPod volume not mounted at {VOLUME_PATH}")
        return False
    
    # Check if we can write to the volume
    try:
        test_file = os.path.join(VOLUME_PATH, ".write_test")
        Path(test_file).touch()
        os.remove(test_file)
        logger.info(f"RunPod volume mounted and writable at {VOLUME_PATH}")
        return True
    except Exception as e:
        logger.error(f"Cannot write to RunPod volume: {e}")
        return False

def check_model_exists(model_name):
    """Check if a model exists on the volume"""
    model_path = os.path.join(VOLUME_MODELS_PATH, model_name)
    
    # Check if directory exists and has model files
    if os.path.exists(model_path):
        files = os.listdir(model_path)
        # Check for either safetensors or pytorch model files
        has_model = any(f.endswith(('.safetensors', '.bin')) for f in files)
        if has_model:
            logger.info(f"Model {model_name} found on volume")
            return True
    
    return False

def copy_model_to_volume(model_name):
    """Copy a model from container to volume"""
    src_path = os.path.join(CONTAINER_MODELS_PATH, model_name)
    dst_path = os.path.join(VOLUME_MODELS_PATH, model_name)
    
    if not os.path.exists(src_path):
        logger.error(f"Model {model_name} not found in container at {src_path}")
        return False
    
    try:
        logger.info(f"Copying model {model_name} to volume...")
        os.makedirs(VOLUME_MODELS_PATH, exist_ok=True)
        
        # Remove destination if it exists (partial copy)
        if os.path.exists(dst_path):
            shutil.rmtree(dst_path)
        
        # Copy the model directory
        shutil.copytree(src_path, dst_path)
        logger.info(f"Successfully copied model {model_name} to volume")
        return True
    except Exception as e:
        logger.error(f"Failed to copy model {model_name}: {e}")
        return False

def setup_model_symlinks():
    """Create symlinks from container paths to volume paths"""
    # This ensures the models are accessible at the expected paths
    for model_name in MODELS:
        container_path = os.path.join(CONTAINER_MODELS_PATH, model_name)
        volume_path = os.path.join(VOLUME_MODELS_PATH, model_name)
        
        # Remove existing path if it's not a symlink
        if os.path.exists(container_path) and not os.path.islink(container_path):
            if os.path.isdir(container_path):
                shutil.rmtree(container_path)
            else:
                os.remove(container_path)
        
        # Create symlink if model exists on volume
        if os.path.exists(volume_path) and not os.path.exists(container_path):
            os.makedirs(os.path.dirname(container_path), exist_ok=True)
            os.symlink(volume_path, container_path)
            logger.info(f"Created symlink for {model_name}")

def update_model_paths():
    """Update MODEL_NAMES environment variable to use volume paths if available"""
    if not os.path.exists(VOLUME_MODELS_PATH):
        logger.info("Using container model paths")
        return
    
    # Map model IDs to local paths
    model_mapping = {
        "Qwen/Qwen3-Embedding-0.6B": os.path.join(VOLUME_MODELS_PATH, "Qwen3-Embedding-0.6B"),
        "Qwen/Qwen3-Reranker-0.6B": os.path.join(VOLUME_MODELS_PATH, "Qwen3-Reranker-0.6B")
    }
    
    # Get current MODEL_NAMES
    current_models = os.environ.get("MODEL_NAMES", "").split(";")
    updated_models = []
    
    for model in current_models:
        model = model.strip()
        if model in model_mapping and os.path.exists(model_mapping[model]):
            # Use local path if model exists on volume
            updated_models.append(model_mapping[model])
            logger.info(f"Using volume path for {model}")
        else:
            # Keep original model ID
            updated_models.append(model)
    
    # Update environment variable
    if updated_models:
        os.environ["MODEL_NAMES"] = ";".join(updated_models)
        logger.info(f"Updated MODEL_NAMES: {os.environ['MODEL_NAMES']}")

def main():
    """Main startup logic"""
    logger.info("Starting RunPod worker...")
    
    # Ensure we have the right transformers version for Qwen3
    try:
        import transformers
        logger.info(f"Transformers version: {transformers.__version__}")
    except ImportError:
        logger.error("Transformers not installed!")
    
    # Always use container models for best performance
    # For now, only load embedding model due to reranker compatibility issues
    os.environ["MODEL_NAMES"] = "/models/Qwen3-Embedding-0.6B"
    logger.info("Using embedding model from container for optimal performance")
    
    # Check if volume is mounted for HF_HOME (cache for any additional models)
    volume_mounted = ensure_volume_mounted()
    
    if volume_mounted:
        # Set HF_HOME to use volume for any additional model downloads/cache
        os.environ['HF_HOME'] = VOLUME_PATH
        logger.info(f"Set HF_HOME to {VOLUME_PATH} for model cache")
        
        # Optional: Copy models to volume if COPY_TO_VOLUME env var is set
        if os.environ.get("COPY_TO_VOLUME", "false").lower() == "true":
            logger.info("COPY_TO_VOLUME is set, copying models to volume for persistence...")
            for model_name in MODELS:
                if not check_model_exists(model_name):
                    logger.info(f"Copying {model_name} to volume...")
                    copy_model_to_volume(model_name)
    else:
        logger.info("No persistent volume mounted - using container filesystem")
        # HF_HOME stays at default container location
    
    logger.info("Starting handler...")
    
    # Import and run the handler
    import handler
    # Execute the handler's main block
    import sys
    sys.argv[0] = '/handler.py'  # Set the script name
    exec(open('/handler.py').read())

if __name__ == "__main__":
    main()