"""
Opinion Generator Service - Judicial opinion generation with RAG
Generates Supreme Court-style opinions using retrieved precedents and LLM
"""

import os
import re
from typing import List, Dict, Optional
from loguru import logger
import httpx

from shared.models import GeneratedOpinion, SearchResult, CaseLawDocument


class OpinionGenerator:
    """
    Service for generating judicial opinions using RAG (Retrieval-Augmented Generation).
    
    Pipeline:
    1. Retrieve relevant precedents using semantic search
    2. Rank precedents by relevance
    3. Build LLM prompt with case context and precedents
    4. Generate opinion using LLM
    5. Format and validate opinion structure
    6. Add citations and disclaimer
    
    Features:
    - Per Curiam opinion generation
    - Supreme Court format compliance
    - Bluebook-style citations
    - Precedent integration
    - Formal judicial tone
    """
    
    def __init__(
        self,
        search_engine: any,
        llm_api_url: str = None,
        llm_api_key: str = None,
        model: str = "gpt-4",
        temperature: float = 0.3,
        max_tokens: int = 2048,
        max_precedents: int = 5,
        timeout: int = 60
    ):
        """
        Initialize the opinion generator.
        
        Args:
            search_engine: SemanticSearchEngine instance
            llm_api_url: LLM API endpoint URL
            llm_api_key: API key for LLM service
            model: LLM model name (gpt-4, gpt-3.5-turbo, etc.)
            temperature: Generation temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            max_precedents: Maximum precedents to include
            timeout: HTTP request timeout in seconds
        """
        self.search_engine = search_engine
        self.llm_api_url = llm_api_url or os.getenv(
            "LLM_API_URL",
            "https://api.openai.com/v1/chat/completions"
        )
        self.llm_api_key = llm_api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_precedents = max_precedents
        self.timeout = timeout
        
        logger.info("Initializing OpinionGenerator")
        logger.info(f"Model: {model}")
        logger.info(f"Temperature: {temperature}")
        logger.info(f"Max precedents: {max_precedents}")
    
    async def generate_opinion(
        self,
        case_context: Dict,
        opinion_type: str = "per_curiam",
        max_precedents: int = None
    ) -> GeneratedOpinion:
        """
        Generate complete judicial opinion.
        
        Args:
            case_context: Dictionary with case information:
                - facts: Case facts
                - issue: Legal issue
                - case_name: Optional case name
                - case_number: Optional case number
                - petitioner: Optional petitioner name
                - respondent: Optional respondent name
                - lower_court: Optional lower court name
            opinion_type: Type of opinion (per_curiam, majority, etc.)
            max_precedents: Override default max precedents
        
        Returns:
            GeneratedOpinion with full text, sections, and citations
        
        Example:
            opinion = await generator.generate_opinion(
                case_context={
                    "facts": "The landlord failed to repair...",
                    "issue": "Whether landlord breached warranty...",
                    "case_name": "Smith v. Jones",
                    "petitioner": "Smith",
                    "respondent": "Jones"
                },
                opinion_type="per_curiam"
            )
        """
        logger.info(f"Generating {opinion_type} opinion")
        
        try:
            # Step 1: Retrieve relevant precedents
            precedents = await self._retrieve_precedents(
                case_context,
                max_precedents or self.max_precedents
            )
            
            logger.info(f"Retrieved {len(precedents)} precedents")
            
            # Step 2: Build LLM prompt
            prompt = self._build_opinion_prompt(
                case_context,
                precedents,
                opinion_type
            )
            
            # Step 3: Generate opinion using LLM
            generated_text = await self._call_llm(prompt)
            
            # Step 4: Parse and structure the opinion
            sections = self._parse_opinion_sections(generated_text)
            
            # Step 5: Format citations
            cited_precedents = self._extract_cited_cases(generated_text, precedents)
            
            # Step 6: Create final opinion with disclaimer
            full_text = self._format_final_opinion(
                generated_text,
                case_context,
                opinion_type
            )
            
            opinion = GeneratedOpinion(
                full_text=full_text,
                sections=sections,
                cited_precedents=cited_precedents,
                generation_metadata={
                    "model": self.model,
                    "temperature": self.temperature,
                    "precedents_used": len(precedents),
                    "opinion_type": opinion_type
                },
                disclaimer=(
                    "This opinion is AI-generated for research and academic purposes only. "
                    "It does not constitute legal advice and should not be relied upon for "
                    "actual legal proceedings."
                )
            )
            
            logger.success("Opinion generated successfully")
            return opinion
        
        except Exception as e:
            logger.error(f"Opinion generation failed: {e}")
            raise
    
    async def _retrieve_precedents(
        self,
        case_context: Dict,
        max_precedents: int
    ) -> List[SearchResult]:
        """
        Retrieve relevant precedents using semantic search.
        
        Args:
            case_context: Case information
            max_precedents: Maximum number of precedents
        
        Returns:
            List of relevant precedent cases
        """
        facts = case_context.get('facts', '')
        issue = case_context.get('issue', '')
        
        # Search in multiple sections for comprehensive precedents
        precedents = []
        
        # Search by issue/reasoning (most relevant for legal analysis)
        reasoning_results = await self.search_engine.search_by_reasoning(
            legal_issue=issue,
            top_k=max_precedents,
            year_range=(2022, 2023)
        )
        precedents.extend(reasoning_results)
        
        # Search by facts (for factual similarity)
        if facts:
            facts_results = await self.search_engine.search_by_facts(
                facts=facts,
                top_k=max_precedents // 2,
                year_range=(2022, 2023)
            )
            precedents.extend(facts_results)
        
        # Remove duplicates and rank by relevance
        precedents = self._rank_by_relevance(precedents)
        
        return precedents[:max_precedents]
    
    def _rank_by_relevance(self, precedents: List[SearchResult]) -> List[SearchResult]:
        """
        Rank precedents by relevance, removing duplicates.
        
        Args:
            precedents: List of search results
        
        Returns:
            Ranked and deduplicated precedents
        """
        # Remove duplicates by case name
        seen = set()
        unique_precedents = []
        
        for precedent in precedents:
            if precedent.case_name not in seen:
                seen.add(precedent.case_name)
                unique_precedents.append(precedent)
        
        # Sort by similarity score
        ranked = sorted(
            unique_precedents,
            key=lambda x: x.similarity_score,
            reverse=True
        )
        
        return ranked
    
    def _build_opinion_prompt(
        self,
        case_context: Dict,
        precedents: List[SearchResult],
        opinion_type: str
    ) -> str:
        """
        Build LLM prompt for opinion generation.
        
        Args:
            case_context: Case information
            precedents: Retrieved precedents
            opinion_type: Opinion type
        
        Returns:
            Formatted prompt string
        """
        facts = case_context.get('facts', '')
        issue = case_context.get('issue', '')
        case_name = case_context.get('case_name', 'Petitioner v. Respondent')
        
        # Format precedents
        precedent_text = self._format_precedents_for_prompt(precedents)
        
        prompt = f"""You are a Supreme Court justice drafting a {opinion_type.replace('_', ' ').title()} opinion.

CASE: {case_name}

FACTS:
{facts}

LEGAL ISSUE:
{issue}

RELEVANT PRECEDENTS:
{precedent_text}

INSTRUCTIONS:
1. Write in formal judicial tone using institutional voice
2. Follow official Supreme Court opinion structure with these sections:
   - PROCEDURAL HISTORY (brief)
   - STATEMENT OF FACTS
   - LEGAL ISSUE
   - REASONING (cite and apply precedents)
   - HOLDING
   - JUDGMENT (Affirmed, Reversed, or Remanded)
3. Cite precedents using proper format: [Case Name] ([Year])
4. Provide clear legal reasoning connecting precedents to this case
5. Use phrases like "The Court has consistently held", "We find that", "It is well established"
6. Conclude with "It is so ordered."
7. Do NOT include individual justice names or attributions
8. Maintain neutral, authoritative tone throughout

Generate the complete opinion now:"""
        
        return prompt
    
    def _format_precedents_for_prompt(
        self,
        precedents: List[SearchResult]
    ) -> str:
        """
        Format precedents for inclusion in LLM prompt.
        
        Args:
            precedents: List of precedent cases
        
        Returns:
            Formatted precedent text
        """
        formatted = []
        
        for i, precedent in enumerate(precedents, 1):
            # Extract relevant information from metadata
            facts = precedent.metadata.get('facts', precedent.snippet)[:300]
            reasoning = precedent.metadata.get('reasoning', '')[:400]
            holding = precedent.metadata.get('holding', '')[:200]
            
            precedent_entry = f"""
{i}. {precedent.case_name} ({precedent.year})
   Facts: {facts}...
   Reasoning: {reasoning}...
   Holding: {holding}...
"""
            formatted.append(precedent_entry)
        
        return "\n".join(formatted)
    
    async def _call_llm(self, prompt: str) -> str:
        """
        Call LLM API to generate opinion text.
        
        Args:
            prompt: Formatted prompt
        
        Returns:
            Generated opinion text
        """
        if not self.llm_api_key:
            logger.warning("No LLM API key configured, returning mock opinion")
            return self._generate_mock_opinion()
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                headers = {
                    "Authorization": f"Bearer {self.llm_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a Supreme Court justice writing formal judicial opinions."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "top_p": 0.9,
                    "frequency_penalty": 0.3
                }
                
                response = await client.post(
                    self.llm_api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                generated_text = data['choices'][0]['message']['content']
                
                logger.debug(f"LLM generated {len(generated_text)} characters")
                return generated_text
            
            except httpx.HTTPError as e:
                logger.error(f"LLM API error: {e}")
                logger.warning("Falling back to mock opinion")
                return self._generate_mock_opinion()
    
    def _generate_mock_opinion(self) -> str:
        """
        Generate a mock opinion for testing when LLM is unavailable.
        
        Returns:
            Mock opinion text
        """
        return """SUPREME COURT OF THE UNITED STATES

PER CURIAM

I. PROCEDURAL HISTORY
This case comes before the Court on writ of certiorari to review the decision of the lower court.

II. STATEMENT OF FACTS
[Facts would be inserted here based on case context]

III. LEGAL ISSUE
The question presented is whether the lower court erred in its application of established legal principles.

IV. REASONING
The Court has consistently held that legal precedents must be applied faithfully to the facts of each case. In reviewing the record, we find that the principles established in prior decisions are directly applicable here.

The reasoning of the lower court, while thorough, failed to adequately consider the controlling precedents. We therefore find it necessary to clarify the proper application of these principles.

V. HOLDING
We hold that the lower court's decision must be reconsidered in light of the controlling precedents.

VI. JUDGMENT
The judgment of the lower court is REMANDED for further proceedings consistent with this opinion.

It is so ordered.

---
[AI-Generated Opinion - For Research Purposes Only]"""
    
    def _parse_opinion_sections(self, generated_text: str) -> Dict[str, str]:
        """
        Parse generated opinion into structured sections.
        
        Args:
            generated_text: Full opinion text
        
        Returns:
            Dictionary mapping section names to content
        """
        sections = {}
        
        # Define section patterns
        section_patterns = {
            'procedural_history': r'I\.\s*PROCEDURAL HISTORY\s*(.*?)(?=II\.|$)',
            'facts': r'II\.\s*STATEMENT OF FACTS\s*(.*?)(?=III\.|$)',
            'issue': r'III\.\s*LEGAL ISSUE\s*(.*?)(?=IV\.|$)',
            'reasoning': r'IV\.\s*REASONING\s*(.*?)(?=V\.|$)',
            'holding': r'V\.\s*HOLDING\s*(.*?)(?=VI\.|$)',
            'judgment': r'VI\.\s*JUDGMENT\s*(.*?)(?=It is so ordered|$)'
        }
        
        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, generated_text, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section_name] = match.group(1).strip()
            else:
                sections[section_name] = ""
        
        return sections
    
    def _extract_cited_cases(
        self,
        generated_text: str,
        precedents: List[SearchResult]
    ) -> List[str]:
        """
        Extract case citations from generated opinion.
        
        Args:
            generated_text: Generated opinion text
            precedents: Retrieved precedents
        
        Returns:
            List of cited case names
        """
        cited = []
        
        for precedent in precedents:
            # Check if case name appears in generated text
            if precedent.case_name in generated_text:
                citation = f"{precedent.case_name} ({precedent.year})"
                cited.append(citation)
        
        return cited
    
    def _format_final_opinion(
        self,
        generated_text: str,
        case_context: Dict,
        opinion_type: str
    ) -> str:
        """
        Format final opinion with header and disclaimer.
        
        Args:
            generated_text: Generated opinion text
            case_context: Case information
            opinion_type: Opinion type
        
        Returns:
            Formatted final opinion
        """
        case_name = case_context.get('case_name', 'Petitioner v. Respondent')
        case_number = case_context.get('case_number', 'No. XX-XXXX')
        
        # Add header if not present
        if "SUPREME COURT" not in generated_text:
            header = f"""SUPREME COURT OF THE UNITED STATES

{case_number}

{case_name}

{opinion_type.upper().replace('_', ' ')}

"""
            generated_text = header + generated_text
        
        # Add disclaimer footer
        disclaimer = """

---
DISCLAIMER: This opinion is AI-generated for research and academic purposes only.
It does not constitute legal advice and should not be relied upon for actual legal proceedings.
"""
        
        return generated_text + disclaimer
    
    def format_citations(self, precedents: List[SearchResult]) -> str:
        """
        Format case citations in Bluebook style.
        
        Args:
            precedents: List of precedent cases
        
        Returns:
            Formatted citations string
        """
        citations = []
        
        for precedent in precedents:
            # Basic Bluebook format: Case Name, Year
            citation = f"{precedent.case_name}, {precedent.year}"
            citations.append(citation)
        
        return "; ".join(citations)


# Singleton instance
_opinion_generator_instance = None


def get_opinion_generator(
    search_engine: any = None,
    llm_api_url: str = None,
    llm_api_key: str = None,
    model: str = "gpt-4"
) -> OpinionGenerator:
    """
    Get or create the singleton OpinionGenerator instance.
    
    Args:
        search_engine: SemanticSearchEngine instance (only used on first call)
        llm_api_url: LLM API URL (only used on first call)
        llm_api_key: LLM API key (only used on first call)
        model: LLM model name (only used on first call)
    
    Returns:
        OpinionGenerator instance
    """
    global _opinion_generator_instance
    
    if _opinion_generator_instance is None:
        if search_engine is None:
            raise ValueError("search_engine must be provided on first call")
        
        model = os.getenv("LLM_MODEL", model)
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2048"))
        
        _opinion_generator_instance = OpinionGenerator(
            search_engine=search_engine,
            llm_api_url=llm_api_url,
            llm_api_key=llm_api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    return _opinion_generator_instance
