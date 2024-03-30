"""Functional module for ExpeL."""

import random
import re

from typing import Any, Dict, List, Tuple

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages.human import HumanMessage
from langchain_core.prompts.prompt import PromptTemplate

from discussion_agents.cog.agent.reflexion import ReflexionReActAgent
from discussion_agents.cog.prompts.expel import (
    CRITIQUE_SUMMARY_SUFFIX_FULL,
    CRITIQUE_SUMMARY_SUFFIX_NOT_FULL,
    EXISTING_INSIGHTS_AI_NAME,
    HUMAN_CRITIQUE_EXISTING_INSIGHTS_ALL_SUCCESS_TEMPLATE,
    HUMAN_CRITIQUE_EXISTING_INSIGHTS_TEMPLATE,
    NON_EXISTENT_INSIGHTS_AT_NAME,
    SYSTEM_CRITIQUE_ALL_SUCCESS_EXISTING_INSIGHTS_INSTRUCTION,
    SYSTEM_CRITIQUE_EXISTING_INSIGHTS_INSTRUCTION,
    SYSTEM_TEMPLATE,
)
from discussion_agents.cog.prompts.react import HOTPOTQA_FEWSHOT_EXAMPLES
from discussion_agents.cog.prompts.reflexion import (
    REFLEXION_REACT_INSTRUCTION,
    REFLEXION_REACT_REFLECT_FEWSHOT_EXAMPLES,
    REFLEXION_REACT_REFLECT_INSTRUCTION,
)

# ============================================== Experience Gathering ==============================================


def gather_experience(
    reflexion_react_agent: ReflexionReActAgent,
    questions: List[str],
    keys: List[str],
    strategy: str = "reflexion",
    prompt: str = REFLEXION_REACT_INSTRUCTION,
    examples: str = HOTPOTQA_FEWSHOT_EXAMPLES,
    reflect_examples: str = REFLEXION_REACT_REFLECT_FEWSHOT_EXAMPLES,
    reflect_prompt: str = REFLEXION_REACT_REFLECT_INSTRUCTION,
) -> Dict[str, List]:
    """Collects and aggregates experiences from a ReflexionReActAgent by generating trajectories and reflections for a set of questions and keys.

    The function iterates over each question-key pair, generates a trajectory using the specified strategy, and records the reflections generated by the agent. Each trajectory and its corresponding reflections are appended to their respective lists within the 'experiences' dictionary.

    Parameters:
        reflexion_react_agent (ReflexionReActAgent): The agent from which experiences are generated.
        questions (List[str]): A list of questions to be processed by the agent.
        keys (List[str]): A list of keys that are paired with the questions to guide the agent's generation.
        strategy (str, optional): The strategy used to generate experiences. Defaults to "reflexion" if not specified.
        prompt (str, optional): Prompt template string. Defaults to REFLEXION_REACT_INSTRUCTION.
            Must include examples, reflections, question, scratchpad, and max_steps.
        examples (str, optional): Fewshot examples. Defaults to HOTPOTQA_FEWSHOT_EXAMPLES.
        reflect_examples (str, optional): Reflection fewshot examples. Defaults to REFLEXION_REACT_REFLECT_FEWSHOT_EXAMPLES.
        reflect_prompt (str, optional): Reflect prompt template string. Defaults to REFLEXION_REACT_REFLECT_INSTRUCTION.
            Must include examples, question, and scratchpad.

    Returns:
        Dict[str, List]: A dictionary containing lists of indices ('idxs'), questions ('questions'), keys ('keys'), generated trajectories ('trajectories'), and reflections ('reflections').

    Each index in 'idxs' corresponds to the respective question, key, trajectory, and reflections at the same position in their lists.
    """
    experiences: Dict[str, List] = {
        "idxs": [],
        "questions": [],
        "keys": [],
        "trajectories": [],
        "reflections": [],
    }
    for idx, (question, key) in enumerate(zip(questions, keys)):
        trajectory = reflexion_react_agent.generate(
            question=question,
            key=key,
            strategy=strategy,
            reset=True,
            prompt=prompt,
            examples=examples,
            reflect_examples=reflect_examples,
            reflect_prompt=reflect_prompt,
        )

        experiences["idxs"].append(idx)
        experiences["questions"].append(question)
        experiences["keys"].append(key)
        experiences["trajectories"].append(trajectory)
        experiences["reflections"].append(reflexion_react_agent.reflector.reflections)

    return experiences


