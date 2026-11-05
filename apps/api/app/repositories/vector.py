from app.db.connection import get_connection


class VectorRepository:

    def search_interactions(
        self,
        embedding: list[float],
        limit: int = 5,
        company_name: str | None = None,
        min_similarity: float = 0.0,
    ) -> list[dict]:

        query = """
            SELECT
                interaction_id,
                company_name,
                person_name,
                content,
                1 - (embedding <=> %s::vector)
                    AS similarity
            FROM interaction_embeddings
            WHERE 1 - (embedding <=> %s::vector) >= %s
        """

        params: list[object] = [
            embedding,
            embedding,
            min_similarity,
        ]

        if company_name:
            query += """
                AND LOWER(company_name) LIKE LOWER(%s)
            """
            params.append(f"%{company_name}%")

        query += """
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """

        params.extend([
            embedding,
            limit,
        ])

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

        return [
            {
                "interaction_id": str(row[0]),
                "company_name": row[1],
                "person_name": row[2],
                "content": row[3],
                "similarity": float(row[4]),
            }
            for row in rows
        ]