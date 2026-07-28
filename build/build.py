"""Python script to build KeyTik executable and installer."""

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path

import tomllib


class Build:
    """Build executable and installer."""

    def main(self):
        """Entry point."""
        # Argument
        parser = argparse.ArgumentParser(description="Development build")
        parser.add_argument(
            "--dev", action="store_true", help="Only build executable with conslo enabled"
        )
        arg = parser.parse_args()
        isdevelopment = bool(arg.dev)

        # Variable
        work_path = os.getcwd()

        version = self.get_version()
        if not version:
            return

        # Build executable
        build_executable = self.build_executable(work_path, version, isdevelopment)
        if not build_executable and build_executable != 0:
            return

        if not isdevelopment:
            # Build zip from executable
            if not self.build_zip(work_path, version):
                return

            # Build installer
            build_installer = self.build_installer(version)
            if not build_installer and build_installer != 0:
                return

            # Bump pyproject.toml version
            bump_project = self.bump_version(version)
            if not bump_project and build_executable != 0:
                return

            # Bump project metadata
            if not self.bump_metadata():
                return

    def get_version(self):
        """Genearate changelog and calculate next version number using git-cliff."""
        version = None
        output_file = "build/dist/CHANGELOG.md"

        try:
            print("Generating changelog . . .")

            calculate_version = subprocess.Popen(  # pylint: disable=R1732
                [
                    "uvx",
                    "git-cliff@latest",
                    "--bump",
                    "--output",
                    output_file,
                    "--verbose",
                ],
                stdout=subprocess.PIPE,
                text=True,
            )
            for result in calculate_version.stdout:
                if result.startswith("v"):
                    version = result.strip()

            if calculate_version.wait() != 0:
                return None

            print("Get version number . . .")

            with Path(output_file).open("r", encoding="utf-8") as f:
                first_line = f.readline().strip()

            match = re.search(r"v([0-9]+(?:\.[0-9]+)+(?:-[A-Za-z0-9.]+)?)", first_line)
            version = f"v{match.group(1)}" if match else None

            return version

        except (FileNotFoundError, PermissionError, ValueError) as error:
            print(f"Failed to build executable\n{error}")
            return None

    def build_executable(self, work_path: str, version: str, isdevelopment: bool):
        """Build executable using Pyinstaller."""
        try:
            print("Building executable . . .")

            command = [
                # Pyinstaller on UV
                "uv",
                "run",
                "--refresh-package",
                "pyinstaller",
                "--with",
                "pyinstaller",
                # Pyinstaller command
                "--",
                "pyinstaller",
                f"--workpath={work_path}/build/build",
                f"--distpath={work_path}/build/dist",
                "-y",
                "build/pyinstaller.spec",
                # Spec command
                "--",
                "--version",
                version,
            ]

            if isdevelopment:
                command.append("--dev")

            build_exec = subprocess.Popen(  # pylint: disable=R1732
                args=command,
                stdout=subprocess.PIPE,
                text=True,
            )

            for result in build_exec.stdout:
                print(result, end="")

            return build_exec.wait()

        except (FileNotFoundError, PermissionError, ValueError) as error:
            print(f"Failed to build executable\n{error}")
            return None

    def build_zip(self, work_path: str, version: str) -> bool:
        """Build zip from Pyinstaller result."""
        output_path = f"{work_path}/build/dist/KeyTik {version}"

        try:
            print("Building zip . . .")

            logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
            logger = logging.getLogger("ls_archiver")

            shutil.make_archive(
                base_name=output_path, format="zip", root_dir=output_path, logger=logger
            )

            return True

        except (FileNotFoundError, PermissionError, ValueError) as error:
            print(f"Failed to build zip. \n{error}")
            return False

    def bump_version(self, version: str) -> int:
        """Bump project version."""
        try:
            print("Bumping project version . . .")

            bump_project = subprocess.Popen(  # pylint: disable=R1732
                ["uv", "version", version],
                stdout=subprocess.PIPE,
                text=True,
            )

            for result in bump_project.stdout:
                print(result, end="")

            return bump_project.wait()

        except (FileNotFoundError, PermissionError, ValueError) as error:
            print(f"Failed to bump version.\n{error}")
            return None

    def bump_metadata(self) -> bool:
        """Bump project metadata."""
        try:
            print("Bumping metadata . . .")

            with Path("pyproject.toml").open("rb") as f:
                data = tomllib.load(f)

            project = data.get("project", {})
            meta = {
                "name": project.get("name", ""),
                "version": f"v{project.get('version', '')}",
            }

            with Path("keytik/_internal/data/metadata.json").open("w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            return True

        except (FileNotFoundError, PermissionError, ValueError) as error:
            print(f"Failed to bump metadata.\n{error}")
            return False

    def get_iscc_path(self) -> str:
        """Get inno setup executable path."""
        path = shutil.which("iscc")
        if path:
            return path

        program_files_86 = shutil.which("iscc", path=r"C:\Program Files (x86)\Inno Setup 6")
        if program_files_86:
            return program_files_86

        program_files_64 = shutil.which("iscc", path=r"C:\Program Files\Inno Setup 6")
        if program_files_64:
            return program_files_64

        return None

    def build_installer(self, version: str) -> int:
        """Build installer using inno setup."""
        issc_path = self.get_iscc_path()
        version = version.replace("v", "")

        try:
            print("Building installer . . .")

            bump_project = subprocess.Popen(  # pylint: disable=R1732
                [issc_path, f"/DAppVersion={version}", "build/inno_setup.iss"],
                stdout=subprocess.PIPE,
                text=True,
            )

            for result in bump_project.stdout:
                print(result, end="")

            return bump_project.wait()

        except (FileNotFoundError, PermissionError, ValueError) as error:
            print(f"Failed to build installer.\n{error}")
            return False


if __name__ == "__main__":
    Build().main()
