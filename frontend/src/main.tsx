import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ErrorApi } from "./api/cliente";
import { App } from "./App";
import "./estilos/global.css";
import { ProveedorIdioma } from "./lib/i18n";
import { ProveedorSesion } from "./lib/sesion";
import { ProveedorTema } from "./lib/tema";

const cliente = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      // No reintentar errores del cliente (4xx): el contrato ya dijo que no.
      retry: (intentos, error) => !(error instanceof ErrorApi && error.status >= 400 && error.status < 500) && intentos < 2,
    },
  },
});

const raiz = document.getElementById("root");
if (!raiz) throw new Error("Falta el elemento #root");

createRoot(raiz).render(
  <StrictMode>
    <QueryClientProvider client={cliente}>
      <BrowserRouter>
        <ProveedorTema>
          <ProveedorIdioma>
            <ProveedorSesion>
              <App />
            </ProveedorSesion>
          </ProveedorIdioma>
        </ProveedorTema>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
