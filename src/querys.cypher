// display graph

MATCH (n:Token)-[r:NEXT_TOKEN]->(m:Token)
RETURN n, r, m
LIMIT 10;

// phrases sampled more times

MATCH path = (root:Root)-[:NEXT_TOKEN*0..]->(leaf:Token)
WHERE NOT (leaf)-[:NEXT_TOKEN]->()

WITH path,
     [node IN nodes(path) | node.name] AS palabras,
     [node IN nodes(path) | coalesce(node.num_visits, 0)] AS visitas

RETURN 
    reduce(phrase = "", w IN palabras | phrase + (CASE WHEN phrase = "" THEN "" ELSE " " END) + w) AS phrase_completa,
    reduce(suma = 0, v IN visitas | suma + v) AS total_num_visits,
    reduce(m = visitas[0], v IN visitas | CASE WHEN v < m THEN v ELSE m END) AS cuello_botella_visits
ORDER BY total_num_visits DESC
LIMIT 10;

// phrases formed
MATCH path = (root:Root)-[:NEXT_TOKEN*0..]->(leaf:Token)
WHERE NOT (leaf)-[:NEXT_TOKEN]->()
RETURN count(path) AS total_trayectorias;

// unique phrase formed
MATCH path = (root:Root)-[:NEXT_TOKEN*0..]->(leaf:Token)
WHERE NOT (leaf)-[:NEXT_TOKEN]->()
WITH [node IN nodes(path) | node.name] AS palabras
WITH reduce(s = "", w IN palabras | s + (CASE WHEN s = "" THEN "" ELSE " " END) + w) AS phrase
RETURN count(DISTINCT phrase) AS total_phrases_unicas;

// Verifying all you need is love
MATCH path = (root:Root {name: "All you need is"})-[:NEXT_TOKEN]->(next:Token {name: "love"})
RETURN count(path) > 0 AS existe, count(path) AS cuantas_veces;

// paths sample 1 time

MATCH path = (root:Root)-[:NEXT_TOKEN*0..]->(leaf:Token)
WHERE NOT (leaf)-[:NEXT_TOKEN]->()
  AND all(node IN nodes(path) WHERE coalesce(node.num_visits, 0) = 1)
RETURN 
    reduce(frase = "", w IN [n IN nodes(path) | n.name] | frase + (CASE WHEN frase = "" THEN "" ELSE " " END) + w) AS frase,
    [n IN nodes(path) | n.id_contexto] AS node_ids,
    length(path) AS path_length;

// delete the graph
MATCH (n) DETACH DELETE n;