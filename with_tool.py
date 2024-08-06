# from dotenv import load_dotenv
import os
from groq import Groq
import requests

# # Load environment variables from .env file
load_dotenv()

class Tool:
    def __init__(self, name, function):
        """
        Initializes a new instance of the Tool class.

        Parameters:
            name (str): The name of the tool.
            function (callable): The function to be executed by the tool.

        Returns:
            None
        """
        self.name = name
        self.function = function

    def execute(self, *args, **kwargs):
        return self.function(*args, **kwargs)

class Agent:
    def __init__(self, client: Groq, system: str = "") -> None:
        self.client = client
        self.system = system
        self.messages: list = []
        self.tools = {}
        if self.system:
            self.messages.append({"role": "system", "content": system})

    def add_tool(self, tool: Tool):
        """
        Adds a tool to the agent's toolset.

        Parameters:
            tool (Tool): The tool to be added.

        Returns:
            None
        """
        self.tools[tool.name] = tool

    def __call__(self, message=""):
        """
        Executes the agent's behavior based on the given message.

        Args:
            message (str, optional): The message to be processed by the agent. Defaults to an empty string.

        Returns:
            Union[str, Any]: If the response starts with "CALL_TOOL", the result of executing the corresponding tool with the given parameters.
                             Otherwise, the response itself.

        Raises:
            KeyError: If the tool specified in the response does not exist in the agent's tools dictionary.
        """
        if message:
            self.messages.append({"role": "user", "content": message})
        response = self.execute()
        if response.startswith("CALL_TOOL"):
            parts = response.split()
            tool_name = parts[1]
            params = parts[2:]
            result = self.tools[tool_name].execute(*params)
            self.messages.append({"role": "tool", "content": result})
            return result
        else:
            self.messages.append({"role": "assistant", "content": response})
            return response

    def execute(self):
        """
        Executes a chat completion using the Gorq API's chat.completions endpoint.

        Returns:
            str: The content of the first choice message from the completion.
        """
        completion = self.client.chat.completions.create(
            model="llama3-70b-8192", messages=self.messages
        )
        return completion.choices[0].message.content

def calculator(a, b, operation):
    a = float(a)
    b = float(b)
    if operation == "add":
        return str(a + b)
    elif operation == "subtract":
        return str(a - b)
    elif operation == "multiply":
        return str(a * b)
    elif operation == "divide":
        return str(a / b)
    else:
        return "Invalid operation"

calc_tool = Tool("calculator", calculator)

def web_search(query):
    """
    Performs a web search using the DuckDuckGo API.

    Args:
        query (str): The search query to be executed.

    Returns:
        list or str: A list of search results if the query is successful, otherwise a failure message.
    """
    response = requests.get(f"https://api.duckduckgo.com/?q={query}&format=json&pretty=1")
    if response.status_code == 200:
        return response.json()["results"]
    else:
        return "Failed to fetch results"

search_tool = Tool("web_search", web_search)

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
client = Groq()
agent = Agent(client, system="You are a helpful assistant.")

# Add tools to the agent
agent.add_tool(calc_tool)
agent.add_tool(search_tool)




response = agent(" CALL_TOOL what is weather today in new york")
print(response)

