import unittest
from unittest.mock import patch
from readmate.modules.project_inspector import ProjectInspector


class TestProjectInspector(unittest.TestCase):
    @patch("readmate.modules.project_inspector.os.walk")
    def test_detect_requirements_files(self, mock_walk):
        # Arrange
        mock_walk.return_value = [
            ("/path/to/project", ("dir1",), ("requirements.txt", "other_file.py")),
            ("/path/to/project/dir1", (), ("Pipfile",)),
        ]
        inspector = ProjectInspector("/path/to/project")

        # Act
        requirements = inspector.detect_requirements_files()

        # Assert
        expected_requirements = {
            "requirements": ["/path/to/project/requirements.txt"],
            "pipenv": ["/path/to/project/dir1/Pipfile"],
        }
        self.assertEqual(requirements, expected_requirements)


if __name__ == "__main__":
    unittest.main()
