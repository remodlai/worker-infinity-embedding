import json
import sys
sys.path.append('src')

# Import the handler
from handler import handler

# Test data
test_job = {
    "input": {
        "query": "Which product offers the best warranty coverage?",
        "documents": [
            "Product A comes with a comprehensive 2-year warranty covering all parts and labor",
            "Product B includes a lifetime warranty but only covers manufacturing defects",
            "Product C has a 90-day limited warranty with no coverage for wear and tear",
            "Product D offers extended warranty options up to 5 years for additional cost",
            "Product E provides 1-year standard warranty with free shipping for repairs"
        ],
        "return_documents": True,
        "top_k": 3
    }
}

print("Testing Qwen3 Reranker...")
print(f"Query: {test_job['input']['query']}")
print(f"Number of documents: {len(test_job['input']['documents'])}")
print("-" * 50)

# Run the handler
result = handler(test_job)

# Print results
print(json.dumps(result, indent=2))