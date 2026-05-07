"""Check Neo4j Aura for nodes and relationships."""
import asyncio
from neo4j import AsyncGraphDatabase

URI = "neo4j+s://bb266240.databases.neo4j.io"
USER = "bb266240"
PASSWORD = "NhltA1Mu-D6JizXUkG7QNKSExlL7bT3CNdZWMcWpJc8"
DB = "bb266240"


async def check():
    driver = AsyncGraphDatabase.driver(URI, auth=(USER, PASSWORD))
    async with driver.session(database=DB) as session:
        # Count nodes
        result = await session.run("MATCH (n) RETURN count(n) as node_count")
        record = await result.single()
        print(f"Total nodes: {record['node_count']}")

        # Count relationships
        result = await session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
        record = await result.single()
        print(f"Total relationships: {record['rel_count']}")

        # Node labels
        result = await session.run("MATCH (n) RETURN DISTINCT labels(n) as labels, count(n) as cnt")
        print("\nNode labels:")
        async for record in result:
            print(f"  {record['labels']}: {record['cnt']}")

        # Relationship types
        result = await session.run("MATCH ()-[r]->() RETURN DISTINCT type(r) as rel_type, count(r) as cnt")
        print("\nRelationship types:")
        async for record in result:
            print(f"  {record['rel_type']}: {record['cnt']}")

        # Sample a few relationships
        result = await session.run(
            "MATCH (a)-[r]->(b) RETURN labels(a)[0] as from_label, type(r) as rel, labels(b)[0] as to_label LIMIT 10"
        )
        print("\nSample relationships (first 10):")
        async for record in result:
            print(f"  ({record['from_label']})-[:{record['rel']}]->({record['to_label']})")

    await driver.close()
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(check())
