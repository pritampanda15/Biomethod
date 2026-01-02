"""Environment parsing for conda, requirements, etc."""

import re
from pathlib import Path
from typing import Any

import yaml

from biomethod.core.models import EnvironmentInfo


class EnvironmentParser:
    """Parse environment files for dependency information."""

    def __init__(self):
        """Initialize the environment parser."""
        pass

    def parse_directory(self, directory: Path) -> EnvironmentInfo:
        """Parse all environment files in a directory.

        Args:
            directory: Directory to scan

        Returns:
            EnvironmentInfo with all detected dependencies
        """
        env_info = EnvironmentInfo()

        # Look for requirements.txt
        for req_file in directory.rglob("requirements*.txt"):
            packages = self.parse_requirements_txt(req_file)
            env_info.packages.update(packages)
            env_info.requirements_files.append(str(req_file))

        # Look for conda environment files
        for env_file in directory.rglob("*.yml"):
            if self._is_conda_env_file(env_file):
                packages = self.parse_conda_yaml(env_file)
                env_info.packages.update(packages)
                env_info.environment_files.append(str(env_file))

        for env_file in directory.rglob("*.yaml"):
            if self._is_conda_env_file(env_file):
                packages = self.parse_conda_yaml(env_file)
                env_info.packages.update(packages)
                env_info.environment_files.append(str(env_file))

        # Look for Docker/Singularity files
        containers = self._find_containers(directory)
        env_info.containers = containers

        return env_info

    def parse_requirements_txt(self, file_path: Path) -> dict[str, str]:
        """Parse a requirements.txt file.

        Args:
            file_path: Path to requirements.txt

        Returns:
            Dictionary mapping package names to versions
        """
        packages: dict[str, str] = {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue

                    # Skip options like -r, -e, --index-url
                    if line.startswith("-"):
                        continue

                    # Parse package specification
                    parsed = self._parse_requirement_line(line)
                    if parsed:
                        name, version = parsed
                        packages[name] = version

        except IOError:
            pass

        return packages

    def _parse_requirement_line(self, line: str) -> tuple[str, str] | None:
        """Parse a single requirement line.

        Args:
            line: Requirement specification line

        Returns:
            Tuple of (package_name, version) or None
        """
        # Remove comments
        if "#" in line:
            line = line.split("#")[0].strip()

        # Handle different specifiers: ==, >=, <=, ~=, !=, >, <
        patterns = [
            r"^([a-zA-Z0-9_-]+)==([\d.]+.*?)$",  # exact version
            r"^([a-zA-Z0-9_-]+)>=([\d.]+.*?)$",  # minimum version
            r"^([a-zA-Z0-9_-]+)<=([\d.]+.*?)$",  # maximum version
            r"^([a-zA-Z0-9_-]+)~=([\d.]+.*?)$",  # compatible version
            r"^([a-zA-Z0-9_-]+)$",  # no version specified
        ]

        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    return (groups[0].lower(), groups[1])
                else:
                    return (groups[0].lower(), "unspecified")

        return None

    def parse_conda_yaml(self, file_path: Path) -> dict[str, str]:
        """Parse a conda environment YAML file.

        Args:
            file_path: Path to environment.yml

        Returns:
            Dictionary mapping package names to versions
        """
        packages: dict[str, str] = {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                env_data = yaml.safe_load(f)
        except (IOError, yaml.YAMLError):
            return packages

        if not env_data or "dependencies" not in env_data:
            return packages

        for dep in env_data["dependencies"]:
            if isinstance(dep, str):
                parsed = self._parse_conda_dep(dep)
                if parsed:
                    name, version = parsed
                    packages[name] = version

            elif isinstance(dep, dict):
                # Handle pip dependencies
                if "pip" in dep:
                    for pip_dep in dep["pip"]:
                        parsed = self._parse_requirement_line(pip_dep)
                        if parsed:
                            name, version = parsed
                            packages[name] = version

        return packages

    def _parse_conda_dep(self, dep: str) -> tuple[str, str] | None:
        """Parse a conda dependency specification.

        Args:
            dep: Conda dependency string

        Returns:
            Tuple of (package_name, version) or None
        """
        # Remove channel prefix
        if "::" in dep:
            dep = dep.split("::")[-1]

        # Parse version specifier
        # Formats: package=version, package>=version, package
        patterns = [
            r"^([a-zA-Z0-9_-]+)==([\d.]+.*?)$",
            r"^([a-zA-Z0-9_-]+)=([\d.]+.*?)$",
            r"^([a-zA-Z0-9_-]+)>=([\d.]+.*?)$",
            r"^([a-zA-Z0-9_-]+)$",
        ]

        for pattern in patterns:
            match = re.match(pattern, dep)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    return (groups[0].lower(), groups[1])
                else:
                    return (groups[0].lower(), "unspecified")

        return None

    def _is_conda_env_file(self, file_path: Path) -> bool:
        """Check if a YAML file is a conda environment file.

        Args:
            file_path: Path to check

        Returns:
            True if it's a conda environment file
        """
        # Check filename patterns
        name = file_path.name.lower()
        if name in ["environment.yml", "environment.yaml", "conda.yml", "conda.yaml"]:
            return True

        if "env" in name and file_path.suffix in [".yml", ".yaml"]:
            return True

        # Check content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read(500)  # Read first 500 chars
                if "dependencies:" in content or "channels:" in content:
                    return True
        except IOError:
            pass

        return False

    def _find_containers(self, directory: Path) -> list[str]:
        """Find container images referenced in the directory.

        Args:
            directory: Directory to scan

        Returns:
            List of container image references
        """
        containers: list[str] = []

        # Look for Dockerfiles
        for dockerfile in directory.rglob("Dockerfile*"):
            images = self._parse_dockerfile(dockerfile)
            containers.extend(images)

        # Look for Singularity files
        for singfile in directory.rglob("*.def"):
            images = self._parse_singularity_def(singfile)
            containers.extend(images)

        for singfile in directory.rglob("Singularity*"):
            images = self._parse_singularity_def(singfile)
            containers.extend(images)

        return list(set(containers))

    def _parse_dockerfile(self, file_path: Path) -> list[str]:
        """Parse a Dockerfile for base images.

        Args:
            file_path: Path to Dockerfile

        Returns:
            List of image references
        """
        images: list[str] = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.upper().startswith("FROM "):
                        # Extract image name
                        parts = line.split()
                        if len(parts) >= 2:
                            image = parts[1]
                            # Remove "as builder" suffix
                            if " as " in image.lower():
                                image = image.split()[0]
                            images.append(image)
        except IOError:
            pass

        return images

    def _parse_singularity_def(self, file_path: Path) -> list[str]:
        """Parse a Singularity definition file for base images.

        Args:
            file_path: Path to .def file

        Returns:
            List of image references
        """
        images: list[str] = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.lower().startswith("from:"):
                        image = line.split(":", 1)[1].strip()
                        images.append(image)
                    elif line.lower().startswith("bootstrap:"):
                        # Could be docker, library, etc.
                        pass
        except IOError:
            pass

        return images

    def parse_pyproject_toml(self, file_path: Path) -> dict[str, str]:
        """Parse a pyproject.toml for dependencies.

        Args:
            file_path: Path to pyproject.toml

        Returns:
            Dictionary mapping package names to versions
        """
        packages: dict[str, str] = {}

        try:
            # Use tomllib in Python 3.11+, otherwise tomli
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib

            with open(file_path, "rb") as f:
                data = tomllib.load(f)

            # Get dependencies from [project] section
            deps = data.get("project", {}).get("dependencies", [])
            for dep in deps:
                parsed = self._parse_requirement_line(dep)
                if parsed:
                    name, version = parsed
                    packages[name] = version

            # Get optional dependencies
            opt_deps = data.get("project", {}).get("optional-dependencies", {})
            for group, group_deps in opt_deps.items():
                for dep in group_deps:
                    parsed = self._parse_requirement_line(dep)
                    if parsed:
                        name, version = parsed
                        packages[name] = version

        except (IOError, Exception):
            pass

        return packages
