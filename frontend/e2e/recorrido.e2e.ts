import { expect, test, type Page } from "@playwright/test";

/**
 * Recorrido de quien evalúa, en inglés (idioma principal): portada, recorrido guiado de 8 pasos por las
 * páginas reales, procedencia de un expediente, verificador numérico y vistas de fenómenos sin errores.
 * La lectura es pública: no hace falta iniciar sesión (el inicio de sesión se prueba en el backend).
 */

function vigilarErrores(page: Page): string[] {
  const errores: string[] = [];
  page.on("pageerror", (e) => errores.push(e.message));
  return errores;
}

test("first visit in English: hero, guided tour across pages, provenance and numeric verifier", async ({ page }) => {
  const errores = vigilarErrores(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Arequipa runs out of water");
  await expect(page.getByRole("note")).toContainText("Not official warnings");
  await expect(page.getByText("API online")).toBeVisible();
  await expect(page.getByText("First time here?")).toBeVisible();

  // Recorrido guiado: cada paso abre su página y resalta un elemento real.
  await page.getByRole("button", { name: "Start the guided tour" }).click();
  const tarjeta = page.getByRole("dialog", { name: "What TerraVerdict solves" });
  await expect(tarjeta).toBeVisible();
  const esperado: [string, RegExp][] = [
    ["Where things stand today", /\/$/],
    ["Five hazards, one verdict each", /\/$/],
    ["3D satellite map of the basin", /\/mapa$/],
    ["Forecast vs reality", /\/modelos$/],
    ["The same engine for all of Peru", /\/peru$/],
    ["Audit: every number has provenance", /\/procesos$/],
    ["Ask Terra, the verified AI", /\/$/],
  ];
  for (const [titulo, ruta] of esperado) {
    await page.getByRole("button", { name: "Next" }).click();
    await expect(page.getByRole("dialog", { name: titulo })).toBeVisible();
    await expect(page).toHaveURL(ruta);
  }
  await page.getByRole("button", { name: "Finish" }).click();
  await expect(page.getByRole("dialog", { name: "Ask Terra, the verified AI" })).toHaveCount(0);

  // Un expediente con su procedencia.
  await page.goto("/expedientes");
  const enlace = page.locator('a[href^="/expedientes/TV-"]').first();
  const href = await enlace.getAttribute("href");
  await enlace.click();
  await expect(page).toHaveURL(new RegExp(`${href}$`));
  await expect(page.getByRole("heading", { name: "Provenance" })).toBeVisible();
  await expect(page.getByText("Content hash:")).toBeVisible();

  // Verificador: el texto propuesto está respaldado; una cifra inventada se marca sin respaldo.
  await page.goto("/asistente");
  const texto = page.getByLabel("Text to verify");
  await expect(texto).not.toHaveValue("");
  await page.getByRole("button", { name: "Verify figures" }).click();
  await expect(page.getByText("All figures are backed")).toBeVisible();
  const original = await texto.inputValue();
  await texto.fill(`${original} Rainfall also rose by 987.65 mm.`);
  await page.getByRole("button", { name: "Verify figures" }).click();
  await expect(page.locator('mark[title="Not backed by the case files"]')).toHaveText("987.65");

  expect(errores).toEqual([]);
});

test("hazard and model views load with their notice and without console errors", async ({ page }) => {
  const errores = vigilarErrores(page);
  for (const [ruta, titulo] of [
    ["/fenomenos", "Scientific catalog"],
    ["/sismos", "Seismic activity"],
    ["/volcanes", "Volcanic activity"],
    ["/caos", "Dynamics"],
    ["/modelos", "Model comparison"],
    ["/metricas", "Metrics, heatmaps and history"],
  ] as const) {
    await page.goto(ruta);
    await expect(page.getByRole("heading", { level: 1 })).toContainText(titulo);
    await expect(page.getByRole("note")).toContainText("Not official warnings");
  }
  expect(errores).toEqual([]);
});

test("Spanish is available as the second language and is remembered", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("radio", { name: "ES", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Arequipa se queda sin agua");
  await page.reload();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Arequipa se queda sin agua");
});
