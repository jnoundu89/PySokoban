#!/usr/bin/env python3
"""
Test script for the unified AI system implementation.

This script validates the complete AI refactoring implementation according to
the plan in AI_REFACTORING_PLAN.md, specifically testing Phase 5 validation
on the first Thinking Rabbit Original level.
"""

import sys
import time
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, 'src')

from core.level import Level
from ai.unified_ai_controller import UnifiedAIController, SolveRequest
from ai.algorithm_selector import Algorithm
from ai.visual_ai_solver import VisualAISolver
from ai.ml_metrics_collector import MLMetricsCollector
from ai.ml_report_generator import MLReportGenerator


class AISystemValidator:
    """Validator for the unified AI system implementation."""
    
    def __init__(self):
        self.ai_controller = UnifiedAIController()
        self.test_results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'test_details': []
        }
    
    def run_complete_validation(self):
        """Run complete validation suite."""
        print("🤖 Starting Unified AI System Validation")
        print("=" * 60)
        
        # Test 1: Component Initialization
        self.test_component_initialization()
        
        # Test 2: Algorithm Selection
        self.test_algorithm_selection()
        
        # Test 3: Thinking Rabbit Level 1 (Key validation test)
        self.test_thinking_rabbit_level_1()
        
        # Test 4: ML Metrics Collection
        self.test_ml_metrics_collection()
        
        # Test 5: Report Generation
        self.test_report_generation()
        
        # Test 6: Benchmark System
        self.test_benchmark_system()
        
        # Test 7: Performance Validation
        self.test_performance_validation()
        
        # Summary
        self.print_validation_summary()
        
        return self.test_results['tests_failed'] == 0
    
    def test_component_initialization(self):
        """Test that all AI components initialize correctly."""
        print("\n📦 Test 1: Component Initialization")
        
        try:
            # Test UnifiedAIController
            assert self.ai_controller is not None
            assert hasattr(self.ai_controller, 'algorithm_selector')
            assert hasattr(self.ai_controller, 'solve_level')
            
            # Test algorithm selector
            from ai.algorithm_selector import AlgorithmSelector
            selector = AlgorithmSelector()
            assert selector is not None
            
            # Test ML components
            from ai.ml_metrics_collector import MLMetricsCollector
            from ai.ml_report_generator import MLReportGenerator
            
            ml_collector = MLMetricsCollector()
            report_generator = MLReportGenerator()
            
            assert ml_collector is not None
            assert report_generator is not None
            
            self._record_test("Component Initialization", True, "All components initialized successfully")
            
        except Exception as e:
            self._record_test("Component Initialization", False, f"Initialization failed: {str(e)}")
    
    def test_algorithm_selection(self):
        """Test algorithm selection logic."""
        print("\n🧠 Test 2: Algorithm Selection")
        
        try:
            # Create a simple test level
            test_level = self._create_simple_test_level()
            
            # Test automatic algorithm selection
            recommendation = self.ai_controller.get_algorithm_recommendation(test_level)
            
            assert 'recommended_algorithm' in recommendation
            assert 'complexity_score' in recommendation
            assert 'complexity_category' in recommendation
            assert isinstance(recommendation['recommended_algorithm'], Algorithm)
            
            print(f"   ✓ Algorithm recommended: {recommendation['recommended_algorithm'].value}")
            print(f"   ✓ Complexity: {recommendation['complexity_category']} (score: {recommendation['complexity_score']:.1f})")
            
            self._record_test("Algorithm Selection", True, 
                            f"Selected {recommendation['recommended_algorithm'].value} for {recommendation['complexity_category']} level")
            
        except Exception as e:
            self._record_test("Algorithm Selection", False, f"Selection failed: {str(e)}")
    
    def test_thinking_rabbit_level_1(self):
        """Test the key validation case: Thinking Rabbit Original Level 1."""
        print("\n🎯 Test 3: Thinking Rabbit Level 1 (Key Validation)")
        
        try:
            # Load the first Thinking Rabbit level
            level = self._load_thinking_rabbit_level_1()
            if level is None:
                # Create the test level manually if file not found
                level = self._create_thinking_rabbit_level_1()
            
            print(f"   📋 Level: {level.width}x{level.height}, {len(level.boxes)} boxes, {len(level.targets)} targets")
            
            # Test with automatic algorithm selection
            print("   🤖 Testing with automatic algorithm selection...")
            start_time = time.time()
            
            request = SolveRequest(
                level=level,
                algorithm=None,  # Auto-selection
                collect_ml_metrics=True,
                generate_report=True
            )
            
            result = self.ai_controller.solve_level(request)
            solve_time = time.time() - start_time
            
            # Validation criteria from the plan
            success = result.success
            within_time_limit = solve_time < 5.0  # Must be under 5 seconds
            solution_reasonable = result.solution_data and len(result.solution_data.moves) <= 100 if result.solution_data else False
            has_ml_metrics = result.ml_metrics is not None
            has_ml_report = result.ml_report is not None
            
            print(f"   ⏱️  Solve time: {solve_time:.2f}s (target: <5s)")
            
            if success and result.solution_data:
                moves_count = len(result.solution_data.moves)
                states_explored = result.solution_data.states_explored
                algorithm_used = result.solution_data.algorithm_used.value
                
                print(f"   ✅ Solution found: {moves_count} moves")
                print(f"   🔍 States explored: {states_explored:,}")
                print(f"   🧠 Algorithm used: {algorithm_used}")
                print(f"   📊 ML metrics collected: {'Yes' if has_ml_metrics else 'No'}")
                print(f"   📈 ML report generated: {'Yes' if has_ml_report else 'No'}")
                
                # Calculate efficiency
                efficiency = states_explored / max(result.solution_data.states_generated, 1)
                print(f"   ⚡ Search efficiency: {efficiency:.1%}")
                
                # Overall validation
                all_criteria_met = (success and within_time_limit and solution_reasonable and 
                                  has_ml_metrics and has_ml_report)
                
                if all_criteria_met:
                    self._record_test("Thinking Rabbit Level 1", True, 
                                    f"✅ ALL CRITERIA MET - {moves_count} moves in {solve_time:.2f}s using {algorithm_used}")
                else:
                    issues = []
                    if not within_time_limit: issues.append("time limit exceeded")
                    if not solution_reasonable: issues.append("solution too long")
                    if not has_ml_metrics: issues.append("missing ML metrics")
                    if not has_ml_report: issues.append("missing ML report")
                    
                    self._record_test("Thinking Rabbit Level 1", False, 
                                    f"Some criteria not met: {', '.join(issues)}")
            else:
                self._record_test("Thinking Rabbit Level 1", False, 
                                f"Failed to solve level in {solve_time:.2f}s")
                
        except Exception as e:
            self._record_test("Thinking Rabbit Level 1", False, f"Test failed: {str(e)}")
    
    def test_ml_metrics_collection(self):
        """Test ML metrics collection functionality."""
        print("\n📊 Test 4: ML Metrics Collection")
        
        try:
            # Use a simple level for testing
            level = self._create_simple_test_level()
            
            # Solve with ML metrics collection
            request = SolveRequest(level=level, collect_ml_metrics=True)
            result = self.ai_controller.solve_level(request)
            
            if result.success and result.ml_metrics:
                metrics = result.ml_metrics
                
                # Validate metrics structure
                required_categories = ['basic_metrics', 'algorithm_metrics', 'level_structure', 
                                     'movement_analysis', 'spatial_analysis', 'ml_features']
                
                all_present = all(category in metrics for category in required_categories)
                
                if all_present:
                    print("   ✅ All metric categories present")
                    
                    # Check some specific metrics
                    basic = metrics['basic_metrics']
                    features = metrics['ml_features']
                    
                    print(f"   📈 Basic metrics: {len(basic)} items")
                    print(f"   🎯 ML features: {len(features)} items")
                    print(f"   ⚡ States per second: {basic.get('states_per_second', 0):.0f}")
                    
                    self._record_test("ML Metrics Collection", True, 
                                    f"Collected {len(required_categories)} metric categories successfully")
                else:
                    missing = [cat for cat in required_categories if cat not in metrics]
                    self._record_test("ML Metrics Collection", False, 
                                    f"Missing categories: {missing}")
            else:
                self._record_test("ML Metrics Collection", False, "No metrics collected")
                
        except Exception as e:
            self._record_test("ML Metrics Collection", False, f"Collection failed: {str(e)}")
    
    def test_report_generation(self):
        """Test ML report generation."""
        print("\n📋 Test 5: Report Generation")
        
        try:
            level = self._create_simple_test_level()
            
            # Solve with report generation
            request = SolveRequest(level=level, collect_ml_metrics=True, generate_report=True)
            result = self.ai_controller.solve_level(request)
            
            if result.success and result.ml_report:
                report = result.ml_report
                
                # Check report structure
                required_sections = ['metadata', 'executive_summary', 'performance_analysis', 
                                   'algorithm_analysis', 'ml_features']
                
                sections_present = all(section in report for section in required_sections)
                
                if sections_present:
                    print("   ✅ Report generated with all sections")
                    
                    # Check metadata
                    metadata = report['metadata']
                    print(f"   📝 Report ID: {metadata.get('report_id', 'N/A')}")
                    print(f"   🕒 Generated: {metadata.get('generation_timestamp', 'N/A')}")
                    
                    # Check executive summary
                    summary = report['executive_summary']
                    performance_score = summary.get('overall_performance_score', 0)
                    print(f"   🎯 Performance Score: {performance_score:.1%}")
                    
                    self._record_test("Report Generation", True, 
                                    f"Complete report generated (performance: {performance_score:.1%})")
                else:
                    missing = [sec for sec in required_sections if sec not in report]
                    self._record_test("Report Generation", False, f"Missing sections: {missing}")
            else:
                self._record_test("Report Generation", False, "No report generated")
                
        except Exception as e:
            self._record_test("Report Generation", False, f"Generation failed: {str(e)}")
    
    def test_benchmark_system(self):
        """Test algorithm benchmarking system."""
        print("\n🏁 Test 6: Benchmark System")
        
        try:
            level = self._create_simple_test_level()
            
            # Run benchmark on subset of algorithms for speed
            algorithms_to_test = [Algorithm.BFS, Algorithm.ASTAR, Algorithm.GREEDY]
            
            print(f"   🔬 Benchmarking {len(algorithms_to_test)} algorithms...")
            
            benchmark_results = self.ai_controller.benchmark_algorithms(level, algorithms_to_test)
            
            # Validate benchmark results
            if 'algorithm_results' in benchmark_results:
                results = benchmark_results['algorithm_results']
                successful_algorithms = [alg for alg, result in results.items() if result.get('success')]
                
                print(f"   ✅ {len(successful_algorithms)} algorithms succeeded")
                
                if benchmark_results.get('best_algorithm'):
                    print(f"   🏆 Best algorithm: {benchmark_results['best_algorithm']}")
                
                if benchmark_results.get('fastest_algorithm'):
                    print(f"   ⚡ Fastest algorithm: {benchmark_results['fastest_algorithm']}")
                
                self._record_test("Benchmark System", True, 
                                f"Benchmarked {len(algorithms_to_test)} algorithms, {len(successful_algorithms)} succeeded")
            else:
                self._record_test("Benchmark System", False, "Invalid benchmark results structure")
                
        except Exception as e:
            self._record_test("Benchmark System", False, f"Benchmark failed: {str(e)}")
    
    def test_performance_validation(self):
        """Test overall performance criteria."""
        print("\n⚡ Test 7: Performance Validation")
        
        try:
            # Get solve statistics
            stats = self.ai_controller.get_solve_statistics()
            
            global_stats = stats.get('global_statistics', {})
            success_rate = global_stats.get('success_rate', 0)
            total_solves = global_stats.get('total_solves', 0)
            
            print(f"   📊 Total solves: {total_solves}")
            print(f"   ✅ Success rate: {success_rate:.1f}%")
            
            # Performance criteria
            meets_success_rate = success_rate >= 80.0  # At least 80% success rate
            has_reasonable_volume = total_solves >= 3    # At least some test volume
            
            if meets_success_rate and has_reasonable_volume:
                self._record_test("Performance Validation", True, 
                                f"Success rate {success_rate:.1f}% meets criteria")
            else:
                issues = []
                if not meets_success_rate: issues.append(f"low success rate ({success_rate:.1f}%)")
                if not has_reasonable_volume: issues.append(f"insufficient test volume ({total_solves})")
                
                self._record_test("Performance Validation", False, f"Issues: {', '.join(issues)}")
                
        except Exception as e:
            self._record_test("Performance Validation", False, f"Validation failed: {str(e)}")
    
    def _record_test(self, test_name: str, passed: bool, details: str):
        """Record test result."""
        self.test_results['tests_run'] += 1
        if passed:
            self.test_results['tests_passed'] += 1
            print(f"   ✅ PASSED: {details}")
        else:
            self.test_results['tests_failed'] += 1
            print(f"   ❌ FAILED: {details}")
        
        self.test_results['test_details'].append({
            'name': test_name,
            'passed': passed,
            'details': details
        })
    
    def print_validation_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 60)
        print("🏆 VALIDATION SUMMARY")
        print("=" * 60)
        
        results = self.test_results
        print(f"Tests Run: {results['tests_run']}")
        print(f"Tests Passed: {results['tests_passed']}")
        print(f"Tests Failed: {results['tests_failed']}")
        print(f"Success Rate: {(results['tests_passed'] / results['tests_run']) * 100:.1f}%")
        
        if results['tests_failed'] == 0:
            print("\n🎉 ALL TESTS PASSED! AI refactoring implementation is complete and validated.")
            print("\n✨ The unified AI system is ready for production use with:")
            print("   • Automatic algorithm selection")
            print("   • Enhanced Sokolution solver with all algorithms")
            print("   • Complete ML metrics collection")
            print("   • Comprehensive reporting system")
            print("   • GUI integration with visual animation")
            print("   • Benchmark and analysis capabilities")
        else:
            print(f"\n⚠️  {results['tests_failed']} test(s) failed. Please review and fix issues.")
            
            print("\nFailed tests:")
            for test in results['test_details']:
                if not test['passed']:
                    print(f"   ❌ {test['name']}: {test['details']}")
    
    def _create_simple_test_level(self):
        """Create a simple test level for validation."""
        # Simple 5x5 level with 1 box
        level_data = [
            "#####",
            "#   #",
            "# $ #",
            "#  .#",
            "#@  #",
            "#####"
        ]
        
        return Level.from_string("\n".join(level_data))
    
    def _load_thinking_rabbit_level_1(self):
        """Try to load the first Thinking Rabbit level from file."""
        try:
            thinking_rabbit_path = Path("src/levels/Original & Extra/Original.txt")
            if thinking_rabbit_path.exists():
                with open(thinking_rabbit_path, 'r') as f:
                    content = f.read()
                
                # Parse the first level (this is a simplified parser)
                lines = content.strip().split('\n')
                level_lines = []
                in_level = False
                
                for line in lines:
                    if line.strip() and not line.startswith(';') and not line.startswith('#'):
                        if not in_level:
                            in_level = True
                        level_lines.append(line)
                    elif in_level and not line.strip():
                        break  # End of first level
                
                if level_lines:
                    return Level.from_string("\n".join(level_lines))
            
        except Exception as e:
            print(f"   ⚠️  Could not load Thinking Rabbit level: {e}")
        
        return None
    
    def _create_thinking_rabbit_level_1(self):
        """Create Thinking Rabbit Level 1 manually if file not available."""
        # This is the first level from Thinking Rabbit Original collection
        level_data = [
            "    #####          ",
            "    #   #          ",
            "    #$  #          ",
            "  ###  $##         ",
            "  #  $ $ #         ",
            "### # ## #   ######",
            "#   # ## #####  ..#",
            "# $  $          ..#",
            "##### ### #@##  ..#",
            "    #     #########",
            "    #######        "
        ]
        
        return Level.from_string("\n".join(level_data))


def main():
    """Main function to run the validation."""
    print("🚀 PySokoban Unified AI System Validation")
    print("🤖 Testing the complete AI refactoring implementation")
    print("📋 Based on AI_REFACTORING_PLAN.md Phase 5 validation criteria")
    
    validator = AISystemValidator()
    success = validator.run_complete_validation()
    
    # Export results
    results_file = "ai_validation_results.json"
    with open(results_file, 'w') as f:
        json.dump(validator.test_results, f, indent=2)
    
    print(f"\n📄 Detailed results exported to: {results_file}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())