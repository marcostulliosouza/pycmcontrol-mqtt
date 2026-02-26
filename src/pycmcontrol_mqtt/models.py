from __future__ import annotations
import base64
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Serial:
    codigo: str

    def to_dict(self) -> Dict[str, Any]:
        return {"codigo": self.codigo}


@dataclass(frozen=True)
class Evidence:
    """
    Evidência (doc 'Evidência'):
      - nome, extensao, conteudo (base64)
      - descricao (opcional)
      - observacao (opcional)
    """

    nome: str
    extensao: str
    conteudo: str
    descricao: str = ""
    observacao: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "nome": self.nome,
            "extensao": self.extensao,
            "conteudo": self.conteudo,
        }
        if self.descricao:
            d["descricao"] = self.descricao
        if self.observacao:
            d["observacao"] = self.observacao
        return d
    @staticmethod
    def from_text(
        *,
        nome: str,
        extensao: str,
        texto: str,
        descricao: str = "",
        observacao: str = "",
        encoding: str = "utf-8",
    ) -> "Evidence":
        conteudo = base64.b64encode(texto.encode(encoding)).decode("ascii")
        return Evidence(
            nome=nome,
            extensao=extensao,
            conteudo=conteudo,
            descricao=descricao,
            observacao=observacao,
        )

    @staticmethod
    def from_file(
        path: str | Path,
        *,
        nome: str | None = None,
        extensao: str | None = None,
        descricao: str = "",
        observacao: str = "",
    ) -> "Evidence":
        p = Path(path)
        data = p.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        n = nome or p.stem
        ext = extensao or p.suffix.lstrip(".")
        if not ext:
            raise ValueError("Arquivo sem extensão. Informe 'extensao=' explicitamente.")
        return Evidence(nome=n, extensao=ext, conteudo=b64, descricao=descricao, observacao=observacao)

@dataclass(frozen=True)
class OrdemTransporte:
    """
    OrdemTransporte (doc 'OrdemTransporte'):
      - codigo
      - acao (default APONTAR_TRANSPORTE)
    """
    codigo: str
    acao: str = "APONTAR_TRANSPORTE"

    def to_dict(self) -> Dict[str, Any]:
        return {"codigo": self.codigo, "acao": self.acao}


@dataclass(frozen=True)
class Apontamento:
    """
    Apontamento (doc 'Apontamento'):
      - ok: bool
      - seriais: lista de Serial (quando serializado)
      - evidencias: lista de Evidence (se obrigatório na operação)
    """
    ok: bool = True
    serial: Optional[Serial] = None
    seriais_vinculados: Optional[List[Serial]] = None
    evidencias: Optional[List[Evidence]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"ok": bool(self.ok)}

        # modo simples: 1 serial
        if self.serial is not None:
            d["seriais"] = [self.serial.to_dict()]

        # modo vinculação: 2+ seriais com regra (não usar como lote!)
        elif self.seriais_vinculados is not None:
            d["seriais"] = [s.to_dict() for s in self.seriais_vinculados]

        if self.evidencias:
            d["evidencias"] = [e.to_dict() for e in self.evidencias]
        return d


@dataclass(frozen=True)
class SetupApontamento:
    """
    Setup (doc 'Setup'):
      - enderecoDispositivo (quando idSessao/idView forem nulos)
      - ciclo (opcional): VALIDAR_ROTA etc.
      - ordemTransporte (opcional)
      - apontamentos: lista de Apontamento (obrigatório)
    """
    enderecoDispositivo: str
    apontamentos: Optional[List[Apontamento]] = None
    ciclo: str = ""
    ordemTransporte: Optional[OrdemTransporte] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"enderecoDispositivo": self.enderecoDispositivo}

        if self.apontamentos is not None:
            d["apontamentos"] = [a.to_dict() for a in self.apontamentos]

        if self.ciclo:
            d["ciclo"] = self.ciclo
        if self.ordemTransporte:
            d["ordemTransporte"] = self.ordemTransporte.to_dict()
        return d