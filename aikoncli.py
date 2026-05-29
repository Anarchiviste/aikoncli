import sys

from pathlib import Path
from aikoncli.function import aikon_to_yolo

if (args_count := len(sys.argv)) > 3:
    print(f"One argument expected, got {args_count - 1}")
    raise SystemExit(2)

elif args_count < 2:
    print("You must specify the target directory")
    raise SystemExit(2)

url_manifest = sys.argv[1]
output_dir = sys.argv[2]

str(url_manifest)
str(output_dir)

aikon_to_yolo(url_manifest, output_dir)