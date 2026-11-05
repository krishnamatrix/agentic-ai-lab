import asyncio

from app.db.connection import get_connection
from app.embeddings.ollama import OllamaEmbeddingClient


def get_interactions() -> list[dict]:

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    i.id,
                    c.id as company_id,
                    p.id as person_id,
                    c.name AS company_name,
                    p.name AS person_name,
                    p.role,
                    i.interaction_type,
                    i.subject,
                    i.content,
                    i.occurred_at
                FROM interactions i
                JOIN companies c
                    ON c.id = i.company_id
                LEFT JOIN people p
                    ON p.id = i.person_id
                ORDER BY i.occurred_at
                """
            )

            rows = cursor.fetchall()

    return [
        {
            "id": str(row[0]),
            "company_id": str(row[1]) if row[1] is not None else None,
            "person_id": str(row[2]) if row[2] is not None else None,
            "company_name": row[3],
            "person_name": row[4],
            "role": row[5],
            "interaction_type": row[6],
            "subject": row[7],
            "content": row[8],
            "occurred_at": row[9].isoformat(),
        }
        for row in rows
    ]


def interaction_to_text(row: dict) -> str:

    return f"""
Company: {row["company_name"]}
Person: {row["person_name"]}
Role: {row["role"]}
Interaction type: {row["interaction_type"]}
Subject: {row["subject"]}
Content: {row["content"]}
Date: {row["occurred_at"]}
""".strip()


async def main():

    embedding_client = OllamaEmbeddingClient()

    interactions = get_interactions()

    print(f"Found {len(interactions)} interactions")

    with get_connection() as connection:
        with connection.cursor() as cursor:

            for interaction in interactions:

                text = interaction_to_text(interaction)

                print(
                    f"Embedding {interaction}"
                )

                embedding = await embedding_client.embed(text)

                cursor.execute(
                    """
                    INSERT INTO interaction_embeddings (
                        interaction_id,
                        content,
                        embedding,
                        company_id,
                        company_name,
                        person_id,
                        person_name
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (interaction_id)
                    DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        company_id = EXCLUDED.company_id,
                        company_name = EXCLUDED.company_name,
                        person_id = EXCLUDED.person_id,
                        person_name = EXCLUDED.person_name
                    """,
                    (
                        interaction["id"],
                        text,
                        embedding,
                        interaction["company_id"],
                        interaction["company_name"],
                        interaction["person_id"],
                        interaction["person_name"],
                    ),
                )

        connection.commit()

    print("Indexing complete")


if __name__ == "__main__":
    asyncio.run(main())