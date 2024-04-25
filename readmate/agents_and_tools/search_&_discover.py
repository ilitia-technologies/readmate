import operator
from typing import TypedDict, Annotated, Union

from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolInvocation
from langchainhub import hub

from langgraph.prebuilt.tool_executor import ToolExecutor
from langchain.agents import create_react_agent
from langchain_core.runnables import Runnable
from langchain_core.agents import (
    AgentAction,
    AgentFinish,
)
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    # The input string
    input: str
    # The list of previous messages in the conversation
    chat_history: list[BaseMessage]
    # The outcome of a given call to the agent
    # Needs `None` as a valid type, since this is what this will start as
    agent_outcome: Union[AgentAction, AgentFinish, None]

    return_direct: bool

    # List of actions and corresponding observations
    # Here we annotate this with `operator.add` to indicate that operations to
    # this state should be ADDED to the existing values (not overwrite it)
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]


class AgentExecutorBase:
    def __init__(self) -> None:
        self.app: StateGraph
        self.agent_runnable: Runnable
        self.tool_executor: ToolExecutor

    # Define the agent
    def run_agent(self, data, agent_runnable):
        """
        inputs = data.copy()
        if len(inputs["intermediate_steps"]) > 5:
            inputs["intermediate_steps"] = inputs["intermediate_steps"][-5:]
        """
        agent_outcome = agent_runnable.invoke(data)
        return {"agent_outcome": agent_outcome}

    # Define the function to execute tools
    def execute_tools(self, data, tool_executor):
        messages = [data["agent_outcome"]]
        last_message = messages[-1]
        ######### HUMAN input y/n ###########
        # Get the most recent agent_outcome - this is the key added in the `agent` above
        # data_action = data['agent_outcome']
        # human_key = input(f"[y/n] continue with: {data_action}?")
        # if human_key == "n":
        #     raise ValueError

        tool_name = last_message.tool
        arguments = last_message
        if tool_name == "Search" and "return_direct" in arguments:
            del arguments["return_direct"]
        action = ToolInvocation(
            tool=tool_name,
            tool_input=last_message.tool_input,
        )
        response = tool_executor.invoke(action)
        return {"intermediate_steps": [(data["agent_outcome"], response)]}

    # Define logic that will be used to determine which conditional edge to go down
    def should_continue(self, data):
        messages = [data["agent_outcome"]]
        last_message = messages[-1]
        if "Action" not in last_message.log:
            return "end"
        else:
            arguments = data["return_direct"]
            if arguments is True:
                return "final"
            else:
                return "continue"

    def toolkit_setup(self):
        pass

    def llm_setup(self):
        pass

    def workflow_compiler(self, llm_model, toolkit):
        prompt = hub.pull("hwchase17/react")

        self.agent_runnable = create_react_agent(llm_model, toolkit, prompt)
        self.tool_executor = ToolExecutor(toolkit)

        # Define a new graph
        workflow = StateGraph(AgentState)

        # Define the two nodes we will cycle between
        workflow.add_node(
            "agent", lambda data: self.run_agent(data, self.agent_runnable)
        )
        workflow.add_node(
            "action", lambda data: self.execute_tools(data, self.tool_executor)
        )

        # Set the entrypoint as `agent`
        # This means that this node is the first one called
        workflow.set_entry_point("agent")

        # We now add a conditional edge
        workflow.add_conditional_edges(
            # First, we define the start node. We use `agent`.
            # This means these are the edges taken after the `agent` node is called.
            "agent",
            # Next, we pass in the function that will determine which node is called next.
            self.should_continue,
            # Finally we pass in a mapping.
            # The keys are strings, and the values are other nodes.
            # END is a special node marking that the graph should finish.
            # What will happen is we will call `should_continue`, and then the output of that
            # will be matched against the keys in this mapping.
            # Based on which one it matches, that node will then be called.
            {
                # If `tools`, then we call the tool node.
                "continue": "action",
                # Otherwise we finish.
                "end": END,
            },
        )

        # We now add a normal edge from `tools` to `agent`.
        # This means that after `tools` is called, `agent` node is called next.
        workflow.add_edge("action", "agent")

        # Finally, we compile it!
        # This compiles it into a LangChain Runnable,
        # meaning you can use it as you would any other runnable
        self.app = workflow.compile()

    def iter_runnable(self):
        """
        # Load tools
        tool_ag_1 = [tool_pool.generate_module_descriptions_and_ratings]

        # Launc hte
        app_ag1, agent_runnable_ag1, tool_executor_ag1 = self.workflow_compiler(llm_model=llm_35, toolkit=tool_ag_1)

        inputs = {
            "input": input_prompt.INPUT_PROMPT_RECURSIVE_SEARCH_FOLDERS.format(
                result_recursive_folder_search
            ),
            "chat_history": [],
        }
        # response = llm_4.invoke(inputs["input"], max_tokens=1000)

        for s in app_ag1.stream(inputs, {"recursion_limit": 20}):
            print(list(s.values())[0])
            print("----")
        """
