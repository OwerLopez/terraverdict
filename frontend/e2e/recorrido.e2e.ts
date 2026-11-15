import { expect, test } from "@playwright/test";

const EMAIL = process.env.E2E_EMAIL ?? "e2e@terraverdict.pe";
const CONTRASENA = process.env.E2E_CONTRASENA ?? "contrasena-e2e-segura";

test("iniciar sesión, ver el panel, abrir un expediente y verificar cifras", async ({ page }) => {
  // Panel y aviso permanente
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Arequipa se queda sin agua");
  await expect(page.getByRole("note")).toContainText("No son alertas oficiales");
  await expect(page.getByText("API en línea")).toBeVisible();

  // Iniciar sesión
  await page.getByRole("button", { name: "Iniciar sesión" }).first().click();
  const dialogo = page.getByRole("dialog");
  await dialogo.getByLabel("Correo").fill(EMAIL);
  await dialogo.getByLabel("Contraseña").fill(CONTRASENA);
  await dialogo.getByRole("button", { name: "Entrar" }).click();
  await expect(page.getByRole("button", { name: "Cerrar sesión" })).toBeVisible();

  // Abrir un expediente y ver su procedencia
  await page.getByRole("link", { name: "Expedientes" }).first().click();
  const tarjeta = page.locator('a[href^="/expedientes/TV-"]').first();
  const href = await tarjeta.getAttribute("href");
  await tarjeta.click();
  await expect(page).toHaveURL(new RegExp(`${href}$`));
  await expect(page.getByText("Hash del contenido:")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Procedencia" })).toBeVisible();

  // Verificador: el texto propuesto está respaldado; una cifra inventada se marca sin respaldo
  await page.getByRole("link", { name: "Asistente" }).first().click();
  const texto = page.getByLabel("Texto a verificar");
  await expect(texto).not.toHaveValue("");
  await page.getByRole("button", { name: "Verificar cifras" }).click();
  await expect(page.getByText("Todas las cifras están respaldadas")).toBeVisible();

  const original = await texto.inputValue();
  await texto.fill(`${original} Además, la lluvia subió 987,65 mm.`);
  await page.getByRole("button", { name: "Verificar cifras" }).click();
  await expect(page.getByText("1 cifra(s) sin respaldo")).toBeVisible();
  await expect(page.locator('mark[title="Sin respaldo en los expedientes"]')).toHaveText("987,65");
});

test("las vistas de fenómenos cargan con su aviso y sin errores de consola", async ({ page }) => {
  const errores: string[] = [];
  page.on("pageerror", (e) => errores.push(e.message));
  for (const [ruta, titulo] of [
    ["/fenomenos", "Catálogo científico"],
    ["/sismos", "Actividad sísmica"],
    ["/volcanes", "Actividad volcánica"],
    ["/caos", "Dinámica"],
    ["/modelos", "Comparación de modelos"],
  ] as const) {
    await page.goto(ruta);
    await expect(page.getByRole("heading", { level: 1 })).toContainText(titulo);
    await expect(page.getByRole("note")).toContainText("No son alertas oficiales");
  }
  expect(errores).toEqual([]);
});
