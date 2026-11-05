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

-- ============================================================
-- ACME
-- ============================================================

(
    '10000000-0000-0000-0000-000000000001',
    '11111111-1111-1111-1111-111111111111',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'meeting',
    'Enterprise Platform Discussion',
    'Acme is evaluating our enterprise platform. They want a product demonstration and requested pricing information.',
    NOW() - INTERVAL '3 days'
),

(
    '10000000-0000-0000-0000-000000000002',
    '11111111-1111-1111-1111-111111111111',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'email',
    'Technical Architecture',
    'Jane requested details about security, SSO and integration capabilities.',
    NOW() - INTERVAL '1 day'
),

(
    '10000000-0000-0000-0000-000000000003',
    '11111111-1111-1111-1111-111111111111',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'meeting',
    'Deployment Architecture',
    'John discussed deployment options and asked whether the platform can be deployed in Acme managed cloud infrastructure.',
    NOW() - INTERVAL '5 days'
),

(
    '10000000-0000-0000-0000-000000000004',
    '11111111-1111-1111-1111-111111111111',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'meeting',
    'Identity and Access Management',
    'Jane wants to understand how enterprise identity providers integrate with the platform and whether SSO can be enforced for all users.',
    NOW() - INTERVAL '7 days'
),

(
    '10000000-0000-0000-0000-000000000005',
    '11111111-1111-1111-1111-111111111111',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'email',
    'Commercial Proposal',
    'John requested information about enterprise pricing, volume discounts and the commercial terms for a large deployment.',
    NOW() - INTERVAL '8 days'
),

(
    '10000000-0000-0000-0000-000000000006',
    '11111111-1111-1111-1111-111111111111',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'meeting',
    'Integration Requirements',
    'Jane discussed integrating the platform with Acme internal applications through APIs and asked about supported integration patterns.',
    NOW() - INTERVAL '10 days'
),

(
    '10000000-0000-0000-0000-000000000007',
    '11111111-1111-1111-1111-111111111111',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'meeting',
    'Data Governance',
    'Acme asked where customer data is stored, what data residency options are available, and how regulatory requirements are supported.',
    NOW() - INTERVAL '12 days'
),

-- ============================================================
-- GLOBEX
-- ============================================================

(
    '20000000-0000-0000-0000-000000000001',
    '22222222-2222-2222-2222-222222222222',
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'meeting',
    'Initial Discussion',
    'Globex is interested in improving operational efficiency across its business processes.',
    NOW() - INTERVAL '10 days'
),

(
    '20000000-0000-0000-0000-000000000002',
    '22222222-2222-2222-2222-222222222222',
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'meeting',
    'Security Review',
    'Bob asked about security controls, authentication mechanisms and integration with existing identity infrastructure.',
    NOW() - INTERVAL '6 days'
),

(
    '20000000-0000-0000-0000-000000000003',
    '22222222-2222-2222-2222-222222222222',
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'email',
    'Analytics Requirements',
    'Globex wants better reporting and analytics to identify operational bottlenecks and measure process improvements.',
    NOW() - INTERVAL '4 days'
),

-- ============================================================
-- INITECH
-- ============================================================

(
    '30000000-0000-0000-0000-000000000001',
    '33333333-3333-3333-3333-333333333333',
    NULL,
    'meeting',
    'API Integration',
    'Initech is evaluating API integration capabilities and wants to connect the platform with several internal applications.',
    NOW() - INTERVAL '9 days'
),

(
    '30000000-0000-0000-0000-000000000002',
    '33333333-3333-3333-3333-333333333333',
    NULL,
    'meeting',
    'Pricing Discussion',
    'Initech requested information about subscription pricing and available licensing models.',
    NOW() - INTERVAL '2 days'
)

ON CONFLICT (id) DO NOTHING;