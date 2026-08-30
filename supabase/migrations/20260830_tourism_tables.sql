-- Tourism (ecotourism) tables — generated from services/tourism/models
-- Run in Supabase SQL editor or psql
begin;
CREATE TABLE tourism_guides (
	id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	village_id VARCHAR(100) NOT NULL, 
	full_name VARCHAR(200) NOT NULL, 
	bio TEXT, 
	languages JSON, 
	specialties JSON, 
	license_number VARCHAR(100), 
	is_verified BOOLEAN, 
	insurance_provider VARCHAR(200), 
	insurance_policy_number VARCHAR(100), 
	insurance_expiry DATE, 
	total_tours INTEGER, 
	rating NUMERIC(3, 2), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_tourism_guides_user_id ON tourism_guides (user_id);

CREATE INDEX ix_tourism_guides_village_id ON tourism_guides (village_id);

CREATE TABLE tourism_tours (
	id VARCHAR(36) NOT NULL, 
	guide_id VARCHAR(36) NOT NULL, 
	village_id VARCHAR(100) NOT NULL, 
	title VARCHAR(300) NOT NULL, 
	slug VARCHAR(300) NOT NULL, 
	description TEXT, 
	tour_type tourismtourtype NOT NULL, 
	duration_hours INTEGER NOT NULL, 
	max_participants INTEGER, 
	min_participants INTEGER, 
	difficulty tourismdifficultylevel, 
	price_per_person NUMERIC(12, 2) NOT NULL, 
	currency VARCHAR(3), 
	includes JSON, 
	excludes JSON, 
	itinerary JSON, 
	meeting_point JSON, 
	images JSON, 
	safety_equipment JSON, 
	ecological_capacity INTEGER, 
	current_bookings INTEGER, 
	status VARCHAR(20), 
	is_regenerative BOOLEAN, 
	regenerative_activity TEXT, 
	approved_by VARCHAR(36), 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	total_bookings INTEGER, 
	rating NUMERIC(3, 2), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(guide_id) REFERENCES tourism_guides (id)
);

CREATE INDEX ix_tourism_tours_village_id ON tourism_tours (village_id);

CREATE INDEX ix_tourism_tours_tour_type ON tourism_tours (tour_type);

CREATE INDEX idx_tour_type ON tourism_tours (tour_type);

CREATE INDEX idx_tour_village ON tourism_tours (village_id);

CREATE INDEX ix_tourism_tours_created_at ON tourism_tours (created_at);

CREATE INDEX ix_tourism_tours_status ON tourism_tours (status);

CREATE UNIQUE INDEX ix_tourism_tours_slug ON tourism_tours (slug);

CREATE INDEX idx_tour_status ON tourism_tours (status);

CREATE TABLE tourism_bookings (
	id VARCHAR(36) NOT NULL, 
	booking_number VARCHAR(50) NOT NULL, 
	tour_id VARCHAR(36) NOT NULL, 
	guest_id VARCHAR(36) NOT NULL, 
	village_id VARCHAR(100) NOT NULL, 
	participants_count INTEGER NOT NULL, 
	tour_date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	special_requests TEXT, 
	subtotal NUMERIC(15, 2) NOT NULL, 
	platform_fee NUMERIC(15, 2), 
	landscape_fee NUMERIC(15, 2), 
	insurance_fee NUMERIC(15, 2), 
	total NUMERIC(15, 2) NOT NULL, 
	currency VARCHAR(3), 
	status VARCHAR(20), 
	payment_status VARCHAR(20), 
	insurance_provider VARCHAR(200), 
	insurance_policy_number VARCHAR(100), 
	blockchain_tx_hash VARCHAR(100), 
	settlement_status VARCHAR(20), 
	regenerative_commitment TEXT, 
	regenerative_completed BOOLEAN, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tour_id) REFERENCES tourism_tours (id)
);

CREATE INDEX idx_booking_tour ON tourism_bookings (tour_id);

CREATE INDEX idx_booking_status ON tourism_bookings (status);

CREATE INDEX ix_tourism_bookings_guest_id ON tourism_bookings (guest_id);

CREATE INDEX idx_booking_guest ON tourism_bookings (guest_id);

CREATE INDEX ix_tourism_bookings_village_id ON tourism_bookings (village_id);

CREATE UNIQUE INDEX ix_tourism_bookings_booking_number ON tourism_bookings (booking_number);

CREATE INDEX ix_tourism_bookings_created_at ON tourism_bookings (created_at);

CREATE INDEX ix_tourism_bookings_status ON tourism_bookings (status);
commit;
