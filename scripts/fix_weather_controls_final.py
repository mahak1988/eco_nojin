#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Fix: Replace ALL icons with Unicode Emojis
=================================================
Problem: @ant-design/icons@5.6.1 missing many icons from v6.x
Solution: Replace ALL icon components with Unicode emojis
Benefits:
- Zero dependency on @ant-design/icons
- Always works (emojis are built into OS)
- Better cinematic/visual appearance
- Cross-platform compatible
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
WEATHER_CONTROLS = FRONTEND / "src" / "components" / "cinematic" / "WeatherControls.tsx"


def ok(m): print(f"[OK] {m}")
def info(m): print(f"[INFO] {m}")
def err(m): print(f"[ERROR] {m}")


def setup_git_path():
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]


# Completely rewritten WeatherControls with emojis instead of icons
WEATHER_CONTROLS_EMOJI = '''import { useWeatherStore, WeatherCondition, TimeOfDay } from '../../hooks/useWeatherStore';
import { useArtisticStore } from '../../hooks/useArtisticStore';
import { Card, Slider, Button, Space, Typography, Row, Col, Divider } from 'antd';
import { useState } from 'react';

const { Text } = Typography;

// Use Unicode emojis instead of @ant-design/icons
// Benefits: no dependency, always works, more cinematic
const conditions: { value: WeatherCondition; label: string; emoji: string }[] = [
  { value: 'clear', label: 'آفتابی', emoji: '☀️' },
  { value: 'rain', label: 'باران', emoji: '🌧️' },
  { value: 'snow', label: 'برف', emoji: '❄️' },
  { value: 'dust', label: 'ریزگرد', emoji: '🌫️' },
  { value: 'drought', label: 'خشکسالی', emoji: '🏜️' },
  { value: 'storm', label: 'طوفان', emoji: '⛈️' },
];

const times: { value: TimeOfDay; label: string; emoji: string }[] = [
  { value: 'dawn', label: 'طلوع', emoji: '🌅' },
  { value: 'day', label: 'روز', emoji: '☀️' },
  { value: 'dusk', label: 'غروب', emoji: '🌇' },
  { value: 'night', label: 'شب', emoji: '🌙' },
];

const agriculturalFeatures = [
  { key: 'enableInsects', label: 'حشرات', emoji: '🐝' },
  { key: 'enableDomesticAnimals', label: 'دام', emoji: '🐄' },
  { key: 'enablePoultry', label: 'طیور', emoji: '🐔' },
  { key: 'enableFlood', label: 'سیلاب', emoji: '🌊' },
  { key: 'enableIrrigation', label: 'آبیاری', emoji: '💧' },
  { key: 'enableWell', label: 'چاه', emoji: '⛲' },
  { key: 'enableRiver', label: 'رودخانه', emoji: '🏞️' },
  { key: 'enableCoastline', label: 'ساحل', emoji: '🏖️' },
  { key: 'enableWatershed', label: 'آبخیزداری', emoji: '🏗️' },
  { key: 'enablePlowing', label: 'شخم‌زنی', emoji: '🚜' },
];

const artisticEffects = [
  { key: 'enableAurora', label: 'شفق قطبی', emoji: '🌌' },
  { key: 'enableRainbow', label: 'رنگین‌کمان', emoji: '🌈' },
  { key: 'enableFireflies', label: 'کرم شب‌تاب', emoji: '✨' },
  { key: 'enableBirds', label: 'پرندگان', emoji: '🦅' },
  { key: 'enableButterflies', label: 'پروانه', emoji: '🦋' },
  { key: 'enableGodRays', label: 'پرتو خورشید', emoji: '☀️' },
  { key: 'enableLetterbox', label: 'لترباکس', emoji: '🎬' },
  { key: 'enableFilmGrain', label: 'گرین فیلم', emoji: '📽️' },
];

export function WeatherControls() {
  const store = useWeatherStore();
  const a = useArtisticStore();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Card
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>🎬 کنترل سینمایی</span>
          <Button type="text" size="small" onClick={() => setCollapsed(!collapsed)}>
            {collapsed ? '▼' : '▲'}
          </Button>
        </div>
      }
      style={{
        position: 'absolute', top: 20, right: 20, width: 380,
        maxHeight: 'calc(100vh - 40px)', overflowY: 'auto',
        background: 'rgba(20, 20, 30, 0.9)', backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)', color: 'white', zIndex: 1000,
      }}
      styles={{
        header: { borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'white' },
        body: { color: 'white', padding: collapsed ? 0 : 16 },
      }}
    >
      {!collapsed && (
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          {/* Weather Condition */}
          <div>
            <Text strong style={{ color: '#aaa' }}>🌤️ آب و هوا</Text>
            <Row gutter={[6, 6]} style={{ marginTop: 6 }}>
              {conditions.map((c) => (
                <Col key={c.value} span={8}>
                  <Button
                    type={store.condition === c.value ? 'primary' : 'default'}
                    onClick={() => store.setCondition(c.value)}
                    block size="small"
                    style={{ fontSize: 13 }}
                  >
                    {c.emoji} {c.label}
                  </Button>
                </Col>
              ))}
            </Row>
          </div>

          {/* Time of Day */}
          <div>
            <Text strong style={{ color: '#aaa' }}>⏰ زمان روز</Text>
            <Row gutter={[6, 6]} style={{ marginTop: 6 }}>
              {times.map((t) => (
                <Col key={t.value} span={6}>
                  <Button
                    type={store.timeOfDay === t.value ? 'primary' : 'default'}
                    onClick={() => store.setTimeOfDay(t.value)}
                    block size="small"
                  >
                    {t.emoji} {t.label}
                  </Button>
                </Col>
              ))}
            </Row>
          </div>

          {/* Wind */}
          <div>
            <Text strong style={{ color: '#aaa' }}>💨 باد: {store.windSpeed} km/h</Text>
            <Slider min={0} max={100} value={store.windSpeed}
              onChange={(v) => store.setWind(v, store.windDirection)} />
          </div>

          {/* Plant Growth */}
          <div>
            <Text strong style={{ color: '#aaa' }}>🌱 رشد گیاه: {Math.round(store.plantGrowthStage * 100)}%</Text>
            <Slider min={0} max={100} value={store.plantGrowthStage * 100}
              onChange={(v) => store.setPlantGrowth(v / 100)} />
          </div>

          <Divider style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '8px 0' }} />

          {/* Agricultural Features */}
          <div>
            <Text strong style={{ color: '#feca57', fontSize: 13 }}>🌾 اکوسیستم کشاورزی</Text>
            <Row gutter={[8, 8]} style={{ marginTop: 8 }}>
              {agriculturalFeatures.map(({ key, label, emoji }) => (
                <Col key={key} span={12}>
                  <Button
                    type={(a as any)[key] ? 'primary' : 'default'}
                    onClick={() => a.toggle(key)}
                    block size="small"
                    style={{ textAlign: 'right' }}
                  >
                    {emoji} {label}
                  </Button>
                </Col>
              ))}
            </Row>
          </div>

          <Divider style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '8px 0' }} />

          {/* Artistic Effects */}
          <div>
            <Text strong style={{ color: '#feca57', fontSize: 13 }}>✨ جلوه‌های هنری</Text>
            <Row gutter={[8, 8]} style={{ marginTop: 8 }}>
              {artisticEffects.map(({ key, label, emoji }) => (
                <Col key={key} span={12}>
                  <Button
                    type={(a as any)[key] ? 'primary' : 'default'}
                    onClick={() => a.toggle(key)}
                    block size="small"
                  >
                    {emoji} {label}
                  </Button>
                </Col>
              ))}
            </Row>
          </div>
        </Space>
      )}
    </Card>
  );
}
'''


