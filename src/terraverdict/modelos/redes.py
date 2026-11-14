"""Zoológico de redes neuronales para series temporales (PyTorch, CPU).

Todas reciben x de forma (lote, L, F) —L pasos de la ventana, F variables, la variable 0 es el
objetivo— y devuelven (lote, H). Son versiones compactas y fieles a la idea de cada artículo,
dimensionadas para series de miles de muestras (no millones):

- MLP: perceptrón multicapa sobre la ventana aplanada.
- DLinear: Zeng et al. (2023), arXiv:2205.13504 — descomposición tendencia/resto + capas lineales.
- LSTM: Hochreiter y Schmidhuber (1997), doi:10.1162/neco.1997.9.8.1735.
- GRU: Cho et al. (2014), arXiv:1406.1078.
- TCN: Bai, Kolter y Koltun (2018), arXiv:1803.01271 — convoluciones causales dilatadas residuales.
- N-BEATS: Oreshkin et al. (2020), arXiv:1905.10437 — bloques MLP con backcast/forecast.
- N-HiTS: Challu et al. (2023), arXiv:2201.12886 — N-BEATS con agrupamiento multitasa por bloque.
- PatchTST: Nie et al. (2023), arXiv:2211.14730 — parches por canal + codificador Transformer.
- iTransformer: Liu et al. (2024), arXiv:2310.06625 — cada variable es un token; atención entre variables.
- SSM selectivo: inspirado en Mamba (Gu y Dao, 2023, arXiv:2312.00752) y S4 (Gu et al., 2022,
  arXiv:2111.00396). Implementación de referencia en PyTorch puro con barrido secuencial; no es el
  núcleo CUDA optimizado de Mamba.
"""

from __future__ import annotations

import math

import torch
from torch import nn


