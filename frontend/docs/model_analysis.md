# 🔬 گزارش تحلیل علمی مدل‌های بک‌اند Eco Nojin

> این گزارش به‌صورت خودکار از روی OpenAPI Schema استخراج شده است.

## ⚙️ سیستمی، احراز هویت و عمومی

### 📦 `ActionResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Generic action response.
- **پارامترهای کلیدی:** `success, message`

### 📦 `AdminAIChatRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `question, page`

### 📦 `AdminUserOut`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Public user representation for admin panel.
- **پارامترهای کلیدی:** `id, email, full_name, role, is_active, is_email_verified, language, created_at`

### 📦 `ErrorOut`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** API error log entry.
- **پارامترهای کلیدی:** `id, path, method, status, message, acked, created_at`

### 📦 `HTTPValidationError`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `detail`

### 📦 `SettingOut`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Platform setting.
- **پارامترهای کلیدی:** `key, value, description, updated_at`

### 📦 `SettingUpdate`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Setting update payload.
- **پارامترهای کلیدی:** `value`

### 📦 `UserResponse`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `id, email, full_name, role, language, phone, country, city`...

### 📦 `ValidationError`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `loc, msg, type, input, ctx`

### 📦 `WalletCreateRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `user_id`

### 📦 `WalletResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `user_id, balance`

### 📦 `services__api_gateway__routers__admin__HealthResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Aggregate health response.
- **پارامترهای کلیدی:** `status, channels, checked_at`

## ⚙️ شبیه‌سازی و موتورهای علمی

### 📦 `ChainInputs`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Everything the orchestrator needs to run one scenario for one site.
- **پارامترهای کلیدی:** `site_id, area_ha, scenario, r_factor, k_factor, ls_factor, c_factor_base, crop`...

### 📦 `MotorRunRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `motor_type, motor_key, scenario_name, start_date, end_date, time_step, region_bounds, parameters`

### 📦 `ScenarioParams`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Intervention scenario parameter matrix (shared across the chain).
- **پارامترهای کلیدی:** `name, cn_change, c_factor_factor, p_factor`

### 📦 `ScenarioRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `baseline_temp, baseline_precip, scenario, year, farm_id, user_id`

### 📦 `ScientificChainRequest`
- **اعتبار علمی:** ⭐⭐⭐ بسیار بالا (مبتنی بر استانداردهای جهانی)
- **مبانی علمی:**
    - **RUSLE  - **: مدل جهانی فرسایش خاک (بسیار معتبر)
    - **RothC  - **: مدل کربن آلی خاک راتامستد (استاندارد IPCC)
    - **AquaCrop  - **: مدل نیاز آبی گیاه سازمان FAO
- **وظیفه:** Phase-2 scientific chain: RUSLE + RothC-26.3 + AquaCrop with REAL data.
- **پارامترهای کلیدی:** `lat, lon, crop, planting_date, years, slope_pct, practice, irrigation_threshold_mm`...

### 📦 `ScientificChainResponse`
- **اعتبار علمی:** ⭐⭐⭐ بسیار بالا (مبتنی بر استانداردهای جهانی)
- **مبانی علمی:**
    - **RothC  - **: مدل کربن آلی خاک راتامستد (استاندارد IPCC)
    - **AquaCrop  - **: مدل نیاز آبی گیاه سازمان FAO
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `chain_id, cache_hit, status, location, inputs, erosion, swat, water`...

## 🌍 کربن، اقلیم و محیط زیست

### 📦 `CarbonBudgetRequest`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `lat, lon, area_ha, practice, crop, slope_pct, measured_soc_t_ha, use_kobo`...

### 📦 `DailyWeather`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Represents daily weather data.
- **پارامترهای کلیدی:** `date, t_max_c, t_min_c, wind_speed_ms, solar_radiation_mj_m2, humidity_mean_percent`

