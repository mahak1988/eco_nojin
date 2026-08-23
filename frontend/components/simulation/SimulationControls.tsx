'use client';

import { Button } from '../ui/button'; // Updated import path
import { Input } from '../ui/input'; // Updated import path
import { Label } from '../ui/label'; // Updated import path
import { Card, CardContent } from '../ui/card'; // Updated import path
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'; // Updated import path
import { SimulationParams } from '../../types/simulation'; // Updated import path
import { useState } from 'react';

interface SimulationControlsProps {
  onSubmit: (params: SimulationParams) => void;
  isLoading: boolean;
  initialParams: SimulationParams;
}

export function SimulationControls({ onSubmit, isLoading, initialParams }: SimulationControlsProps) {
  const [baselineTemp, setBaselineTemp] = useState(initialParams.baseline_temp?.toString() || '20');
  const [baselinePrecip, setBaselinePrecip] = useState(initialParams.baseline_precip?.toString() || '500');
  const [scenario, setScenario] = useState(initialParams.scenario || 'ssp245');
  const [targetYear, setTargetYear] = useState(initialParams.target_year?.toString() || '2030');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      baseline_temp: parseFloat(baselineTemp),
      baseline_precip: parseFloat(baselinePrecip),
      scenario,
      target_year: parseInt(targetYear),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardContent className="pt-6">
            <Label htmlFor="baselineTemp">Baseline Temperature (°C)</Label>
            <Input
              id="baselineTemp"
              type="number"
              value={baselineTemp}
              onChange={(e) => setBaselineTemp(e.target.value)}
              placeholder="e.g., 20"
              min="-50"
              max="50"
              step="0.1"
              required
            />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <Label htmlFor="baselinePrecip">Baseline Precipitation (mm)</Label>
            <Input
              id="baselinePrecip"
              type="number"
              value={baselinePrecip}
              onChange={(e) => setBaselinePrecip(e.target.value)}
              placeholder="e.g., 500"
              min="0"
              step="1"
              required
            />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <Label htmlFor="scenario">Climate Scenario</Label>
            <Select value={scenario} onValueChange={setScenario} required>
              <SelectTrigger id="scenario">
                <SelectValue placeholder="Select a scenario" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ssp126">SSP1-2.6 (Low)</SelectItem>
                <SelectItem value="ssp245">SSP2-4.5 (Medium)</SelectItem>
                <SelectItem value="ssp370">SSP3-7.0 (High)</SelectItem>
                <SelectItem value="ssp585">SSP5-8.5 (Very High)</SelectItem>
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <Label htmlFor="targetYear">Target Year</Label>
            <Input
              id="targetYear"
              type="number"
              value={targetYear}
              onChange={(e) => setTargetYear(e.target.value)}
              placeholder="e.g., 2030"
              min="2024"
              max="2100"
              required
            />
          </CardContent>
        </Card>
      </div>

      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? 'Running Simulation...' : 'Run Simulation'}
      </Button>
    </form>
  );
}