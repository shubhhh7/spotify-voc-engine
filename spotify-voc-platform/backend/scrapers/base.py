"""
Base scraper interface. All scraper adapters implement this.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class ScraperResult:
    """Standard result returned by every scraper."""
    status: str = "completed"           # completed | failed
    reviews: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    runtime_seconds: float = 0.0


# Type alias for the progress callback
# progress_callback(current_step, total_steps, message)
ProgressCallback = Optional[Callable[[int, int, str], None]]


class BaseScraper(ABC):
    """Interface that all scraper adapters must implement."""
    name: str = "Unknown"
    source: str = "unknown"

    @abstractmethod
    def run(self, progress_callback: ProgressCallback = None) -> ScraperResult:
        """
        Execute the scraper.
        
        Args:
            progress_callback: Optional function called with (current, total, message)
                               to report progress to the frontend.
        
        Returns:
            ScraperResult with reviews collected and any errors.
        """
        pass

    @abstractmethod
    def validate_config(self) -> tuple[bool, str]:
        """
        Check if the scraper can run (dependencies, keys, etc.).
        
        Returns:
            (is_valid, message) tuple.
        """
        pass