### 📦 `MonthClimate`
- **اعتبار علمی:** ⭐⭐ بالا (مبتنی بر یک مدل علمی مشخص)
- **مبانی علمی:**
    - **RothC  - **: مدل کربن آلی خاک راتامستد (استاندارد IPCC)
- **وظیفه:** One monthly climate slice used by the RothC runner.
- **پارامترهای کلیدی:** `year, month, tmean_c, smd_mm, max_smd_mm`

### 📦 `WeatherResponse`
- **اعتبار علمی:** ⭐⭐ بالا (مبتنی بر یک مدل علمی مشخص)
- **مبانی علمی:**
    - **ERA5  - **: داده‌های اقلیمی بازتحلیل‌شده ECMWF
- **وظیفه:** Real weather summary (ERA5 primary, NASA POWER secondary).
- **پارامترهای کلیدی:** `status, source, lat, lon, days, summary, daily, era5`...

## 🌱 کود زیستی نوژین و خاک

### 📦 `CompostMaterial`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** Represents a single input material for composting.
- **پارامترهای کلیدی:** `name, mass_kg, carbon_content, nitrogen_content`

### 📦 `CompostRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Request model for compost mix calculation.
- **پارامترهای کلیدی:** `materials`

### 📦 `CompostResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Response model for compost mix calculation.
- **پارامترهای کلیدی:** `cn_ratio, status`

### 📦 `MaterialResponse`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** Response schema for material.
- **پارامترهای کلیدی:** `material_code, common_name, scientific_name, category, nitrogen_pct, phosphorus_pct, potassium_pct, calcium_pct`...

### 📦 `RecipeResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Response schema for formulation recipe.
- **پارامترهای کلیدی:** `recipe_code, recipe_name, soil_code, soil_name, area_min_ha, area_max_ha, material_composition, total_kg_per_ha`...

### 📦 `SoilAnalysisRequest`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `farm_id, user_id, pH, organic_matter, nitrogen, phosphorus, potassium, clay`...

### 📦 `SoilClassificationRequest`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** Request for soil classification.
- **پارامترهای کلیدی:** `ph, ec_dsm, om_pct, texture, region`

### 📦 `SoilClassificationResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Response for soil classification.
- **پارامترهای کلیدی:** `classified_as, soil_code, soil_name, confidence, recommended_recipe, warnings, next_steps`

### 📦 `SoilProfileCreate`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** Request model for creating a soil profile.
- **پارامترهای کلیدی:** `name, texture, ph, ec, organic_matter`

### 📦 `SoilProfileRead`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** Response model for soil profile.
- **پارامترهای کلیدی:** `id, name, texture, ph, ec, organic_matter, created_at`

### 📦 `SoilTypeResponse`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** Response schema for soil type.
- **پارامترهای کلیدی:** `soil_code, soil_name, soil_category, texture, typical_ph_min, typical_ph_max, typical_om_pct, typical_cec_cmol_kg`...

### 📦 `services__api_gateway__routers__nojin__HealthResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Health check.
- **پارامترهای کلیدی:** `status, version, database_connected, materials_count, recipes_count, timestamp`

## 📦 سایر

### 📦 `AddTraceEventRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `product_id, event_type, location, actor, notes`

### 📦 `AnalysisResult`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** Complete analysis result.
- **پارامترهای کلیدی:** `landscape_id, name, location, area_ha, timestamp, climate, vegetation, erosion`...

### 📦 `AnalyzeDrainageRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** درخواست تحلیل زهکشی
- **پارامترهای کلیدی:** `dem_array, resolution, area_km2`

### 📦 `AnalyzeRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Request model for land analysis.
- **پارامترهای کلیدی:** `name, latitude, longitude, area_ha, crop_type, soil_texture`

### 📦 `AssessCapabilityRequest`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** درخواست ارزیابی قابلیت
- **پارامترهای کلیدی:** `slope_degrees, soil_depth_m, erosion_risk, drainage_class, climate_zone, soil_texture`

