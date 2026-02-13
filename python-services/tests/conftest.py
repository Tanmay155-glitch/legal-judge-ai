"""Pytest configuration and shared fixtures"""

import pytest
from hypothesis import settings

# Configure Hypothesis for property-based testing
settings.register_profile("ci", max_examples=100)
settings.register_profile("dev", max_examples=10)
settings.register_profile("debug", max_examples=10, verbosity=2)

# Load the appropriate profile
settings.load_profile("dev")


@pytest.fixture
def sample_case_law():
    """Sample case law document for testing"""
    return {
        "case_name": "Doe v. Smith",
        "year": 2023,
        "court": "Supreme Court of the United States",
        "opinion_type": "per_curiam",
        "facts": "Plaintiff entered into a residential lease agreement with defendant. The premises suffered from severe water leaks and mold growth.",
        "issue": "Whether the landlord breached the implied warranty of habitability.",
        "reasoning": "The Court has consistently held that residential leases contain an implied warranty of habitability. The landlord's failure to repair constitutes a breach.",
        "holding": "The landlord breached the implied warranty of habitability.",
        "final_judgment": "Affirmed"
    }


@pytest.fixture
def sample_vector():
    """Sample 768-dimensional vector for testing"""
    import numpy as np
    return np.random.randn(768).tolist()
