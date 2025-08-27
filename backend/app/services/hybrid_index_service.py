import tiktoken, traceback, torch, logging
from typing import List, Optional, Tuple
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class HybridIndexService:
    def __init__(self):
        # Use tiktoken for token counting and encoding
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.model = None
        self.vector_store = ""
        # Get model configuration from environment
        self.default_model_name = ""
        self.default_max_tokens = ""
        self.default_chunk_ratio = 0.9
        self.default_overlap_ratio = 0.05

    def _count_tokens(self, text: str) -> int:
        try:
            token_count = len(self.tokenizer.encode(text))
            logger.debug(f"Token count: {token_count}")
            return token_count
        except Exception as e:
            logger.error(f"Error counting tokens: {str(e)}")
            return len(text.split())

    def _get_model_max_tokens(self, model_name: str) -> int:
        max_tokens = self.default_max_tokens
        logger.debug(f"Max tokens for model {model_name}: {max_tokens}")
        return max_tokens

    def _get_optimal_chunk_config(self, model_name: str) -> tuple[int, int]:
        max_tokens = self._get_model_max_tokens(model_name)
        chunk_size = int(max_tokens * self.default_chunk_ratio)
        chunk_overlap = int(chunk_size * self.default_overlap_ratio)
        logger.info(
            f"Chunk config for {model_name}: size={chunk_size}, overlap={chunk_overlap}"
        )
        return chunk_size, chunk_overlap

    def _chunk_text(self, text: str, model_name: str) -> List[str]:
        try:
            tokens = self.tokenizer.encode(text)
            chunk_size, chunk_overlap = self._get_optimal_chunk_config(model_name)
            chunks = []

            logger.info(
                f"Chunking text with {len(tokens)} tokens into chunks of size {chunk_size}"
            )

            for i in range(0, len(tokens), chunk_size - chunk_overlap):
                chunk_tokens = tokens[i : i + chunk_size]
                chunk_text = self.tokenizer.decode(chunk_tokens)
                if len(chunk_tokens) > 0:
                    chunks.append(chunk_text)
                    logger.debug(
                        f"Created chunk {len(chunks)} with {len(chunk_tokens)} tokens"
                    )

            logger.info(f"Successfully created {len(chunks)} chunks from original text")
            return chunks

        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            words = text.split()
            chunk_size = 1000
            chunks = []
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i : i + chunk_size])
                chunks.append(chunk)
            logger.info(f"Fallback chunking created {len(chunks)} chunks")
            return chunks

    def _load_model(self, model_name: str):
        try:
            if (
                self.model is None
                or getattr(self.model, "_model_name", None) != model_name
            ):
                logger.info(f"Loading model: {model_name}")
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.model = SentenceTransformer(
                    model_name, device=device, trust_remote_code=True
                )
                logger.info(f"Model {model_name} loaded successfully on {device}")
            else:
                logger.debug(f"Model {model_name} already loaded")
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {str(e)}")
            self.model = None

    async def embed_document_text(
        self, text: str, token_count: int, model_name: str | None = None
    ) -> Tuple[bool, Optional[List[List[float]]], str, Optional[List[str]]]:
        try:
            logger.info(f"Starting embedding for text with {token_count} tokens")

            if model_name is None:
                model_name_str = self.default_model_name
            else:
                model_name_str = model_name

            max_tokens = self._get_model_max_tokens(model_name_str)
            logger.info(f"Using model: {model_name_str}, max tokens: {max_tokens}")

            if token_count > max_tokens:
                logger.info(
                    f"Token count {token_count} exceeds limit {max_tokens}, chunking required"
                )

                chunks = self._chunk_text(text, model_name_str)
                if not chunks:
                    logger.error("No chunks created from text")
                    return (False, None, "Failed to chunk text", None)

                embeddings = []
                self._load_model(model_name_str)

                if self.model is None:
                    logger.error("Model failed to load")
                    return (
                        False,
                        None,
                        "SentenceTransformer model is not loaded",
                        None,
                    )

                logger.info(f"Processing {len(chunks)} chunks for embedding")
                for i, chunk in enumerate(chunks):
                    try:
                        chunk_tokens = self._count_tokens(chunk)
                        if chunk_tokens > max_tokens:
                            logger.warning(
                                f"Chunk {i} still too large ({chunk_tokens} tokens), truncating"
                            )
                            chunk_token_list = self.tokenizer.encode(chunk)[:max_tokens]
                            chunk = self.tokenizer.decode(chunk_token_list)

                        logger.debug(
                            f"Embedding chunk {i+1}/{len(chunks)} with {chunk_tokens} tokens"
                        )
                        chunk_embedding = self.model.encode(
                            chunk, convert_to_tensor=False
                        )
                        embeddings.append(chunk_embedding.tolist())

                    except Exception as chunk_error:
                        logger.error(f"Error embedding chunk {i}: {str(chunk_error)}")
                        continue

                if not embeddings:
                    logger.error("No embeddings generated from chunks")
                    return (
                        False,
                        None,
                        "Failed to generate embeddings from chunks",
                        None,
                    )

                logger.info(
                    f"Successfully generated {len(embeddings)} embeddings from {len(chunks)} chunks"
                )
                return (
                    True,
                    embeddings,
                    f"Success: Chunked embedding generated from {len(chunks)} chunks for {token_count} tokens",
                    chunks,
                )

            else:
                logger.info("Generating single embedding for small document")
                self._load_model(model_name_str)
                if self.model is None:
                    logger.error("Model failed to load")
                    return (
                        False,
                        None,
                        "SentenceTransformer model is not loaded",
                        None,
                    )

                embedding = self.model.encode(text, convert_to_tensor=False)
                logger.info(
                    f"Single embedding generated successfully for {token_count} tokens"
                )
                return (
                    True,
                    [embedding.tolist()],
                    f"Success: Single embedding generated for {token_count} tokens",
                    [text],
                )

        except Exception as e:
            logger.error(f"Error during embedding: {str(e)}", exc_info=True)
            return (False, None, f"Error during embedding: {str(e)}", None)

    async def delete_document_if_exists(
        self, collection_name: str, filter: dict
    ) -> bool:
        try:
            logger.info(
                f"Deleting documents from collection {collection_name} with filter {filter}"
            )
            await self.vector_store.delete_documents(filter, collection_name)
            logger.info("Documents deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error during document deletion: {str(e)}")
            return False

    async def vectorize_document(
        self,
        collection_name: str,
        embeds: List[List[float]],
        chunks: List[str],
        metadata: dict,
    ) -> bool:
        try:
            logger.info(
                f"Vectorizing {len(chunks)} chunks to collection {collection_name}"
            )
            for i, (chunk_text, embedding) in enumerate(zip(chunks, embeds)):
                chunk_metadata = {**metadata, "chunk_index": i}
                await self.vector_store.add_document(
                    text=chunk_text,
                    embedding=embedding,
                    metadata=chunk_metadata,
                    collection_name=collection_name,
                )
                logger.debug(f"Vectorized chunk {i+1}/{len(chunks)}")

            logger.info(f"Successfully vectorized all {len(chunks)} chunks")
            return True
        except Exception as e:
            logger.error(f"Error during vectorization: {str(e)}")
            return False

    async def check_model_exists(self, model_name: str) -> bool:
        exists = model_name == self.default_model_name
        logger.debug(f"Model {model_name} exists: {exists}")
        return exists

    async def health_check(self, model_name: str | None = None) -> Optional[str]:
        try:
            logger.info("Performing health check")
            if model_name:
                self._load_model(model_name)
            else:
                self._load_model(self.default_model_name)
            logger.info("Health check passed")
            return None
        except Exception as e:
            logger.error(f"Model health check failed: {str(e)}")
            return f"Model health check failed: {str(e)}"

    async def query_vectorized_documents(
        self,
        collection_name: str,
        query: str,
        top_k: int = 5,
        filters: Optional[dict] = None,
    ):
        try:
            logger.info(
                f"Querying collection {collection_name} with query: '{query[:100]}...' (top_k={top_k})"
            )
            if self.model is None:
                self._load_model(self.default_model_name)

            if self.model is None:
                logger.error("No model available for querying")
                return []

            embedding = self.model.encode(query, convert_to_tensor=False)
            results = await self.vector_store.fetch_document(
                query_embedding=embedding.tolist(),
                top_k=top_k,
                collection_name=collection_name,
                filters=filters,
            )
            logger.debug(f"Query returned {results} results")
            return results
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Error during document querying: {str(e)}")
            return []


hybrid_service = HybridIndexService()
