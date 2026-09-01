"""Script to parse generated JSON datasets and upload graph elements
into Neo4j."""

import argparse
import json
from typing import Dict, List, Any
from neo4j import GraphDatabase, Driver


class Neo4jGraphUploader:
    """Loads exported JSON graph datasets directly into a Neo4j Database."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        """
        Initialize the Neo4jGraphUploader instance.

        :param uri: Bolt URI for Neo4j database connection.
        :param user: Database user credential.
        :param password: Database password credential.
        """
        self.uri: str = uri
        self.user: str = user
        self.password: str = password

    def upload_from_files(
        self,
        nodes_file: str,
        edges_file: str,
    ) -> None:
        """
        Parses graph structure from JSON files and executes batch ingestion queries in Neo4j.

        :param nodes_file: Path to source JSON file containing nodes.
        :param edges_file: Path to source JSON file containing edges.
        """
        with open(nodes_file, "r", encoding="utf-8") as f:
            nodes_data: List[Dict[str, Any]] = json.load(f)
        with open(edges_file, "r", encoding="utf-8") as f:
            edges_data: List[Dict[str, Any]] = json.load(f)

        print("Uploading node and edge datasets into Neo4j...")
        driver: Driver = GraphDatabase.driver(
            self.uri, auth=(self.user, self.password)
        )

        with driver.session() as session:
            # Batch Node Insertion (Including probability metric)
            session.run(
                """
                UNWIND $batch_nodes AS node
                MERGE (n:Token {id_contexto: node.id_contexto})
                SET n.name = node.name, 
                    n.num_visits = node.num_visits,
                    n.probability = node.probability
                WITH n, node
                WHERE node.is_root = true
                SET n:Root
                """,
                batch_nodes=nodes_data,
            )

            # Batch Edge Insertion
            session.run(
                """
                UNWIND $batch_edges AS edge
                MATCH (origin:Token {id_contexto: edge.origin})
                MATCH (destination:Token {id_contexto: edge.destination})
                MERGE (origin)-[r:NEXT_TOKEN]->(destination)
                SET r.weight = edge.weight
                """,
                batch_edges=edges_data,
            )

        driver.close()
        print("Neo4j database batch ingestion completed successfully!")


def main() -> None:
    """Parses arguments and performs Neo4j graph batch upload."""
    parser = argparse.ArgumentParser(
        description="Batch upload JSON graph dataset to Neo4j."
    )
    parser.add_argument(
        "--uri",
        type=str,
        default="bolt://localhost:7687",
        help="Neo4j connection Bolt URI",
    )
    parser.add_argument(
        "--user", type=str, default="neo4j", help="Neo4j database username"
    )
    parser.add_argument(
        "--password", type=str, default="password123", help="Neo4j user password"
    )
    parser.add_argument(
        "--nodes-file",
        type=str,
        default="nodes.json",
        help="Input nodes JSON file path",
    )
    parser.add_argument(
        "--edges-file",
        type=str,
        default="edges.json",
        help="Input edges JSON file path",
    )

    args = parser.parse_args()

    uploader = Neo4jGraphUploader(
        uri=args.uri, user=args.user, password=args.password
    )
    uploader.upload_from_files(
        nodes_file=args.nodes_file, edges_file=args.edges_file
    )


if __name__ == "__main__":
    main()