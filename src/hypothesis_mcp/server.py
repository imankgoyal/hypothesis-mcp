import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from urllib.parse import urlparse

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from hypothesis_mcp.client import HypothesisClient
from hypothesis_mcp.context import AppContext
from hypothesis_mcp.tools import annotations, groups, profile, pdf_reader, pdf_discovery

load_dotenv()


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    api_key = os.environ.get("HYPOTHESIS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "HYPOTHESIS_API_KEY environment variable is not set. "
            "Get your key at https://hypothes.is/account/developer"
        )
    base_url = os.environ.get("HYPOTHESIS_BASE_URL", "https://api.hypothes.is/api")
    if urlparse(base_url).scheme != "https":
        raise RuntimeError(
            f"HYPOTHESIS_BASE_URL must use https://. Got: {base_url!r}. "
            "Allowing non-HTTPS would expose your API key in transit."
        )
    async with HypothesisClient(api_key=api_key, base_url=base_url) as client:
        yield AppContext(hypothesis_client=client)


mcp = FastMCP("hypothesis-mcp", lifespan=lifespan)

annotations.register(mcp)
groups.register(mcp)
profile.register(mcp)
pdf_reader.register(mcp)
pdf_discovery.register(mcp)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
