export interface BazaarType {
  id: string;
  tenant_id: string;
  market_profile_id: string | null;
  name: string;
  slug: string;
  code: string;
  description: string | null;
  bazaar_type: string;
  geom: string | null;
  bounding_box: Record<string, unknown> | null;
  address: string | null;
  latitude: number | null;
  longitude: number | null;
  area_ha: number | null;
  store_count: number;
  status: string;
  established_date: string | null;
  regulator_notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  tax_id: string | null;
  legal_form: string | null;
  address: string | null;
  phone: string | null;
  email: string | null;
  registration_number: string | null;
  province: string | null;
  city: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BazaarTrustee {
  id: string;
  bazaar_id: string;
  tenant_id: string;
  user_id: string;
  full_name: string;
  national_id: string | null;
  role: string;
  position: number;
  phone: string | null;
  email: string | null;
  is_approved: boolean;
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DigitalSignature {
  id: string;
  bazaar_id: string;
  trustee_id: string;
  tenant_id: string;
  step_number: number;
  agreement_type: string;
  signature_hex: string;
  pq_public_hex: string;
  ciphertext_hex: string | null;
  shared_secret_hex: string | null;
  algorithm: string;
  kem_algorithm: string | null;
  signed_at: string | null;
  is_valid: boolean;
  verified_at: string | null;
  created_at: string;
}

export interface MarketProfile {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  region_type: string;
  center_lat: number | null;
  center_lon: number | null;
  coverage_radius_m: number | null;
  bazaar_count: number;
  store_count: number;
  established_date: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
