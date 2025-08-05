#!/bin/bash

# Create models directory
mkdir -p models/hub

echo "Downloading Qwen3 models with git-lfs..."

# Function to download a model
download_model() {
    local model_name=$1
    local model_dir=$2
    
    echo "Downloading $model_name..."
    
    # Clone the repo
    git clone https://huggingface.co/$model_name $model_dir
    
    # Enter the directory and pull LFS files
    cd $model_dir
    git lfs install
    git lfs pull
    cd -
    
    echo "$model_name download complete!"
}

# Download all models
download_model "Qwen/Qwen3-Embedding-0.6B" "models/hub/models--Qwen--Qwen3-Embedding-0.6B"
download_model "Qwen/Qwen3-Reranker-0.6B" "models/hub/models--Qwen--Qwen3-Reranker-0.6B"
download_model "Qwen/Qwen3-Embedding-4B" "models/hub/models--Qwen--Qwen3-Embedding-4B"
download_model "Qwen/Qwen3-Reranker-4B" "models/hub/models--Qwen--Qwen3-Reranker-4B"

echo "All models downloaded successfully!"

# Show disk usage
echo "Model sizes:"
du -sh models/hub/*