# E2E Tests - Playwright

## Overview

This directory contains end-to-end tests using Playwright.

## Running Tests

Always run commands from the frontend directory:

    cd D:\eco_nojin\frontend

### Run all E2E tests

    pnpm test:e2e

### Run with UI mode (visual debugger)

    pnpm test:e2e:ui

### Run in debug mode

    pnpm test:e2e:debug

### Run specific test file

    pnpm exec playwright test e2e/tests/home.spec.ts

## Running Coverage

    pnpm test:coverage

Output: coverage/index.html

## Test Categories

### 1. Home Page (home.spec.ts)

- Page load verification
- Responsive layout testing

### 2. Navigation (navigation.spec.ts)

- Multi-page navigation
- 404 handling

### 3. Authentication (auth.spec.ts)

- Login form rendering
- Register form rendering

## Directory Structure

    frontend/
      e2e/
        tests/
          home.spec.ts
          navigation.spec.ts
          auth.spec.ts
        README.md
      playwright.config.ts    (root config)
      vitest.config.ts        (with coverage)
      package.json            (with all scripts)

## Important Notes

- Always run commands from frontend/ directory
- E2E tests automatically start dev server
- Coverage report: frontend/coverage/index.html
- Playwright report: frontend/playwright-report/index.html
