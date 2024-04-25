SYSTEM_MESSAGE_FILE_AGENT = """
You are a useful chatbot expert in this technologies {} analyzing files for python projects.
"""

README_SECTIONS = """
[ requirements, deployment_ci_cd, main_modules,
recommended_modules, installation, configuration, license]
"""

FILE_ANALYZER = """

Readme Sections: {readme_section}
According to the the preliminary analysis of the file: {non_module_file} and a portion or full text of the file: {file_info}, Obtain the following information:

'ReadmeSection': "In what section of the readme sections should this file be contained. Put None if the file should not be part of any section"
'Description': "A extended description joining the input dict description and a description of the contents of the file"
'CodeExtractions': "short snippet of the code,configuration,task... of the file. it should be based on the text read"
'Technologies' "update the technologies with the new information you gathered after reading the file"

Take into account that this information will be displayed in a markdown readme file so take into account the writing convention of python readme files
and write it as similar as possible.
"""
