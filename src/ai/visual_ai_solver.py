"""
Interface visuelle pour le système IA Sokoban.

Ce module gère l'intégration entre le système IA unifié et l'interface graphique,
incluant l'animation en temps réel, le debugging visuel, et les contrôles utilisateur.
"""

import time
import pygame
from typing import List, Optional, Callable, Dict, Any, Tuple
from enum import Enum

from .unified_ai_controller import UnifiedAIController, SolveRequest
from .algorithm_selector import Algorithm


class AnimationSpeed(Enum):
    """Vitesses d'animation disponibles."""
    VERY_SLOW = 1000
    SLOW = 600
    NORMAL = 400
    FAST = 200
    VERY_FAST = 100


class VisualAISolver:
    """
    Interface visuelle pour le système IA Sokoban.
    
    Gère l'intégration entre l'IA et l'interface graphique avec :
    - Animation en temps réel des solutions
    - Contrôles de vitesse et de pause
    - Affichage des métriques en direct
    - Mode debug avec information détaillée
    - Interface utilisateur pour sélection d'algorithme
    """
    
    def __init__(self, renderer, skin_manager):
        self.renderer = renderer
        self.skin_manager = skin_manager
        self.ai_controller = UnifiedAIController()
        
        # État de l'animation
        self.is_animating = False
        self.is_paused = False
        self.animation_speed = AnimationSpeed.NORMAL
        self.current_move_index = 0
        self.solution_moves = []
        
        # État du debugging
        self.debug_mode = False
        self.show_metrics = True
        self.show_algorithm_info = True
        
        # Données de la dernière résolution
        self.last_solve_result = None
        self.last_solve_metrics = None
        
        # Interface utilisateur
        self.ui_elements = {}
        self.font = None
        self._initialize_ui()
    
    def _initialize_ui(self):
        """Initialise les éléments d'interface utilisateur."""
        try:
            pygame.font.init()
            self.font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 16)
        except:
            self.font = None
            self.small_font = None
    
    def solve_level_visual(self, level, algorithm: Optional[Algorithm] = None,
                          animate_immediately: bool = True,
                          progress_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """
        Résout un niveau avec visualisation complète.
        
        Args:
            level: Niveau à résoudre
            algorithm: Algorithme spécifique (None pour sélection automatique)
            animate_immediately: Si animer la solution immédiatement
            progress_callback: Callback pour les mises à jour de progression
            
        Returns:
            Dict: Résultats complets de la résolution
        """
        # Afficher l'info de démarrage
        if progress_callback:
            if algorithm:
                progress_callback(f"🤖 Résolution avec algorithme {algorithm.value}...")
            else:
                progress_callback("🤖 Analyse du niveau et sélection d'algorithme...")
        
        # Créer la requête de résolution
        request = SolveRequest(
            level=level,
            algorithm=algorithm,
            collect_ml_metrics=True,
            generate_report=self.debug_mode
        )
        
        # Résoudre avec l'IA
        solve_result = self.ai_controller.solve_level(request, progress_callback)
        
        # Stocker les résultats
        self.last_solve_result = solve_result
        self.last_solve_metrics = solve_result.ml_metrics
        
        if solve_result.success and solve_result.solution_data:
            self.solution_moves = solve_result.solution_data.moves
            
            if animate_immediately:
                if progress_callback:
                    progress_callback("🎬 Animation de la solution...")
                
                self.animate_solution(level, progress_callback)
        
        return {
            'success': solve_result.success,
            'solve_result': solve_result,
            'animation_completed': animate_immediately and solve_result.success
        }
    
    def animate_solution(self, level, progress_callback: Optional[Callable[[str], None]] = None):
        """
        Anime la solution step-by-step.
        
        Args:
            level: Niveau à animer
            progress_callback: Callback pour les mises à jour
        """
        if not self.solution_moves:
            if progress_callback:
                progress_callback("❌ Aucune solution à animer")
            return
        
        self.is_animating = True
        self.is_paused = False
        self.current_move_index = 0
        
        if progress_callback:
            total_moves = len(self.solution_moves)
            progress_callback(f"🎬 Animation: {total_moves} mouvements")
        
        try:
            for i, move in enumerate(self.solution_moves):
                if not self.is_animating:
                    break
                
                # Gérer la pause
                while self.is_paused and self.is_animating:
                    self._handle_pause_events()
                    pygame.time.wait(50)
                
                if not self.is_animating:
                    break
                
                # Afficher les informations de debug si activé
                if self.debug_mode and progress_callback:
                    self._show_debug_info(i, move, progress_callback)
                
                # Exécuter le mouvement
                success = self._execute_move(level, move)
                self.current_move_index = i
                
                if progress_callback:
                    progress = (i + 1) / len(self.solution_moves) * 100
                    progress_callback(f"🤖 Mouvement {i+1}/{len(self.solution_moves)}: {move} -> {'✅' if success else '❌'} ({progress:.1f}%)")
                
                # Rendre l'état actuel
                self._render_current_state(level)
                
                # Afficher les métriques si activé
                if self.show_metrics:
                    self._render_metrics_overlay()
                
                # Attendre selon la vitesse d'animation
                pygame.time.wait(self.animation_speed.value)
                
                # Vérifier si le niveau est terminé
                if level.is_completed():
                    if progress_callback:
                        progress_callback("🎉 Niveau résolu par l'IA!")
                    
                    # Afficher l'écran de victoire avec métriques
                    self._show_completion_screen(level)
                    break
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ Erreur durant l'animation: {str(e)}")
        
        finally:
            self.is_animating = False
            self.is_paused = False
    
    def _execute_move(self, level, move: str) -> bool:
        """Exécute un mouvement sur le niveau."""
        direction_map = {
            'UP': (0, -1),
            'DOWN': (0, 1),
            'LEFT': (-1, 0),
            'RIGHT': (1, 0)
        }
        
        if move in direction_map:
            dx, dy = direction_map[move]
            return level.move(dx, dy)
        
        return False
    
    def _render_current_state(self, level):
        """Rend l'état actuel du niveau."""
        if self.renderer:
            # Utiliser le renderer existant
            self.renderer.render_level(
                level=level,
                level_manager=None,  # Peut être None pour le rendu IA
                show_grid=False,
                zoom_level=1.0,
                scroll_x=0,
                scroll_y=0,
                skin_manager=self.skin_manager,
                show_completion_message=False
            )
            
            # Ajouter des overlays IA
            self._render_ai_overlay()
            
            pygame.display.flip()
    
    def _render_ai_overlay(self):
        """Rend l'overlay d'information IA."""
        if not self.font:
            return
        
        screen = pygame.display.get_surface()
        if not screen:
            return
        
        overlay_y = 10
        
        # Indicateur d'IA active
        ai_indicator = self.font.render("🤖 IA Active", True, (0, 255, 0))
        screen.blit(ai_indicator, (10, overlay_y))
        overlay_y += 30
        
        # Progression
        if self.is_animating and self.solution_moves:
            progress_text = f"Mouvement {self.current_move_index + 1}/{len(self.solution_moves)}"
            progress_surf = self.small_font.render(progress_text, True, (255, 255, 255))
            screen.blit(progress_surf, (10, overlay_y))
            overlay_y += 20
            
            # Barre de progression
            progress_ratio = (self.current_move_index + 1) / len(self.solution_moves)
            progress_width = 200
            progress_height = 10
            
            # Fond de la barre
            pygame.draw.rect(screen, (100, 100, 100), (10, overlay_y, progress_width, progress_height))
            # Progression
            pygame.draw.rect(screen, (0, 255, 0), (10, overlay_y, int(progress_width * progress_ratio), progress_height))
            overlay_y += 25
        
        # Contrôles
        if self.is_animating:
            if self.is_paused:
                control_text = "PAUSE - Appuyez sur ESPACE pour continuer"
            else:
                control_text = "Appuyez sur ESPACE pour pause, ESC pour arrêter"
            
            control_surf = self.small_font.render(control_text, True, (255, 255, 0))
            screen.blit(control_surf, (10, overlay_y))
    
    def _render_metrics_overlay(self):
        """Rend les métriques en overlay."""
        if not self.show_metrics or not self.last_solve_result or not self.font:
            return
        
        screen = pygame.display.get_surface()
        if not screen:
            return
        
        # Position en haut à droite
        screen_width = screen.get_width()
        overlay_x = screen_width - 250
        overlay_y = 10
        
        # Fond semi-transparent
        overlay_rect = pygame.Rect(overlay_x - 10, overlay_y - 5, 240, 150)
        overlay_surface = pygame.Surface((240, 150))
        overlay_surface.set_alpha(180)
        overlay_surface.fill((0, 0, 0))
        screen.blit(overlay_surface, (overlay_x - 10, overlay_y - 5))
        
        # Métriques de base
        if self.last_solve_result.solution_data:
            solution_data = self.last_solve_result.solution_data
            
            metrics_info = [
                f"Algorithme: {solution_data.algorithm_used.value}",
                f"Temps: {solution_data.solve_time:.2f}s",
                f"Mouvements: {len(solution_data.moves)}",
                f"États explorés: {solution_data.states_explored:,}",
                f"Deadlocks évités: {solution_data.deadlocks_pruned}",
                f"Mémoire: {solution_data.memory_peak:,} états"
            ]
            
            for i, info in enumerate(metrics_info):
                info_surf = self.small_font.render(info, True, (255, 255, 255))
                screen.blit(info_surf, (overlay_x, overlay_y + i * 20))
    
    def _show_debug_info(self, move_index: int, move: str, progress_callback):
        """Affiche les informations de debug pour un mouvement."""
        debug_info = f"🔍 Debug - Mouvement {move_index + 1}: {move}"
        
        if self.last_solve_metrics:
            movement_analysis = self.last_solve_metrics.get('movement_analysis', {})
            direction_freq = movement_analysis.get('direction_frequency', {})
            
            if move in direction_freq:
                freq = direction_freq[move]
                debug_info += f" (Fréquence: {freq:.1%})"
        
        progress_callback(debug_info)
    
    def _show_completion_screen(self, level):
        """Affiche l'écran de completion avec métriques IA."""
        if not self.renderer or not self.last_solve_result:
            return
        
        # Attendre un moment pour que l'utilisateur voie la solution
        pygame.time.wait(1000)
        
        # Afficher les métriques finales
        if self.last_solve_result.solution_data:
            solution_data = self.last_solve_result.solution_data
            print(f"✅ Résolution IA complète!")
            print(f"   Algorithme: {solution_data.algorithm_used.value}")
            print(f"   Temps total: {solution_data.solve_time:.2f}s")
            print(f"   Mouvements: {len(solution_data.moves)}")
            print(f"   États explorés: {solution_data.states_explored:,}")
            print(f"   Efficacité: {solution_data.states_explored/max(solution_data.states_generated, 1):.1%}")
    
    def _handle_pause_events(self):
        """Gère les événements pendant la pause."""
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.is_paused = False
                elif event.key == pygame.K_ESCAPE:
                    self.is_animating = False
                    self.is_paused = False
            elif event.type == pygame.QUIT:
                self.is_animating = False
                self.is_paused = False
    
    def handle_events(self, events: List[pygame.event.Event]) -> bool:
        """
        Gère les événements liés à l'interface IA.
        
        Args:
            events: Liste des événements pygame
            
        Returns:
            bool: True si un événement a été traité
        """
        handled = False
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.is_animating:
                    if event.key == pygame.K_SPACE:
                        self.is_paused = not self.is_paused
                        handled = True
                    elif event.key == pygame.K_ESCAPE:
                        self.stop_animation()
                        handled = True
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS:
                        self.increase_speed()
                        handled = True
                    elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                        self.decrease_speed()
                        handled = True
                
                # Raccourcis globaux
                if event.key == pygame.K_F1:
                    self.toggle_debug_mode()
                    handled = True
                elif event.key == pygame.K_F2:
                    self.toggle_metrics_display()
                    handled = True
        
        return handled
    
    def stop_animation(self):
        """Arrête l'animation en cours."""
        self.is_animating = False
        self.is_paused = False
    
    def pause_animation(self):
        """Met en pause ou reprend l'animation."""
        if self.is_animating:
            self.is_paused = not self.is_paused
    
    def increase_speed(self):
        """Augmente la vitesse d'animation."""
        speeds = list(AnimationSpeed)
        current_index = speeds.index(self.animation_speed)
        if current_index > 0:
            self.animation_speed = speeds[current_index - 1]
    
    def decrease_speed(self):
        """Diminue la vitesse d'animation."""
        speeds = list(AnimationSpeed)
        current_index = speeds.index(self.animation_speed)
        if current_index < len(speeds) - 1:
            self.animation_speed = speeds[current_index + 1]
    
    def set_animation_speed(self, speed: AnimationSpeed):
        """Définit la vitesse d'animation."""
        self.animation_speed = speed
    
    def toggle_debug_mode(self):
        """Active/désactive le mode debug."""
        self.debug_mode = not self.debug_mode
        print(f"Mode debug IA: {'Activé' if self.debug_mode else 'Désactivé'}")
    
    def toggle_metrics_display(self):
        """Active/désactive l'affichage des métriques."""
        self.show_metrics = not self.show_metrics
        print(f"Affichage métriques: {'Activé' if self.show_metrics else 'Désactivé'}")
    
    def toggle_algorithm_info(self):
        """Active/désactive l'affichage des infos algorithme."""
        self.show_algorithm_info = not self.show_algorithm_info
    
    def get_algorithm_recommendation(self, level) -> Dict[str, Any]:
        """Obtient une recommandation d'algorithme pour un niveau."""
        return self.ai_controller.get_algorithm_recommendation(level)
    
    def benchmark_algorithms(self, level, progress_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """Lance un benchmark des algorithmes sur le niveau."""
        if progress_callback:
            progress_callback("🔬 Démarrage du benchmark des algorithmes...")
        
        return self.ai_controller.benchmark_algorithms(level, progress_callback=progress_callback)
    
    def get_solve_statistics(self) -> Dict[str, Any]:
        """Obtient les statistiques de résolution."""
        return self.ai_controller.get_solve_statistics()
    
    def get_last_solve_info(self) -> Optional[Dict[str, Any]]:
        """Obtient les informations de la dernière résolution."""
        if not self.last_solve_result:
            return None
        
        info = {
            'success': self.last_solve_result.success,
            'has_solution': self.last_solve_result.solution_data is not None,
            'has_ml_metrics': self.last_solve_result.ml_metrics is not None,
            'has_ml_report': self.last_solve_result.ml_report is not None
        }
        
        if self.last_solve_result.solution_data:
            solution_data = self.last_solve_result.solution_data
            info.update({
                'algorithm_used': solution_data.algorithm_used.value,
                'search_mode': solution_data.search_mode.value,
                'moves_count': len(solution_data.moves),
                'solve_time': solution_data.solve_time,
                'states_explored': solution_data.states_explored,
                'states_generated': solution_data.states_generated,
                'deadlocks_pruned': solution_data.deadlocks_pruned,
                'memory_peak': solution_data.memory_peak,
                'heuristic_calls': solution_data.heuristic_calls,
                'macro_moves_used': solution_data.macro_moves_used
            })
        
        if self.last_solve_result.algorithm_recommendation:
            info['algorithm_recommendation'] = self.last_solve_result.algorithm_recommendation
        
        return info
    
    def export_last_ml_report(self, filepath: str) -> bool:
        """Exporte le dernier rapport ML généré."""
        if not self.last_solve_result or not self.last_solve_result.ml_report:
            return False
        
        try:
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.last_solve_result.ml_report, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            print(f"Erreur lors de l'export du rapport ML: {e}")
            return False
    
    def create_solution_demo(self, level, algorithm: Optional[Algorithm] = None) -> bool:
        """
        Crée une démonstration complète de résolution.
        
        Args:
            level: Niveau à démontrer
            algorithm: Algorithme spécifique (optionnel)
            
        Returns:
            bool: True si la démonstration a été créée avec succès
        """
        def demo_progress(message):
            print(f"🎬 Demo: {message}")
        
        try:
            # Phase 1: Analyse et recommandation
            demo_progress("Analyse du niveau...")
            recommendation = self.get_algorithm_recommendation(level)
            
            demo_progress(f"Complexité: {recommendation['complexity_category']} (score: {recommendation['complexity_score']:.1f})")
            demo_progress(f"Algorithme recommandé: {recommendation['recommended_algorithm'].value}")
            
            # Phase 2: Résolution
            demo_progress("Résolution en cours...")
            result = self.solve_level_visual(
                level=level,
                algorithm=algorithm,
                animate_immediately=True,
                progress_callback=demo_progress
            )
            
            # Phase 3: Rapport final
            if result['success']:
                demo_progress("✅ Démonstration terminée avec succès!")
                
                solve_info = self.get_last_solve_info()
                if solve_info:
                    demo_progress(f"📊 Résumé: {solve_info['moves_count']} mouvements en {solve_info['solve_time']:.2f}s")
                    demo_progress(f"🧠 Algorithme: {solve_info['algorithm_used']}")
                    demo_progress(f"🔍 États explorés: {solve_info['states_explored']:,}")
                
                return True
            else:
                demo_progress("❌ Échec de la démonstration")
                return False
        
        except Exception as e:
            demo_progress(f"❌ Erreur lors de la démonstration: {str(e)}")
            return False
    
    def get_available_algorithms(self) -> List[Algorithm]:
        """Obtient la liste des algorithmes disponibles."""
        return list(Algorithm)
    
    def get_animation_speeds(self) -> List[AnimationSpeed]:
        """Obtient la liste des vitesses d'animation disponibles."""
        return list(AnimationSpeed)
    
    def is_busy(self) -> bool:
        """Vérifie si l'IA est occupée."""
        return self.ai_controller.is_solving or self.is_animating
    
    def get_status(self) -> Dict[str, Any]:
        """Obtient le statut actuel du système IA visuel."""
        return {
            'is_solving': self.ai_controller.is_solving,
            'is_animating': self.is_animating,
            'is_paused': self.is_paused,
            'animation_speed': self.animation_speed.name,
            'debug_mode': self.debug_mode,
            'show_metrics': self.show_metrics,
            'has_solution': len(self.solution_moves) > 0,
            'current_move_index': self.current_move_index,
            'total_moves': len(self.solution_moves)
        }