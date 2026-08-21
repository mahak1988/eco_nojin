-- Eco Nojin Platform Tables
-- Created: 2026-08-19 23:31:12
-- These tables COMPLEMENT existing eco_nojin tables
-- No conflicts with existing schema

-- =============================================================================
-- ENUMS (prefixed with 'platform_' to avoid conflicts)
-- =============================================================================

DO $$ BEGIN
    CREATE TYPE platform_user_role AS ENUM (
        'farmer', 'seller', 'tour_guide', 'host', 'artisan',
        'landscape_manager', 'council_member', 'admin', 'auditor'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE platform_project_status AS ENUM (
        'draft', 'submitted', 'verified', 'active', 'retired'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- =============================================================================
-- TABLES
-- =============================================================================

CREATE TABLE IF NOT EXISTS platform_landscapes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    country TEXT NOT NULL,
    province TEXT,
    geo_boundary JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS platform_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    phone TEXT UNIQUE,
    display_name TEXT,
    avatar_url TEXT,
    bio TEXT,
    language TEXT DEFAULT 'fa',
    kyc_level INT DEFAULT 0,
    wallet_address TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS platform_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES platform_profiles(id) ON DELETE CASCADE,
    landscape_id UUID REFERENCES platform_landscapes(id) ON DELETE CASCADE,
    role platform_user_role NOT NULL DEFAULT 'farmer',
    approved BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, landscape_id)
);

CREATE TABLE IF NOT EXISTS platform_carbon_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    landscape_id UUID REFERENCES platform_landscapes(id),
    owner_id UUID REFERENCES platform_profiles(id),
    name TEXT NOT NULL,
    project_type TEXT NOT NULL,
    area_ha DECIMAL(10,2) NOT NULL,
    duration_years INT NOT NULL,
    status platform_project_status DEFAULT 'draft',
    credits_issued DECIMAL(10,2) DEFAULT 0,
    credits_retired DECIMAL(10,2) DEFAULT 0,
    tx_hash TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS platform_carbon_credits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES platform_carbon_projects(id) ON DELETE CASCADE,
    owner_id UUID REFERENCES platform_profiles(id),
    amount DECIMAL(10,2) NOT NULL,
    issued_at TIMESTAMPTZ DEFAULT NOW(),
    retired BOOLEAN DEFAULT FALSE,
    retired_at TIMESTAMPTZ,
    tx_hash TEXT
);

-- =============================================================================
-- RLS (Row Level Security)
-- =============================================================================

ALTER TABLE platform_landscapes ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform_carbon_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform_carbon_credits ENABLE ROW LEVEL SECURITY;

-- Read policies
CREATE POLICY "public_read_landscapes" ON platform_landscapes FOR SELECT USING (true);
CREATE POLICY "own_read_profile" ON platform_profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "public_read_credits" ON platform_carbon_credits FOR SELECT USING (true);

-- Write policies
CREATE POLICY "own_update_profile" ON platform_profiles FOR UPDATE USING (auth.uid() = id);

-- =============================================================================
-- INDEXES
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_landscapes_slug ON platform_landscapes(slug);
CREATE INDEX IF NOT EXISTS idx_profiles_wallet ON platform_profiles(wallet_address);
CREATE INDEX IF NOT EXISTS idx_carbon_projects_status ON platform_carbon_projects(status);
CREATE INDEX IF NOT EXISTS idx_carbon_credits_project ON platform_carbon_credits(project_id);
