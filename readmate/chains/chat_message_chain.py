from readmate.utils.token_callback_tracker import TokenUsageTracker

from tenacity import retry, stop_after_attempt, wait_fixed
from typing import Optional, List

import openai
from langchain.prompts.chat import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI

from langchain.output_parsers import PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel

from langchain_community.callbacks import get_openai_callback


from readmate.utils.logger import set_logger

from readmate.utils.utils_tools import (
    log_retry,
)

import tiktoken
import json

_logger = set_logger()


class ChatMessageChain:
    def __init__(
        self,
        input_variables: List[str],
        human_prompt: str,
        system_prompt: str,
        llm_selection: AzureChatOpenAI,
        msg_values: List[str],
        base_model=None,
    ) -> None:
        self.base_model: Optional[BaseModel] = base_model
        self.HUMAN_PROMPT: str = human_prompt
        self.SYSTEM_PROMPT: str = system_prompt
        self.input_variables: list = input_variables
        self.llm_selection: AzureChatOpenAI = llm_selection
        self.msg_values: list = msg_values
        self.chain = None

        self.max_input_tokens = 10000

        self.token_tracker_inst = TokenUsageTracker()

        self.warning_tenacity = (
            "(Tenacity) Error after # 3 attemps during chain invoke operation: {}"
        )

    def setup_parser(self):
        """
        Initializes a parser for the base model's output using a Pydantic schema.
        Creates an instance of PydanticOutputParser with the base model provided to the class.
        """
        self.parser = PydanticOutputParser(pydantic_object=self.base_model)

    def define_human_prompt(self):
        """
        Constructs a human-readable message prompt based on input variables and a template.

        Returns:
            HumanMessagePromptTemplate: An object configured with the generated prompt.
        """
        human_prompt_msg: PromptTemplate = PromptTemplate(
            input_variables=self.input_variables,
            template=self.HUMAN_PROMPT,
        )
        human_message_prompt = HumanMessagePromptTemplate(prompt=human_prompt_msg)

        return human_message_prompt

    # Function to remove text between specific substrings including those substrings
    @staticmethod
    def remove_text_between(s, start, end):
        """
        Remove text between two substrings including the substrings themselves.

        :param s: The original string
        :param start: The start substring
        :param end: The end substring
        :return: The string with the specified section removed
        """
        while start in s and end in s:
            pre, _, post = s.partition(start)
            post = post.partition(end)[2]
            s = pre + post
        return s

    def define_ai_prompt(self):
        """
        Creates a system prompt using predefined template and system prompt text.

        Optionally includes formatting instructions from the parser if a base model is set.

        Returns:
            SystemMessagePromptTemplate: An object configured with the constructed prompt.
        """
        partial_variables = {
            "SYSTEM_PROMPT": self.SYSTEM_PROMPT,
        }

        if self.base_model is not None:
            partial_variables["format_instructions"] = (
                self.parser.get_format_instructions()
            )
        else:
            partial_variables["format_instructions"] = ""

        sys_prompt: PromptTemplate = PromptTemplate(
            template="{SYSTEM_PROMPT}.\n{format_instructions}",
            input_variables=[],
            partial_variables=partial_variables,
        )
        system_message_prompt = SystemMessagePromptTemplate(prompt=sys_prompt)

        # _logger.info(f"System prompt: {system_message_prompt}")
        return system_message_prompt

    def setup_chain(self):
        """
        Sets up the message chain for processing.

        Initializes the parser if a base model is provided, combines AI and human prompts into a chat prompt template,
        and constructs the processing chain with or without the parser based on its availability.
        """
        if self.base_model:
            self.setup_parser()
        chat_prompt = ChatPromptTemplate.from_messages(
            [self.define_ai_prompt(), self.define_human_prompt()]
        )

        if hasattr(self, "parser"):
            self.chain = chat_prompt | self.llm_selection | self.parser
        else:
            self.chain = chat_prompt | self.llm_selection

    async def run_chain_json_retry(self):
        """
        Attempts to run the current message chain and handles exceptions by retrying up to three times.
        On failure, returns a default response based on the base model, or an empty string if no base model is provided.

        Returns:
            str or dict: Default response from the base model or an empty string if an error persists.
        """
        try:
            response = await self.run_current_chain()
        except Exception as e:
            _logger.warning(self.warning_tenacity.format(e.last_attempt._exception))
            # TODO: Fix the dict before the error : JSON FIXER
            if self.base_model:
                response = self.base_model.default_dict()
            else:
                response = ""
        return response

    def run_chain_json_retry_non_async(self):
        """
        Synchronously attempts to run the current message chain, handling exceptions by retrying up to three times.

        Returns a default dictionary response from the base model in case of exceptions.

        Returns:
            dict: Default response from the base model.
        """
        try:
            response = self.run_current_chain_non_async()
        except Exception as e:
            _logger.warning(self.warning_tenacity.format(e.last_attempt._exception))
            response = self.base_model.default_dict()

        return response

    @retry(
        stop=stop_after_attempt(3),  # Maximum of 3 retry attempts
        wait=wait_fixed(2),  # Wait 2 seconds between retries
        after=log_retry,
    )
    async def run_current_chain(self, truncation: bool = False):
        """
        Executes the message chain operation asynchronously, handling token and cost tracking.
        Optionally applies truncation to the message text if the truncation flag is set and necessary due to token limits.

        Args:
            truncation (bool, optional): Specifies whether to truncate the message text to manage token limits. Defaults to False.

        Raises:
            RuntimeError: Thrown if truncation is set but fails to reduce the message size sufficiently to avoid token limits.

        Returns:
            dict: Returns the response from the message chain as a dictionary, possibly modified to meet API constraints.
        """
        try:
            msg_text = dict(zip(self.input_variables, self.msg_values))

            # msg_text max tokens should be 10k
            encoding = tiktoken.get_encoding(encoding_name="cl100k_base")
            json_str = json.dumps(msg_text)
            num_tokens = len(encoding.encode(json_str))

            if num_tokens > self.max_input_tokens:
                truncation = True

            if truncation:
                msg_text = self.truncate_strings_in_dict(data=msg_text)
            with get_openai_callback() as cb:
                response = await self.chain.ainvoke(msg_text)
                self.token_tracker_inst.log_cost(cost=cb.total_cost)
                self.token_tracker_inst.log_token_usage(tokens_used=cb.total_tokens)

            if self.base_model:
                response = response.dict()

        except openai._exceptions.BadRequestError:
            if truncation:
                raise RuntimeError(
                    "Truncation did not work as expected. This module surpasses the max token of the model. Continuing without analyzing it..."
                )
            # Log and reduce tokens if BadRequestError due to token limit
            _logger.warning(
                "openai._exceptions.BadRequestError encountered. Reducing tokens and retrying..."
            )

            response = await self.run_current_chain(truncation=True)

        return response

    @retry(
        stop=stop_after_attempt(3),  # Maximum of 3 retry attempts
        wait=wait_fixed(2),  # Wait 2 seconds between retries
        after=log_retry,
    )
    def run_current_chain_non_async(self):
        """
        Executes the message chain synchronously, invoking an API call and handling token and cost tracking.

        This method combines the input variables and their values into a message text, sends it through the
        established chain, and logs the costs and token usage.

        Returns:
            dict: Returns the response from the chain processed into a dictionary format.
        """
        msg_text = dict(zip(self.input_variables, self.msg_values))
        with get_openai_callback() as cb:
            response = self.chain.invoke(msg_text)
            self.token_tracker_inst.log_cost(cost=cb.total_cost)
            self.token_tracker_inst.log_token_usage(tokens_used=cb.total_tokens)
        response = response.dict()

        return response

    @staticmethod
    def truncate_strings_in_dict(data, max_tokens=10000, encoding_name="cl100k_base"):
        """
        Recursively truncates all strings in a dictionary to ensure that the total token count does not exceed
        a specified limit. This helps in managing payloads in environments with strict token limits.

        Args:
            data (dict): The original dictionary containing strings that may need truncation.
            max_tokens (int, optional): The maximum number of tokens allowed. Defaults to 8000.
            encoding_name (str, optional): The encoding model used to measure token length. Defaults to "cl100k_base".

        Returns:
            dict: A new dictionary with the strings truncated to fit within the specified token limit.
        """

        encoding = tiktoken.get_encoding(encoding_name=encoding_name)
        json_str = json.dumps(data)
        num_tokens = len(encoding.encode(json_str))

        reduction_factor = max_tokens / num_tokens

        def truncate_string(s):
            tokens = encoding.encode(s)
            truncated_tokens = tokens[: int(len(tokens) * reduction_factor)]
            return encoding.decode(truncated_tokens)

        def recurse(item):
            if isinstance(item, dict):
                return {k: recurse(v) for k, v in item.items()}
            elif isinstance(item, list):
                return [recurse(element) for element in item]
            elif isinstance(item, str):
                return truncate_string(item)
            else:
                return item

        return recurse(data)
