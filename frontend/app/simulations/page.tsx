import { SimulationEngineDashboard } from '@/components/simulation/SimulationEngineDashboard'; // Updated import path

// Mock initial data for the dashboard - this would come from an API call in a real app
const mockInitialResults = [
  { year: 2024, yield: 5.2, profit: 2100, co2_absorbed: 55, water_usage: 520 },
  { year: 2025, yield: 5.8, profit: 2300, co2_absorbed: 58, water_usage: 510 },
  { year: 2026, yield: 6.1, profit: 2450, co2_absorbed: 60, water_usage: 505 },
];

const mockInitialParams = {
  baseline_temp: 20.5,
  baseline_precip: 510,
  scenario: 'ssp245',
  target_year: 2030,
};

export default function SimulationPage() {
  return (
    <div className="container mx-auto py-10">
      <h1 className="text-3xl font-bold mb-6">Eco Nojin Simulation Engine</h1>
      <SimulationEngineDashboard initialResults={mockInitialResults} initialParams={mockInitialParams} />
    </div>
  );
}