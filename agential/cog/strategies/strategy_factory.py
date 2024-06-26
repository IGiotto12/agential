"""Strategy factory classes."""

from typing import Any, Dict

from agential.cog.strategies.critic.base import CriticBaseStrategy
from agential.cog.strategies.critic.code import (
    CritHEvalCodeStrategy,
    CritMBPPCodeStrategy,
)
from agential.cog.strategies.critic.math import (
    CritGSM8KStrategy,
    CritSVAMPStrategy,
    CritTabMWPStrategy,
)
from agential.cog.strategies.critic.qa import (
    CritAmbigNQStrategy,
    CritFEVERStrategy,
    CritHotQAStrategy,
    CritTriviaQAStrategy,
)
from agential.cog.strategies.react.base import ReActBaseStrategy
from agential.cog.strategies.react.code import ReActHEvalStrategy, ReActMBPPStrategy
from agential.cog.strategies.react.qa import (
    ReActAmbigNQStrategy,
    ReActFEVERStrategy,
    ReActHotQAStrategy,
    ReActTriviaQAStrategy,
)
from agential.cog.strategies.self_refine.base import SelfRefineBaseStrategy
from agential.cog.strategies.self_refine.math import SelfRefineGSM8KStrategy


class CriticStrategyFactory:
    """A factory class for creating instances of different CRITIC strategies based on the specified mode and benchmark.

    Methods:
        get_strategy(mode: Dict[str, str], **strategy_kwargs) -> CriticBaseStrategy:
            Returns an instance of the appropriate Critic strategy based on the provided mode and benchmark.
    """

    @staticmethod
    def get_strategy(
        mode: Dict[str, str], **strategy_kwargs: Any
    ) -> CriticBaseStrategy:
        """Returns an instance of the appropriate Critic strategy based on the provided mode and benchmark.

        Available modes:
            - qa: "hotpotqa", "triviaqa", "ambignq", "fever"
            - math: "gsm8k", "svamp", "tabmwp"
            - code: "mbpp", "humaneval"

        Args:
            mode (Dict[str, str]): A dictionary specifying the mode and benchmark.
                Example: {"qa": "hotpotqa"}, {"math": "gsm8k"}, {"code": "mbpp"}.
            **strategy_kwargs (Dict[str, Any]): Additional keyword arguments to pass to the strategy's constructor.

        Returns:
            CriticBaseStrategy: An instance of the appropriate Critic strategy.

        Raises:
            ValueError: If the mode or benchmark is unsupported.
        """
        if "qa" in mode:
            if mode["qa"] == "hotpotqa":
                return CritHotQAStrategy(**strategy_kwargs)
            elif mode["qa"] == "triviaqa":
                return CritTriviaQAStrategy(**strategy_kwargs)
            elif mode["qa"] == "ambignq":
                return CritAmbigNQStrategy(**strategy_kwargs)
            elif mode["qa"] == "fever":
                return CritFEVERStrategy(**strategy_kwargs)
            else:
                raise ValueError(f"Unsupported QA benchmark: {mode['qa']}")
        elif "math" in mode:
            if mode["math"] == "gsm8k":
                return CritGSM8KStrategy(**strategy_kwargs)
            elif mode["math"] == "svamp":
                return CritSVAMPStrategy(**strategy_kwargs)
            elif mode["math"] == "tabmwp":
                return CritTabMWPStrategy(**strategy_kwargs)
            else:
                raise ValueError(f"Unsupported Math benchmark: {mode['math']}")
        elif "code" in mode:
            if mode["code"] == "mbpp":
                return CritMBPPCodeStrategy(**strategy_kwargs)
            elif mode["code"] == "humaneval":
                return CritHEvalCodeStrategy(**strategy_kwargs)
            else:
                raise ValueError(f"Unsupported Code benchmark: {mode['code']}")
        else:
            raise ValueError(f"Unsupported mode: {mode}")


