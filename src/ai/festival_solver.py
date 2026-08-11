"""Solveur Festival — l'implémentation de référence de FESS, en MIT.

Festival 3.1, de Yaron Shoham, est le premier programme à résoudre les 90
niveaux XSokoban. C'est l'auteur même de l'algorithme FESS, et il publie son
code sous licence MIT.

Pourquoi ce module existe
-------------------------
Ce dépôt a tenté d'écrire FESS lui-même : 14 modules, ~8 500 lignes, supprimés
au commit ecdc5ee (« FESS was an experimental solver that never worked
reliably »). Le solveur restant, EnhancedSokolutionSolver, a été mesuré le
2026-08-11 sur les 10 premiers XSokoban avec 60 s par niveau : **1 résolu sur
10**. Festival, sur la même machine, résout les **90 en 3 min 34**.

Le savoir qui manquait n'était pas algorithmique. C'était de savoir que
l'implémentation de l'auteur existait, libre, tout ce temps.

Ce module ne réimplémente donc rien : il sérialise le niveau, appelle le
binaire, relit sa sortie — et **rejoue la solution dans le moteur de ce dépôt**
avant de la rendre. Une solution non rejouable est refusée, pas retournée.

Installation du binaire
-----------------------
Festival n'est pas fourni ici. Le chemin est cherché dans cet ordre :

    $PYSOKOBAN_FESTIVAL                       (variable d'environnement)
    ./festival, ./bin/festival
    ~/.local/bin/festival
    ~/GameMakerProjects/jeux/prototypes/sokoban-fess/outils/festival

Pour le construire (sources et script dans le projet sokoban-fess) :

    bash outils/construire-festival.sh

Licence : MIT, Copyright (c) 2019-2022 Yaron Shoham. La mention doit
accompagner toute redistribution du binaire.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

NOM_BINAIRE = "festival"

_CHEMINS = (
    os.environ.get("PYSOKOBAN_FESTIVAL", ""),
    os.path.join(os.getcwd(), NOM_BINAIRE),
    os.path.join(os.getcwd(), "bin", NOM_BINAIRE),
    os.path.expanduser(f"~/.local/bin/{NOM_BINAIRE}"),
    os.path.expanduser(
        "~/GameMakerProjects/jeux/prototypes/sokoban-fess/outils/festival"),
)

# LURD : minuscule = déplacement, majuscule = poussée. Le sens seul nous
# intéresse ici — la distinction pousse/déplace est recalculée par le moteur.
_SENS = {"l": "LEFT", "r": "RIGHT", "u": "UP", "d": "DOWN"}
_DELTAS = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}


class FestivalIndisponible(RuntimeError):
    """Le binaire est absent ou non exécutable."""


class SolutionRefusee(RuntimeError):
    """Festival a rendu une solution que le moteur de ce dépôt ne rejoue pas."""


@dataclass
class FestivalResultat:
    """Compatible avec l'usage que le jeu fait de SolutionData."""
    moves: List[str] = field(default_factory=list)
    solve_time: float = 0.0
    states_explored: int = 0
    states_generated: int = 0
    deadlocks_pruned: int = 0
    algorithm_used: str = "Festival 3.1 (FESS)"
    search_mode: str = "portfolio de 8 recherches"
    memory_peak: int = 0
    heuristic_calls: int = 0
    macro_moves_used: int = 0
    pushes: int = 0
    lurd: str = ""


def trouver_binaire() -> Optional[str]:
    """Le chemin du binaire Festival, ou None."""
    for chemin in _CHEMINS:
        if chemin and os.path.isfile(chemin) and os.access(chemin, os.X_OK):
            return chemin
    return shutil.which(NOM_BINAIRE)


def disponible() -> bool:
    return trouver_binaire() is not None


