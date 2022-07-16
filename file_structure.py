from __future__ import annotations

import shutil
from enum import Enum
from pathlib import Path
import os
from typing import Optional, Union


"""
Assumptions:
- It is a directory if it doesn't have an extension (i.e. os.path.splitext(path)[1] == "" --> path is directory)
- Filenames do not contain '[' or ']' or '{' or '}' or ','.
"""


def _remove(path: Path, prompt: bool = True) -> None:
    if path.is_dir():
        if len(os.listdir(path)) == 0:
            os.rmdir(path)
        else:
            if prompt:
                choice = input(f"A non-empty directory '{path}' will be removed. Proceed? (Y/n) ").strip().lower()
                if choice == "" or choice == "y":
                    shutil.rmtree(path)
                else:
                    exit(1)
    else:
        os.remove(path)


def _is_seemingly_dir(path: Union[Path, str]) -> bool:
    # Different from os.path.isdir(path)
    # We do not check if it really exist.
    return os.path.splitext(path)[1] == ""


def _as_path(path_or_file_structure: Union[Path, FileStructure]) -> Path:
    if isinstance(path_or_file_structure, Path):
        path = path_or_file_structure
    elif isinstance(path_or_file_structure, FileStructure):
        path = path_or_file_structure.path()
    else:
        assert False
    return path


def _absent_but_create(path: Path) -> None:
    assert not path.exists(), f"There must not be '{path}' but there is."
    if _is_seemingly_dir(path):
        os.makedirs(path)
    else:
        open(path, "w").close()


def _present_but_remove(path: Path, prompt: bool = True) -> None:
    assert path.exists(), f"There must be '{path}' but there is not."
    _remove(path, prompt)


def _remove_comments(lines: list[str]) -> list[str]:
    for line_no, line in enumerate(lines):
        if "#" in line:
            lines[line_no] = line[:line.index("#")]
    return lines


def _remove_empty_lines(lines: list[str]) -> list[str]:
    while lines[0].strip() == "":
        lines = lines[1:]
    while lines[-1].strip() == "":
        lines = lines[:-1]
    return lines


def _remove_trailing_slash_if_exists(s: str) -> str:
    if s.endswith("/"):
        s = s[:-1]
    return s


def _remove_enclosing_quotation_marks(s: str) -> str:
    if s.startswith("'") or s.startswith('"'):
        s = s[1:]
    if s.endswith("'") or s.endswith('"'):
        s = s[:-1]
    return s


class FileCommand(Enum):
    # Command = Assertion + Action

    PRESENT = "<0>"                 # Assertion             -- It exists.
    ABSENT = "<1>"                  # Assertion             -- It does not exist.
    PRESENT_BUT_REMOVE = "<2>"      # Assertion + Action    -- It exists & Remove it.
    PRESENT_BUT_RECREATE = "<3>"    # Assertion + Action    -- It exists & Create it from scratch (i.e. Remove it and create it).
    ABSENT_BUT_CREATE = "<4>"       # Assertion + Action    -- It does not exit & Create it.
    CREATE = "<5>"                  # Action                -- If it exists, create it from scratch. If not, create it.
    CREATE_IF_ABSENT = "<6>"        # Action                -- If it does not exist, create it.

    @staticmethod
    def from_str(s: str) -> FileCommand:
        command_dict = {command.value: command for command in FileCommand}
        return command_dict[s]

    @staticmethod
    def run(file_command: FileCommand, path: Path, prompt: bool = True) -> None:
        if file_command == FileCommand.PRESENT:
            assert path.exists(), f"You said there must be '{path}' but there is not."

        elif file_command == FileCommand.ABSENT:
            assert not path.exists(), f"You said there must not be '{path}' but there is."

        elif file_command == FileCommand.PRESENT_BUT_REMOVE:
            _present_but_remove(path, prompt)

        elif file_command == FileCommand.PRESENT_BUT_RECREATE:
            _present_but_remove(path, prompt)
            _absent_but_create(path)

        elif file_command == FileCommand.ABSENT_BUT_CREATE:
            _absent_but_create(path)

        elif file_command == FileCommand.CREATE:
            if path.exists():
                _present_but_remove(path, prompt)
            _absent_but_create(path)

        elif file_command == FileCommand.CREATE_IF_ABSENT:
            if not path.exists():
                _absent_but_create(path)

        else:
            assert False

    def __str__(self):
        return self.value


