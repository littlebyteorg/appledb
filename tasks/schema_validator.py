from pathlib import Path
import json
import jsonschema
import jsonschema.exceptions
for file in Path("osFiles").rglob("*.json"):
    try:
        jsonschema.validate(json.load(file.open()), json.load(Path("schemas/osFiles.json").open()))
    except jsonschema.exceptions.ValidationError as e:
        # raise
        print(f"Error: {file}")
        print(e)