### 📦 `AuditOut`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Audit log entry for public consumption.
- **پارامترهای کلیدی:** `id, actor_email, action, target, detail, created_at`

### 📦 `BotOut`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Bot platform status.
- **پارامترهای کلیدی:** `key, label, kind, verified, configured, enabled`

### 📦 `CapabilityAssessment`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `profile_id, capability_class, subclass, limiting_factors, suitable_uses, constraints, recommendations, confidence_score`...

### 📦 `ChangePasswordRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `current_password, new_password`

### 📦 `ChannelStatus`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Health status of a single platform channel.
- **پارامترهای کلیدی:** `channel, status, detail`

### 📦 `ChatRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `question, language, farm_id`

### 📦 `ChatResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `answer, sources, confidence, saved_id, farm_context`

### 📦 `ContentCreate`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Content creation payload.
- **پارامترهای کلیدی:** `title, body, category, language, source, generated_by_ai`

### 📦 `ContentOut`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Content item representation.
- **پارامترهای کلیدی:** `id, title, body, category, language, status, source, updated_at`...

### 📦 `ContentUpdate`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Content update payload (partial).
- **پارامترهای کلیدی:** `title, body, category, language, source, generated_by_ai`

### 📦 `CostBenefitRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Request for cost-benefit analysis.
- **پارامترهای کلیدی:** `formulation, area_ha, crop_type, current_yield_t_ha, current_irrigation_m3_ha, current_fertilizer_cost_usd_ha`

### 📦 `CostBenefitResponse`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** Response for cost-benefit analysis.
- **پارامترهای کلیدی:** `total_investment_usd, annual_benefit_usd, annual_cost_usd, net_annual_benefit_usd, roi_annual_percent, payback_simple_months, npv_10year_usd, irr_percent`...

### 📦 `CreateProfileRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** درخواست ایجاد پروفایل
- **پارامترهای کلیدی:** `name, location_lat, location_lon, description, area_hectares, dem_source, dem_resolution_m`

### 📦 `CropWaterReqInput`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Input parameters for crop water requirement calculation.
- **پارامترهای کلیدی:** `crop_type, planting_date, harvest_date, daily_weather_data, kc_coefficients`

### 📦 `CurvatureResult`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `profile_curvature, plan_curvature, total_curvature, convergence_index`

### 📦 `CurveNumberType`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Common Curve Number values based on land use and hydrologic soil group.
- **پارامترهای کلیدی:** ``

### 📦 `DrainageAnalysis`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `profile_id, drainage_pattern, drainage_density, density_class, stream_orders, stream_order_max, bifurcation_ratio, flow_accumulation`...

### 📦 `DrainageDensityClass`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Drainage density classes
- **پارامترهای کلیدی:** ``

### 📦 `DrainagePattern`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Drainage patterns
- **پارامترهای کلیدی:** ``

### 📦 `EarnRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `user_id, category, quantity, language`

### 📦 `EarnResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `amount_earned, new_balance, category`

### 📦 `ForgotPasswordRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `email`

### 📦 `FullAnalysisRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Complete analysis request combining all calculators.
- **پارامترهای کلیدی:** `soil_code, area_ha, crop_type, current_yield_t_ha, current_irrigation_m3_ha, current_fertilizer_cost_usd_ha, budget_per_ha_usd`

### 📦 `FullAnalysisResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Complete analysis response.
- **پارامترهای کلیدی:** `recommendation, cost_benefit, water_savings, scale, overall_assessment`

### 📦 `GroundwaterInput`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Input parameters for groundwater analysis.
- **پارامترهای کلیدی:** `model_type, transmissivity_m2day, storativity, pumping_rate_m3day, observation_distance_m, time_days`

### 📦 `IrrigationDesignInput`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Input parameters for irrigation system design.
- **پارامترهای کلیدی:** `site_location_lat, site_location_lon, crop_type, area_ha, irrigation_type, water_source_flow_m3hr, plant_spacing_m, row_spacing_m`