class FileStructureCommand(Enum):
    THAT_IS_ALL = "<<0>>"               # Assertion     -- There is no other file.
    REMOVE_EVERYTHING_ELSE = "<<1>>"    # Action        -- Remove all other files if exist.

    @staticmethod
    def from_str(s: str) -> FileStructureCommand:
        command_dict = {command.value: command for command in FileStructureCommand}
        return command_dict[s]

    @staticmethod
    def run(file_structure_command: FileStructureCommand, path: Path, paths: list[Path], prompt: bool = True) -> None:
        if not os.path.exists(path):
            return

        all_files = {path / filename for filename in os.listdir(path)}
        everything_else = all_files.difference(paths)

        if file_structure_command == FileStructureCommand.THAT_IS_ALL:
            assert len(everything_else) == 0, f"'{path}' must not contain these: {everything_else}"

        elif file_structure_command == FileStructureCommand.REMOVE_EVERYTHING_ELSE:
            for current_path in everything_else:
                _remove(current_path, prompt)

        else:
            assert False

    def __str__(self):
        return self.value


class FileStructure:

    @staticmethod
    def _parse_normal_line(line: str) -> tuple[str, Optional[FileCommand]]:
        if line.endswith(">"):
            last_space_index = line.rindex(" ")
            filename = line[:last_space_index].strip()
            command_str = line[last_space_index + 1:].strip()
            file_command = FileCommand.from_str(command_str)
        else:
            filename = line
            file_command = None

        filename = _remove_trailing_slash_if_exists(filename)

        return filename, file_command

    @staticmethod
    def _parse_file_structure_command_line(line: str) -> FileStructureCommand:
        assert line.startswith("<<"), f"A {FileStructureCommand.__name__} must always be provided alone (i.e. not with a file)."
        file_structure_command = FileStructureCommand.from_str(line)
        return file_structure_command

    def _process_lines(self, lines: list[str]) -> None:

        def calc_indent_length() -> int:
            first_line, second_line = lines[:2]
            first_line_num_spaces = len(first_line) - len(first_line.lstrip())
            second_line_num_spaces = len(second_line) - len(second_line.lstrip())
            indent_length = second_line_num_spaces - first_line_num_spaces  # There should be this many spaces for each indent.
            assert indent_length > 0, f"Second line must be indented relative to first line.\nFirst line: {first_line}\nSecond line: {second_line}"
            return indent_length

        def calc_num_leading_spaces() -> int:
            first_line = lines[0]
            num_leading_spaces = len(first_line) - len(first_line.lstrip())
            return num_leading_spaces

        def calc_num_indents(line: str, indent_length: int, prev_is_ordinary_file: bool) -> int:
            num_spaces = len(line) - len(line.lstrip()) - num_leading_spaces
            assert num_spaces > 0, "All lines must be indented."
            assert num_spaces % indent_length == 0, f"Indentations must be consistent: {line}"  # e.g. always 4*k spaces where k is an integer.
            num_indents = num_spaces // indent_length

            if prev_is_ordinary_file:
                assert num_indents <= prev_num_indents, f"This line has too many indents: {line}"
            else:
                assert num_indents <= prev_num_indents + 1, f"This line has too many indents: {line}"
            assert num_indents != 0, "There must be only one main directory."
            return num_indents

        def process_line(lines: list[str], line_no: int, num_indents: int, num_leading_spaces: int, indent_length: int) -> tuple[int, bool]:

            def process_line_block(lines: list[str], line_no: int, num_indents: int, num_leading_spaces: int, indent_length: int):
                current_line_block = []
                line_no += 1
                while line_no < len(lines):
                    current_line = lines[line_no]
                    current_num_spaces = len(current_line) - len(current_line.lstrip()) - num_leading_spaces
                    this_num_indents = current_num_spaces // indent_length
                    if this_num_indents <= num_indents:
                        break
                    current_line_block.append(current_line)
                    line_no += 1

                return current_line_block, line_no

            line = lines[line_no].strip()

            if line.endswith(">>"):
                file_structure_command = FileStructure._parse_file_structure_command_line(line)
                assert self.main_dir_file_structure_command is None, f"At most 1 {FileStructureCommand.__name__} can be provided for a directory."
                self.main_dir_file_structure_command = file_structure_command
                line_no += 1
                is_ordinary_file = True  # Beyond it: This must be the last line.

            elif ("[" in line and "]" in line) or ("{" in line and "}" in line):
                line = line.replace("{", "[").replace("}", "]")
                filenames_str, file_command = FileStructure._parse_normal_line(line)
                assert filenames_str[0] == "[" and filenames_str[-1] == "]"
                filenames = [_remove_trailing_slash_if_exists(_remove_enclosing_quotation_marks(filename.strip()).strip()) for filename in filenames_str[1:-1].split(",")]

                new_paths = [self.main_dir / filename for filename in filenames]

                assert all([_is_seemingly_dir(filename) for filename in filenames]) or all([not _is_seemingly_dir(filename) for filename in filenames])
                if _is_seemingly_dir(filenames[0]):
                    # All are directories
                    current_line_block, line_no = process_line_block(lines, line_no, num_indents, num_leading_spaces, indent_length)
                    new_paths_or_file_structures = []
                    for new_path in new_paths:
                        this_line_block = [" " * (num_leading_spaces + indent_length) + str(new_path) + ("" if file_command is None else " " + file_command.value)] + current_line_block
                        new_path_or_file_structure = FileStructure("\n".join(this_line_block), lazy_commands=True, prompt=self.prompt)  # Recursion
                        new_paths_or_file_structures.append(new_path_or_file_structure)

                    file_command = None  # We delegate the command (if exists) to the inner FileStructure.
                    is_ordinary_file = False

                else:
                    # All are ordinary files
                    new_paths_or_file_structures = new_paths
                    is_ordinary_file = True
                    line_no += 1

                self.list_dir.extend(new_paths_or_file_structures)
                self.list_dir_file_commands.extend([file_command] * len(filenames))
                for filename, new_path_or_file_structure in zip(filenames, new_paths_or_file_structures):
                    self.dict_dir[filename] = new_path_or_file_structure

            else:
                filename, file_command = FileStructure._parse_normal_line(line)
                new_path = self.main_dir / filename

                if _is_seemingly_dir(new_path):

                    current_line_block, line_no = process_line_block(lines, line_no, num_indents, num_leading_spaces, indent_length)

                    current_line_block = [" " * (num_leading_spaces + indent_length) + str(new_path) + ("" if file_command is None else " " + file_command.value)] + current_line_block
                    new_path_or_file_structure = FileStructure("\n".join(current_line_block), lazy_commands=True, prompt=self.prompt)  # Recursion
                    file_command = None  # We delegate the command (if exists) to the inner FileStructure.

                    is_ordinary_file = False

                else:
                    line_no += 1
                    new_path_or_file_structure = new_path
                    is_ordinary_file = True

                self.list_dir.append(new_path_or_file_structure)
                self.list_dir_file_commands.append(file_command)
                self.dict_dir[filename] = new_path_or_file_structure

            return line_no, is_ordinary_file

        indent_length = calc_indent_length()
        num_leading_spaces = calc_num_leading_spaces()

        prev_num_indents = 0
        prev_is_ordinary_file = False

        line_no = 1
        while line_no < len(lines):
            line = lines[line_no]
            num_indents = calc_num_indents(line, indent_length, prev_is_ordinary_file)

            if num_indents == 1:
                line_no, prev_is_ordinary_file = process_line(lines, line_no, num_indents, num_leading_spaces, indent_length)
            else:
                assert False, "..."

            prev_num_indents = num_indents

    def __init__(self, structure: str, lazy_commands=False, prompt=True):
        # TODO: There may be "\t" rather than " ".

        self.prompt = prompt  # prompt for removing non-empty directories
        lines = structure.splitlines()

        lines = _remove_comments(lines)
        lines = _remove_empty_lines(lines)

        first_line = lines[0].strip()
        assert not first_line.endswith(">>"), f"First line must not be a {FileStructureCommand.__name__}."
        main_dir_path, main_dir_file_command = FileStructure._parse_normal_line(first_line)
        assert _is_seemingly_dir(main_dir_path), "The first line must be a directory."

        self.main_dir = Path(main_dir_path)
        self.main_dir_file_command = main_dir_file_command
        self.main_dir_file_structure_command = None

        self.list_dir = []
        self.list_dir_file_commands = []

        self.dict_dir = {}

        if len(lines) > 1:
            self._process_lines(lines)

        self.commands_run = False
        if not lazy_commands:
            self.do()

    def path(self) -> Path:
        return self.main_dir

    def children(self) -> list[Union[Path, FileStructure]]:
        return self.list_dir

    def do(self) -> None:
        if not self.commands_run:

            if self.main_dir_file_structure_command is not None:
                paths = [child if isinstance(child, Path) else child.path() for child in self.children()]
                FileStructureCommand.run(self.main_dir_file_structure_command, self.path(), paths, prompt=self.prompt)

            if self.main_dir_file_command is not None:
                FileCommand.run(self.main_dir_file_command, self.path(), prompt=self.prompt)

            for child, file_command in zip(self.list_dir, self.list_dir_file_commands):
                if isinstance(child, Path):
                    if file_command is not None:
                        FileCommand.run(file_command, child, prompt=self.prompt)

                elif isinstance(child, FileStructure):
                    assert file_command is None, "Bug :("  # We have delegated the command.
                    child.do()

                else:
                    assert False, "Bug :("

            self.commands_run = True

    def __str__(self):
        return str(self.path())

    def _repr_simple(self, parent: Path):
        # TODO: Commands??
        # TODO: Later: Lists...

        # e.g. parent is Path("abc/def")
        # e.g. self.path() is Path("abc/def/ghi")
        # We need "ghi"
        parent = str(parent)
        first_line = str(self.path())
        assert first_line.startswith(parent)
        first_line = first_line[len(parent) + 1:]

        rest = "\n".join(["\t" + (str(child) if isinstance(child, Path) else child._repr_simple()) for child in self.children()])
        # TODO: FIXME: We must provide parent to _repr_simple? Is it the parent?
        return first_line + rest + "\n"

    def __repr__(self):
        # TODO: Commands??
        # TODO: Later: Lists...

        # This is for: print(file_structure.children())

        children_str = "".join(["\t" + (str(child) if isinstance(child, Path) else child._repr_simple(self.path())) for child in self.children()])

        # Below is a PEP-8 compliant multiline f-string
        return (
            "FileStructure('''\n"
            f"{self.path()}\n"
            f"{children_str}''')"
        )

    def __getitem__(self, key: str) -> Path:
        # file_structure["abc"] is file_structure.path() / "abc"
        # So: file_structure[""] is file_structure.path()
        # And: file_structure["abc/def"] is the same as file_structure["abc"]["def"]

        # The given key must exist!
        # So the files may be imaginary.
        # But they must be defined when constructing the FileStructure object.
        # This is a design decision.
        # A FileStructure object contains all the files that already exist and that will be existing at some point in the future.
        assert isinstance(key, str)

        if key == "" or key == "/":
            return self.path()

        # Remove leading and trailing slash(es).
        while key[0] == "/":
            key = key[1:]
        while key[-1] == "/":
            key = key[:-1]
        # Note: file_structure[a][b] and file_structure[a+"/"+b] are the same thing if b != ""

        if "/" in key:
            filenames = key.split("/")
            path_or_file_structure = self  # This is FileStructure now.
            for filename in filenames:
                path_or_file_structure = path_or_file_structure[filename]
            return _as_path(path_or_file_structure)
        else:
            path_or_file_structure = self.dict_dir[key]
            return _as_path(path_or_file_structure)

    def __truediv__(self, other: str) -> Path:
        # file_structure / s  is the same as  file_structure[s]
        return self[other]
