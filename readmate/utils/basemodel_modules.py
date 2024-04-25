from typing import Optional, Union

# from warnings import deprecated
from langchain_core.pydantic_v1 import BaseModel, Field, validator


class DescriptionTemplates(BaseModel):
    technologies: str = (
        "Enumerate any specific programming languages or libraries involved"
    )
    system_message: str = "{system_msg}\n{format_instructions}\n{query}\n"
    validator_message: str = "{} cannot be empty!"


class ModuleAnalysis(BaseModel):
    """Description, technologies and rating."""

    Description: str = Field(
        default="",
        description="Describe the role and content of the file within the project",
    )
    Technologies: list = Field(
        default=[], description=DescriptionTemplates.__fields__["technologies"].default
    )
    Rating: str = Field(
        default="",
        description="Evaluate the module's relevance, and overall contribution to the project.",
    )

    @validator("Description", always=True)
    def validate_description(cls, field):
        if field is None:
            raise ValueError(
                DescriptionTemplates.__fields__["validator_message"].default.format(
                    "Description"
                )
            )
        return field

    @validator("Technologies", always=True)
    def validate_technologies(cls, field):
        if field is None:
            raise ValueError(
                DescriptionTemplates.__fields__["validator_message"].default.format(
                    "Technologies"
                )
            )
        return field

    @validator("Rating", always=True)
    def validate_rating(cls, field):
        if field is None:
            raise ValueError(
                DescriptionTemplates.__fields__["validator_message"].default.format(
                    "Rating"
                )
            )
        return field

    @classmethod
    def default_dict(cls):
        # Create an instance with default values
        instance = cls()
        # Return its dictionary representation
        return instance.dict()


class FileAnalysis(BaseModel):
    """Description, technologies and rating."""

    Description: str = Field(
        default="",
        description="Describe the role and content of the file within the project",
    )
    Technologies: list = Field(
        default=[], description=DescriptionTemplates.__fields__["technologies"].default
    )
    Rating: str = Field(
        default="",
        description="Evaluate the file's relevance, and overall contribution to the project.",
    )

    @validator("Description", always=True)
    def validate_description(cls, field):
        if field is None:
            raise ValueError(
                DescriptionTemplates.__fields__["validator_message"].default.format(
                    "Description"
                )
            )
        return field

    @validator("Technologies", always=True)
    def validate_technologies(cls, field):
        if field is None:
            raise ValueError(
                DescriptionTemplates.__fields__["validator_message"].default.format(
                    "Technologies"
                )
            )
        return field

    @validator("Rating", always=True)
    def validate_rating(cls, field):
        if field is None:
            raise ValueError(
                DescriptionTemplates.__fields__["validator_message"].default.format(
                    "Rating"
                )
            )
        return field

    @classmethod
    def default_dict(cls):
        # Create an instance with default values
        instance = cls()
        # Return its dictionary representation
        return instance.dict()


class FileAnalyzer(BaseModel):
    """File reader for analyzing files at low-level."""

    ReadmeSection: str = Field(
        default="",
        description="The section in which the information should be contained",
    )
    Description: str = Field(
        default="",
        description="Extended description of what the file does or its purpose",
    )
    CodeExtractions: str = Field(
        default="", description="Code extractions retrieved from the file"
    )
    Technologies: list = Field(
        default=[], description=DescriptionTemplates.__fields__["technologies"].default
    )

    Classes: Optional[Union[list, dict, str]] = Field(
        default=None, description="Classes contained in the file, if any"
    )
    Functions: Optional[Union[list, dict, str]] = Field(
        default=None, description="Functions contained in the file, if any"
    )

    @validator("ReadmeSection", always=True)
    def validate_readmesection(cls, field):
        if field is None:
            raise ValueError(
                DescriptionTemplates.__fields__["validator_message"].default.format(
                    "ReadmeSection"
                )
            )
        return field

    @validator("Description", always=True)
    def validate_description(cls, field):
        if field is None:
            raise ValueError(
                DescriptionTemplates.__fields__["validator_message"].default.format(
                    "Description"
                )
            )
        return field

    @validator("CodeExtractions", always=True)
    def validate_example(cls, field):
        if field is None:
            raise ValueError(
                DescriptionTemplates.__fields__["validator_message"].default.format(
                    "Example"
                )
            )
        return field

    @validator("Technologies", always=True)
    def validate_technologies(cls, field):
        if field is None:
            raise ValueError(
                DescriptionTemplates.__fields__["validator_message"].default.format(
                    "Technologies"
                )
            )
        return field

    @classmethod
    def default_dict(cls):
        # Create an instance with default values
        instance = cls()
        # Return its dictionary representation
        return instance.dict()


