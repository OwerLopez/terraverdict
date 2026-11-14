# Genera la referencia de GR2M con airGR para la prueba de paridad (S5).
# Uso (en tu máquina local):  Rscript tests/fixtures/airgr/generar_gr2m.R
# Salida: tests/fixtures/airgr/gr2m_ref.csv  (se versiona; el test de Python lo lee, no necesita R)
# IMPORTANTE: al terminar, anota en gr2m_ref.meta.json la versión de airGR y los estados iniciales
# usados, y fuerza los MISMOS estados iniciales en la implementación de Python.
suppressMessages(library(airGR))
set.seed(42)
n  <- 240
fechas <- seq(as.Date("2000-01-01"), by = "month", length.out = n)
P  <- pmax(0, rgamma(n, shape = 1.5, scale = 40))          # mm/mes
E  <- pmax(5, 90 + 25 * sin(2 * pi * (seq_len(n) - 1) / 12) + rnorm(n, 0, 5))  # mm/mes
Inputs <- CreateInputsModel(FUN_MOD = RunModel_GR2M, DatesR = as.POSIXct(fechas, tz = "UTC"),
                            Precip = P, PotEvap = E)
Run <- CreateRunOptions(FUN_MOD = RunModel_GR2M, InputsModel = Inputs, IndPeriod_Run = seq_len(n),
                        IniStates = NULL, IniResLevels = NULL, IndPeriod_WarmUp = 0L)
casos <- list(c(X1 = 400, X2 = 0.8), c(X1 = 150, X2 = 0.5), c(X1 = 1200, X2 = 1.4))  # incluye X2 > 1
salida <- do.call(rbind, lapply(seq_along(casos), function(i) {
  o <- RunModel_GR2M(Inputs, Run, casos[[i]])
  data.frame(caso = i, X1 = casos[[i]]["X1"], X2 = casos[[i]]["X2"], fecha = fechas, P = P, E = E, Q = o$Qsim)
}))
write.csv(salida, "tests/fixtures/airgr/gr2m_ref.csv", row.names = FALSE)
writeLines(sprintf('{"airGR": "%s", "R": "%s"}', as.character(packageVersion("airGR")), R.version.string),
           "tests/fixtures/airgr/gr2m_ref.meta.json")
cat("OK ->", nrow(salida), "filas\n")
