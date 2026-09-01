# Token Tree: LLM Sampling & Generation Visualizer

![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![Package Manager](https://img.shields.io/badge/uv-managed-purple.svg)
![Database](https://img.shields.io/badge/Neo4j-5.12--community-008CC1.svg)
![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)

This repository contains the implementation and experimental setup for the Substack post: **["Why Do LLM’s Need Token Sampling, and How Do They Generate Text?"](https://cesarzammar.substack.com/p/why-do-llms-need-token-sampling-and?r=2iqk5m&utm_campaign=post&utm_medium=web&showWelcomeOnShare=true)** written by **Cesar Zamora**.

The project provides a pipeline to sample autoregressive text generation paths from a local LLM (via **Ollama**) and map probabilistic token branching into a directed hierarchical graph structure (**Token Tree**). Data can be loaded into **Neo4j** for Cypher graph analysis and rendered visually using **NetworkX** / **Matplotlib**.

---

## 🛠️ Prerequisites

1. **Python 3.11** and the [`uv`](https://github.com/astral-sh/uv) package manager.
2. **Docker** and **Docker Compose** (for running the Neo4j instance).
3. **Ollama** running locally on `http://localhost:11434` with the `qwen3.5:0.8b` model pulled:
   ```bash
   ollama pull qwen3.5:0.8b
   ```

---

## Installation & Setup

All environment setups and tasks are automated using a parameterized `Makefile`.

1. **Clone the repository and install dependencies:**
   ```bash
   make all
   ```
   *This command checks/installs `uv`, pins Python to `3.11.14`, and syncs virtual environment dependencies.*

2. **Start the Neo4j database:**
   ```bash
   make up
   ```
   *Spins up a Neo4j 5.12 Docker container. The web console will be available at `http://localhost:7474` (User: `neo4j`, Password: `password123`).*

---

## 💻 Workflow & Usage

The pipeline follows a 3-step execution flow:

```
[ Ollama (qwen3.5:0.8b) ] ──(01_generate_dataset.py)──> [ nodes.json / edges.json ]
                                                              │
                                     ┌────────────────────────┴────────────────────────┐
                                     ▼                                                 ▼
                         (02_upload_neo4j.py)                               (03_render_networkx.py)
                                     │                                                 │
                                     ▼                                                 ▼
                             [ Neo4j Database ]                                [ Matplotlib Visual ]
```

### 1. Sample Token Tree (Ollama Generation)
Run the recursive autoregressive sampling script to produce `nodes.json` and `edges.json`:
```bash
make sample-token-graph
```
*Or execute the script directly with custom parameters:*
```bash
uv run 01_generate_dataset.py \
  --ollama-url "http://localhost:11434/api/generate" \
  --model "qwen3.5:0.8b" \
  --prompt "All you need is" \
  --depth 5 \
  --attempts 5 \
  --temperature 0.3 \
  --top-k 50 \
  --nodes-file "nodes.json" \
  --edges-file "edges.json"
```

### 2. Ingest Data into Neo4j
Batch upload node and edge datasets into the graph database:
```bash
make populate-token-graph
```
or just run:

```bash
uv run 02_upload_neo4j.py \
  --uri "bolt://localhost:7687" \
  --user "neo4j" \
  --password "password123" \
  --nodes-file "nodes.json" \
  --edges-file "edges.json"
```

### 3. Render Graph with NetworkX
Generate a hierarchical plot where edge width and color intensity represent token traversal frequencies:
```bash
make render-graph
```

---

## Cypher Query Example (Neo4j)

Once the database is populated, open `http://localhost:7474` and run Cypher queries to analyze generated text paths.

**Example:** Check if the model sampled the classic Beatles phrase *"All you need is love"*:
```cypher
MATCH path = (root:Root {name: "All you need is"})-[:NEXT_TOKEN*]->(next:Token {name: "love"})
RETURN path;
```

Please review `/src/querys.cypher` for more exploratory querys

---

## Repository Structure

```text
.
├── 01_generate_dataset.py   # Recursively samples tokens via Ollama API and outputs JSON files.
├── 02_upload_neo4j.py       # Batch ingests nodes.json and edges.json into Neo4j.
├── 03_render_networkx.py    # Builds and renders the hierarchical tree using NetworkX & Matplotlib.
├── notebooks/
│   └── logits_pytorch.ipynb # PyTorch notebook demonstrating Logits, Softmax, Top-K, and Top-P operations.
├── docker-compose.yml       # Docker configuration for Neo4j 5.12.
├── Makefile                 # Environment management and execution tasks.
├── pyproject.toml           # Project dependencies managed via uv.
└── src
│   └── querys.cypher.       # Cypher Querys to explore the Token Tree in Neo4j
└── README.md
```

---

## Management Commands (`Makefile`)

| Command | Description |
| :--- | :--- |
| `make help` | Displays available targets in the Makefile. |
| `make up` / `make down` | Starts or stops the Neo4j Docker container. |
| `make clean-files-graph` | Removes generated `nodes.json` and `edges.json` files. |
| `make clean` | Removes the `.venv` virtual environment. |

---
