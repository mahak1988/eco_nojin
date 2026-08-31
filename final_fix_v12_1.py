#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
اصلاح نهایی هیدروما - نسخه ۱۲.۱
فقط اصلاح فاکتور سیل افراطی
============================================================================
"""

# فقط تغییر یک خط در فاکتور سیل:
# از: disaster_factor = 0.15  # flood_depth >= 10
# به: disaster_factor = 0.25  # flood_depth >= 10

class HydromaV12_1:
    """نسخه نهایی با اصلاح سیل"""
    
    def simulate(self, location, crop, disaster=None):
        # ... (همان کد قبلی)
        
        if disaster:
            disaster_type = disaster.get("type", "")
            
            if disaster_type == "flood":
                flood_depth = disaster.get("flood_depth", 0)
                # ✅ اصلاح نهایی
                if flood_depth >= 10:
                    disaster_factor = 0.25  # ✅ افزایش از 0.15
                elif flood_depth >= 5:
                    disaster_factor = 0.35
                # ... (بقیه کد)
        
        # ... (بقیه کد)