/**
 * Establishment-flow contracts.
 *
 * The per-step form components were removed: their translation namespaces
 * (`market.bazaarWizard.*`, `market.storeWizard.*`) are not part of the shipped
 * catalogues and steps 2-10 have no gateway endpoint, so the forms could only
 * ever render untranslated copy and submit nowhere. The validation schemas stay
 * exported because they describe the bazaar establishment data contract.
 */
export * from '@/lib/validation/bazaar-establishment';