### 📦 `IssueCreditsRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `amount, owner`

### 📦 `LoginRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `email, password`

### 📦 `ManualSiteRunRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `site_id, crop_name, planting_date, sim_start, sim_end, season_days, crops, species_id`...

### 📦 `MessageResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `message, success, data`

### 📦 `OptimizeRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Request for formulation optimization.
- **پارامترهای کلیدی:** `soil_code, area_ha, target_om_increase_pct, target_cn_ratio, budget_per_ha_usd, required_materials, excluded_materials`

### 📦 `OrderRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `product_id, buyer_name, quantity_kg`

### 📦 `ProfileUpdateRequest`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `full_name, phone, date_of_birth, country, city, address, language, avatar_url`

### 📦 `ProjectCalculateRequest`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `name, area_hectares, species, trees_per_ha, avg_diameter_cm, avg_height_m, project_years, latitude`...

### 📦 `QueryRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** User query for the knowledge assistant.
- **پارامترهای کلیدی:** `question`

### 📦 `QueryResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Response from the knowledge assistant.
- **پارامترهای کلیدی:** `query, answer, sources, confidence, citations`

### 📦 `RecommendRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Request for recommendation.
- **پارامترهای کلیدی:** `soil_code, area_ha, budget_per_ha_usd, crop_type`

### 📦 `RecommendResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Response for recommendation.
- **پارامترهای کلیدی:** `recipe_code, recipe_name, area_ha, material_quantities, total_tons, estimated_cost_usd, expected_results, traditional_technique`...

### 📦 `RedeemRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `user_id, category, language`

### 📦 `RedeemResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `amount_redeemed, new_balance, category`

### 📦 `RefreshRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `refresh_token`

### 📦 `RegisterProductRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `producer, batch_number, initial_event, location, notes`

### 📦 `RegisterProjectRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `owner, project_type, area_ha, duration_years`

### 📦 `RegisterRequest`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `email, full_name, password, role, phone, date_of_birth, country, city`...

### 📦 `ResetPasswordRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `token, new_password`

### 📦 `RetireCreditsRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `owner`

### 📦 `ScaleRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Request for scale calculation.
- **پارامترهای کلیدی:** `formulation, area_ha`

### 📦 `ScaleResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Response for scale calculation.
- **پارامترهای کلیدی:** `area_ha, scale_category, material_quantities, total_tons, total_cost_usd, economies_of_scale_pct, implementation_days, equipment_needed`...

### 📦 `SlopeClass`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** USDA Slope Classes
- **پارامترهای کلیدی:** ``

### 📦 `SourceResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Reference source for the answer.
- **پارامترهای کلیدی:** `id, title, source, category, relevance`

### 📦 `StatisticsResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** System statistics.
- **پارامترهای کلیدی:** `materials_count, soil_types_count, recipes_count, arid_priority_materials, high_water_saving_recipes, avg_roi_percent, avg_water_saving_percent, system_status`

### 📦 `StatsResponse`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** DuckDB NDVI summary for a farm.
- **پارامترهای کلیدی:** `farm_id, analyses, ndvi_mean, ndvi_min, ndvi_max, ndvi_latest, real_data_count, engine`

### 📦 `StructureDesignInput`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Input parameters for designing a water conservation structure.
- **پارامترهای کلیدی:** `site_location_lat, site_location_lon, structure_type, area_ha, max_flow_m3s, soil_type`

### 📦 `StructureRequest`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `structure_type, slope_pct, area_m2, rainfall_mm`

### 📦 `SupportChatRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `question, lang, page`

### 📦 `TokenResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `access_token, refresh_token, token_type, user`

### 📦 `TopographyInput`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** Input parameters for topographic analysis.
- **پارامترهای کلیدی:** `site_id, dem_path, analysis_types, target_crs`