def main():
    print("")
    print("=" * 70)
    print("  Final Fix: Replace ALL Icons with Unicode Emojis")
    print("=" * 70)
    print("")

    setup_git_path()

    # Step 1: Write completely new file
    print("[Step 1] Rewriting WeatherControls.tsx with emojis")
    print("-" * 70)
    
    WEATHER_CONTROLS.write_text(WEATHER_CONTROLS_EMOJI, encoding="utf-8")
    ok("Wrote new WeatherControls.tsx")
    
    info("Changes:")
    info("  - Removed ALL @ant-design/icons imports")
    info("  - Replaced with Unicode emojis")
    info("  - Better visual appearance")
    info("  - No dependency issues")
    print("")

    # Step 2: Build verification
    print("[Step 2] Building project")
    print("-" * 70)
    info("This will take 1-2 minutes...")
    
    result = subprocess.run(
        "pnpm build",
        shell=True, cwd=FRONTEND,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300,
    )
    
    build_ok = result.returncode == 0
    output = result.stdout + result.stderr
    
    if build_ok:
        ok("🎉 Build successful!")
        
        print("\n  Bundle sizes:")
        for line in output.splitlines():
            if "dist/assets/" in line and ("kB" in line or "MB" in line):
                if any(k in line for k in ["vendor", "index", "HyDroMaCenter", "cinematic"]):
                    print(f"    {line.strip()}")
    else:
        err("Build still failing")
        print("\n  Error output (last 25 lines):")
        for line in output.splitlines()[-25:]:
            if line.strip():
                print(f"    {line}")
    print("")

    # Step 3: Commit if successful
    if build_ok:
        print("[Step 3] Committing fix")
        print("-" * 70)
        try:
            subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
            msg = (
                "fix(icons): replace all @ant-design/icons with Unicode emojis\\n\\n"
                "Problem:\\n"
                "- Multiple missing icons in @ant-design/icons@5.6.1\\n"
                "- CloudSnowOutlined, CloudRainOutlined, WindOutlined, etc. missing\\n"
                "- Kept hitting MISSING_EXPORT errors\\n\\n"
                "Solution:\\n"
                "- Completely removed @ant-design/icons from WeatherControls\\n"
                "- Replaced with Unicode emojis (☀️🌧️❄️🌫️🏜️⛈️🌅🌙🐝🐄🐔🌊💧⛲🏞️🏖️🏗️🚜🌌🌈✨🦅🦋🎬📽️)\\n\\n"
                "Benefits:\\n"
                "- Zero dependency on @ant-design/icons\\n"
                "- Always works (emojis built into OS)\\n"
                "- Better cinematic/visual appearance\\n"
                "- Cross-platform compatible\\n\\n"
                "Cinematic agricultural simulator now accessible at:\\n"
                "- http://localhost:5173/hydroma"
            )
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            print(f"[WARN] {e}")
        
        print("")
        print("=" * 70)
        print("  🎉 FIX SUCCESSFUL!")
        print("=" * 70)
        print("")
        print("  ✅ All icons replaced with Unicode emojis!")
        print("")
        print("  Next steps:")
        print("    cd D:\\eco_nojin\\frontend")
        print("    pnpm dev")
        print("    Visit: http://localhost:5173/hydroma")
        print("")
        print("  🌾 Agricultural Cinematic Simulator Ready!")
        print("    ☀️🌧️❄️🌫️🏜️⛈️ Weather effects")
        print("    🐝🐄🐔 Insects, Animals, Poultry")
        print("    🌊💧⛲🏞️🏖️🏗️🚜 Water & Land features")
        print("    🌌🌈✨🦅🦋🎬 Artistic effects")
        print("")
    
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())