class MLP(nn.Module):
    def __init__(self, L: int, F: int, H: int = 1, d: int = 64, abandono: float = 0.2):
        super().__init__()
        self.red = nn.Sequential(
            nn.Flatten(),
            nn.Linear(L * F, d),
            nn.GELU(),
            nn.Dropout(abandono),
            nn.Linear(d, d),
            nn.GELU(),
            nn.Linear(d, H),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.red(x)


class DLinear(nn.Module):
    def __init__(self, L: int, F: int, H: int = 1, kernel: int = 7):
        super().__init__()
        k = min(kernel, L if L % 2 == 1 else L - 1)
        self.media = nn.AvgPool1d(k, stride=1, padding=k // 2, count_include_pad=False)
        self.tendencia = nn.Linear(L, H)
        self.resto = nn.Linear(L, H)
        self.mezcla = nn.Linear(F, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        xc = x.transpose(1, 2)  # (B, F, L)
        t = self.media(xc)[..., : xc.shape[-1]]
        y = self.tendencia(t) + self.resto(xc - t)  # (B, F, H)
        return self.mezcla(y.transpose(1, 2)).squeeze(-1)


class Recurrente(nn.Module):
    def __init__(self, L: int, F: int, H: int = 1, d: int = 48, tipo: str = "lstm", abandono: float = 0.2):
        super().__init__()
        celda = nn.LSTM if tipo == "lstm" else nn.GRU
        self.rnn = celda(F, d, num_layers=1, batch_first=True)
        self.salida = nn.Sequential(nn.Dropout(abandono), nn.Linear(d, H))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h, _ = self.rnn(x)
        return self.salida(h[:, -1])


class _BloqueTCN(nn.Module):
    def __init__(self, c_in: int, c_out: int, dilatacion: int, k: int = 3, abandono: float = 0.1):
        super().__init__()
        self.relleno = (k - 1) * dilatacion
        self.c1 = nn.Conv1d(c_in, c_out, k, dilation=dilatacion)
        self.c2 = nn.Conv1d(c_out, c_out, k, dilation=dilatacion)
        self.abandono = nn.Dropout(abandono)
        self.atajo = nn.Conv1d(c_in, c_out, 1) if c_in != c_out else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = self.abandono(torch.relu(self.c1(nn.functional.pad(x, (self.relleno, 0)))))
        y = self.abandono(torch.relu(self.c2(nn.functional.pad(y, (self.relleno, 0)))))
        return torch.relu(y + self.atajo(x))


class TCN(nn.Module):
    def __init__(self, L: int, F: int, H: int = 1, d: int = 32, niveles: int = 4):
        super().__init__()
        capas = [_BloqueTCN(F if i == 0 else d, d, 2**i) for i in range(niveles)]
        self.red = nn.Sequential(*capas)
        self.salida = nn.Linear(d, H)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.salida(self.red(x.transpose(1, 2))[..., -1])


class _BloqueNBeats(nn.Module):
    def __init__(self, entrada: int, H: int, d: int, agrupar: int = 1, L: int = 1, F: int = 1):
        super().__init__()
        self.agrupar, self.L, self.F = agrupar, L, F
        tam = entrada if agrupar == 1 else F * math.ceil(L / agrupar)
        self.mlp = nn.Sequential(nn.Linear(tam, d), nn.ReLU(), nn.Linear(d, d), nn.ReLU(), nn.Linear(d, d), nn.ReLU())
        self.backcast = nn.Linear(d, entrada)
        self.forecast = nn.Linear(d, H)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        z = x
        if self.agrupar > 1:  # N-HiTS: agrupamiento máximo multitasa sobre el tiempo
            z = x.view(-1, self.L, self.F).transpose(1, 2)
            z = nn.functional.max_pool1d(z, self.agrupar, self.agrupar, ceil_mode=True).flatten(1)
        h = self.mlp(z)
        return self.backcast(h), self.forecast(h)


class NBeats(nn.Module):
    def __init__(
        self, L: int, F: int, H: int = 1, d: int = 96, bloques: int = 3, agrupamientos: list[int] | None = None
    ):
        super().__init__()
        agrupamientos = agrupamientos or [1] * bloques
        self.H = H
        self.bloques = nn.ModuleList([_BloqueNBeats(L * F, H, d, a, L, F) for a in agrupamientos])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        resto = x.flatten(1)
        pronostico = x.new_zeros(x.shape[0], self.H)
        for b in self.bloques:
            back, fore = b(resto)
            resto = resto - back
            pronostico = pronostico + fore
        return pronostico


def NHiTS(L: int, F: int, H: int = 1, d: int = 96) -> NBeats:
    return NBeats(L, F, H, d, bloques=3, agrupamientos=[max(1, L // 4), max(1, L // 8), 1])


class PatchTST(nn.Module):
    def __init__(
        self, L: int, F: int, H: int = 1, d: int = 32, parche: int = 8, paso: int = 4, capas: int = 2, cabezas: int = 4
    ):
        super().__init__()
        self.parche, self.paso = min(parche, L), min(paso, max(1, L // 2))
        n = (L - self.parche) // self.paso + 1
        self.embebido = nn.Linear(self.parche, d)
        self.posicion = nn.Parameter(torch.zeros(1, n, d))
        capa = nn.TransformerEncoderLayer(d, cabezas, dim_feedforward=2 * d, dropout=0.1, batch_first=True)
        self.codificador = nn.TransformerEncoder(capa, capas)
        self.cabeza = nn.Linear(n * d, H)
        self.mezcla = nn.Linear(F, 1)
        self.F = F

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B = x.shape[0]
        canales = x.transpose(1, 2).reshape(B * self.F, -1)  # independencia de canal
        parches = canales.unfold(1, self.parche, self.paso)  # (B·F, n, parche)
        z = self.codificador(self.embebido(parches) + self.posicion)
        y = self.cabeza(z.flatten(1)).view(B, self.F, -1)  # (B, F, H)
        return self.mezcla(y.transpose(1, 2)).squeeze(-1)


class ITransformer(nn.Module):
    def __init__(self, L: int, F: int, H: int = 1, d: int = 32, capas: int = 2, cabezas: int = 4):
        super().__init__()
        self.token = nn.Linear(L, d)  # cada variable (su ventana completa) es un token
        capa = nn.TransformerEncoderLayer(d, cabezas, dim_feedforward=2 * d, dropout=0.1, batch_first=True)
        self.codificador = nn.TransformerEncoder(capa, capas)
        self.salida = nn.Linear(d, H)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.codificador(self.token(x.transpose(1, 2)))  # (B, F, d): atención entre variables
        return self.salida(z[:, 0])  # token de la variable objetivo


class _CapaSelectiva(nn.Module):
    def __init__(self, d: int, n_estado: int = 8):
        super().__init__()
        self.delta = nn.Linear(d, d)
        self.B = nn.Linear(d, n_estado)
        self.C = nn.Linear(d, n_estado)
        self.A_log = nn.Parameter(torch.log(torch.arange(1, n_estado + 1, dtype=torch.float32)).repeat(d, 1))
        self.D = nn.Parameter(torch.ones(d))
        self.puerta = nn.Linear(d, d)
        self.norma = nn.LayerNorm(d)

    def forward(self, u: torch.Tensor) -> torch.Tensor:
        Bsz, L, d = u.shape
        delta = nn.functional.softplus(self.delta(u))  # paso de discretización dependiente de la entrada
        Bm, Cm = self.B(u), self.C(u)
        A = -torch.exp(self.A_log)  # (d, N), estable
        h = torch.zeros(Bsz, d, A.shape[1], device=u.device)
        salidas = []
        for t in range(L):
            dA = torch.exp(delta[:, t, :, None] * A)
            h = dA * h + delta[:, t, :, None] * Bm[:, t, None, :] * u[:, t, :, None]
            salidas.append((h * Cm[:, t, None, :]).sum(-1) + self.D * u[:, t])
        y = torch.stack(salidas, 1) * nn.functional.silu(self.puerta(u))
        return self.norma(u + y)


class SSMSelectivo(nn.Module):
    def __init__(self, L: int, F: int, H: int = 1, d: int = 32, capas: int = 2, n_estado: int = 8):
        super().__init__()
        self.entrada = nn.Linear(F, d)
        self.capas = nn.Sequential(*[_CapaSelectiva(d, n_estado) for _ in range(capas)])
        self.salida = nn.Linear(d, H)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.salida(self.capas(self.entrada(x))[:, -1])


ARQUITECTURAS = {
    "mlp": lambda L, F, H: MLP(L, F, H),
    "dlinear": lambda L, F, H: DLinear(L, F, H),
    "lstm": lambda L, F, H: Recurrente(L, F, H, tipo="lstm"),
    "gru": lambda L, F, H: Recurrente(L, F, H, tipo="gru"),
    "tcn": lambda L, F, H: TCN(L, F, H),
    "nbeats": lambda L, F, H: NBeats(L, F, H),
    "nhits": lambda L, F, H: NHiTS(L, F, H),
    "patchtst": lambda L, F, H: PatchTST(L, F, H),
    "itransformer": lambda L, F, H: ITransformer(L, F, H),
    "ssm_selectivo": lambda L, F, H: SSMSelectivo(L, F, H),
}

REFERENCIAS = {
    "mlp": "Perceptrón multicapa",
    "dlinear": "Zeng et al. (2023), AAAI, arXiv:2205.13504",
    "lstm": "Hochreiter y Schmidhuber (1997), doi:10.1162/neco.1997.9.8.1735",
    "gru": "Cho et al. (2014), arXiv:1406.1078",
    "tcn": "Bai, Kolter y Koltun (2018), arXiv:1803.01271",
    "nbeats": "Oreshkin et al. (2020), ICLR, arXiv:1905.10437",
    "nhits": "Challu et al. (2023), AAAI, arXiv:2201.12886",
    "patchtst": "Nie et al. (2023), ICLR, arXiv:2211.14730",
    "itransformer": "Liu et al. (2024), ICLR, arXiv:2310.06625",
    "ssm_selectivo": "Inspirado en Gu y Dao (2023), arXiv:2312.00752 (implementación de referencia, no el núcleo CUDA)",
}


def contar_parametros(modelo: nn.Module) -> int:
    return int(sum(p.numel() for p in modelo.parameters() if p.requires_grad))
