from config import EmbeddingServiceConfig
from infinity_emb.engine import AsyncEngineArray, EngineArgs
from utils import (
    OpenAIModelInfo,
    ModelInfo,
    list_embeddings_to_response,
    to_rerank_response,
)

import asyncio


class EmbeddingService:
    def __init__(self):
        self.config = EmbeddingServiceConfig()
        engine_args = []
        for model_name, batch_size, dtype in zip(
            self.config.model_names, self.config.batch_sizes, self.config.dtypes
        ):
            engine_args.append(
                EngineArgs(
                    model_name_or_path=model_name,
                    batch_size=batch_size,
                    engine=self.config.backend,
                    dtype=dtype,
                    model_warmup=False,
                    lengths_via_tokenize=True,
                )
            )

        self.engine_array = AsyncEngineArray.from_args(engine_args)
        self.is_running = False
        self.sepamore = asyncio.Semaphore(1)

    async def start(self):
        """starts the engine background loop"""
        async with self.sepamore:
            if not self.is_running:
                await self.engine_array.astart()
                self.is_running = True

    async def stop(self):
        """stops the engine background loop"""
        async with self.sepamore:
            if self.is_running:
                await self.engine_array.astop()
                self.is_running = False

    async def route_openai_models(self) -> OpenAIModelInfo:
        return OpenAIModelInfo(
            data=[ModelInfo(id=model_id, stats={}) for model_id in self.list_models()]
        ).model_dump()

    def list_models(self) -> list[str]:
        return list(self.engine_array.engines_dict.keys())

    async def route_openai_get_embeddings(
        self,
        embedding_input: str | list[str],
        model_name: str,
        return_as_list: bool = False,
        instruction: str | None = None,
        prompt_type: str | None = None,
    ):
        """returns embeddings for the input text"""
        if not self.is_running:
            await self.start()
        if not isinstance(embedding_input, list):
            embedding_input = [embedding_input]

        # Apply instruction if provided
        if instruction or prompt_type:
            processed_input = []
            for text in embedding_input:
                # Build the instruction prefix
                if instruction:
                    # Custom instruction provided
                    prefix = f"Instruct: {instruction}\nQuery: "
                elif prompt_type == "query":
                    # Use default query instruction for Qwen3
                    prefix = "Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery: "
                elif prompt_type == "document":
                    # Documents typically don't have instructions for Qwen3
                    prefix = ""
                else:
                    prefix = ""
                
                processed_input.append(prefix + text)
            embedding_input = processed_input

        embeddings, usage = await self.engine_array[model_name].embed(embedding_input)
        if return_as_list:
            return [
                list_embeddings_to_response(embeddings, model=model_name, usage=usage)
            ]
        else:
            return list_embeddings_to_response(
                embeddings, model=model_name, usage=usage
            )

    async def infinity_rerank(
        self, query: str, docs: str, return_docs: str, model_name: str
    ):
        """Rerank the documents based on the query"""
        if not self.is_running:
            await self.start()
        scores, usage = await self.engine_array[model_name].rerank(
            query=query, docs=docs, raw_scores=False
        )
        if not return_docs:
            docs = None
        return to_rerank_response(
            scores=scores, documents=docs, model=model_name, usage=usage
        )
