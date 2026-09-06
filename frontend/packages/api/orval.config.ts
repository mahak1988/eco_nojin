import { defineConfig } from 'orval';

export default defineConfig({
  eco: {
    output: {
      mode: 'tags-split',
      target: 'src/generated/endpoints',
      schemas: 'src/generated/schemas',
      client: 'axios',
      prettier: false,
      clean: true,
      override: {
        mutator: {
          path: './src/mutator.ts',
          name: 'customAxios',
        },
        operations: {
          getDashboardOverview: { operationName: 'getDashboardOverview' },
          postCarbonCalculate: { operationName: 'postCarbonCalculate' },
          getCarbonProjects: { operationName: 'getCarbonProjects' },
          getModelsList: { operationName: 'getModelsList' },
          postMotorsRun: { operationName: 'postMotorsRun' },
          postSatelliteAnalyze: { operationName: 'postSatelliteAnalyze' },
          postSoilAnalyze: { operationName: 'postSoilAnalyze' },
          postClimateDrought: { operationName: 'postClimateDrought' },
          getWeather: { operationName: 'getWeather' },
          getSatelliteHistory: { operationName: 'getSatelliteHistory' },
        },
      },
    },
    input: {
      target: './openapi.json',
    },
  },
});