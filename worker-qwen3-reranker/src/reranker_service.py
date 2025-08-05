import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Dict, Optional, Tuple
import logging
from config import RerankerConfig

logger = logging.getLogger(__name__)


class Qwen3RerankerService:
    def __init__(self):
        self.config = RerankerConfig()
        self._load_model()
        
    def _load_model(self):
        """Load the Qwen3 reranker model and tokenizer"""
        logger.info(f"Loading model from {self.config.model_name}")
        
        # Load tokenizer with left padding for batch processing
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name, 
            padding_side='left',
            local_files_only=True if self.config.model_name.startswith("/") else False
        )
        
        # Load model with appropriate settings
        model_kwargs = {
            "torch_dtype": self.config.get_torch_dtype(),
            "local_files_only": True if self.config.model_name.startswith("/") else False
        }
        
        if self.config.use_flash_attention:
            model_kwargs["attn_implementation"] = "flash_attention_2"
            
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            **model_kwargs
        )
        
        if self.config.device == "cuda":
            self.model = self.model.cuda()
            
        self.model.eval()
        
        # Get token IDs for yes/no
        self.token_false_id = self.tokenizer.convert_tokens_to_ids("no")
        self.token_true_id = self.tokenizer.convert_tokens_to_ids("yes")
        
        # Prepare prefix and suffix
        self.prefix = "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n"
        self.suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
        self.prefix_tokens = self.tokenizer.encode(self.prefix, add_special_tokens=False)
        self.suffix_tokens = self.tokenizer.encode(self.suffix, add_special_tokens=False)
        
        logger.info("Model loaded successfully")
        
    def format_instruction(self, instruction: Optional[str], query: str, doc: str) -> str:
        """Format the input according to Qwen3 reranker requirements"""
        if instruction is None:
            instruction = 'Given a web search query, retrieve relevant passages that answer the query'
        output = f"<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {doc}"
        return output
    
    def process_inputs(self, pairs: List[str]) -> Dict[str, torch.Tensor]:
        """Tokenize and prepare inputs for the model"""
        inputs = self.tokenizer(
            pairs, 
            padding=False, 
            truncation='longest_first',
            return_attention_mask=False, 
            max_length=self.config.max_length - len(self.prefix_tokens) - len(self.suffix_tokens)
        )
        
        # Add prefix and suffix tokens
        for i, ele in enumerate(inputs['input_ids']):
            inputs['input_ids'][i] = self.prefix_tokens + ele + self.suffix_tokens
            
        # Pad inputs
        inputs = self.tokenizer.pad(
            inputs, 
            padding=True, 
            return_tensors="pt", 
            max_length=self.config.max_length
        )
        
        # Move to device
        for key in inputs:
            inputs[key] = inputs[key].to(self.model.device)
            
        return inputs
    
    @torch.no_grad()
    def compute_scores(self, inputs: Dict[str, torch.Tensor]) -> List[float]:
        """Compute reranking scores"""
        batch_scores = self.model(**inputs).logits[:, -1, :]
        true_vector = batch_scores[:, self.token_true_id]
        false_vector = batch_scores[:, self.token_false_id]
        batch_scores = torch.stack([false_vector, true_vector], dim=1)
        batch_scores = torch.nn.functional.log_softmax(batch_scores, dim=1)
        scores = batch_scores[:, 1].exp().tolist()
        return scores
    
    def rerank(
        self, 
        query: str, 
        documents: List[str], 
        instruction: Optional[str] = None,
        return_documents: bool = False,
        top_k: Optional[int] = None
    ) -> Dict:
        """
        Rerank documents based on the query
        
        Args:
            query: The search query
            documents: List of documents to rerank
            instruction: Optional custom instruction
            return_documents: Whether to return the documents with scores
            top_k: Return only top k results
            
        Returns:
            Dictionary with scores and optionally reranked documents
        """
        # Format inputs
        pairs = [
            self.format_instruction(instruction, query, doc) 
            for doc in documents
        ]
        
        # Process and score
        inputs = self.process_inputs(pairs)
        scores = self.compute_scores(inputs)
        
        # Create results
        results = []
        for i, (score, doc) in enumerate(zip(scores, documents)):
            result = {
                "index": i,
                "score": score
            }
            if return_documents:
                result["document"] = doc
            results.append(result)
        
        # Sort by score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Apply top_k if specified
        if top_k is not None:
            results = results[:top_k]
            
        return {
            "results": results,
            "model": self.config.model_name,
            "query": query
        }