# ============================================== Insight Extraction ==============================================


def categorize_experiences(experiences: Dict[str, List]) -> Dict[str, List]:
    """Categorizes experiences based on the success of trials in the trajectories.

    This function iterates over each index in the experiences and categorizes them into 'compare', 'success', or 'fail' based on the outcomes of the trials. Each trial is represented by a tuple, with the first element indicating success (True) or failure (False).

    Parameters:
        experiences (Dict[str, List]): A dictionary containing the trajectories to be categorized. The dictionary should have the following structure:
            {
                "idxs": List[int],  # Indices of the tasks
                "trajectories": List[List[Tuple[bool, Any, Any]]]  # Trajectories as a list of tuples
            }

    Returns:
        Dict[str, List]: A dictionary with the indices of tasks categorized into 'compare', 'success', and 'fail'.

    Raises:
    - ValueError: If a trajectory does not fit into any category, indicating an unhandled scenario.
    """
    count_dict: Dict[str, List] = {"compare": [], "success": [], "fail": []}

    for idx in experiences["idxs"]:  # Index for a particular task.
        trajectory = experiences["trajectories"][idx]  # type: ignore
        trials_are_correct = [
            trial[0] for trial in trajectory
        ]  # (is_correct, answer, output)[0].

        # Success.
        if (
            all(trials_are_correct) and len(trials_are_correct) == 1
        ):  # If success @ first trial, then stop generation.
            count_dict["success"].append(idx)
        # Compare.
        elif trials_are_correct[
            -1
        ]:  # If fail(s), then succeeds, then only last trial is True.
            count_dict["compare"].append(idx)
        # Fail.
        elif not all(trials_are_correct):  # All trials failed, then fail case.
            count_dict["fail"].append(idx)
        else:
            raise ValueError(f"Unhandled scenario for trajectory at index {idx}.")

    return count_dict


def get_folds(
    categories: Dict[str, List], n_instances: int, n_folds: int = 2, seed: int = 42
) -> Dict[int, List]:
    """Distributes indices into a specified number of stratified folds for cross-validation.

    Indices from each category ('compare', 'success', 'fail') are shuffled and then distributed across the folds. Each fold will serve as a validation set once during cross-validation, with the remaining data used for training.

    Parameters:
        categories (Dict[str, List]): A dictionary containing lists of indices for each category.
        n_instances (int): The total number of instances across all categories.
        n_folds (int, optional): The number of folds to create for cross-validation. Default is 2.

    Returns:
        Dict[int, List]: A dictionary where keys are fold indices and values are the lists of indices representing the training set for that fold.
    """
    random.seed(seed)

    folds: Dict[int, List] = {fold: [] for fold in range(n_folds)}

    # Assign labels for 'compare', 'success', and  'fail'.
    for _, indices in categories.items():
        indices = random.sample(indices, len(indices))
        for count, idx in enumerate(indices):
            folds[count % n_folds].append(idx)

    # Each fold is a validation set. Take the difference to get the training set of each fold.
    folds = {
        fold: list(set(list(range(n_instances))).difference(values))
        for fold, values in folds.items()
    }

    return folds


def _build_compare_prompt(
    insights: List[Dict[str, Any]],
    question: str,
    success_trial: str,
    failed_trial: str,
    is_full: bool,
) -> str:
    """Constructs a comparison prompt for an AI by combining system instructions, task details, and a list of existing insights.

    This function formats a prompt intended for AI to critique existing insights based on a given task. The task is described by a question and includes examples of both successful and failed trials.

    Parameters:
        insights (List[Tuple[str, int]]): A list of strings where each string represents an existing insight with a score. If the list is empty, it is treated as if there are no existing insights.
        question (str): The question that defines the task.
        success_trial (str): A description or example of a successful trial for the task.
        failed_trial (str): A description or example of a failed trial for the task.
        is_full (bool): A flag indicating whether the prompt should be in its full form or not. This affects the suffix of the critique summary.

    Returns:
        str: A fully constructed prompt ready to be presented to the AI. The prompt includes a prefixed system instruction, task details formatted according to human critique template,
            and a suffix based on whether the prompt is in its full form.
    """
    # System prompt.
    prefix = PromptTemplate.from_template(SYSTEM_TEMPLATE).format(
        ai_name=NON_EXISTENT_INSIGHTS_AT_NAME
        if not insights
        else EXISTING_INSIGHTS_AI_NAME,
        instruction=SYSTEM_CRITIQUE_EXISTING_INSIGHTS_INSTRUCTION,
    )

    # Task prompt.
    human_format_dict = {
        "question": question,
        "failed_traj": failed_trial,
        "success_traj": success_trial,
        "existing_insights": "\n".join(
            [f"{i}. {insight['insight']}" for i, insight in enumerate(insights)]
        )
        if insights
        else "",
    }

    human_critique_summary_message = PromptTemplate.from_template(
        HUMAN_CRITIQUE_EXISTING_INSIGHTS_TEMPLATE
    ).format(**human_format_dict)
    critique_summary_suffix = (
        CRITIQUE_SUMMARY_SUFFIX_FULL if is_full else CRITIQUE_SUMMARY_SUFFIX_NOT_FULL
    )

    prompt = prefix + "\n" + human_critique_summary_message + critique_summary_suffix

    return prompt


