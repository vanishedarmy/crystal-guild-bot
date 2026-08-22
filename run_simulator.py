from pathlib import Path
import os

os.chdir(Path(__file__).resolve().parent)

from crystal_guild.simulator import main

if __name__ == "__main__":
    main()
