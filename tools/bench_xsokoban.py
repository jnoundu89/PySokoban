#!/usr/bin/env python3
"""Mesurer le solveur de PySokoban sur les 90 XSokoban, par AutoSolver.

    python3 tools/bench_xsokoban.py                 # les 90
    python3 tools/bench_xsokoban.py --a 10          # les 10 premiers
    python3 tools/bench_xsokoban.py --sans-festival # forcer le solveur interne

Ce banc passe par AutoSolver, donc par le chemin que le jeu emprunte
réellement — pas par un appel direct au solveur. Et il ne fait pas confiance au
verdict : chaque solution est rejouée sur un niveau neuf, par Level.move(),
jusqu'à is_completed().

Repères mesurés le 2026-08-11 (Steam Deck, Zen 2) :

    solveur interne (EnhancedSokolutionSolver), 60 s/niveau :  1/10
    Festival 3.1 (FESS), 1 cœur                             : 90/90
"""
from __future__ import annotations

import argparse
import os
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

COLLECTION = os.path.join(RACINE, "src", "levels", "Original & Extra", "Original.txt")
_DELTAS = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}


def rejouer(texte: str, coups: list[str]) -> tuple[bool, str]:
    """Appliquer la solution à un niveau neuf, par le moteur du jeu."""
    from src.core.level import Level
    essai = Level(level_data=texte)
    for n, coup in enumerate(coups, 1):
        dx, dy = _DELTAS.get(coup, (0, 0))
        if (dx, dy) == (0, 0):
            return False, f"coup {n} : « {coup} » inconnu"
        if not essai.move(dx, dy):
            return False, f"coup {n}/{len(coups)} ({coup}) refusé par le moteur"
    if not essai.is_completed():
        return False, f"{len(coups)} coups appliqués, niveau non terminé"
    return True, "rejoué jusqu'à la position finale"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--de", type=int, default=1)
    ap.add_argument("--a", type=int, default=90)
    ap.add_argument("--budget", type=float, default=600.0)
    ap.add_argument("--sans-festival", action="store_true",
                    help="masquer le binaire pour mesurer le solveur interne")
    a = ap.parse_args()

    if a.sans_festival:
        import src.ai.festival_solver as fs
        fs._CHEMINS = ()
        fs.shutil.which = lambda _n: None

    from src.level_management.level_collection_parser import LevelCollectionParser
    from src.core.auto_solver import AutoSolver
    import src.core.auto_solver as autosolver_module
    autosolver_module._FESTIVAL_BUDGET = a.budget

    coll = LevelCollectionParser.parse_file(COLLECTION)
    total = coll.get_level_count()
    fin = min(a.a, total)
    print(f"collection : {coll.title} — {total} niveaux")
    print(f"tranche    : {a.de}..{fin}, budget {a.budget:g} s\n")

    resolus = verifies = 0
    duree_totale = 0.0
    echecs: list[str] = []

    for i in range(a.de - 1, fin):
        titre, niveau = coll.get_level(i)
        texte = niveau.get_state_string(show_fess_coordinates=False)

        solveur = AutoSolver(niveau)
        depart = time.time()
        ok = solveur.solve_level()
        duree = time.time() - depart
        duree_totale += duree

        if not ok:
            print(f"  #{i+1:<3} ÉCHEC          {duree:7.2f} s")
            echecs.append(f"#{i+1} non résolu")
            continue
        resolus += 1

        bon, explication = rejouer(texte, solveur.solution)
        if bon:
            verifies += 1
            print(f"  #{i+1:<3} OK et rejoué   {duree:7.2f} s  "
                  f"{len(solveur.solution):5} coups")
        else:
            print(f"  #{i+1:<3} NON REJOUABLE  {duree:7.2f} s  → {explication}")
            echecs.append(f"#{i+1} {explication}")
        sys.stdout.flush()

    nombre = fin - a.de + 1
    print(f"\n  solveur            : {solveur.solver_type}")
    print(f"  annoncés résolus    : {resolus}/{nombre}")
    print(f"  REJOUÉS ET VÉRIFIÉS : {verifies}/{nombre}")
    print(f"  temps total         : {duree_totale:.1f} s "
          f"({int(duree_totale) // 60} min {int(duree_totale) % 60:02d})")
    if echecs:
        print("\n  restent :")
        for e in echecs:
            print(f"    {e}")
    return 0 if verifies == nombre else 1


if __name__ == "__main__":
    sys.exit(main())
