"""
Outcome Predictor Service - Judicial outcome prediction
Predicts case outcomes (Affirmed, Reversed, Remanded) using similarity-based classification
"""

import os
from typing import List, Dict, Tuple
from collections import Counter
from loguru import logger

from shared.models import OutcomePrediction, SearchResult


class OutcomePredictor:
    """
    Service for predicting judicial outcomes using similarity-based classification.
    
    Algorithm:
    1. Use semantic search to find similar historical cases
    2. Extract outcomes from top-k similar cases
    3. Calculate weighted vote based on similarity scores
    4. Normalize to probability distribution
    5. Determine predicted outcome as max probability
    
    Features:
    - Similarity-based classification
    - Confidence scoring
    - Low confidence flagging
    - Supporting case citations
    - Explanation generation
    """
    
    def __init__(
        self,
        search_engine: any,
        top_k_similar: int = 20,
        confidence_threshold: float = 0.6,
        min_supporting_cases: int = 3
    ):
        """
        Initialize the outcome predictor.
        
        Args:
            search_engine: SemanticSearchEngine instance
            top_k_similar: Number of similar cases to retrieve for prediction
            confidence_threshold: Minimum confidence for high-confidence predictions
            min_supporting_cases: Minimum number of supporting cases required
        """
        self.search_engine = search_engine
        self.top_k_similar = top_k_similar
        self.confidence_threshold = confidence_threshold
        self.min_supporting_cases = min_supporting_cases
        
        logger.info("Initializing OutcomePredictor")
        logger.info(f"Top-k similar cases: {top_k_similar}")
        logger.info(f"Confidence threshold: {confidence_threshold}")
    
    async def predict_outcome(
        self,
        facts: str,
        issue: str,
        year_range: Tuple[int, int] = None
    ) -> OutcomePrediction:
        """
        Predict judicial outcome based on case facts and legal issue.
        
        Args:
            facts: Case facts description
            issue: Legal issue or question presented
            year_range: Optional year range for historical cases
        
        Returns:
            OutcomePrediction with outcome, probabilities, confidence, and explanation
        
        Example:
            prediction = await predictor.predict_outcome(
                facts="Landlord failed to repair heating system...",
                issue="Whether landlord breached warranty of habitability",
                year_range=(2022, 2023)
            )
        """
        logger.info("Predicting outcome")
        logger.debug(f"Facts: {facts[:100]}...")
        logger.debug(f"Issue: {issue}")
        
        try:
            # Step 1: Retrieve similar cases using semantic search
            # Combine facts and issue for comprehensive search
            query = f"{issue}. {facts}"
            
            similar_cases = await self.search_engine.search(
                query=query,
                top_k=self.top_k_similar,
                year_range=year_range,
                min_similarity=0.5  # Lower threshold for prediction
            )
            
            if not similar_cases:
                logger.warning("No similar cases found")
                return self._create_low_confidence_prediction(
                    "No similar cases found in the database"
                )
            
            logger.info(f"Found {len(similar_cases)} similar cases")
            
            # Step 2: Extract outcomes and calculate weighted probabilities
            probabilities = self._calculate_outcome_probabilities(similar_cases)
            
            # Step 3: Determine predicted outcome
            predicted_outcome = max(probabilities, key=probabilities.get)
            confidence = probabilities[predicted_outcome]
            
            # Step 4: Get supporting cases
            supporting_cases = self._get_supporting_cases(
                similar_cases,
                predicted_outcome
            )
            
            # Step 5: Generate explanation
            explanation = self._generate_explanation(
                predicted_outcome,
                probabilities,
                similar_cases,
                supporting_cases
            )
            
            # Step 6: Check confidence level
            is_low_confidence = confidence < self.confidence_threshold
            if is_low_confidence:
                logger.warning(f"Low confidence prediction: {confidence:.2f}")
                explanation = f"[LOW CONFIDENCE] {explanation}"
            
            prediction = OutcomePrediction(
                outcome=predicted_outcome,
                probabilities=probabilities,
                confidence=confidence,
                supporting_cases=supporting_cases,
                explanation=explanation
            )
            
            logger.success(f"Predicted outcome: {predicted_outcome} "
                          f"(confidence: {confidence:.2f})")
            
            return prediction
        
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise
    
    def _calculate_outcome_probabilities(
        self,
        similar_cases: List[SearchResult]
    ) -> Dict[str, float]:
        """
        Calculate outcome probabilities using weighted voting.
        
        Algorithm:
        - Each case votes for its outcome
        - Vote weight = similarity score
        - Normalize to probability distribution
        
        Args:
            similar_cases: List of similar cases with similarity scores
        
        Returns:
            Dictionary mapping outcomes to probabilities
        """
        # Initialize outcome weights
        outcome_weights = {
            'Affirmed': 0.0,
            'Reversed': 0.0,
            'Remanded': 0.0
        }
        
        total_weight = 0.0
        
        # Accumulate weighted votes
        for case in similar_cases:
            # Extract outcome from metadata
            outcome = case.metadata.get('final_judgment', None)
            
            if outcome not in outcome_weights:
                logger.warning(f"Unknown outcome: {outcome} in case {case.case_name}")
                continue
            
            # Weight by similarity score
            weight = case.similarity_score
            outcome_weights[outcome] += weight
            total_weight += weight
        
        # Normalize to probabilities
        if total_weight > 0:
            probabilities = {
                outcome: weight / total_weight
                for outcome, weight in outcome_weights.items()
            }
        else:
            # Equal probabilities if no valid cases
            probabilities = {
                outcome: 1.0 / 3.0
                for outcome in outcome_weights.keys()
            }
        
        logger.debug(f"Outcome probabilities: {probabilities}")
        return probabilities
    
    def _get_supporting_cases(
        self,
        similar_cases: List[SearchResult],
        predicted_outcome: str,
        max_cases: int = 5
    ) -> List[str]:
        """
        Get list of supporting cases for the predicted outcome.
        
        Args:
            similar_cases: All similar cases
            predicted_outcome: The predicted outcome
            max_cases: Maximum number of supporting cases to return
        
        Returns:
            List of case names that support the prediction
        """
        supporting = []
        
        for case in similar_cases:
            outcome = case.metadata.get('final_judgment', None)
            
            if outcome == predicted_outcome:
                case_citation = f"{case.case_name} ({case.year})"
                supporting.append(case_citation)
                
                if len(supporting) >= max_cases:
                    break
        
        return supporting
    
    def _generate_explanation(
        self,
        predicted_outcome: str,
        probabilities: Dict[str, float],
        similar_cases: List[SearchResult],
        supporting_cases: List[str]
    ) -> str:
        """
        Generate human-readable explanation for the prediction.
        
        Args:
            predicted_outcome: Predicted outcome
            probabilities: Outcome probabilities
            similar_cases: All similar cases
            supporting_cases: Supporting case citations
        
        Returns:
            Explanation string
        """
        # Count outcomes in similar cases
        outcome_counts = Counter(
            case.metadata.get('final_judgment', 'Unknown')
            for case in similar_cases
        )
        
        # Build explanation
        explanation_parts = []
        
        # Main prediction
        explanation_parts.append(
            f"Based on analysis of {len(similar_cases)} similar cases, "
            f"the predicted outcome is '{predicted_outcome}' with "
            f"{probabilities[predicted_outcome]:.1%} confidence."
        )
        
        # Outcome distribution
        distribution = ", ".join(
            f"{outcome}: {count} cases"
            for outcome, count in outcome_counts.most_common()
        )
        explanation_parts.append(f"Outcome distribution: {distribution}.")
        
        # Supporting cases
        if supporting_cases:
            explanation_parts.append(
                f"Key supporting precedents include: {', '.join(supporting_cases[:3])}."
            )
        
        # Confidence assessment
        confidence = probabilities[predicted_outcome]
        if confidence >= 0.8:
            explanation_parts.append(
                "This is a high-confidence prediction with strong precedent support."
            )
        elif confidence >= self.confidence_threshold:
            explanation_parts.append(
                "This is a moderate-confidence prediction with reasonable precedent support."
            )
        else:
            explanation_parts.append(
                "This is a low-confidence prediction. Similar cases show mixed outcomes."
            )
        
        return " ".join(explanation_parts)
    
    def _create_low_confidence_prediction(self, reason: str) -> OutcomePrediction:
        """
        Create a low-confidence prediction when insufficient data is available.
        
        Args:
            reason: Reason for low confidence
        
        Returns:
            OutcomePrediction with equal probabilities
        """
        equal_prob = 1.0 / 3.0
        
        return OutcomePrediction(
            outcome="Affirmed",  # Default to most common outcome
            probabilities={
                'Affirmed': equal_prob,
                'Reversed': equal_prob,
                'Remanded': equal_prob
            },
            confidence=equal_prob,
            supporting_cases=[],
            explanation=f"[LOW CONFIDENCE] {reason}. "
                       f"Prediction based on equal probability distribution."
        )
    
    def get_confidence_score(self, prediction: OutcomePrediction) -> float:
        """
        Get confidence score for a prediction.
        
        Args:
            prediction: OutcomePrediction object
        
        Returns:
            Confidence score (0.0 to 1.0)
        """
        return prediction.confidence
    
    def is_low_confidence(self, prediction: OutcomePrediction) -> bool:
        """
        Check if prediction has low confidence.
        
        Args:
            prediction: OutcomePrediction object
        
        Returns:
            True if confidence is below threshold
        """
        return prediction.confidence < self.confidence_threshold


# Singleton instance
_predictor_instance = None


def get_outcome_predictor(
    search_engine: any = None,
    top_k_similar: int = 20,
    confidence_threshold: float = 0.6
) -> OutcomePredictor:
    """
    Get or create the singleton OutcomePredictor instance.
    
    Args:
        search_engine: SemanticSearchEngine instance (only used on first call)
        top_k_similar: Top-k similar cases (only used on first call)
        confidence_threshold: Confidence threshold (only used on first call)
    
    Returns:
        OutcomePredictor instance
    """
    global _predictor_instance
    
    if _predictor_instance is None:
        if search_engine is None:
            raise ValueError("search_engine must be provided on first call")
        
        top_k_similar = int(os.getenv("PREDICTION_TOP_K", top_k_similar))
        confidence_threshold = float(os.getenv(
            "PREDICTION_CONFIDENCE_THRESHOLD",
            confidence_threshold
        ))
        
        _predictor_instance = OutcomePredictor(
            search_engine=search_engine,
            top_k_similar=top_k_similar,
            confidence_threshold=confidence_threshold
        )
    
    return _predictor_instance
