## HUMAN README for READMATE
This readme contains the rest of the relevant information that the  AI-Generated README does not contain:


## Getting Started

Instructions to set up the project locally. This includes installing dependencies and setting up any necessary configurations.

### Environmental Variables

The project uses several environmental variables to configure its behavior. These should be set in your `.env` file, which you must create in the project root. Below is a description of each variable:

- **LANGCHAIN_PROJECT**: Name of the project to keep track of the lifecycle of the LLM. https://www.langchain.com/langsmith.

- **LANGCHAIN_TRACING_V2**: Set to `"true"` to enable version 2 tracing within LangChain.
- **LANGCHAIN_API_KEY**: Your API key for LangChain services.

- **SERVICE_ENTRYPOINT**: Specifies the service entry point, default is "AzureChatOpenAI".
- **MODEL**: The model used for processing, such as "gpt-35-turbo-16k".

- **OPENAI_API_KEY**: Your API key for accessing OpenAI services.
- **OPENAI_API_VERSION**: The API version of OpenAI to use (leave empty if unsure).
- **OPENAI_MODEL_TEMPERATURE**: Controls the randomness of the model's responses (leave empty for default behavior).

- **AZURE_ENDPOINT**: The endpoint URL for Azure services (specify if using Azure as a backend).

Ensure you replace placeholder values with actual data relevant to your setup.


#### Using LangSmith with LangChain
To enhance monitoring and debugging capabilities when using LangChain services, you can utilize LangSmith along with specific environment variables:

- **LANGCHAIN_TRACING_V2**: Set this to "true" in your .env file to enable advanced tracing features, which are essential for keeping track of API calls, LLM models, and parsers used during execution.
- **LANGCHAIN_API_KEY**: Ensure this variable is set with your LangChain API key to authenticate and log all interactions with LangChain services.

This setup is particularly useful for developers who need to closely monitor their interactions and performance with various language models and parsers, enhancing the ability to debug and optimize their application.

### CLI 

`cli.py` acts as the command-line interface for the application, enabling efficient interaction directly from the terminal. Here’s how to utilize it effectively:

Commands

- **Output Directory**: Specify the directory where the experiments, logs, JSON files, and generated README are stored.
    ```bash
    --output-dir -o TEXT
    ```
- **Input Directory**: Define the folder or zip file to analyze. This directory can also function as the input for when JSONs are already obtained, and only README generation is needed.
    ```bash
    --input-dir -id TEXT
    ```
- **Readme Only Generation**: Activate this boolean flag to generate a README when JSON files are already present in the input directory.
    ```bash
    --readme-only -ro BOOL     
    ```

![Project Screenshot_1](assets\https://github.com/ilitia-technologies/readmate/blob/4c9552a380b41885c4e30eff966c1860d1a5563b/assets/cli.png)


### Workflow 

This project consists of two main workflows, each facilitated by `cli.py`. Below are visuals to help you understand the processes involved in obtaining JSONs and generating the README.

#### Obtaining JSONs

The first part of the workflow involves using the CLI to obtain JSON files, which are necessary for processing and data handling within the application.

![Project Screenshot_2](https://github.com/ilitia-technologies/readmate/blob/4c9552a380b41885c4e30eff966c1860d1a5563b/assets/top_level.drawio.png)

#### Generating README

Once the JSON files are prepared, the second workflow focuses on generating the README file. This is done using the previously obtained JSONs, automating the documentation process based on the data processed.

![Project Screenshot_3](https://github.com/ilitia-technologies/readmate/blob/4c9552a380b41885c4e30eff966c1860d1a5563b/assets/readme.drawio.png)


### Tests

**WIP**