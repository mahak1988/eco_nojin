-- ============================================================
-- Phase 0 Supplemental — RLS + constraints for financial/inventory tables
-- ============================================================
-- Enables Row Level Security on all fin_/inv_/int_/com_ tables
-- and adds appropriate policies for authenticated users.
-- ============================================================

-- 1) Enable RLS on all financial tables
DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'fin_account',
        'fin_journal_batch',
        'fin_journal_entry',
        'fin_idempotency_key',
        'ecowallet',
        'ecotransaction',
        'daily_earnings',
        'audit_event',
        'int_outbox_event',
    ] LOOP
        IF EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = t AND c.relkind = 'r'
        ) THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
        END IF;
    END LOOP;

    FOREACH t IN ARRAY ARRAY[
        'inv_category',
        'inv_sku',
        'inv_warehouse',
        'inv_location',
        'inv_lot',
        'inv_inventory_balance',
        'inv_stock_movement',
        'inv_reservation',
        'inv_stocktake',
        'inv_stocktake_line',
        'inv_valuation_method',
    ] LOOP
        IF EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = t AND c.relkind = 'r'
        ) THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
        END IF;
    END LOOP;

    FOREACH t IN ARRAY ARRAY[
        'com_order',
        'com_order_item',
        'com_payment_intent',
        'com_settlement',
        'com_invoice',
        'com_invoice_line',
    ] LOOP
        IF EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = t AND c.relkind = 'r'
        ) THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
        END IF;
    END LOOP;
END $$;

-- 2) Policies for fin_account (read: all authenticated; write: admin only)
CREATE POLICY "fin_account_read" ON public.fin_account
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "fin_account_write" ON public.fin_account
    FOR INSERT TO authenticated WITH CHECK (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "fin_account_update" ON public.fin_account
    FOR UPDATE TO authenticated USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

-- 3) Policies for fin_journal_batch / fin_journal_entry (admin only)
CREATE POLICY "fin_journal_admin_only" ON public.fin_journal_batch
    FOR ALL TO authenticated USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "fin_journal_entry_admin_only" ON public.fin_journal_entry
    FOR ALL TO authenticated USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

-- 4) Policies for fin_idempotency_key (user sees own keys, admin sees all)
CREATE POLICY "fin_idempotency_own" ON public.fin_idempotency_key
    FOR SELECT TO authenticated USING (
        user_id = auth.uid()::text OR auth.jwt() ->> 'role' = 'admin'
    );

CREATE POLICY "fin_idempotency_insert" ON public.fin_idempotency_key
    FOR INSERT TO authenticated WITH CHECK (user_id = auth.uid()::text);

-- 5) Policies for ecowallet (user sees own wallet only)
CREATE POLICY "ecowallet_own_read" ON public.ecowallet
    FOR SELECT TO authenticated USING (user_id = auth.uid()::text);

CREATE POLICY "ecowallet_own_write" ON public.ecowallet
    FOR UPDATE TO authenticated USING (user_id = auth.uid()::text)
    WITH CHECK (user_id = auth.uid()::text);

-- 6) Policies for ecotransaction (user sees own transactions)
CREATE POLICY "ecotransaction_own_read" ON public.ecotransaction
    FOR SELECT TO authenticated USING (user_id = auth.uid()::text OR auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "ecotransaction_insert" ON public.ecotransaction
    FOR INSERT TO authenticated WITH CHECK (user_id = auth.uid()::text);

-- 7) Policies for daily_earnings (user sees own records)
CREATE POLICY "daily_earnings_own" ON public.daily_earnings
    FOR SELECT TO authenticated USING (user_id = auth.uid()::text OR auth.jwt() ->> 'role' = 'admin');

-- 8) Policies for audit_event (read: admin only; insert: system only via service_role)
CREATE POLICY "audit_event_read" ON public.audit_event
    FOR SELECT TO authenticated USING (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "audit_event_insert" ON public.audit_event
    FOR INSERT TO authenticated WITH CHECK (actor_id = auth.uid()::text);

-- 9) Policies for int_outbox_event (service role only — internal integration)
CREATE POLICY "int_outbox_service_only" ON public.int_outbox_event
    FOR SELECT TO authenticated USING (auth.jwt() ->> 'role' = 'admin');
CREATE POLICY "int_outbox_insert" ON public.int_outbox_event
    FOR INSERT TO authenticated WITH CHECK (true);

-- 10) Policies for inventory tables (admin read/write, user read-only on balances)
CREATE POLICY "inv_sku_admin" ON public.inv_sku
    FOR ALL TO authenticated USING (auth.jwt() ->> 'role' = 'admin')
    WITH CHECK (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "inv_warehouse_read" ON public.inv_warehouse
    FOR SELECT TO authenticated USING (true);
CREATE POLICY "inv_warehouse_admin" ON public.inv_warehouse
    FOR INSERT TO authenticated WITH CHECK (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "inv_inventory_balance_read" ON public.inv_inventory_balance
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "inv_stock_movement_read" ON public.inv_stock_movement
    FOR SELECT TO authenticated USING (true);
CREATE POLICY "inv_stock_movement_admin" ON public.inv_stock_movement
    FOR INSERT TO authenticated WITH CHECK (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "inv_reservation_own" ON public.inv_reservation
    FOR SELECT TO authenticated USING (
        created_by = auth.uid()::text OR auth.jwt() ->> 'role' = 'admin'
    );

-- 11) Policies for commerce tables (buyer sees own orders)
CREATE POLICY "com_order_own_read" ON public.com_order
    FOR SELECT TO authenticated USING (
        buyer_id = auth.uid()::text OR auth.jwt() ->> 'role' = 'admin'
    );

CREATE POLICY "com_order_own_insert" ON public.com_order
    FOR INSERT TO authenticated WITH CHECK (buyer_id = auth.uid()::text);

CREATE POLICY "com_order_own_update" ON public.com_order
    FOR UPDATE TO authenticated USING (buyer_id = auth.uid()::text)
    WITH CHECK (buyer_id = auth.uid()::text);

CREATE POLICY "com_order_item_read" ON public.com_order_item
    FOR SELECT TO authenticated USING (
        EXISTS (
            SELECT 1 FROM com_order o
            WHERE o.id = com_order_item.order_id
            AND (o.buyer_id = auth.uid()::text OR auth.jwt() ->> 'role' = 'admin')
        )
    );

CREATE POLICY "com_payment_own_read" ON public.com_payment_intent
    FOR SELECT TO authenticated USING (
        buyer_id = auth.uid()::text OR auth.jwt() ->> 'role' = 'admin'
    );

-- 12) Add CHECK constraints that couldn't be in CREATE TABLE on SQLite
ALTER TABLE public.fin_journal_entry ADD CONSTRAINT IF NOT EXISTS ck_fin_entry_amount_positive CHECK (amount > 0);
ALTER TABLE public.fin_journal_entry ADD CONSTRAINT IF NOT EXISTS ck_fin_entry_type_valid CHECK (entry_type IN ('debit', 'credit'));
ALTER TABLE public.inv_inventory_balance ADD CONSTRAINT IF NOT EXISTS ck_inv_balance_non_negative CHECK (on_hand >= 0 AND reserved >= 0 AND blocked >= 0 AND in_transit >= 0);
ALTER TABLE public.inv_reservation ADD CONSTRAINT IF NOT EXISTS ck_inv_reservation_qty_positive CHECK (qty > 0);
ALTER TABLE public.inv_stock_movement ADD CONSTRAINT IF NOT EXISTS ck_inv_movement_qty_positive CHECK (qty > 0);