def _build_all_success_prompt(
    insights: List[Dict[str, Any]],
    success_trajs_str: str,
    is_full: bool,
) -> str:
    """Constructs a prompt focused on critiquing and enhancing existing insights based on successful task trials.

    This function generates a prompt for AI interaction that incorporates a series of successful trials and existing insights.

    Parameters:
        insights (List[Dict[str, Any]]): A list of strings where each string represents an existing insight with a score. If the list is empty, it is treated as if there are no existing insights.
        success_trajs_str (str): A string containing descriptions of successful trials related to the task. These descriptions are meant to provide context for the AI's critique of the existing insights.
        is_full (bool): A boolean flag that determines the verbosity of the critique summary's suffix. If `True`, a more comprehensive suffix is used.

    Returns:
        str: A string that combines the system's instruction, the task context with successful trials, and the existing insights into a coherent prompt.
    """
    # System prompt.
    prefix = PromptTemplate.from_template(SYSTEM_TEMPLATE).format(
        ai_name=NON_EXISTENT_INSIGHTS_AT_NAME
        if not insights
        else EXISTING_INSIGHTS_AI_NAME,
        instruction=SYSTEM_CRITIQUE_ALL_SUCCESS_EXISTING_INSIGHTS_INSTRUCTION,
    )

    # Task prompt.
    human_format_dict = {
        "success_trajs": success_trajs_str,
        "existing_insights": "\n".join(
            [f"{i}. {insight['insight']}" for i, insight in enumerate(insights)]
        )
        if insights
        else "",
    }

    human_critique_summary_message = PromptTemplate.from_template(
        HUMAN_CRITIQUE_EXISTING_INSIGHTS_ALL_SUCCESS_TEMPLATE
    ).format(**human_format_dict)
    critique_summary_suffix = (
        CRITIQUE_SUMMARY_SUFFIX_FULL if is_full else CRITIQUE_SUMMARY_SUFFIX_NOT_FULL
    )

    prompt = prefix + "\n" + human_critique_summary_message + critique_summary_suffix

    return prompt


def _prompt_compare_critique(
    llm: BaseChatModel,
    insights: List[Dict[str, Any]],
    question: str,
    success_trial: str,
    failed_trial: str,
    is_full: bool,
    replace_newline: bool = False,
) -> str:
    """Generates a critique from an LLM based on a comparison between successful and failed task trials, within the context of existing insights.

    This function constructs a prompt that juxtaposes successful and failed trials of a task with a set of existing insights. It then requests a critique from the Large Language Model (LLM) based on this information. The critique aims to evaluate the insights' effectiveness and suggest modifications if necessary. An option is provided to format the LLM's output by removing newline characters.

    Parameters:
        llm (BaseChatModel): The Large Language Model instance used to generate the critique.
        insights (List[Dict[str, Any]]): A list of strings where each string represents an existing insight with a score. If the list is empty, it is treated as if there are no existing insights.
        question (str): The task question related to the trials.
        success_trial (str): A description of a successful trial for the task.
        failed_trial (str): A description of a failed trial for the task.
        is_full (bool): A flag indicating if the full version of the critique summary should be used.
        replace_newline (bool, optional): If `True`, newline characters in the LLM's output will be replaced with empty strings, defaulting to `False`.

    Returns:
        str: The critique generated by the LLM, potentially with newline characters removed, based on the `replace_newline` parameter.
    """
    prompt = _build_compare_prompt(
        insights=insights,
        question=question,
        success_trial=success_trial,
        failed_trial=failed_trial,
        is_full=is_full,
    )
    out = llm(
        [
            HumanMessage(
                content=prompt,
            )
        ]
    ).content
    out = out.strip("\n").strip()  # type: ignore

    if replace_newline:
        out = out.replace("\n", "")
    return out


