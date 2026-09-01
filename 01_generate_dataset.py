"""Script to sample tokens from an LLM via Ollama and generate graph JSON files."""

import argparse
import json
import requests
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Set


class LLMSampler:
    """Handles communications with the Ollama server to sample tokens and
    retrieve logits/logprobs."""

    def __init__(self, base_url: str, model_name: str) -> None:
        """
        Initialize the LLMSampler instance.

        :param base_url: The URL endpoint for Ollama API.
        :param model_name: Name of the target model loaded in Ollama.
        """
        self.base_url: str = base_url
        self.model_name: str = model_name

    def sample_token_with_probability(
        self, prompt: str, options: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[float]]:
        """
        Sends a request to the LLM to get the next predicted token along with
        its probability.

        :param prompt: The input text context.
        :param options: Sampling parameters (temperature, top_k, logprobs, etc.).
        :return: A tuple containing (sampled_token, token_probability).
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "raw": True,
            "think": False,
            "options": options,
        }
        try:
            response = requests.post(self.base_url, json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                token: str = data.get("response", "")

                probability: Optional[float] = None
                logprobs = data.get("logprobs")
                if logprobs and "sample_logits" in logprobs:
                    sample = logprobs["sample_logits"][0]
                    logprob = sample.get("logprob", 0)
                    probability = float(sample.get("prob", np.exp(logprob)))

                return token, probability
        except requests.RequestException as e:
            print(f"Ollama API request failed: {e}")

        return None, None


class TokenGraphGenerator:
    """Generates an in-memory token tree structure and exports nodes and
    edges to JSON files."""

    def __init__(
        self,
        sampler: LLMSampler,
        initial_prompt: str,
        depth: int,
        attempts_per_node: int,
        llm_config: Dict[str, Any],
    ) -> None:
        """
        Initialize the TokenGraphGenerator instance.

        :param sampler: Instance of LLMSampler to query tokens.
        :param initial_prompt: Root text prompt to expand.
        :param depth: Number of layers (depth) to explore.
        :param attempts_per_node: Sampling attempts per node at each layer.
        :param llm_config: LLM sampling parameters.
        """
        self.sampler: LLMSampler = sampler
        self.initial_prompt: str = initial_prompt
        self.depth: int = depth
        self.attempts_per_node: int = attempts_per_node
        self.llm_config: Dict[str, Any] = llm_config

    def generate_and_export(
        self,
        nodes_file: str,
        edges_file: str,
    ) -> None:
        """
        Explores token expansions level-by-level and saves the graph
        structures to JSON files.

        :param nodes_file: Path to output JSON file for graph nodes.
        :param edges_file: Path to output JSON file for graph edges.
        """
        print(f"Generating token tree in memory (Depth={self.depth})...")

        nodes: Dict[str, Dict[str, Any]] = {
            self.initial_prompt: {
                "name": self.initial_prompt,
                "is_root": True,
                "num_visits": 1,
                "probability": 1.0,
            }
        }
        edges: Dict[Tuple[str, str], int] = {}
        current_layer_nodes: List[str] = [self.initial_prompt]

        for layer in range(self.depth):
            print(f"   -> Processing Layer {layer + 1}/{self.depth}...")
            next_layer_nodes: Set[str] = set()

            for parent_context in current_layer_nodes:
                for _ in range(self.attempts_per_node):
                    token, prob = self.sampler.sample_token_with_probability(
                        parent_context, self.llm_config
                    )
                    if not token:
                        continue

                    child_context: str = parent_context + token

                    if child_context not in nodes:
                        nodes[child_context] = {
                            "name": token,
                            "is_root": False,
                            "num_visits": 1,
                            "probability": prob,
                        }
                    else:
                        nodes[child_context]["num_visits"] += 1

                    edge_key: Tuple[str, str] = (parent_context, child_context)
                    edges[edge_key] = edges.get(edge_key, 0) + 1
                    next_layer_nodes.add(child_context)

            current_layer_nodes = list(next_layer_nodes)

        nodes_list: List[Dict[str, Any]] = [
            {"id_contexto": k, **v} for k, v in nodes.items()
        ]
        edges_list: List[Dict[str, Any]] = [
            {"origin": k[0], "destination": k[1], "weight": v} for k, v in edges.items()
        ]

        with open(nodes_file, "w", encoding="utf-8") as f:
            json.dump(nodes_list, f, ensure_ascii=False, indent=2)

        with open(edges_file, "w", encoding="utf-8") as f:
            json.dump(edges_list, f, ensure_ascii=False, indent=2)

        print(
            f"Successfully saved {len(nodes_list)} nodes "
            f"and {len(edges_list)} edges to disk."
        )


def main() -> None:
    """Parses arguments and runs the graph generation pipeline."""
    parser = argparse.ArgumentParser(
        description="Sample tokens from an LLM and generate graph JSON files."
    )
    parser.add_argument(
        "--ollama-url",
        type=str,
        default="http://localhost:11434/api/generate",
        help="Ollama API URL",
    )
    parser.add_argument(
        "--model", type=str, default="qwen3.5:0.8b", help="Model name in Ollama"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="All you need is",
        help="Initial prompt root",
    )
    parser.add_argument(
        "--depth", type=int, default=5, help="Number of layers to explore"
    )
    parser.add_argument(
        "--attempts",
        type=int,
        default=5,
        help="Sampling attempts per node",
    )
    parser.add_argument(
        "--temperature", type=float, default=1.0, help="Sampling temperature"
    )
    parser.add_argument(
        "--top-k", type=int, default=50, help="Top-K sampling constraint"
    )
    parser.add_argument(
        "--nodes-file",
        type=str,
        default="nodes.json",
        help="Output nodes JSON file path",
    )
    parser.add_argument(
        "--edges-file",
        type=str,
        default="edges.json",
        help="Output edges JSON file path",
    )

    args = parser.parse_args()

    llm_config = {
        "temperature": args.temperature,
        "top_k": args.top_k,
        "num_predict": 1,
        "logprobs": True,
    }

    sampler = LLMSampler(base_url=args.ollama_url, model_name=args.model)
    generator = TokenGraphGenerator(
        sampler=sampler,
        initial_prompt=args.prompt,
        depth=args.depth,
        attempts_per_node=args.attempts,
        llm_config=llm_config,
    )
    generator.generate_and_export(
        nodes_file=args.nodes_file, edges_file=args.edges_file
    )


if __name__ == "__main__":
    main()
