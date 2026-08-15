# User Guide

## Welcome to Eco Nojin

Eco Nojin is your intelligent companion for ecosystem restoration and smart
agriculture. This guide helps you make the most of the platform.

---

## Access Methods

### Web Application (Recommended)

1. Open your browser
2. Go to: **http://localhost:3000** (development)
3. Explore 9 interactive panels

### Progressive Web App (PWA)

For mobile devices:
1. Open the website in Chrome or Safari
2. Click the "Install" icon in the address bar
3. The app will be installed on your home screen
4. Works offline after first load

### USSD (Feature Phones)

For phones without internet:
1. Dial: **`*384*73#`**
2. Navigate the menu:
   ```
   Eco Nojin Services
   1. Soil Analysis
   2. Crop Advice
   3. Market Prices
   4. Weather
   5. Ask Expert
   0. Exit
   ```

### SMS Commands

Send SMS to our number:
- `SOIL 36.8 54.4` - Get soil analysis for coordinates
- `PRICE wheat` - Get current wheat price
- `WEATHER tehran` - Get Tehran weather
- `ASK how to make compost?` - Ask AI expert
- `LANG fa` - Switch to Persian
- `HELP` - Get help

### Voice IVR (Low-Literacy Users)

Call the Eco Nojin hotline:
- Listen to the voice menu
- Press numbers on keypad
- Or speak your question after the beep
- Get spoken answers from our AI

---

## Using the Web Application

### 1. Soil Dashboard
View your registered soil profiles with texture, pH, EC, organic matter.

### 2. Satellite Field Analysis
Analyze vegetation health from space:
1. Enter latitude and longitude (e.g., `36.8, 54.4`)
2. Click "Analyze Field"
3. View NDVI, EVI, SAVI, NDWI, NBR indices
4. Read the recommendation

### 3. Crop Planner
Plan your crops:
1. Select crop type
2. Enter available water (mm)
3. Enter mean temperature (C)
4. Click "Simulate Yield"

### 4. Scenario Analysis
Explore climate change impacts:
1. Select SSP scenario (SSP1-2.6, SSP2-4.5, SSP5-8.5)
2. Select time horizon (2030, 2050, 2100)
3. Click "Climate Transition Analysis"

### 5. Carbon Credits
Calculate carbon sequestration potential:
1. Select project type
2. Enter area (hectares)
3. Enter duration (years)
4. Click "Calculate Carbon"

### 6. Watershed Structures
Design water conservation structures:
1. Select structure type
2. Enter slope (%), area (m2), rainfall (mm)
3. Click "Calculate Structure"

### 7. Marketplace
Buy and sell agricultural products with traceability.

### 8. Performance Benchmark
See how fast our engine is (NumPy vs Numba).

### 9. AI Assistant
Ask any agricultural question and get scientific answers with citations.

---

## Common Tasks

### "I want to know if my field is healthy"
1. Use **Satellite Field Analysis**
2. Enter your field coordinates
3. Check NDVI value:
   - > 0.6: Very healthy
   - 0.4-0.6: Healthy
   - 0.2-0.4: Moderate stress
   - < 0.2: Severe stress

### "I want to choose the best crop for next season"
1. Use **Crop Planner**
2. Enter your water availability and temperature
3. Compare all crops
4. Select the one with best revenue and low stress

### "I want to prepare for climate change"
1. Use **Scenario Analysis**
2. Compare SSP1-2.6 vs SSP5-8.5 for 2050
3. See which crops perform better under warming

### "I want to earn from carbon credits"
1. Use **Carbon Credits**
2. Select your project type (e.g., afforestation)
3. Enter your land area
4. Register project for verification

---

## Languages

Supported languages:
- English (en)
- Persian (fa) - RTL
- Arabic (ar) - RTL
- French (fr)
- Spanish (es)
- Portuguese (pt)
- Russian (ru)
- Hindi (hi)
- Chinese (zh)
- Urdu (ur) - RTL
- Bengali (bn)
- German (de)
- Italian (it)
- Malay (ms)

---

## Troubleshooting

### "Geolocation does not work"
- Make sure you are on `http://localhost:3000`
- Allow location permission in browser
- Check if GPS is enabled on device

### "App is slow"
- Clear browser cache
- Check internet connection
- Try different browser (Chrome recommended)

### "USSD menu does not appear"
- Check you dialed `*384*73#` correctly
- Ensure you have network coverage
- Contact your mobile operator

---

## Tips for Best Results

1. **Use accurate coordinates** for satellite analysis
2. **Update soil profiles regularly** with new measurements
3. **Compare multiple scenarios** before making decisions
4. **Consult local experts** alongside platform recommendations
5. **Keep app updated** for latest features and data
6. **Use offline mode** in remote areas, sync when back online
7. **Share feedback** to help us improve the platform

---

**Thank you for using Eco Nojin!**

*Together, we can restore ecosystems and build sustainable agriculture.*