def _prompt_all_success_critique(
    llm: BaseChatModel,
    insights: List[Dict[str, Any]],
    success_trajs_str: str,
    is_full: bool,
    replace_newline: bool = False,
) -> str:
    """Generates a critique from an LLM based on a compilation of successful task trials in the context of existing insights.

    This function constructs a prompt emphasizing the successes in task trials and existing insights, and requests a critique from the Large Language Model (LLM).

    Parameters:
        llm (BaseChatModel): The Large Language Model instance used for generating the critique.
        insights (List[Dict[str, Any]]): A list of strings where each string represents an existing insight with a score. If the list is empty, it is treated as if there are no existing insights.
        success_trajs_str (str): A string concatenating descriptions of successful trials related to the task.
        is_full (bool): Indicates whether the full critique summary is to be used in the prompt.
        replace_newline (bool, optional): If set to `True`, newline characters in the LLM output will be replaced with empty strings. The default is `False`.

    Returns:
        str: The generated critique from the LLM, optionally with newline characters removed depending on the `replace_newline` parameter.
    """
    prompt = _build_all_success_prompt(
        insights=insights, success_trajs_str=success_trajs_str, is_full=is_full
    )
    out = llm(
        [
            HumanMessage(
                content=prompt,
            )
        ]
    ).content
    out = out.strip("\n").strip()  # type: ignore

    if replace_newline:
        out = out.replace("\n", "")
    return out


def parse_insights(llm_text: str) -> List[Tuple[str, str]]:
    """Parses and extracts insight operations and their descriptions from a given text.

    This function searches through the provided text for occurrences of insight operations (ADD, REMOVE, EDIT, AGREE) followed by their descriptions.
    It applies specific criteria to ensure the extracted insights are valid: the insight description must not be empty, must not
    contain certain banned words (to avoid inclusion of formatting instructions or similar), and must end with a period.

    Parameters:
        llm_text (str): The text from which to extract insight operations and descriptions.
            This text is expected to contain one or more statements formatted according to predefined insight operation patterns.

    Returns:
        List[Tuple[str, str]]: A list of tuples where each tuple contains two elements: the operation (ADD, REMOVE, EDIT, AGREE) and the clean, validated insight description.
            The insights that do not meet the validation criteria are omitted.
    """
    pattern = r"((?:REMOVE|EDIT|ADD|AGREE)(?: \d+|)): (?:[a-zA-Z\s\d]+: |)(.*)"
    matches = re.findall(pattern, llm_text)

    res = []
    banned_words = ["ADD", "AGREE", "EDIT"]
    for operation, text in matches:
        text = text.strip()
        if (
            text != ""
            and not any([w in text for w in banned_words])
            and text.endswith(".")
        ):
            # If text is not empty.
            # If text doesn't contain banned words (avoid weird formatting cases from llm).
            # If text ends with a period (avoid cut off sentences from llm).
            if "ADD" in operation:
                res.append(("ADD", text))
            else:
                res.append((operation.strip(), text))
    return res


def retrieve_insight_index(
    insights: List[Dict[str, Any]], operation_rule_text: str
) -> int:
    """Retrieves the index of a rule based on its text.

    Searches through a list of insights to find the index of the rule that matches part of the given operation rule text. This function is useful for identifying which rule is being referred to in operations like EDIT, REMOVE, or AGREE, where the rule text is included in the operation.

    Parameters:
        insights (List[Dict[str, Any]]): A list of tuples, where each tuple contains the rule text and its associated strength or any other numeric value.
        operation_rule_text (str): The text of the operation which may contain or exactly match the text of a rule.

    Returns:
        int: The index of the rule within the list if found; otherwise, -1.
    """
    for i in range(len(insights)):
        if insights[i]["insight"] in operation_rule_text:
            return i
    return -1