class SelfRefineStrategyFactory:
    """A factory class for creating instances of different Self-Refine strategies based on the specified mode and benchmark.

    Methods:
        get_strategy(mode: Dict[str, str], **strategy_kwargs) -> SelfRefineBaseStrategy:
            Returns an instance of the appropriate Self-Refine strategy based on the provided mode and benchmark.
    """

    @staticmethod
    def get_strategy(
        mode: Dict[str, str], **strategy_kwargs: Any
    ) -> SelfRefineBaseStrategy:
        """Returns an instance of the appropriate Self-Refine strategy based on the provided mode and benchmark.

        Available modes:
            - qa: "hotpotqa", "triviaqa", "ambignq", "fever"
            - math: "gsm8k", "svamp", "tabmwp"
            - code: "mbpp", "humaneval"

        Args:
            mode (Dict[str, str]): A dictionary specifying the mode and benchmark.
                Example: {"qa": "hotpotqa"}, {"math": "gsm8k"}, {"code": "mbpp"}.
            **strategy_kwargs (Dict[str, Any]): Additional keyword arguments to pass to the strategy's constructor.

        Returns:
            SelfRefineBaseStrategy: An instance of the appropriate Self-Refine strategy.

        Raises:
            ValueError: If the mode or benchmark is unsupported.
        """
        if "qa" in mode:
            if mode["qa"] == "hotpotqa":
                pass
            elif mode["qa"] == "triviaqa":
                pass
            elif mode["qa"] == "ambignq":
                pass
            elif mode["qa"] == "fever":
                pass
            else:
                raise ValueError(f"Unsupported QA benchmark: {mode['qa']}")
        elif "math" in mode:
            if mode["math"] == "gsm8k":
                return SelfRefineGSM8KStrategy(**strategy_kwargs)
            elif mode["math"] == "svamp":
                pass
            elif mode["math"] == "tabmwp":
                pass
            else:
                raise ValueError(f"Unsupported Math benchmark: {mode['math']}")
        elif "code" in mode:
            if mode["code"] == "mbpp":
                pass
            elif mode["code"] == "humaneval":
                pass
            else:
                raise ValueError(f"Unsupported Code benchmark: {mode['code']}")
        else:
            raise ValueError(f"Unsupported mode: {mode}")

        return  # type: ignore


class ReActStrategyFactory:
    """A factory class for creating instances of different ReAct strategies based on the specified mode and benchmark.

    Methods:
        get_strategy(mode: Dict[str, str], **strategy_kwargs) -> ReActBaseStrategy:
            Returns an instance of the appropriate ReAct strategy based on the provided mode and benchmark.
    """

    @staticmethod
    def get_strategy(mode: Dict[str, str], **strategy_kwargs: Any) -> ReActBaseStrategy:
        """Returns an instance of the appropriate ReAct strategy based on the provided mode and benchmark.

        Available modes:
            - qa: "hotpotqa", "triviaqa", "ambignq", "fever"
            - math: "gsm8k", "svamp", "tabmwp"
            - code: "mbpp", "humaneval"

        Args:
            mode (Dict[str, str]): A dictionary specifying the mode and benchmark.
                Example: {"qa": "hotpotqa"}, {"math": "gsm8k"}, {"code": "mbpp"}.
            **strategy_kwargs (Dict[str, Any]): Additional keyword arguments to pass to the strategy's constructor.

        Returns:
            ReActBaseStrategy: An instance of the appropriate ReAct strategy.

        Raises:
            ValueError: If the mode or benchmark is unsupported.
        """
        if "qa" in mode:
            if mode["qa"] == "hotpotqa":
                return ReActHotQAStrategy(**strategy_kwargs)
            elif mode["qa"] == "triviaqa":
                return ReActTriviaQAStrategy(**strategy_kwargs)
            elif mode["qa"] == "ambignq":
                return ReActAmbigNQStrategy(**strategy_kwargs)
            elif mode["qa"] == "fever":
                return ReActFEVERStrategy(**strategy_kwargs)
            else:
                raise ValueError(f"Unsupported QA benchmark: {mode['qa']}")
        elif "math" in mode:
            if mode["math"] == "gsm8k":
                pass
            elif mode["math"] == "svamp":
                pass
            elif mode["math"] == "tabmwp":
                pass
            else:
                raise ValueError(f"Unsupported Math benchmark: {mode['math']}")
        elif "code" in mode:
            if mode["code"] == "mbpp":
                return ReActMBPPStrategy(**strategy_kwargs)
            elif mode["code"] == "humaneval":
                return ReActHEvalStrategy(**strategy_kwargs)
            else:
                raise ValueError(f"Unsupported Code benchmark: {mode['code']}")
        else:
            raise ValueError(f"Unsupported mode: {mode}")

        return  # type: ignore
