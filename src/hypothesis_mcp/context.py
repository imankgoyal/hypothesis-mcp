from dataclasses import dataclass
from hypothesis_mcp.client import HypothesisClient


@dataclass
class AppContext:
    hypothesis_client: HypothesisClient
