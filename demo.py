from pathlib import Path

from file_structure import FileStructure, FileCommand, FileStructureCommand

if __name__ == "__main__":

    DEMO_NO = 0

    if DEMO_NO == 0:
        # FileStructure enables defining more readable file structures.

        # Some variables:
        root_dir = "/home/ersin/Desktop/abc"
        a_filename = "a.mp4"

        # The old way of defining file paths:

        # Common directories:
        abc = Path(root_dir)
        xyz = abc / "xyz"
        # Actual paths that we need:
        x = xyz / "x.txt"
        y = xyz / "y.png"
        z = xyz / "z"
        a = abc / a_filename
        b = abc / "b.mp4"
        # It is difficult to understand the file structures (i.e. what is where) especially when the hierarchy gets deeper and wider.

        # The new way of defining file paths:

        # Common directories:
        abc = FileStructure(f"""
        {root_dir}                  # This is a comment. You can add comments.
            xyz
                x.txt
                y.png
                z
            {a_filename}            # e.g. a.mp4
            b.mp4
        """)
        xyz = abc["xyz"]
        # Actual paths that we need (Exactly the same code):
        x = xyz / "x.txt"
        y = xyz / "y.png"
        z = xyz / "z"
        a = abc / a_filename
        b = abc / "b.mp4"
        # Note that abc and xyz are not Path objects. Use abc.path() and xyz.path() to obtain Path objects.

        # Short summary:

        # (1) For ordinary files:
        # using indexing or division brings a Path:
        # e.g. abc["x.txt"] is a Path, abc / "x.txt" is also a Path.

        # (2) For directories: 
        # indexing brings a FileStructure, division brings a Path:
        # e.g. abc["xyz"] is a FileStructure but abc / "xyz" is a Path.
        # Alternatively, abc["xyz"].path() is also a Path.
        # This of course can be used for getting the main directory as well: abc.path()

        # Some details:

        # Indexing returns a Path (if it is an ordinary file) or a FileStructure (if it is a directory).
        # e.g. abc is a FileStructure. So is abc["xyz"]. So is abc["xyz"]["z"].
        # But abc["a.mp4"] is a Path. So is abc["xyz"]["x.txt"].

        # Consecutive filenames can be chained together:
        # e.g. abc["xyz"]["z"] can be obtained by abc["xyz/z"].

        # If you have a FileStructure but actually want the Path (of the main directory), use .path()
        # e.g. abc.path() is a Path object.

        # If you are not sure if you get a Path or FileStructure, you can convert it to a str.
        # e.g.      str(abc[variable]) is a path of type str.
        # e.g. Path(str(abc[variable])) is a Path object.
        # But there is a simpler way to achieve this. See below.

        # Division always returns a Path object.
        # e.g. abc / variable is a Path object.

    elif DEMO_NO == 1:

        # With FileStructure, common assertions and actions become straightforward:

        # There are file commands that you can use for each file, and file structure commands that you can use at the end of each directory content.

        abc = FileStructure(f"""
        /home/ersin/Desktop/abc {FileCommand.PRESENT}       # Assertion: This directory exists.
            xyz {FileCommand.CREATE_IF_ABSENT}              # Action: If this directory doesn't exist, then create it.
                x.txt {FileCommand.ABSENT_BUT_CREATE}       # Assertion: This file does not exist. Action: Create it (as an empty file).
                y.png
                z
                {FileStructureCommand.THAT_IS_ALL}          # Assertion: There is nothing else in xyz: only x.txt, y.png and z.
            a.mp4
            b.mp4
            {FileStructureCommand.REMOVE_EVERYTHING_ELSE}   # Action: If there are other files, then remove all of them.
        """)

        # Another example:

        file_structure = FileStructure(f"""
            main_dir {FileCommand.PRESENT}
                a.txt {FileCommand.PRESENT_BUT_RECREATE}
                b.png {FileCommand.ABSENT}
                c {FileCommand.PRESENT}
                    d {FileCommand.CREATE_IF_ABSENT}
                    e {FileCommand.CREATE}                  # After this, d may not be empty, but e will be empty for sure.
                    f {FileCommand.CREATE_IF_ABSENT}                      
                    {FileStructureCommand.THAT_IS_ALL}
                g {FileCommand.CREATE}
                {FileStructureCommand.REMOVE_EVERYTHING_ELSE}
        """)

    elif DEMO_NO == 2:

        # You can use lists (or sets) of filenames.

        abc = FileStructure(f"""
        ../abc1 {FileCommand.CREATE}
            {[1, 5, 10]} {FileCommand.CREATE}       # i.e. Create directories named 1, 5 and 10 in ../abc1.
            a {FileCommand.CREATE}                  # Also create a directory named a.
        """)

        # For now, they all must be directories, or all must be ordinary files. 
        # e.g. Instead of ["a", 1, 5, 10], write 2 lines: "a" and [1, 5, 10].
        # TODO: Ideally there should not be this limitation.

        # Another example:

        abc = FileStructure(f"""
        ../abc2 {FileCommand.CREATE_IF_ABSENT}
            {[f"{letter}.txt" for letter in ("A", "B", "C")]} {FileCommand.CREATE_IF_ABSENT}    # A.txt, B.txt, C.txt inside ../abc2
            {[i for i in range(1, 10)]} {FileCommand.CREATE_IF_ABSENT}                          # 1, 2, 3, ..., 9 inside ../abc2
            a {FileCommand.CREATE_IF_ABSENT}                                                    # a inside ../abc2
                {[i for i in range(1, 10)]} {FileCommand.CREATE_IF_ABSENT}                      # 1, 2, 3, ..., 9 inside ../abc2/a
                {FileStructureCommand.REMOVE_EVERYTHING_ELSE}
        """)

        # This feature is very powerful: Lists (or sets) of directories can have the same content.

        abc = FileStructure(f"""
        ../abc3 {FileCommand.CREATE_IF_ABSENT}
            {[i for i in range(1, 10)]} {FileCommand.CREATE_IF_ABSENT}
                a {FileCommand.CREATE_IF_ABSENT}                        # There will be "a" in all those directories.
                {["x", "y", "z"]} {FileCommand.CREATE_IF_ABSENT}        # i.e. There will be these three in all those directories.
        """)

        example_path = abc / "1" / "results.txt"

        # Maybe one of them has extra content:

        abc = FileStructure(f"""
        ../abc4 {FileCommand.CREATE_IF_ABSENT}
            {[i for i in range(1, 10)]} {FileCommand.CREATE_IF_ABSENT}
                a {FileCommand.CREATE_IF_ABSENT}                            # There will be "a" in all those directories.
                {["x", "y", "z"]} {FileCommand.CREATE_IF_ABSENT}            # i.e. There will be these three in all those directories.
            1 {FileCommand.PRESENT}
                extra_dir {FileCommand.CREATE}                              # One of those 9 directories will have one more sub-directory named extra-dir.
        """)
