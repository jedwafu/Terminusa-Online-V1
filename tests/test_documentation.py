import unittest
import sys
import os
import ast
import re
import inspect
import docstring_parser
import pylint.lint
import black
import isort
from typing import get_type_hints
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestDocumentation(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.project_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.python_files = list(self.project_root.rglob('*.py'))
        
        # Exclude test files and virtual environment
        self.python_files = [
            f for f in self.python_files
            if not str(f).startswith(str(self.project_root / 'tests'))
            and not str(f).startswith(str(self.project_root / 'venv'))
        ]

    def test_docstring_coverage(self):
        """Test docstring coverage and quality"""
        for file_path in self.python_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                module = ast.parse(f.read())
            
            # Check module docstring
            self.assertIsNotNone(
                ast.get_docstring(module),
                f"Module {file_path} missing docstring"
            )
            
            for node in ast.walk(module):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    docstring = ast.get_docstring(node)
                    self.assertIsNotNone(
                        docstring,
                        f"{node.name} in {file_path} missing docstring"
                    )
                    
                    # Parse docstring
                    parsed = docstring_parser.parse(docstring)
                    
                    # Check docstring quality
                    if isinstance(node, ast.FunctionDef):
                        # Functions should document parameters and return value
                        params = {p.name for p in parsed.params}
                        func_params = {
                            p.arg for p in node.args.args
                            if p.arg != 'self'
                        }
                        self.assertEqual(
                            params,
                            func_params,
                            f"Mismatch in documented parameters for {node.name}"
                        )
                        
                        if node.returns:
                            self.assertIsNotNone(
                                parsed.returns,
                                f"{node.name} missing return documentation"
                            )

    def test_type_hints(self):
        """Test type hint coverage"""
        for file_path in self.python_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                module = ast.parse(f.read())
            
            for node in ast.walk(module):
                if isinstance(node, ast.FunctionDef):
                    # Check parameter type hints
                    for arg in node.args.args:
                        if arg.arg != 'self':
                            self.assertIsNotNone(
                                arg.annotation,
                                f"Parameter {arg.arg} in {node.name} missing type hint"
                            )
                    
                    # Check return type hint
                    if not isinstance(node.returns, ast.Constant):
                        self.assertIsNotNone(
                            node.returns,
                            f"Function {node.name} missing return type hint"
                        )

    def test_code_style(self):
        """Test code style compliance"""
        # Run black
        for file_path in self.python_files:
            try:
                black.format_file_in_place(
                    file_path,
                    fast=False,
                    mode=black.FileMode()
                )
            except black.report.Changed:
                self.fail(f"{file_path} does not match black formatting")
        
        # Run isort
        for file_path in self.python_files:
            isort.file(file_path)
        
        # Run pylint
        pylint_output = pylint.lint.Run(
            [str(f) for f in self.python_files],
            do_exit=False
        )
        
        self.assertGreaterEqual(
            pylint_output.linter.stats.global_note,
            9.0,  # Minimum score requirement
            "Code quality score below threshold"
        )

    def test_readme_quality(self):
        """Test README.md quality and completeness"""
        readme_path = self.project_root / 'README.md'
        self.assertTrue(readme_path.exists(), "README.md not found")
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check required sections
        required_sections = [
            '# Terminusa Online',
            '## Features',
            '## Prerequisites',
            '## Installation',
            '## Project Structure',
            '## Game Systems',
            '## API Documentation',
            '## Contributing'
        ]
        
        for section in required_sections:
            self.assertIn(
                section,
                content,
                f"README missing section: {section}"
            )
        
        # Check code examples
        code_blocks = re.findall(r'```[a-z]*\n[\s\S]*?\n```', content)
        self.assertGreater(
            len(code_blocks),
            0,
            "README should include code examples"
        )

    def test_api_documentation(self):
        """Test API documentation completeness"""
        api_patterns = [
            (r'/api/.*', 'API endpoint'),
            (r'/ws/.*', 'WebSocket endpoint')
        ]
        
        for file_path in self.python_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for pattern, endpoint_type in api_patterns:
                endpoints = re.finditer(pattern, content)
                for endpoint in endpoints:
                    # Find the associated function
                    func_def = re.search(
                        rf'def \w+\([^)]*\).*?{endpoint.group()}',
                        content,
                        re.DOTALL
                    )
                    
                    if func_def:
                        # Check docstring
                        func_content = content[func_def.start():]
                        docstring = re.search(
                            r'"""[\s\S]*?"""',
                            func_content
                        )
                        
                        self.assertIsNotNone(
                            docstring,
                            f"{endpoint_type} {endpoint.group()} missing documentation"
                        )

    def test_error_documentation(self):
        """Test error documentation"""
        for file_path in self.python_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find custom exceptions
            exceptions = re.finditer(
                r'class \w+(?:Error|Exception)\(.*?\):',
                content
            )
            
            for exception in exceptions:
                # Check exception docstring
                exc_content = content[exception.start():]
                docstring = re.search(
                    r'"""[\s\S]*?"""',
                    exc_content
                )
                
                self.assertIsNotNone(
                    docstring,
                    f"Exception {exception.group()} missing documentation"
                )

    def test_function_complexity(self):
        """Test function complexity metrics"""
        for file_path in self.python_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                module = ast.parse(f.read())
            
            for node in ast.walk(module):
                if isinstance(node, ast.FunctionDef):
                    # Count number of lines
                    func_lines = len(node.body)
                    self.assertLess(
                        func_lines,
                        50,  # Maximum function length
                        f"Function {node.name} is too long ({func_lines} lines)"
                    )
                    
                    # Count cyclomatic complexity
                    complexity = 1
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.While, ast.For, ast.Try)):
                            complexity += 1
                    
                    self.assertLess(
                        complexity,
                        10,  # Maximum complexity
                        f"Function {node.name} is too complex (complexity: {complexity})"
                    )

    def test_dependency_documentation(self):
        """Test dependency documentation"""
        req_path = self.project_root / 'requirements.txt'
        self.assertTrue(req_path.exists(), "requirements.txt not found")
        
        with open(req_path, 'r', encoding='utf-8') as f:
            requirements = f.readlines()
        
        # Check dependency format
        for req in requirements:
            req = req.strip()
            if req and not req.startswith('#'):
                # Should match package==version or package>=version
                self.assertRegex(
                    req,
                    r'^[a-zA-Z0-9\-_]+(?:==|>=|~=)[0-9\.]+$',
                    f"Invalid requirement format: {req}"
                )

    def test_comment_quality(self):
        """Test comment quality and coverage"""
        for file_path in self.python_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find inline comments
            comments = re.finditer(r'#.*$', content, re.MULTILINE)
            
            for comment in comments:
                comment_text = comment.group()
                # Comments should be meaningful
                self.assertGreater(
                    len(comment_text),
                    5,  # Minimum comment length
                    f"Short or meaningless comment: {comment_text}"
                )
                
                # Comments should be properly formatted
                self.assertTrue(
                    comment_text.startswith('# '),
                    f"Improperly formatted comment: {comment_text}"
                )

if __name__ == '__main__':
    unittest.main()
