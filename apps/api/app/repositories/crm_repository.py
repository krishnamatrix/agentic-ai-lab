from app.db.connection import get_connection

class CRMRepository:
    def search_companies(
        self,
        name: str
    ) -> list[dict]:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                        SELECT
                            id,
                            name,
                            description,
                            industry,
                            revenue_usd,
                            employees
                        FROM companies
                        WHERE LOWER(name) LIKE LOWER(%s)
                        ORDER BY name
                        LIMIT 20
                    """,
                    [f"%{name}%"],
                )

                rows = cursor.fetchall()


        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "description": row[2],
                "industry": row[3],
                "revenue_usd": float(row[4])
                if row[4] is not None
                else None,
                "employees": row[5]
            }
            for row in rows
        ]

    
    def search_people(
        self,
        company_name: str | None = None,
        role: str | None = None,
        name: str | None = None,
        limit: int = 50,
    ) -> list[dict]:

        query = """
            SELECT
                p.id,
                p.name,
                c.name AS company_name,
                p.role,
                p.email
            FROM people p
            JOIN companies c
                ON c.id = p.company_id
            WHERE TRUE
        """

        params: list[object] = []

        if company_name:
            query += """
                AND LOWER(c.name) LIKE LOWER(%s)
            """
            params.append(f"%{company_name}%")

        if role:
            query += """
                AND LOWER(p.role) LIKE LOWER(%s)
            """
            params.append(f"%{role}%")

        if name:
            query += """
                AND LOWER(p.name) LIKE LOWER(%s)
            """
            params.append(f"%{name}%")

        query += """
            ORDER BY p.name
            LIMIT %s
        """

        params.append(limit)

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "company_name": row[2],
                "role": row[3],
                "email": row[4],
            }
            for row in rows
        ]

    def search_interactions(
        self,
        company_name: str | None = None,
        person_name: str | None = None,
        query_text: str | None = None,
        limit: int = 20,
    ) -> list[dict]:

        query = """
            SELECT
                i.id,
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
            WHERE TRUE
        """

        params: list[object] = []

        if company_name:
            query += """
                AND LOWER(c.name) LIKE LOWER(%s)
            """
            params.append(f"%{company_name}%")

        if person_name:
            query += """
                AND LOWER(p.name) LIKE LOWER(%s)
            """
            params.append(f"%{person_name}%")

        if query_text:
            query += """
                AND (
                    LOWER(i.subject) LIKE LOWER(%s)
                    OR LOWER(i.content) LIKE LOWER(%s)
                )
            """

            value = f"%{query_text}%"
            params.extend([value, value])

        query += """
            ORDER BY i.occurred_at DESC
            LIMIT %s
        """

        params.append(limit)

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

        return [
            {
                "id": str(row[0]),
                "company_name": row[1],
                "person_name": row[2],
                "role": row[3],
                "interaction_type": row[4],
                "subject": row[5],
                "content": row[6],
                "occurred_at": row[7].isoformat(),
            }
            for row in rows
        ]