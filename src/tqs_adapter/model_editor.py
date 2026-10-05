import os
import sys
import unicodedata
import re
from typing import List, Dict, Optional, Any, Tuple

import src.tqs_adapter.tqs_env
from TQS import TQSBuild, TQSModel, TQSUtil
from src.tqs_adapter.building_reader import TQSBuildingReader

def normalizar_texto(texto: str) -> str:
    """Remove acentos, símbolos ordinais (^, º, °) e converte para maiúsculas para comparações tolerantes."""
    if not texto:
        return ""
    texto = texto.replace("^", " ").replace("º", " ").replace("°", " ").replace("ª", " ")
    nfkd = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return " ".join(sem_acento.upper().split())

class TQSModelEditor:
    """
    Controlador de Leitura e Edição Programática de Elementos do Modelador Estrutural do TQS V25.
    Permite inspecionar e modificar vigas, lajes, pilares e carregamentos distribuídos/adicionais
    de forma segura e em modo headless (batch) através das bibliotecas oficiais do TQS.
    """

    def __init__(self, edificio_nome_ou_caminho: Optional[str] = None):
        self.edificio_alvo = edificio_nome_ou_caminho
        self.caminho_edificio = ""
        self.nome_edificio = ""
        self.cwd_original = os.getcwd()

        self._build: Optional[Any] = None
        self._model: Optional[Any] = None
        self._aberto = False

        if edificio_nome_ou_caminho:
            self._resolver_caminho_edificio(edificio_nome_ou_caminho)

    def _resolver_caminho_edificio(self, identificador: str) -> None:
        """Localiza a pasta do edifício no sistema TQS a partir de nome, código ou caminho."""
        if os.path.isabs(identificador) and os.path.isdir(identificador):
            self.caminho_edificio = os.path.abspath(identificador)
            self.nome_edificio = os.path.basename(self.caminho_edificio)
            return

        edificios = TQSBuildingReader.listar_edificios_disponiveis()
        id_norm = normalizar_texto(identificador)

        # Critério de desempate: prioriza "CA" (Concreto Armado) e processados
        def score_edificio(e: Dict[str, Any]) -> int:
            score = 0
            nome = e["nome"].upper()
            if " CA" in nome or "[CA]" in nome or nome.endswith("CA"):
                score += 10
            if " AE" in nome or "[AE]" in nome:
                score -= 10
            if e.get("processado", False):
                score += 5
            return score

        # Candidatos que batem com o identificador
        candidatos = []
        for ed in edificios:
            ed_norm = normalizar_texto(ed["nome"])
            if id_norm in ed_norm or identificador in ed["nome"]:
                candidatos.append(ed)

        if candidatos:
            candidatos.sort(key=score_edificio, reverse=True)
            melhor = candidatos[0]
            self.caminho_edificio = melhor["caminho"]
            self.nome_edificio = melhor["nome"]
            return

        # 2. Busca por substring nos tokens
        tokens = [t for t in re.split(r"[\s\-_\[\]]+", id_norm) if len(t) >= 2]
        candidatos_tokens = []
        for ed in edificios:
            ed_norm = normalizar_texto(ed["nome"])
            if any(t in ed_norm for t in tokens):
                candidatos_tokens.append(ed)

        if candidatos_tokens:
            candidatos_tokens.sort(key=score_edificio, reverse=True)
            melhor = candidatos_tokens[0]
            self.caminho_edificio = melhor["caminho"]
            self.nome_edificio = melhor["nome"]
            return

        raise FileNotFoundError(f"Edifício '{identificador}' não foi localizado nos diretórios padrão do TQS.")

    def __enter__(self):
        self.abrir()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fechar()

    def abrir(self) -> None:
        """Abre o contexto do edifício e o modelo estrutural no TQS V25."""
        if self._aberto:
            return

        if not self.caminho_edificio:
            raise ValueError("Nenhum edifício foi especificado para o TQSModelEditor.")

        self.cwd_original = os.getcwd()
        os.chdir(self.caminho_edificio)

        self._build = TQSBuild.Building()
        ret_b = self._build.file.Open(self.nome_edificio)
        if ret_b != 0:
            os.chdir(self.cwd_original)
            raise RuntimeError(f"Erro ao abrir dados do edifício '{self.nome_edificio}' (istat={ret_b}).")

        self._build.RootFolder(self.nome_edificio)

        self._model = TQSModel.Model()
        ret_m = self._model.file.OpenModel()
        if ret_m != 0:
            os.chdir(self.cwd_original)
            raise RuntimeError(f"Erro ao abrir modelo estrutural do edifício '{self.nome_edificio}' (istat={ret_m}).")

        self._aberto = True

    def salvar(self) -> None:
        """Salva as alterações do modelo estrutural em disco."""
        if not self._aberto or not self._model:
            raise RuntimeError("O modelo estrutural não está aberto para salvamento.")
        ret = self._model.file.Save()
        if ret != 0:
            raise RuntimeError(f"Erro ao salvar modelo estrutural (istat={ret}).")

    def fechar(self) -> None:
        """Fecha o modelo estrutural e restaura o diretório de trabalho original."""
        if self._aberto:
            try:
                if self._model:
                    self._model.file.Close()
            except Exception:
                pass
            finally:
                self._aberto = False
                self._model = None
                self._build = None
                try:
                    os.chdir(self.cwd_original)
                except Exception:
                    pass

    def _obter_objeto_pavimento(self, nome_pavimento: str) -> Tuple[Any, str]:
        """Localiza a planta do pavimento especificado com tolerância a acentos e maiúsculas."""
        if not self._aberto:
            self.abrir()

        n_floors = self._model.floors.GetNumFloors()
        pav_norm = normalizar_texto(nome_pavimento)

        # Procura correspondência
        nome_real = None
        for i in range(1, n_floors + 1):
            fname = self._model.floors.GetFloorName(i)
            fn_norm = normalizar_texto(fname)
            if fn_norm == pav_norm or pav_norm in fn_norm or fn_norm in pav_norm:
                nome_real = fname
                break

        if not nome_real:
            nomes_disponiveis = [self._model.floors.GetFloorName(i) for i in range(1, n_floors + 1)]
            raise ValueError(
                f"Pavimento '{nome_pavimento}' não encontrado no edifício '{self.nome_edificio}'. "
                f"Pavimentos disponíveis: {nomes_disponiveis}"
            )

        floor = self._model.floors.GetFloor(nome_real)
        return floor, nome_real

    # =========================================================================
    # CONSULTAS (GETTERS / LISTAGEM)
    # =========================================================================

    def listar_pavimentos(self) -> List[Dict[str, Any]]:
        """Retorna todos os pavimentos do edifício com contagem de elementos estruturais."""
        if not self._aberto:
            self.abrir()

        pavimentos = []
        n_floors = self._model.floors.GetNumFloors()
        for i in range(1, n_floors + 1):
            fname = self._model.floors.GetFloorName(i)
            fl = self._model.floors.GetFloor(fname)
            it = fl.iterator
            nv = it.GetNumObjects(TQSModel.TYPE_VIGAS)
            nl = it.GetNumObjects(TQSModel.TYPE_LAJES)
            np = it.GetNumObjects(TQSModel.TYPE_PILARES)
            n_carare = it.GetNumObjects(TQSModel.TYPE_CARARE)
            n_carlin = it.GetNumObjects(TQSModel.TYPE_CARLIN)

            pavimentos.append({
                "indice": i,
                "nome": fname,
                "num_vigas": nv,
                "num_lajes": nl,
                "num_pilares": np,
                "num_cargas_area": n_carare,
                "num_cargas_lineares": n_carlin,
            })
        return pavimentos

    def listar_vigas(self, pavimento: str) -> List[Dict[str, Any]]:
        """Lista todas as vigas de um pavimento com suas seções geométricas e nós."""
        fl, nome_real = self._obter_objeto_pavimento(pavimento)
        it = fl.iterator
        nv = it.GetNumObjects(TQSModel.TYPE_VIGAS)

        vigas = []
        for i in range(nv):
            v = it.GetObject(TQSModel.TYPE_VIGAS, i)
            geo = v.GetBeamGeometry()
            nome_viga = v.formattedTitle or f"V{v.number}"
            
            # Nós e coordenadas
            num_nodes = v.NumNodes()
            coordenadas = []
            for ino in range(num_nodes):
                node = v.GetBeamNode(ino)
                coordenadas.append({"x_m": round(node.nodeX / 100.0, 3), "y_m": round(node.nodeY / 100.0, 3)})

            vigas.append({
                "indice": i,
                "nome": nome_viga,
                "numero": v.number,
                "b_cm": geo.width,
                "h_cm": geo.depth,
                "desnivel_cm": geo.recess,
                "excentricidade_cm": geo.eccentricity,
                "num_nos": num_nodes,
                "coordenadas": coordenadas,
            })

        # Ordena pelo número da viga
        vigas.sort(key=lambda x: x["numero"])
        return vigas

    def obter_viga(self, pavimento: str, identificador_viga: Any) -> Optional[Dict[str, Any]]:
        """Busca os dados detalhados de uma viga específica pelo nome ('V1', 'V12') ou número."""
        vigas = self.listar_vigas(pavimento)
        alvo_norm = normalizar_texto(str(identificador_viga)).lstrip("V")
        for v in vigas:
            if str(v["numero"]) == alvo_norm or normalizar_texto(v["nome"]).lstrip("V") == alvo_norm:
                return v
        return None

    def listar_lajes(self, pavimento: str) -> List[Dict[str, Any]]:
        """Lista todas as lajes de um pavimento com suas espessuras, desníveis e tipos."""
        fl, nome_real = self._obter_objeto_pavimento(pavimento)
        it = fl.iterator
        nl = it.GetNumObjects(TQSModel.TYPE_LAJES)

        lajes = []
        for i in range(nl):
            l = it.GetObject(TQSModel.TYPE_LAJES, i)
            geo = l.slabGeometry
            nome_laje = l.formattedTitle or f"L{l.number}"
            tipo_desc = "Maciça" if geo.type == 0 else f"Tipo {geo.type}"

            lajes.append({
                "indice": i,
                "nome": nome_laje,
                "numero": l.number,
                "espessura_cm": geo.thickness,
                "desnivel_cm": geo.recess,
                "tipo_codigo": geo.type,
                "tipo_descricao": tipo_desc,
                "angulo_principal_graus": l.mainAngle,
            })

        lajes.sort(key=lambda x: x["numero"])
        return lajes

    def obter_laje(self, pavimento: str, identificador_laje: Any) -> Optional[Dict[str, Any]]:
        """Busca os dados de uma laje específica pelo nome ('L1', 'L3') ou número."""
        lajes = self.listar_lajes(pavimento)
        alvo_norm = normalizar_texto(str(identificador_laje)).lstrip("L")
        for l in lajes:
            if str(l["numero"]) == alvo_norm or normalizar_texto(l["nome"]).lstrip("L") == alvo_norm:
                return l
        return None

    def listar_pilares(self, pavimento: str) -> List[Dict[str, Any]]:
        """Lista todos os pilares de um pavimento com seção transversal e coordenadas."""
        fl, nome_real = self._obter_objeto_pavimento(pavimento)
        it = fl.iterator
        np = it.GetNumObjects(TQSModel.TYPE_PILARES)

        pilares = []
        for i in range(np):
            p = it.GetObject(TQSModel.TYPE_PILARES, i)
            nome_pilar = p.formattedTitle or f"P{p.number}"
            
            n_sec = p.ColumnNumSections()
            b_cm = 0.0
            h_cm = 0.0
            tipo_sec = 0
            x_m = 0.0
            y_m = 0.0

            if n_sec > 0:
                sec = p.ColumnGetSection(0)
                geo = sec.columnGeometry
                b_cm = geo.sectionB1
                h_cm = geo.sectionH1
                tipo_sec = geo.sectionType
                x_m = round(sec.insertionX / 100.0, 3)
                y_m = round(sec.insertionY / 100.0, 3)

            pilares.append({
                "indice": i,
                "nome": nome_pilar,
                "numero": p.number,
                "b_cm": b_cm,
                "h_cm": h_cm,
                "secao_cm": f"{b_cm:.0f}x{h_cm:.0f}" if b_cm and h_cm else "-",
                "tipo_secao": tipo_sec,
                "x_m": x_m,
                "y_m": y_m,
            })

        pilares.sort(key=lambda x: x["numero"])
        return pilares

    def obter_pilar(self, pavimento: str, identificador_pilar: Any) -> Optional[Dict[str, Any]]:
        """Busca os dados de um pilar específico pelo nome ('P1', 'P4') ou número."""
        pilares = self.listar_pilares(pavimento)
        alvo_norm = normalizar_texto(str(identificador_pilar)).lstrip("P")
        for p in pilares:
            if str(p["numero"]) == alvo_norm or normalizar_texto(p["nome"]).lstrip("P") == alvo_norm:
                return p
        return None

    def listar_cargas(self, pavimento: str) -> Dict[str, List[Dict[str, Any]]]:
        """Lista todas as cargas por área, lineares e adicionais cadastradas no pavimento."""
        fl, nome_real = self._obter_objeto_pavimento(pavimento)
        it = fl.iterator

        cargas_area = []
        n_carare = it.GetNumObjects(TQSModel.TYPE_CARARE)
        for i in range(n_carare):
            ca = it.GetObject(TQSModel.TYPE_CARARE, i)
            cargas_area.append({
                "indice": i,
                "nome": ca.formattedTitle or f"CA{ca.number}",
                "numero": ca.number,
            })

        cargas_lineares = []
        n_carlin = it.GetNumObjects(TQSModel.TYPE_CARLIN)
        for i in range(n_carlin):
            cl = it.GetObject(TQSModel.TYPE_CARLIN, i)
            cargas_lineares.append({
                "indice": i,
                "nome": cl.formattedTitle or f"CL{cl.number}",
                "numero": cl.number,
                "x1_m": round(cl.startPointX / 100.0, 3),
                "y1_m": round(cl.startPointY / 100.0, 3),
                "x2_m": round(cl.endPointX / 100.0, 3),
                "y2_m": round(cl.endPointY / 100.0, 3),
            })

        return {
            "cargas_area": cargas_area,
            "cargas_lineares": cargas_lineares,
        }

    # =========================================================================
    # EDIÇÃO E MODIFICAÇÃO (SETTERS / MUTATIONS)
    # =========================================================================

    def editar_viga(
        self,
        pavimento: str,
        identificador_viga: Any,
        b_cm: Optional[float] = None,
        h_cm: Optional[float] = None,
        desnivel_cm: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Modifica a seção geométrica de uma viga no modelador estrutural.
        Altera largura b, altura h e/ou desnível/rebaixo recess e salva o modelo.
        """
        fl, nome_real = self._obter_objeto_pavimento(pavimento)
        it = fl.iterator
        nv = it.GetNumObjects(TQSModel.TYPE_VIGAS)

        alvo_norm = normalizar_texto(str(identificador_viga)).lstrip("V")
        viga_encontrada = None

        for i in range(nv):
            v = it.GetObject(TQSModel.TYPE_VIGAS, i)
            if str(v.number) == alvo_norm or normalizar_texto(v.formattedTitle or "").lstrip("V") == alvo_norm:
                viga_encontrada = v
                break

        if not viga_encontrada:
            raise ValueError(f"Viga '{identificador_viga}' não foi encontrada no pavimento '{nome_real}'.")

        geo = viga_encontrada.GetBeamGeometry()
        nome_viga = viga_encontrada.formattedTitle or f"V{viga_encontrada.number}"

        antes = {
            "b_cm": geo.width,
            "h_cm": geo.depth,
            "desnivel_cm": geo.recess,
        }

        # Aplica alterações
        if b_cm is not None:
            geo.width = float(b_cm)
        if h_cm is not None:
            geo.depth = float(h_cm)
        if desnivel_cm is not None:
            geo.recess = float(desnivel_cm)

        # Salva o modelo
        self.salvar()

        depois = {
            "b_cm": geo.width,
            "h_cm": geo.depth,
            "desnivel_cm": geo.recess,
        }

        return {
            "status": "sucesso",
            "elemento": "viga",
            "edificio": self.nome_edificio,
            "pavimento": nome_real,
            "nome": nome_viga,
            "numero": viga_encontrada.number,
            "antes": antes,
            "depois": depois,
            "mensagem": f"Viga {nome_viga} atualizada de {antes['b_cm']:.0f}x{antes['h_cm']:.0f} cm para {depois['b_cm']:.0f}x{depois['h_cm']:.0f} cm com sucesso.",
        }

    def editar_laje(
        self,
        pavimento: str,
        identificador_laje: Any,
        espessura_cm: Optional[float] = None,
        desnivel_cm: Optional[float] = None,
        carga_permanente_tf_m2: Optional[float] = None,
        carga_acidental_tf_m2: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Modifica a espessura, desnível e/ou carregamento distribuído de uma laje.
        Salva o modelo após a aplicação das alterações.
        """
        fl, nome_real = self._obter_objeto_pavimento(pavimento)
        it = fl.iterator
        nl = it.GetNumObjects(TQSModel.TYPE_LAJES)

        alvo_norm = normalizar_texto(str(identificador_laje)).lstrip("L")
        laje_encontrada = None

        for i in range(nl):
            l = it.GetObject(TQSModel.TYPE_LAJES, i)
            if str(l.number) == alvo_norm or normalizar_texto(l.formattedTitle or "").lstrip("L") == alvo_norm:
                laje_encontrada = l
                break

        if not laje_encontrada:
            raise ValueError(f"Laje '{identificador_laje}' não foi encontrada no pavimento '{nome_real}'.")

        geo = laje_encontrada.slabGeometry
        nome_laje = laje_encontrada.formattedTitle or f"L{laje_encontrada.number}"

        antes = {
            "espessura_cm": geo.thickness,
            "desnivel_cm": geo.recess,
        }

        # Aplica alterações geométricas
        if espessura_cm is not None:
            geo.thickness = float(espessura_cm)
        if desnivel_cm is not None:
            geo.recess = float(desnivel_cm)

        # Aplica cargas se especificadas
        cargas_info = {}
        if carga_permanente_tf_m2 is not None or carga_acidental_tf_m2 is not None:
            load = laje_encontrada.GetLoad(fl)
            if carga_permanente_tf_m2 is not None:
                load.SetMainLoad(1, float(carga_permanente_tf_m2))
                cargas_info["carga_permanente_tf_m2"] = float(carga_permanente_tf_m2)
            if carga_acidental_tf_m2 is not None:
                load.SetLiveLoad(1, float(carga_acidental_tf_m2))
                cargas_info["carga_acidental_tf_m2"] = float(carga_acidental_tf_m2)

        # Salva o modelo
        self.salvar()

        depois = {
            "espessura_cm": geo.thickness,
            "desnivel_cm": geo.recess,
        }

        return {
            "status": "sucesso",
            "elemento": "laje",
            "edificio": self.nome_edificio,
            "pavimento": nome_real,
            "nome": nome_laje,
            "numero": laje_encontrada.number,
            "antes": antes,
            "depois": depois,
            "cargas_aplicadas": cargas_info,
            "mensagem": f"Laje {nome_laje} atualizada (h={depois['espessura_cm']:.1f} cm) com sucesso.",
        }

    def editar_pilar(
        self,
        pavimento: str,
        identificador_pilar: Any,
        b_cm: Optional[float] = None,
        h_cm: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Modifica a seção retangular de um pilar em um pavimento específico.
        """
        fl, nome_real = self._obter_objeto_pavimento(pavimento)
        it = fl.iterator
        np = it.GetNumObjects(TQSModel.TYPE_PILARES)

        alvo_norm = normalizar_texto(str(identificador_pilar)).lstrip("P")
        pilar_encontrado = None

        for i in range(np):
            p = it.GetObject(TQSModel.TYPE_PILARES, i)
            if str(p.number) == alvo_norm or normalizar_texto(p.formattedTitle or "").lstrip("P") == alvo_norm:
                pilar_encontrado = p
                break

        if not pilar_encontrado:
            raise ValueError(f"Pilar '{identificador_pilar}' não foi encontrado no pavimento '{nome_real}'.")

        n_sec = pilar_encontrado.ColumnNumSections()
        if n_sec == 0:
            raise ValueError(f"O pilar '{identificador_pilar}' não possui seção cadastrada no pavimento.")

        sec = pilar_encontrado.ColumnGetSection(0)
        geo = sec.columnGeometry
        nome_pilar = pilar_encontrado.formattedTitle or f"P{pilar_encontrado.number}"

        antes = {
            "b_cm": geo.sectionB1,
            "h_cm": geo.sectionH1,
        }

        if b_cm is not None:
            geo.sectionB1 = float(b_cm)
        if h_cm is not None:
            geo.sectionH1 = float(h_cm)

        pilar_encontrado.ColumnSectionUpdateGeometry(sec)
        self.salvar()

        depois = {
            "b_cm": geo.sectionB1,
            "h_cm": geo.sectionH1,
        }

        return {
            "status": "sucesso",
            "elemento": "pilar",
            "edificio": self.nome_edificio,
            "pavimento": nome_real,
            "nome": nome_pilar,
            "numero": pilar_encontrado.number,
            "antes": antes,
            "depois": depois,
            "mensagem": f"Pilar {nome_pilar} atualizado de {antes['b_cm']:.0f}x{antes['h_cm']:.0f} cm para {depois['b_cm']:.0f}x{depois['h_cm']:.0f} cm com sucesso.",
        }

    def adicionar_carga_distribuida(
        self,
        pavimento: str,
        coordenadas_poligono_m: List[Tuple[float, float]],
        carga_permanente_tf_m2: float = 0.0,
        carga_acidental_tf_m2: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Adiciona uma carga por área (TYPE_CARARE) delimitada por um polígono de vértices no pavimento.
        Coordenadas são passadas em metros [(x1, y1), (x2, y2), ...].
        """
        fl, nome_real = self._obter_objeto_pavimento(pavimento)

        # Configura valor da carga nos dados correntes do pavimento
        floorLoadData = fl.current.floorLoadData
        loadare = floorLoadData.GetLoad(TQSModel.TPLOAD_CARARE)
        loadare.SetLoad(TQSModel.LOADTYPE_DISARE)
        loadare.SetMainLoad(1, float(carga_permanente_tf_m2))
        loadare.SetLiveLoad(1, float(carga_acidental_tf_m2))

        # Cria polígono com as coordenadas convertidas para cm
        polig = TQSModel.Polygon(self._model)
        for pt in coordenadas_poligono_m:
            polig.Enter(pt[0] * 100.0, pt[1] * 100.0)

        carare = fl.create.CreateAreaDistributedLoad(polig)
        self.salvar()

        return {
            "status": "sucesso",
            "elemento": "carga_area",
            "edificio": self.nome_edificio,
            "pavimento": nome_real,
            "carga_permanente_tf_m2": carga_permanente_tf_m2,
            "carga_acidental_tf_m2": carga_acidental_tf_m2,
            "vertices_m": coordenadas_poligono_m,
            "mensagem": f"Carga por área ({carga_permanente_tf_m2:.2f} tf/m² perm, {carga_acidental_tf_m2:.2f} tf/m² acid) adicionada com sucesso.",
        }

    def adicionar_carga_linear(
        self,
        pavimento: str,
        x1_m: float,
        y1_m: float,
        x2_m: float,
        y2_m: float,
        carga_permanente_tf_m: float = 0.0,
        carga_acidental_tf_m: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Adiciona uma carga distribuída linear (TYPE_CARLIN) de (x1, y1) até (x2, y2) no pavimento.
        Coordenadas em metros e valores em tf/m.
        """
        fl, nome_real = self._obter_objeto_pavimento(pavimento)

        floorLoadData = fl.current.floorLoadData
        loaddis = floorLoadData.GetLoad(TQSModel.TPLOAD_CARLIN)
        loaddis.SetLoad(TQSModel.LOADTYPE_DISLIN)
        loaddis.SetMainLoad(1, float(carga_permanente_tf_m))
        loaddis.SetLiveLoad(1, float(carga_acidental_tf_m))

        carlin = fl.create.CreateLinearyDistributedLoad(
            x1_m * 100.0, y1_m * 100.0, x2_m * 100.0, y2_m * 100.0
        )
        self.salvar()

        return {
            "status": "sucesso",
            "elemento": "carga_linear",
            "edificio": self.nome_edificio,
            "pavimento": nome_real,
            "trecho": {"x1_m": x1_m, "y1_m": y1_m, "x2_m": x2_m, "y2_m": y2_m},
            "carga_permanente_tf_m": carga_permanente_tf_m,
            "carga_acidental_tf_m": carga_acidental_tf_m,
            "mensagem": f"Carga linear ({carga_permanente_tf_m:.2f} tf/m perm) adicionada com sucesso de ({x1_m:.2f}, {y1_m:.2f}) a ({x2_m:.2f}, {y2_m:.2f}).",
        }
