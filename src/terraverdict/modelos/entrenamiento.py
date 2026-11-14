"""Entrenamiento reproducible con parada temprana sobre el conjunto de validación."""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field

import numpy as np
import torch
from torch import nn


@dataclass
class Historia:
    perdida_entrenamiento: list[float] = field(default_factory=list)
    perdida_validacion: list[float] = field(default_factory=list)
    mejor_epoca: int = 0
    segundos: float = 0.0


def fijar_semilla(semilla: int) -> None:
    torch.manual_seed(semilla)
    np.random.seed(semilla)
    torch.set_num_threads(max(1, min(4, torch.get_num_threads())))


def _perdida(tarea: str, peso_positivo: float | None) -> nn.Module:
    if tarea == "clasificacion":
        return nn.BCEWithLogitsLoss(pos_weight=None if peso_positivo is None else torch.tensor([peso_positivo]))
    if tarea == "conteo":
        return nn.PoissonNLLLoss(log_input=True)
    return nn.MSELoss()


def entrenar(
    modelo: nn.Module,
    X_tr: np.ndarray,
    y_tr: np.ndarray,
    X_va: np.ndarray,
    y_va: np.ndarray,
    *,
    tarea: str = "regresion",
    epocas: int = 80,
    lote: int = 128,
    lr: float = 1e-3,
    paciencia: int = 10,
    peso_positivo: float | None = None,
    semilla: int = 0,
    decaimiento: float = 1e-4,
) -> tuple[nn.Module, Historia]:
    fijar_semilla(semilla)
    xt, yt = torch.tensor(X_tr, dtype=torch.float32), torch.tensor(y_tr, dtype=torch.float32).reshape(len(y_tr), -1)
    xv, yv = torch.tensor(X_va, dtype=torch.float32), torch.tensor(y_va, dtype=torch.float32).reshape(len(y_va), -1)
    criterio = _perdida(tarea, peso_positivo)
    opt = torch.optim.AdamW(modelo.parameters(), lr=lr, weight_decay=decaimiento)
    generador = torch.Generator().manual_seed(semilla)
    mejor, mejor_estado, sin_mejora = float("inf"), copy.deepcopy(modelo.state_dict()), 0
    h = Historia()
    inicio = time.perf_counter()
    for epoca in range(epocas):
        modelo.train()
        orden = torch.randperm(len(xt), generator=generador)
        total = 0.0
        for i in range(0, len(xt), lote):
            idx = orden[i : i + lote]
            opt.zero_grad()
            perdida = criterio(modelo(xt[idx]), yt[idx])
            perdida.backward()
            nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
            opt.step()
            total += perdida.item() * len(idx)
        modelo.eval()
        with torch.no_grad():
            pv = criterio(modelo(xv), yv).item()
        h.perdida_entrenamiento.append(total / len(xt))
        h.perdida_validacion.append(pv)
        if pv < mejor - 1e-6:
            mejor, mejor_estado, sin_mejora, h.mejor_epoca = pv, copy.deepcopy(modelo.state_dict()), 0, epoca
        else:
            sin_mejora += 1
            if sin_mejora >= paciencia:
                break
    modelo.load_state_dict(mejor_estado)
    modelo.eval()
    h.segundos = time.perf_counter() - inicio
    return modelo, h


def predecir(modelo: nn.Module, X: np.ndarray, tarea: str = "regresion") -> np.ndarray:
    with torch.no_grad():
        salida = modelo(torch.tensor(X, dtype=torch.float32)).numpy().reshape(len(X), -1)[:, 0]
    if tarea == "clasificacion":
        return 1 / (1 + np.exp(-salida))
    if tarea == "conteo":
        return np.exp(salida)
    return salida