### 📦 `TransferCreditsRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `credit_id, from_owner, to_owner`

### 📦 `UssdRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `user_id, action, language`

### 📦 `UssdResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `action, balance, message`

### 📦 `VerifyProjectRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `verifier`

### 📦 `VerifyRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `baseline_activity, has_financing, would_happen_without_project, activity_displacement, market_leakage, commitment_years, risk_flag`

### 📦 `WaterSavingsRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Request for water savings calculation.
- **پارامترهای کلیدی:** `formulation, area_ha, baseline_irrigation_m3_ha`

### 📦 `WaterSavingsResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Response for water savings.
- **پارامترهای کلیدی:** `baseline_irrigation_m3_ha, new_irrigation_m3_ha, water_saved_m3_ha, water_saved_percent, annual_water_saved_m3, annual_savings_usd, drought_resistance_days, recommendations`

## 🚜 مدیریت مزرعه و آبخیزداری

### 📦 `FarmCreate`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `name, latitude, longitude, elevation_m, area_hectares, soil_type, climate_zone`

### 📦 `FarmOut`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `id, name, latitude, longitude, elevation_m, area_hectares, soil_type, climate_zone`

### 📦 `LandCapabilityClass`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** USDA Land Capability Classes
- **پارامترهای کلیدی:** ``

### 📦 `LandProfile`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `id, name, description, country, region, city, location_lat, location_lon`...

### 📦 `LandformType`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** TPI-based landform types
- **پارامترهای کلیدی:** ``

### 📦 `LandscapeCreate`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Request model for creating a landscape.
- **پارامترهای کلیدی:** `name, slug, country, province, latitude, longitude, area_ha`

### 📦 `LandscapeOut`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Response model for landscape.
- **پارامترهای کلیدی:** `id, name, slug, country, province, created_at`

### 📦 `RealLandResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Aggregated REAL land intelligence (satellite + climate + soil).

Every block carries an explicit ``status`` and ``data_source`` label.
The satellite block may be ``credentials_required`` until free CDSE
credentials are configured — this endpoint never fabricates data.
- **پارامترهای کلیدی:** `lat, lon, analysis_date, satellite, climate, soil, summary`

### 📦 `RunoffInput`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Input parameters for point-scale runoff calculation.
- **پارامترهای کلیدی:** `precipitation_mm, curve_number, area_ha, method, rational_coefficient`

## 🛰️ سنجش از دور و توپوگرافی

### 📦 `AnalyzeTerrainRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** درخواست تحلیل توپوگرافی
- **پارامترهای کلیدی:** `dem_array, resolution`

### 📦 `SatelliteAnalyzeRequest`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Request model for satellite analysis.
- **پارامترهای کلیدی:** `lat, lon, analysis_date, farm_id`

### 📦 `SatelliteAnalyzeResponse`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** Response model for satellite analysis.
- **پارامترهای کلیدی:** `lat, lon, ndvi, evi, savi, recommendation, vegetation_health, analysis_date`...

### 📦 `SatelliteHistoryResponse`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** One stored satellite analysis row.
- **پارامترهای کلیدی:** `id, farm_id, ndvi, evi, savi, ndwi, nbr, satellite`...

### 📦 `TerrainAnalysis`
- **اعتبار علمی:** ⭐ متوسط (پارامترهای استاندارد زراعی/خاکی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `profile_id, terrain_type, elevation_min, elevation_max, elevation_mean, elevation_range, slope_mean, slope_max`...

### 📦 `TerrainIndices`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** بدون توضیح
- **پارامترهای کلیدی:** `twi, tpi, roughness_index, landform, wetness_class`

### 📦 `services__api_gateway__routers__satellite__HealthResponse`
- **اعتبار علمی:** پایه (ساختاری/سیستمی)
- **وظیفه:** Health check response.
- **پارامترهای کلیدی:** `status, module, supported_indices, providers, data_source`

