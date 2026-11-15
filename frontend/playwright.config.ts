import { existsSync } from "node:fs";
import { defineConfig, devices } from "@playwright/test";

/**
 * Prueba de punta a punta. Por defecto levanta su propio backend (SQLite temporal con los datos
 * reales del repositorio y un admin) y el build del frontend. Para probar otro despliegue
 * (p. ej., docker compose en :8080) defina E2E_BASE_URL, E2E_EMAIL y E2E_CONTRASENA.
 * El navegador: PLAYWRIGHT_CHROMIUM, /usr/bin/chromium si existe, o el de `npx playwright install`.
 */
const externo = process.env.E2E_BASE_URL;
const puertoApi = process.env.E2E_PUERTO_API ?? "8799";
const chromium = process.env.PLAYWRIGHT_CHROMIUM ?? (existsSync("/usr/bin/chromium") ? "/usr/bin/chromium" : undefined);

export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.e2e.ts",
  timeout: 60_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: externo ?? "http://127.0.0.1:4174",
    trace: "retain-on-failure",
    locale: "es-PE",
    launchOptions: chromium ? { executablePath: chromium } : {},
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: externo
    ? undefined
    : [
        {
          command: "sh e2e/servidor-api.sh",
          url: `http://127.0.0.1:${puertoApi}/api/v1/salud/lista`,
          timeout: 120_000,
          reuseExistingServer: false,
        },
        {
          command: "npm run build && npx vite preview --port 4174 --strictPort --host 127.0.0.1",
          url: "http://127.0.0.1:4174",
          env: { VITE_PROXY_API: `http://127.0.0.1:${puertoApi}` },
          timeout: 180_000,
          reuseExistingServer: false,
        },
      ],
});