def remove_err_operations(
    insights: List[Dict[str, Any]], operations: List[Tuple[str, str]]
) -> List[Tuple[str, str]]:
    """Cleans a list of rule operations by removing or modifying erroneous entries.

    This function iterates through a list of operations intended to modify a set of insights. It removes operations that are incorrect or not applicable (e.g., attempting to add a rule that already exists) and modifies certain operations based on their context (e.g., changing an EDIT to AGREE if the edited rule matches an existing rule). The goal is to ensure that the resulting list of operations is coherent and can be applied to update the insights without causing inconsistencies.

    Parameters:
        insights (List[Dict[str, Any]]): A list of tuples representing the existing insights. Each tuple contains the rule text and an associated numeric value, which could represent the rule's strength or priority.
        operations (List[Tuple[str, str]]): A list of tuples representing the operations to be performed on the insights. Each tuple contains an operation type (ADD, REMOVE, EDIT, AGREE) and the associated rule text or modification.

    Returns:
        List[Tuple[str, str]]: A cleaned list of operations where erroneous or inapplicable operations have been removed or modified to ensure consistency and correctness when applied to the set of existing insights.
    """
    corrected_operations = []
    for operation, text in operations.copy():
        operation_type = operation.split(" ")[0]
        insight_idx = int(operation.split(" ")[1]) if " " in operation else None
        index = retrieve_insight_index(insights, text)

        # ADDing an insight that doesn't exist.
        if operation_type == "ADD" and retrieve_insight_index(insights, text) == -1:
            corrected_operations.append((operation, text))
        # REMOVEing or AGREEing with an insight given that it exists.
        elif (operation_type == "REMOVE" or operation_type == "AGREE") and index != -1:
            corrected_operations.append((operation, text))
        # EDITing an insight (AGREEing) given that it exists.
        elif operation_type == "EDIT" and index != -1:
            corrected_operations.append((f"AGREE {index}", text))
        # EDITing an insight given:
        # - it doesn't exist (text match) in the insights
        # - the insight index to EDIT is not None
        # - the insight index to EDIT is less than or equal to the length of insights (within range of the length of the insights)
        elif (
            operation_type == "EDIT"
            and insight_idx is not None
            and insight_idx <= len(insights)
        ):
            corrected_operations.append((operation, text))

    return corrected_operations


def get_operations_compare(
    llm: BaseChatModel,
    insights: List[Dict[str, Any]],
    question: str,
    success_trial: str,
    failed_trial: str,
    is_full: bool,
) -> List[Tuple[str, str]]:
    """Generates a list of operations based on a comparison between a successful trial and a failed trial of a question.

    This function generates a critique prompt that includes the question, a successful trial, a failed trial, and existing insights. It then processes the critique from the LLM to identify actionable operations to update the insights.

    Parameters:
        llm (BaseChatModel): The language model used for generating the critique.
        insights (List[Dict[str, Any]]): Current insights with their scores.
        question (str): The question related to the trials.
        success_trial (str): Description of the successful trial.
        failed_trial (str): Description of the failed trial.
        is_full (bool): Flag to indicate if the critique should consider all insights or be limited.

    Returns:
        List[Tuple[str, str]]: A list of tuples representing operations (e.g., "ADD", "EDIT") and their corresponding insights or modifications.
    """
    # Prompt.
    out = _prompt_compare_critique(
        llm,
        insights,
        question,
        success_trial,
        failed_trial,
        is_full,
    )

    # Parse.
    operations = parse_insights(out)

    # Remove no-ops.
    operations = remove_err_operations(insights, operations)

    return operations


def get_operations_success(
    llm: BaseChatModel,
    success_trials: str,
    insights: List[Dict[str, Any]],
    is_full: bool,
) -> List[Tuple[str, str]]:
    """Generates a list of operations based on a set of successful trials.

    This function creates a critique prompt from a string of successful trials and existing insights, requesting the LLM to provide a critique. The critique is analyzed to extract operations for insight modification or addition based on the success patterns identified in the trials.

    Parameters:
        llm (BaseChatModel): The language model used for generating the critique.
        success_trials (str): A concatenated string of descriptions for each successful trial.
        insights (List[Dict[str, Any]]): Current insights with their scores.
        is_full (bool): Flag to indicate if the critique should consider all insights or be limited.

    Returns:
        List[Tuple[str, str]]: A list of tuples representing operations (e.g., "ADD", "EDIT") and their corresponding insights or modifications.
    """
    # Prompt.
    out = _prompt_all_success_critique(llm, insights, success_trials, is_full)

    # Parse.
    operations = parse_insights(out)

    # Remove no-ops.
    operations = remove_err_operations(insights, operations)

    return operations