from pathlib import Path
import json
import jsonschema
import jsonschema.exceptions

osfiles_schema = json.loads(Path("schemas/osFiles.json").read_text())

for file in Path("osFiles").rglob("*.json"):
    try:
        jsonschema.validate(json.loads(file.read_text()), osfiles_schema)
    except jsonschema.exceptions.ValidationError as e:
        # raise
        print(f"Error: {file}")
        print(e)