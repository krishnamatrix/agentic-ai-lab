INSERT INTO companies (
    id,
    name,
    description,
    industry,
    revenue_usd,
    employees
)
VALUES
(
    '11111111-1111-1111-1111-111111111111',
    'Acme Corporation',
    'A leading provider of innovative solutions.',
    'Business',
    1000000000,
    5000
),
(
    '22222222-2222-2222-2222-222222222222',
    'Globex',
    'A global financial services company.',
    'Finance',
    750000000,
    3000
),
(
    '33333333-3333-3333-3333-333333333333',
    'Initech',
    'Enterprise software provider.',
    'Software',
    250000000,
    1200
)
ON CONFLICT (id) DO NOTHING;


INSERT INTO people (
    id,
    company_id,
    name,
    role,
    email
)
VALUES
(
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    '11111111-1111-1111-1111-111111111111',
    'John Doe',
    'CEO',
    'john.doe@acme.example'
),
(
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    '11111111-1111-1111-1111-111111111111',
    'Jane Smith',
    'VP of Engineering',
    'jane.smith@acme.example'
),
(
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    '22222222-2222-2222-2222-222222222222',
    'Bob Wilson',
    'CTO',
    'bob.wilson@globex.example'
)
ON CONFLICT (id) DO NOTHING;


INSERT INTO interactions (
    id,
    company_id,
    person_id,
    interaction_type,
    subject,
    content,
    occurred_at
)
VALUES
(
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    '11111111-1111-1111-1111-111111111111',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'meeting',
    'Enterprise Platform Discussion',
    'Acme is evaluating our enterprise platform. They want a product demonstration and requested pricing information.',
    NOW() - INTERVAL '3 days'
),
(
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    '11111111-1111-1111-1111-111111111111',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'email',
    'Technical Architecture',
    'Jane requested details about security, SSO and integration capabilities.',
    NOW() - INTERVAL '1 day'
),
(
    'ffffffff-ffff-ffff-ffff-ffffffffffff',
    '22222222-2222-2222-2222-222222222222',
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'meeting',
    'Initial Discussion',
    'Globex is interested in improving operational efficiency.',
    NOW() - INTERVAL '10 days'
)
ON CONFLICT (id) DO NOTHING;