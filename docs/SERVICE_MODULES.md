# Service Modules Overview

This document provides a high-level overview of the responsibilities of each major service module within the `services/` directory.

## Core Gateway and Coordination

- **api_gateway**: The central FastAPI application. Handles routing, authentication middleware, and acts as the primary entry point for all external requests. Orchestrates communication with other internal services.
- **workflow**: Manages complex, multi-step processes and business workflows, potentially involving interactions between multiple other services.
- **models**: Contains shared data models and schemas used across multiple services to ensure data consistency.

## User Management and Access

- **auth**: Handles user authentication, authorization, session management, and security policies.
- **admin**: Provides administrative interfaces and functions for managing users, permissions, and system settings.
- **notification**: Manages sending notifications to users via email, push, SMS, or in-app alerts.

## Data and Integration

- **data_sources**: Connects to and manages external data sources, such as weather APIs, market prices, or third-party databases.
- **supabase**: Integrates with the Supabase backend-as-a-service for database and real-time features.
- **analytics**: Aggregates data from various sources for analysis, reporting, and dashboard generation.

## Financial and Economic Logic

- **ecowallet**: Manages user wallets, transactions, payments, and potentially cryptocurrency interactions related to Eco Coin.
- **ledger**: Maintains a record of all financial and carbon credit transactions for accounting and auditing purposes.
- **finance**: Contains financial calculation logic, potentially for cost-benefit analysis, pricing, or investment planning.

## Platform Features

- **platform**: Likely contains core platform logic, user profiles, settings, and general platform-wide features.
- **content**: Manages static or dynamic content displayed on the platform, such as news, articles, or educational material.
- **marketplace**: Handles product listings, orders, inventory, and transaction processing for the internal marketplace.

## Scientific and Technical Engines

- **science**: A facade or core service providing access to the main scientific calculations, potentially delegating to `engine/hydroma`.
- **scientific_motors**: Reusable, modular scientific computation units that can be called by other services or the API gateway.
- **carbon**: Specific logic for carbon credit calculation, registration, verification, and management, likely interfacing with the blockchain service.
- **satellite**: Processes satellite imagery and data, potentially triggering analysis pipelines within the `engine/hydroma.satellite` module.
- **blockchain**: Interacts with the blockchain layer for immutable records, especially for carbon credits and supply chain traceability.

## Domain-Specific Modules

- **land**: Manages land parcel data, ownership, usage rights, and land-specific analyses.
- **soil**: Handles soil health data, analysis results, and recommendations specific to soil conditions.
- **climate**: Processes and provides access to climate and weather data relevant to agricultural decisions.
- **hydrology**: Manages water resource data, watershed information, and hydrological modeling results.
- **ecotourism**: Contains logic for the ecotourism platform, including site listings, bookings, and visitor management.
- **biofertilizer**: Provides recommendations and information related to biofertilizer use based on soil and crop data.

## Communication and Monitoring

- **bots**: Houses chatbot logic, potentially for Telegram, Facebook Messenger, or other platforms.
- **telegram_bot**: Specific implementation for a Telegram bot, likely interacting with other services for information or actions.
- **ussd**: Handles USSD menu logic for feature phone users.
- **voice**: Manages voice-based interactions (IVR) for users without text-capable devices.
- **field_monitoring**: Interfaces with sensors or manual data entry for real-time field condition monitoring.
- **mobile_monitoring**: Similar to field monitoring, but specifically tailored for mobile device data collection.

## Planning and Design

- **design_engine**: Potentially involved in designing farm layouts, infrastructure plans, or intervention strategies.
- **infrastructure**: Manages data related to physical infrastructure like wells, roads, or storage facilities.
- **map_engine**: Provides advanced mapping capabilities, potentially integrating with GIS data.