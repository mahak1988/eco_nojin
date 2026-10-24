#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include "nojin_calculator.h"

namespace py = pybind11;

PYBIND11_MODULE(cpp_nojin, m) {
    m.doc() = "Pybind11 binding for Nojin C++ calculator";

    m.def("calculate_biofertilizer_efficacy", &cpp_core::calculate_biofertilizer_efficacy,
          "Calculates biofertilizer efficacy based on soil conditions.",
          py::arg("soil_nitrogen_ppm"), py::arg("soil_phosphorus_ppm"), py::arg("soil_potassium_ppm"),
          py::arg("ph"), py::arg("organic_matter_pct"), py::arg("biofert_type"));

    m.def("predict_yield_response", &cpp_core::predict_yield_response,
          "Predicts yield response based on biofertilizer application.",
          py::arg("baseline_yield"), py::arg("biofert_efficacy"), py::arg("baseline_fertilizer_rate"), py::arg("biofert_dosage"));

    // Example of binding a more complex function that takes/returns numpy arrays
    // m.def("process_array_cpp", [](py::array_t<double> input) {
    //     py::buffer_info buf = input.request();
    //     double *ptr = static_cast<double *>(buf.ptr);
    //     size_t size = buf.size;
    //     // Process data pointed to by ptr
    //     // ...
    //     // Return processed data as a new numpy array
    //     py::array_t<double> result = py::array_t<double>(size);
    //     py::buffer_info res_buf = result.request();
    //     double *res_ptr = static_cast<double *>(res_buf.ptr);
    //     // Fill res_ptr
    //     return result;
    // });
}