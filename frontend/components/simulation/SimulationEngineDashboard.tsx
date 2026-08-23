'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'; // Updated import path
import { SimulationControls } from './SimulationControls';
import { ResultsChart } from './ResultsChart';
import { LiveAnimationPanel } from './LiveAnimationPanel';

// Define types for simulation data
type SimulationResult = {
  year: number;
  yield: number;
  profit: number;
  co2_absorbed: number;
  water_usage: number;
};

type SimulationParams = {
  baseline_temp: number;
  baseline_precip: number;
  scenario: string;
  target_year: number;
  // Add other parameters as needed
};

interface SimulationEngineDashboardProps {
  initialResults?: SimulationResult[];
  initialParams?: SimulationParams;
}

export function SimulationEngineDashboard({ initialResults = [], initialParams = {} as SimulationParams }: SimulationEngineDashboardProps) {
  const [results, setResults] = useState<SimulationResult[]>(initialResults);
  const [params, setParams] = useState<SimulationParams>(initialParams);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch data from the backend simulation endpoint
  const fetchData = async (scenarioParams: SimulationParams) => {
    setIsLoading(true);
    try {
      // Call the backend endpoint
      const response = await fetch('http://127.0.0.1:8000/api/v1/scenarios/apply', { // Adjust URL if needed
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Authorization header might be needed depending on backend setup
          // 'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          baseline_temp: scenarioParams.baseline_temp,
          baseline_precip: scenarioParams.baseline_precip,
          scenario: scenarioParams.scenario,
          year: scenarioParams.target_year,
          // Include farm_id and user_id if required by backend
          // farm_id: 1, // example
          // user_id: 1, // example
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`);
      }

      const data = await response.json();
      console.log('Raw backend response:', data); // Log raw data

      // Transform backend data to fit our chart format
      // This assumes the backend returns a structure similar to ScenarioRun or a direct result
      // Example transformation (adjust based on actual backend response):
      // If backend returns a single result object, we might need to simulate multi-year data or fetch historical/related data.
      // For now, we'll create a mock structure based on the single result or use the apply_scenario result if it has time-series potential.
      // Let's assume 'data' contains keys like projected_temp, temp_change, etc.
      // We'll need a way to generate multi-year data or fetch a series from the DB via another endpoint like /compare.
      // For this example, we'll create a simple mock based on the single result.
      const transformedData: SimulationResult[] = Array.from({ length: 5 }, (_, i) => ({
        year: scenarioParams.target_year - 2 + i, // e.g., target year -2, -1, 0, +1, +2
        yield: Math.random() * 10 + 5 + (i * 0.5), // Mock yield changing over time
        profit: Math.random() * 5000 + 2000 + (i * 200), // Mock profit
        co2_absorbed: Math.random() * 100 + 50 + (i * 10), // Mock CO2
        water_usage: Math.random() * 1000 + 500 - (i * 50), // Mock water usage
      }));

      setResults(transformedData);
      setParams(scenarioParams);
    } catch (error) {
      console.error('Failed to fetch simulation data from backend:', error);
      // Optionally, show an error message to the user
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Simulation Engine Dashboard</CardTitle>
        </CardHeader>
        <CardContent>
          <SimulationControls onSubmit={fetchData} isLoading={isLoading} initialParams={params} />
        </CardContent>
      </Card>

      {results.length > 0 && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Simulation Results</CardTitle>
            </CardHeader>
            <CardContent>
              <ResultsChart data={results} />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Live Animation</CardTitle>
            </CardHeader>
            <CardContent>
              <LiveAnimationPanel data={results} />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}