// HyDroMa C++ core — pybind11 bindings.
//
// Build with CMake (HYDROMA_BUILD_PYTHON_BINDINGS=ON, requires pybind11).
// Produces module `hydroma_core`. Example:
//   import hydroma_core
//   result = hydroma_core.route_flood_wave([0, 50, 100, 50, 0], 1000.0, 50, 0.03, 0.002, 3600.0, 5.0)
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "hydroma/climate.hpp"
#include "hydroma/crop_water.hpp"
#include "hydroma/erosion.hpp"
#include "hydroma/hydrology.hpp"
#include "hydroma/indices.hpp"
#include "hydroma/richards.hpp"
#include "hydroma/saint_venant.hpp"
#include "hydroma/sampling.hpp"
#include "hydroma/sediment.hpp"
#include "hydroma/soil.hpp"

namespace py = pybind11;
using namespace hydroma;

PYBIND11_MODULE(hydroma_core, m) {
    m.doc() = "HyDroMa high-performance scientific core (C++20)";

    // --- Hydrology -------------------------------------------------------
    py::class_<WaveParameters>(m, "WaveParameters")
        .def_readonly("K", &WaveParameters::K)
        .def_readonly("x", &WaveParameters::x)
        .def_readonly("celerity", &WaveParameters::celerity)
        .def_readonly("normal_depth", &WaveParameters::normal_depth)
        .def_readonly("velocity", &WaveParameters::velocity)
        .def_readonly("travel_time", &WaveParameters::travel_time);

    py::class_<RoutingResult>(m, "RoutingResult")
        .def_readonly("outflow_hydrograph", &RoutingResult::outflow)
        .def_readonly("peak_inflow", &RoutingResult::peak_inflow)
        .def_readonly("peak_outflow", &RoutingResult::peak_outflow)
        .def_readonly("peak_attenuation", &RoutingResult::peak_attenuation)
        .def_readonly("attenuation_ratio", &RoutingResult::attenuation_ratio)
        .def_readonly("time_lag", &RoutingResult::time_lag)
        .def_readonly("time_to_peak_out", &RoutingResult::time_to_peak_out)
        .def_readonly("travel_time", &RoutingResult::travel_time)
        .def_readonly("celerity", &RoutingResult::celerity)
        .def_readonly("normal_depth", &RoutingResult::normal_depth)
        .def_readonly("volume_in", &RoutingResult::volume_in)
        .def_readonly("volume_out", &RoutingResult::volume_out)
        .def_readonly("mass_balance", &RoutingResult::mass_balance);

    m.def("muskingum_cunge_route", &muskingum_cunge_route,
          py::arg("inflow"), py::arg("K"), py::arg("x"), py::arg("dt"),
          "Route inflow hydrograph with Muskingum-Cunge");
    m.def("compute_wave_parameters", &compute_wave_parameters,
          py::arg("channel_length"), py::arg("bed_slope"), py::arg("manning_n"),
          py::arg("channel_width"), py::arg("peak_flow"),
          "Kinematic wave parameters from channel geometry");
    m.def("route_flood_wave", &route_flood_wave,
          py::arg("inflow_hydrograph"), py::arg("channel_length") = 1000.0,
          py::arg("n_cells") = 50, py::arg("manning_n") = 0.030,
          py::arg("bed_slope") = 0.002, py::arg("dt") = 10.0,
          py::arg("channel_width") = 5.0,
          "Route a flood wave and return statistics");
    m.def("route_multi_reach", &route_multi_reach,
          py::arg("inflow_hydrograph"), py::arg("channel_length"),
          py::arg("n_reaches"), py::arg("manning_n") = 0.030,
          py::arg("bed_slope") = 0.002, py::arg("dt") = 10.0,
          py::arg("channel_width") = 5.0,
          "Route through multiple reaches");

    // --- Soil ------------------------------------------------------------
    m.def("soil_water_content", &soil_water_content,
          py::arg("h_matric"), py::arg("soil_texture"),
          "van Genuchten water content [cm3/cm3]");
    m.def("hydraulic_conductivity", &hydraulic_conductivity,
          py::arg("h_matric"), py::arg("soil_texture"),
          "van Genuchten-Mualem conductivity [cm/day]");
    m.def("soil_params", &soil_params, py::arg("texture"),
          "van Genuchten parameters for a texture class");
    m.def("supported_textures", &supported_textures,
          "List supported soil texture keys");

    // --- Erosion ---------------------------------------------------------
    m.def("rusle_annual_soil_loss", &rusle_annual_soil_loss,
          py::arg("R"), py::arg("K"), py::arg("LS"), py::arg("C"), py::arg("P"),
          "A = R * K * LS * C * P  [t/(ha yr)]");
    m.def("ls_factor", &ls_factor, py::arg("slope_length_m"),
          py::arg("slope_percent"), "RUSLE slope length/steepness factor");
    m.def("estimate_rainfall_erosivity", &estimate_rainfall_erosivity,
          py::arg("annual_rainfall_mm"),
          "R factor estimate (Renard & Freimund 1994)");
    m.def("soil_erodibility_k", &soil_erodibility_k, py::arg("texture"),
          "Typical K factor for a texture class");

    // --- Climate ---------------------------------------------------------
    m.def("hargreaves_et0", &hargreaves_et0, py::arg("t_min"), py::arg("t_max"),
          py::arg("t_mean"), py::arg("ra_mj"), "Hargreaves-Samani ET0 [mm/day]");
    m.def("extraterrestrial_radiation", &extraterrestrial_radiation,
          py::arg("lat_deg"), py::arg("doy"), "FAO-56 Ra [MJ/m2/day]");
    m.def("penman_monteith_et0", &penman_monteith_et0, py::arg("t_min"),
          py::arg("t_max"), py::arg("rh_mean_pct"), py::arg("u2"),
          py::arg("rs_mj"), py::arg("elevation_m"), py::arg("lat_deg"),
          py::arg("doy"), "FAO-56 Penman-Monteith ET0 [mm/day]");
    m.def("fao56_net_radiation", &fao56_net_radiation, py::arg("t_min"),
          py::arg("t_max"), py::arg("rh_mean_pct"), py::arg("rs_mj"),
          py::arg("elevation_m"), py::arg("lat_deg"), py::arg("doy"),
          "FAO-56 net radiation [MJ/m2/day]");

    // --- Indices ---------------------------------------------------------
    m.def("ndvi", &ndvi, py::arg("red"), py::arg("nir"));
    m.def("evi", &evi, py::arg("red"), py::arg("nir"), py::arg("blue"));
    m.def("savi", &savi, py::arg("red"), py::arg("nir"), py::arg("L") = 0.5);
    m.def("ndwi", &ndwi, py::arg("green"), py::arg("nir"));
    m.def("nbr", &nbr, py::arg("nir"), py::arg("swir"));
    m.def("ndvi_array", &ndvi_array, py::arg("red"), py::arg("nir"));
    m.def("evi_array", &evi_array, py::arg("red"), py::arg("nir"),
          py::arg("blue"));
    m.def("savi_array", &savi_array, py::arg("red"), py::arg("nir"),
          py::arg("L") = 0.5);
    m.def("ndwi_array", &ndwi_array, py::arg("green"), py::arg("nir"));
    m.def("nbr_array", &nbr_array, py::arg("nir"), py::arg("swir"));

    // --- Richards -------------------------------------------------------
    py::enum_<TopBoundary>(m, "TopBoundary")
        .value("Flux", TopBoundary::Flux)
        .value("Head", TopBoundary::Head);
    py::enum_<BottomBoundary>(m, "BottomBoundary")
        .value("FreeDrainage", BottomBoundary::FreeDrainage)
        .value("Head", BottomBoundary::Head);
    py::class_<RichardsOptions>(m, "RichardsOptions")
        .def(py::init<>())
        .def_readwrite("n_cells", &RichardsOptions::n_cells)
        .def_readwrite("column_depth_cm", &RichardsOptions::column_depth_cm)
        .def_readwrite("dt_days", &RichardsOptions::dt_days)
        .def_readwrite("n_steps", &RichardsOptions::n_steps)
        .def_readwrite("tolerance_cm", &RichardsOptions::tolerance_cm)
        .def_readwrite("max_iter", &RichardsOptions::max_iter)
        .def_readwrite("top", &RichardsOptions::top)
        .def_readwrite("top_value_cm_day", &RichardsOptions::top_value_cm_day)
        .def_readwrite("bottom", &RichardsOptions::bottom)
        .def_readwrite("bottom_head_cm", &RichardsOptions::bottom_head_cm);
    py::class_<RichardsResult>(m, "RichardsResult")
        .def_readonly("head_cm", &RichardsResult::head_cm)
        .def_readonly("theta", &RichardsResult::theta)
        .def_readonly("storage_cm", &RichardsResult::storage_cm)
        .def_readonly("cumulative_top_flux_cm", &RichardsResult::cumulative_top_flux_cm)
        .def_readonly("cumulative_bottom_flux_cm", &RichardsResult::cumulative_bottom_flux_cm)
        .def_readonly("converged", &RichardsResult::converged);
    m.def("simulate_richards", &simulate_richards, py::arg("texture"),
          py::arg("initial_head_cm"), py::arg("opts"),
          "1D vertical Richards (mixed form, modified Picard)");
    m.def("specific_moisture_capacity", &specific_moisture_capacity,
          py::arg("h_cm"), py::arg("texture"));

    // --- Saint-Venant ---------------------------------------------------
    py::class_<SaintVenantOptions>(m, "SaintVenantOptions")
        .def(py::init<>())
        .def_readwrite("length_m", &SaintVenantOptions::length_m)
        .def_readwrite("n_cells", &SaintVenantOptions::n_cells)
        .def_readwrite("width_m", &SaintVenantOptions::width_m)
        .def_readwrite("bed_slope", &SaintVenantOptions::bed_slope)
        .def_readwrite("manning_n", &SaintVenantOptions::manning_n)
        .def_readwrite("t_end_s", &SaintVenantOptions::t_end_s)
        .def_readwrite("cfl", &SaintVenantOptions::cfl)
        .def_readwrite("dry_tolerance", &SaintVenantOptions::dry_tolerance)
        .def_readwrite("output_every", &SaintVenantOptions::output_every);
    py::class_<SaintVenantResult>(m, "SaintVenantResult")
        .def_readonly("depth_m", &SaintVenantResult::depth_m)
        .def_readonly("discharge_m3s", &SaintVenantResult::discharge_m3s)
        .def_readonly("time_s", &SaintVenantResult::time_s)
        .def_readonly("total_volume_initial_m3", &SaintVenantResult::total_volume_initial_m3)
        .def_readonly("total_volume_final_m3", &SaintVenantResult::total_volume_final_m3)
        .def_readonly("mass_balance", &SaintVenantResult::mass_balance)
        .def_readonly("stable", &SaintVenantResult::stable);
    m.def("simulate_saint_venant", &simulate_saint_venant,
          py::arg("initial_depth_m"), py::arg("inflow_m3s"), py::arg("opts"),
          "1D Saint-Venant (Rusanov FV, Manning friction)");
    m.def("manning_normal_depth", &manning_normal_depth, py::arg("discharge_m3s"),
          py::arg("width_m"), py::arg("bed_slope"), py::arg("manning_n"));

    // --- Crop water (FAO-56 dual Kc) ------------------------------------
    py::class_<CropWaterParams>(m, "CropWaterParams")
        .def(py::init<>())
        .def_readwrite("l_ini", &CropWaterParams::l_ini)
        .def_readwrite("l_dev", &CropWaterParams::l_dev)
        .def_readwrite("l_mid", &CropWaterParams::l_mid)
        .def_readwrite("l_late", &CropWaterParams::l_late)
        .def_readwrite("kcb_ini", &CropWaterParams::kcb_ini)
        .def_readwrite("kcb_mid", &CropWaterParams::kcb_mid)
        .def_readwrite("kcb_end", &CropWaterParams::kcb_end)
        .def_readwrite("root_depth_m", &CropWaterParams::root_depth_m)
        .def_readwrite("theta_fc", &CropWaterParams::theta_fc)
        .def_readwrite("theta_wp", &CropWaterParams::theta_wp)
        .def_readwrite("p_fraction", &CropWaterParams::p_fraction)
        .def_readwrite("rew_mm", &CropWaterParams::rew_mm)
        .def_readwrite("tew_mm", &CropWaterParams::tew_mm)
        .def_readwrite("fraction_wetted", &CropWaterParams::fraction_wetted)
        .def_readwrite("kc_max", &CropWaterParams::kc_max);
    py::class_<CropWaterResult>(m, "CropWaterResult")
        .def_readonly("et0_mm", &CropWaterResult::et0_mm)
        .def_readonly("etc_mm", &CropWaterResult::etc_mm)
        .def_readonly("kc_effective", &CropWaterResult::kc_effective)
        .def_readonly("stress_factor", &CropWaterResult::stress_factor)
        .def_readonly("depletion_mm", &CropWaterResult::depletion_mm)
        .def_readonly("deep_percolation_mm", &CropWaterResult::deep_percolation_mm)
        .def_readonly("irrigation_mm", &CropWaterResult::irrigation_mm)
        .def_readonly("total_etc_mm", &CropWaterResult::total_etc_mm)
        .def_readonly("total_rain_mm", &CropWaterResult::total_rain_mm)
        .def_readonly("total_irrigation_mm", &CropWaterResult::total_irrigation_mm)
        .def_readonly("total_dp_mm", &CropWaterResult::total_dp_mm)
        .def_readonly("water_balance_error_mm", &CropWaterResult::water_balance_error_mm);
    m.def("simulate_crop_water", &simulate_crop_water, py::arg("et0_mm"),
          py::arg("rain_mm"), py::arg("auto_irrigate"), py::arg("p"),
          "FAO-56 dual crop coefficient daily water balance");

    // --- Sediment -------------------------------------------------------
    py::class_<RusleCell>(m, "RusleCell")
        .def(py::init<>())
        .def_readwrite("k", &RusleCell::k)
        .def_readwrite("c", &RusleCell::c)
        .def_readwrite("p", &RusleCell::p)
        .def_readwrite("slope_percent", &RusleCell::slope_percent)
        .def_readwrite("slope_length_m", &RusleCell::slope_length_m);
    m.def("rusle_grid", &rusle_grid, py::arg("cells"), py::arg("r_factor"));
    m.def("rusle_grid_total", &rusle_grid_total, py::arg("cells"),
          py::arg("r_factor"), py::arg("cell_area_ha"));
    m.def("sediment_delivery_ratio", &sediment_delivery_ratio,
          py::arg("watershed_area_km2"), py::arg("coefficient") = 0.41,
          py::arg("exponent") = -0.3);
    m.def("sediment_yield", &sediment_yield, py::arg("cells"), py::arg("r_factor"),
          py::arg("cell_area_ha"), py::arg("watershed_area_km2"));
    m.def("trap_efficiency_brune", &trap_efficiency_brune,
          py::arg("capacity_inflow_ratio"), py::arg("k") = 0.15);
    m.def("sediment_trapped", &sediment_trapped, py::arg("cells"),
          py::arg("r_factor"), py::arg("cell_area_ha"), py::arg("watershed_area_km2"),
          py::arg("capacity_inflow_ratio"));

    // --- Sampling -------------------------------------------------------
    m.def("latin_hypercube", &latin_hypercube, py::arg("n"), py::arg("dims"),
          py::arg("seed"));
    m.def("monte_carlo_uniform", &monte_carlo_uniform, py::arg("n"),
          py::arg("dims"), py::arg("seed"));
    m.def("scale_samples", &scale_samples, py::arg("unit_samples"),
          py::arg("lo"), py::arg("hi"));
    m.def("estimate_mean_mc", &estimate_mean_mc, py::arg("f"), py::arg("dims"),
          py::arg("n"), py::arg("seed"));
    m.def("estimate_mean_lhs", &estimate_mean_lhs, py::arg("f"), py::arg("dims"),
          py::arg("n"), py::arg("seed"));
    m.def("simplified_yield", &simplified_yield, py::arg("available_water_mm"),
          py::arg("mean_temp_c"), py::arg("crop"));
    py::class_<YieldStats>(m, "YieldStats")
        .def_readonly("mean_kg_ha", &YieldStats::mean_kg_ha)
        .def_readonly("std_kg_ha", &YieldStats::std_kg_ha)
        .def_readonly("p5_kg_ha", &YieldStats::p5_kg_ha)
        .def_readonly("p50_kg_ha", &YieldStats::p50_kg_ha)
        .def_readonly("p95_kg_ha", &YieldStats::p95_kg_ha)
        .def_readonly("failure_probability", &YieldStats::failure_probability)
        .def_readonly("n_samples", &YieldStats::n_samples);
    m.def("yield_ensemble_lhs", &yield_ensemble_lhs, py::arg("mean_water_mm"),
          py::arg("water_std_mm"), py::arg("mean_temp_c"), py::arg("temp_std_c"),
          py::arg("crop"), py::arg("n_samples"), py::arg("seed"));
}
