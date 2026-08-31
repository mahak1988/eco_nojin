/**
 * Central frontend configuration.
 *
 * All environment-dependent values live here. Override them with a
 * `frontend/.env` file (see `frontend/.env.example`) or real environment
 * variables. Never hardcode backend URLs in components — import from here.
 */
export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const APP_NAME: string = 'Eco Nojin';