class FestivalSolver:
    """Résout un niveau en appelant Festival, et vérifie ce qu'il rend.

    >>> solveur = FestivalSolver(level, time_limit=60)
    >>> resultat = solveur.solve()
    >>> resultat.moves[:4]
    ['UP', 'LEFT', 'LEFT', 'LEFT']
    """

    def __init__(self, level, time_limit: float = 600.0, cores: int = 1,
                 binaire: Optional[str] = None):
        self.level = level
        self.time_limit = max(1, int(time_limit))
        # UN SEUL CŒUR PAR DÉFAUT, et c'est contre-intuitif — mesuré le
        # 2026-08-11 sur un Steam Deck (Zen 2, 8 cœurs logiques) :
        #
        #   niveau    1 cœur    4 cœurs
        #        1     537 ms    1902 ms
        #        3     537 ms    1873 ms
        #       10    3221 ms    5218 ms
        #       40    8222 ms   11516 ms
        #       71   14793 ms   18125 ms
        #
        # Un cœur gagne sur TOUS les niveaux essayés, faciles comme durs. La
        # raison : chaque thread alloue ses propres tables (search_trees[8],
        # helpers[8], et un `helper` contient des tableaux indexés par
        # MAX_SOL_LEN). Sur un niveau trivial — une caisse, une cible — le
        # plancher passe de 480 ms à 1 cœur à 1,8 s à 4 : le coût croît
        # linéairement avec les cœurs, avant toute recherche.
        #
        # À 1 cœur, Festival enchaîne ses 8 stratégies séquentiellement
        # (solve_with_time_control_single_core) ; à 4, il les répartit. Le
        # parallélisme ne paie donc que sur un niveau dont seule une stratégie
        # tardive vient à bout, en acceptant un plancher 4x plus lourd.
        # Augmenter `cores` est un choix à mesurer, pas un réglage par défaut.
        self.cores = max(1, cores)
        self.binaire = binaire or trouver_binaire()
        if not self.binaire:
            raise FestivalIndisponible(
                "binaire `festival` introuvable. Poser son chemin dans "
                "$PYSOKOBAN_FESTIVAL, ou le construire — voir le docstring "
                "de ce module.")

    # ------------------------------------------------------------------ public
    def solve(self, progress_callback: Optional[Callable[[str], None]] = None
              ) -> Optional[FestivalResultat]:
        """Rendre une solution vérifiée, ou None si le niveau résiste."""
        def dire(message: str) -> None:
            if progress_callback:
                progress_callback(message)

        texte = self._niveau_en_texte()
        dire("Festival : analyse du niveau…")

        dossier = tempfile.mkdtemp(prefix="pysokoban-festival-")
        try:
            collection = os.path.join(dossier, "niveau.sok")
            with open(collection, "w", encoding="utf-8") as f:
                f.write(texte + "\n")

            commande = [self.binaire, collection,
                        "-time", str(self.time_limit),
                        "-cores", str(self.cores),
                        "-out_dir", dossier]
            dire(f"Festival : recherche (budget {self.time_limit} s, "
                 f"{self.cores} cœurs)…")
            depart = time.time()
            subprocess.run(commande, cwd=dossier, stdout=subprocess.DEVNULL,
                           stderr=subprocess.STDOUT,
                           timeout=self.time_limit + 60, check=False)
            duree = time.time() - depart

            lurd = self._lire_lurd(os.path.join(dossier, "solutions.sok"))
            if not lurd:
                dire(f"Festival : aucune solution en {duree:.1f} s")
                return None

            coups = [_SENS[c.lower()] for c in lurd]
            pousses = sum(1 for c in lurd if c.isupper())

            # Le contrôle qui fait toute la valeur de ce module : la solution
            # est rejouée dans le moteur de CE dépôt. Un désaccord de format,
            # de repère ou de règle se voit ici, jamais chez le joueur.
            self._verifier(texte, coups)

            dire(f"Festival : solution vérifiée — {len(coups)} coups, "
                 f"{pousses} poussées, {duree:.1f} s")
            return FestivalResultat(
                moves=coups, solve_time=duree, pushes=pousses, lurd=lurd)

        except subprocess.TimeoutExpired:
            dire("Festival : le processus a dépassé son budget")
            return None
        finally:
            shutil.rmtree(dossier, ignore_errors=True)

    # ------------------------------------------------------------------ privé
    def _niveau_en_texte(self) -> str:
        """Le niveau au format Sokoban standard, sans décor de coordonnées."""
        try:
            return self.level.get_state_string(show_fess_coordinates=False)
        except TypeError:
            # Niveaux plus anciens : pas de paramètre.
            return self.level.get_state_string()

    @staticmethod
    def _lire_lurd(chemin: str) -> str:
        if not os.path.exists(chemin):
            return ""
        contenu = open(chemin, encoding="utf-8", errors="replace").read()
        m = re.search(r"^Solution\s*\n\s*([lrudLRUD]+)\s*$", contenu, re.M)
        return m.group(1) if m else ""

    def _verifier(self, texte: str, coups: List[str]) -> None:
        """Rejouer dans un Level neuf, et exiger la complétion."""
        from src.core.level import Level  # import tardif : évite un cycle

        essai = Level(level_data=texte)
        for n, coup in enumerate(coups, 1):
            dx, dy = _DELTAS[coup]
            if not essai.move(dx, dy):
                raise SolutionRefusee(
                    f"coup {n}/{len(coups)} ({coup}) refusé par le moteur — "
                    f"la solution de Festival ne correspond pas à ce niveau")
        if not essai.is_completed():
            raise SolutionRefusee(
                f"les {len(coups)} coups s'appliquent mais le niveau n'est pas "
                f"terminé — désaccord de règles ou de cibles")
