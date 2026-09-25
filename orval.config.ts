import { defineConfig } from 'orval';

export default defineConfig({
  ecoNojin: {
    input: {
      target: './openapi.json',
      validate: true,
    },
    output: {
      target: './packages/api-client/src/generated.ts',
      client: 'react-query',
      clean: false,
      override: {
        mutator: {
          path: './packages/api-client/src/mutator.ts',
          name: 'apiRequest',
        },
        query: { useQuery: true, useMutation: true, version: 5 },
      },
    },
  },
});
