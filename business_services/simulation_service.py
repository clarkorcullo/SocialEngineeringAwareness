"""
Simulation service for handling simulation-related business logic
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import random
import json

from data_models.progress_models import SimulationResult, SimulationType
from data_models.user_models import User
from simulations import PhishingSimulation, PretextingSimulation, BaitingSimulation, QuidProQuoSimulation

class SimulationService:
    """Service class for simulation operations"""
    
    def __init__(self):
        """Initialize simulation service"""
        pass
    
    @staticmethod
    def create_phishing_simulation() -> Dict[str, Any]:
        """Create a phishing simulation scenario"""
        phishing_sim = PhishingSimulation()
        return phishing_sim.get_random_scenario()
    
    @staticmethod
    def create_pretexting_simulation() -> Dict[str, Any]:
        """Create a pretexting simulation scenario"""
        pretexting_sim = PretextingSimulation()
        return pretexting_sim.get_random_scenario()
    
    @staticmethod
    def grade_simulation(simulation_data: Dict[str, Any], user_answers: Dict[str, str]) -> Dict[str, Any]:
        """Grade a simulation and return results"""
        try:
            # Use the base simulation class to calculate score
            simulation_type = simulation_data.get('type', '')
            
            if simulation_type == 'phishing':
                sim = PhishingSimulation()
            elif simulation_type == 'pretexting':
                sim = PretextingSimulation()
            elif simulation_type == 'baiting':
                sim = BaitingSimulation()
            elif simulation_type == 'quid_pro_quo':
                sim = QuidProQuoSimulation()
            else:
                raise ValueError(f"Unknown simulation type: {simulation_type}")
            
            return sim.calculate_score(simulation_data, user_answers)
            
        except Exception as e:
            print(f"Error grading simulation: {e}")
            return {
                'score': 0,
                'total_questions': 0,
                'percentage': 0,
                'detailed_results': [],
                'passed': False
            }
    
    @staticmethod
    def save_simulation_result(
        user_id: int,
        simulation_type: str,
        score: int,
        total_questions: int,
        decisions_made: List[Dict[str, Any]],
        scenario_data: Dict[str, Any],
        time_taken: int = 0,
        module_id: Optional[int] = None
    ) -> Optional[SimulationResult]:
        """Save simulation result to database"""
        try:
            # Validate simulation type
            if simulation_type not in [e.value for e in SimulationType]:
                raise ValueError(f"Invalid simulation type: {simulation_type}")
            
            # Create simulation result
            result = SimulationResult(
                user_id=user_id,
                module_id=module_id,
                simulation_type=simulation_type,
                score=score,
                time_taken=time_taken
            )
            
            # Set decisions and scenario data
            result.set_decisions_data(decisions_made)
            result.set_scenario_data(scenario_data)
            
            # Complete simulation
            result.complete_simulation(score)
            
            # Save to database
            if result.save():
                return result
            return None
            
        except Exception as e:
            print(f"Error saving simulation result: {e}")
            return None
    
    @staticmethod
    def get_user_simulation_history(user_id: int, simulation_type: Optional[str] = None) -> List[SimulationResult]:
        """Get user's simulation history"""
        try:
            return SimulationResult.get_user_simulations(user_id, simulation_type)
        except Exception as e:
            print(f"Error getting simulation history: {e}")
            return []
    
    @staticmethod
    def get_simulation_statistics(simulation_type: str) -> Dict[str, Any]:
        """Get statistics for a specific simulation type"""
        try:
            # Get all results for this simulation type
            results = SimulationResult.query.filter_by(simulation_type=simulation_type).all()
            
            if not results:
                return {
                    'total_attempts': 0,
                    'average_score': 0.0,
                    'completion_rate': 0.0,
                    'best_score': 0,
                    'total_participants': 0
                }
            
            total_attempts = len(results)
            total_participants = len(set(r.user_id for r in results))
            completed_simulations = [r for r in results if r.completed]
            average_score = sum(r.score for r in completed_simulations) / len(completed_simulations) if completed_simulations and len(completed_simulations) > 0 else 0
            completion_rate = (len(completed_simulations) / total_attempts) * 100 if total_attempts and total_attempts > 0 else 0
            best_score = max(r.score for r in results) if results else 0
            
            return {
                'total_attempts': total_attempts,
                'average_score': round(average_score, 2),
                'completion_rate': round(completion_rate, 2),
                'best_score': best_score,
                'total_participants': total_participants
            }
            
        except Exception as e:
            print(f"Error getting simulation statistics: {e}")
            return {}
    
    @staticmethod
    def get_simulation_by_type(simulation_type: str) -> Optional[Dict[str, Any]]:
        """Get simulation scenario by type"""
        try:
            if simulation_type == SimulationType.PHISHING.value:
                return SimulationService.create_phishing_simulation()
            elif simulation_type == SimulationType.PRETEXTING.value:
                return SimulationService.create_pretexting_simulation()
            elif simulation_type == SimulationType.BAITING.value:
                baiting_sim = BaitingSimulation()
                return baiting_sim.get_random_scenario()
            elif simulation_type == SimulationType.QUID_PRO_QUO.value:
                quid_pro_quo_sim = QuidProQuoSimulation()
                return quid_pro_quo_sim.get_random_scenario()
            else:
                raise ValueError(f"Unsupported simulation type: {simulation_type}")
                
        except Exception as e:
            print(f"Error getting simulation by type: {e}")
            return None
    
    @staticmethod
    def validate_simulation_answers(simulation_data: Dict[str, Any], answers: Dict[str, str]) -> bool:
        """Validate simulation answers"""
        try:
            options = simulation_data.get('options', [])
            option_ids = {str(option['id']) for option in options}
            answer_ids = set(answers.keys())
            
            # Check if all questions have answers
            missing_answers = option_ids - answer_ids
            if missing_answers:
                print(f"Missing answers for questions: {missing_answers}")
                return False
            
            # Check if all answers are valid
            valid_options = {'a', 'b', 'c', 'd'}
            for answer in answers.values():
                if answer.lower() not in valid_options:
                    print(f"Invalid answer option: {answer}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error validating simulation answers: {e}")
            return False
    
    @staticmethod
    def get_simulation_content(simulation_type: str) -> Dict[str, Any]:
        """Get simulation content for display"""
        try:
            return SimulationService.get_simulation_by_type(simulation_type)
        except Exception as e:
            print(f"Error getting simulation content: {e}")
            return {}