# DEPRECATED: BaseModel for the folder analysis
# @deprecated()
class FolderAnalysis(BaseModel):
    """List of useful files"""

    list_of_useful_files: list[str] = Field(
        default="", description="Files worth to read"
    )

    @validator("list_of_useful_files")
    def validate_description(cls, field):
        if not field:
            raise ValueError(
                DescriptionTemplates.__fields__["validator_message"].default.format(
                    "list_of_useful_files"
                )
            )
        return field

    @classmethod
    def default_dict(cls):
        # Create an instance with default values
        instance = cls()
        # Return its dictionary representation
        return instance.dict()


class ReadmeOutput(BaseModel):
    """Readme Output filled with information."""

    ReadmeMarkdown: str = Field(
        description="The readme markdown document filled with all the information of the project"
    )

    @validator("ReadmeMarkdown")
    def validate_description(cls, field):
        if not field:
            raise ValueError(
                DescriptionTemplates.__fields__["validator_message"].default.format(
                    "ReadmeMarkdown"
                )
            )
        return field


class BadgesGeneration(BaseModel):
    """Badges for the languages and technologies."""

    Badges: list[str] = Field(default=[], description="List of github badges")

    @validator("Badges")
    def validate_badges(cls, field):
        if field is None:
            raise ValueError(
                DescriptionTemplates.__fields__["validator_message"].default.format(
                    "Badges"
                )
            )
        return field

    @classmethod
    def default_dict(cls):
        # Create an instance with default values
        instance = cls()
        # Return its dictionary representation
        return instance.dict()


class PythonAnalysis(BaseModel):
    """Python Function Analysis."""

    Description: list = Field(
        default=[],
        description="Extended description of what the function does or its purpose",
    )
    CodeExtractions: Union[list, dict] = Field(
        default={}, description="Code extractions retrieved from the functions"
    )

    @validator("Description", always=True)
    def validate_description(cls, field):
        if field is None:
            raise ValueError(
                DescriptionTemplates.__fields__["validator_message"].default.format(
                    "Description"
                )
            )
        return field

    @validator("CodeExtractions", always=True)
    def validate_extractions(cls, field):
        if field is None:
            raise ValueError(
                DescriptionTemplates.__fields__["validator_message"].default.format(
                    "Example"
                )
            )
        return field

    @classmethod
    def default_dict(cls):
        # Create an instance with default values
        instance = cls()
        # Return its dictionary representation
        return instance.dict()


class PythonAnalysisTopLevelCode(BaseModel):
    """Python Function Analysis."""

    Description: str = Field(
        default="",
        description="Extended description of what the function does or its purpose",
    )
    CodeExtractions: Union[list, dict, str] = Field(
        default={}, description="Code extractions retrieved from the functions"
    )

    @validator("Description", always=True)
    def validate_description(cls, field):
        if field is None:
            raise ValueError(
                DescriptionTemplates.__fields__["validator_message"].default.format(
                    "Description"
                )
            )
        return field

    @validator("CodeExtractions", always=True)
    def validate_extractions(cls, field):
        if field is None:
            raise ValueError(
                DescriptionTemplates.__fields__["validator_message"].default.format(
                    "Example"
                )
            )
        return field

    @classmethod
    def default_dict(cls):
        # Create an instance with default values
        instance = cls()
        # Return its dictionary representation
        return instance.dict()
