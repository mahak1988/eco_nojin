// HyDroMa C++ core — Climate kernels
// Reference evapotranspiration: FAO-56 Penman-Monteith and
// Hargreaves-Samani (FAO-56 Appendix / Hargreaves & Samani 1985).
//
// References:
//  - Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). "Crop
//    evapotranspiration - Guidelines for computing crop water requirements."
//    FAO Irrigation and Drainage Paper 56.
//  - Hargreaves, G.H., Samani, Z.A. (1985). "Reference crop evapotranspiration
//    from temperature." Applied Engineering in Agriculture 1(2):96-99.
//
// The Python counterpart lives in engine/hydroma/climate/et_calculator.py.
#pragma once

namespace hydroma {

/// Hargreaves-Samani ET0 (temperature-only method, FAO-56 recommended
/// when humidity and wind data are unavailable).
/// ET0 = 0.0023 * 0.408 * Ra * (Tmean + 17.8) * sqrt(Tmax - Tmin)
/// \param t_min  minimum temperature [degC]
/// \param t_max  maximum temperature [degC]
/// \param t_mean mean temperature [degC]
/// \param ra_mj  extraterrestrial radiation [MJ/m2/day]
/// \return ET0 [mm/day]
double hargreaves_et0(double t_min, double t_max, double t_mean, double ra_mj);

/// Extraterrestrial radiation (FAO-56 eq. 21-25).
/// \param lat_deg  latitude [decimal degrees]
/// \param doy      day of year [1..365]
/// \return Ra [MJ/m2/day]
double extraterrestrial_radiation(double lat_deg, int doy);

/// Full FAO-56 Penman-Monteith reference evapotranspiration.
/// ET0 = (0.408*delta*(Rn-G) + gamma*(900/(T+273))*u2*(es-ea))
///       / (delta + gamma*(1+0.34*u2))
/// \param t_min          minimum temperature [degC]
/// \param t_max          maximum temperature [degC]
/// \param rh_mean_pct    mean relative humidity [%]
/// \param u2             wind speed at 2 m [m/s]
/// \param rs_mj          measured solar radiation [MJ/m2/day]
/// \param elevation_m    station elevation [m]
/// \param lat_deg        latitude [decimal degrees]
/// \param doy            day of year [1..365]
/// \return ET0 [mm/day]
double penman_monteith_et0(double t_min, double t_max, double rh_mean_pct,
                           double u2, double rs_mj, double elevation_m,
                           double lat_deg, int doy);

/// Net radiation Rn = Rns - Rnl computed with FAO-56 equations (exposed for tests).
/// \return net radiation [MJ/m2/day]
double fao56_net_radiation(double t_min, double t_max, double rh_mean_pct,
                           double rs_mj, double elevation_m, double lat_deg,
                           int doy);

}  // namespace hydroma
