CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    industry TEXT,
    revenue_usd NUMERIC,
    employees INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS people (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL REFERENCES companies(id),
    name TEXT NOT NULL,
    role TEXT,
    email TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_companies_name
    ON companies (LOWER(name));

CREATE INDEX IF NOT EXISTS idx_people_company_id
    ON people (company_id);

CREATE TABLE IF NOT EXISTS interactions (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    person_id UUID REFERENCES people(id),
    interaction_type TEXT NOT NULL,
    subject TEXT,
    content TEXT,
    occurred_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_interactions_company
    ON interactions(company_id);

CREATE INDEX IF NOT EXISTS idx_interactions_person
    ON interactions(person_id);

CREATE INDEX IF NOT EXISTS idx_interactions_occurred_at
    ON interactions(occurred_at DESC);