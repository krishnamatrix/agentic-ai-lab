CREATE TABLE companies (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT,
    employee_count INTEGER,
    annual_revenue NUMERIC,
    headquarters TEXT,
    website TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE people (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    title TEXT,
    email TEXT,
    phone TEXT,
    location TEXT,
    linkedin_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE interactions (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    person_id UUID REFERENCES people(id),
    interaction_type TEXT NOT NULL,
    subject TEXT,
    content TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE opportunities (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    name TEXT NOT NULL,
    stage TEXT NOT NULL,
    value NUMERIC,
    probability NUMERIC,
    expected_close_date DATE,
    owner TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE notes (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    person_id UUID REFERENCES people(id),
    content TEXT NOT NULL,
    author TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);