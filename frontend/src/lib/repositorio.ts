/** Repositorio público del proyecto: el código que respalda cada cifra se enlaza, no se imprime como ruta. */
export const REPOSITORIO_URL = "https://github.com/OwerLopez/terraverdict";

export function urlCodigo(ruta: string): string {
  return `${REPOSITORIO_URL}/blob/main/${ruta}`;
}
