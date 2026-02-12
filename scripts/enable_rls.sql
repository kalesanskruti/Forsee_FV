-- Enable Row Level Security (RLS) for FORSEE Multi-Tenancy

-- 1. Enable RLS on core tables
ALTER TABLE organization ENABLE ROW LEVEL SECURITY;
ALTER TABLE "user" ENABLE ROW LEVEL SECURITY;
ALTER TABLE asset ENABLE ROW LEVEL SECURITY;
ALTER TABLE asset_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE inspection ENABLE ROW LEVEL SECURITY;
ALTER TABLE outbox_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE ml_model ENABLE ROW LEVEL SECURITY;

-- 2. Create Isolation Policies
-- Assumption: org_id is the tenant identifier column

-- Organization policy: can only see own organization
CREATE POLICY tenant_isolation_policy_organization ON organization
USING (id = current_setting('app.current_tenant')::uuid);

-- User policy
CREATE POLICY tenant_isolation_policy_user ON "user"
USING (org_id = current_setting('app.current_tenant')::uuid);

-- Asset policy
CREATE POLICY tenant_isolation_policy_asset ON asset
USING (org_id = current_setting('app.current_tenant')::uuid);

-- Metadata policy
CREATE POLICY tenant_isolation_policy_metadata ON asset_metadata
USING (org_id = current_setting('app.current_tenant')::uuid);

-- Inspection policy
CREATE POLICY tenant_isolation_policy_inspection ON inspection
USING (org_id = current_setting('app.current_tenant')::uuid);

-- Outbox policy
CREATE POLICY tenant_isolation_policy_outbox ON outbox_event
USING (org_id = current_setting('app.current_tenant')::uuid);

-- ML Model policy
CREATE POLICY tenant_isolation_policy_ml_model ON ml_model
USING (org_id = current_setting('app.current_tenant')::uuid);

-- 3. Grant permissions (ensure app user can set session variable)
-- In a real prod env, the app user needs permission to call current_setting
