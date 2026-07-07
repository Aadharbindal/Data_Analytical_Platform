"""
Fix Pydantic v2 deprecation warnings across all schema files.
Replaces:
  class Config:
      orm_mode = True
With:
  model_config = ConfigDict(from_attributes=True)

Also adds: from pydantic import ConfigDict   (if not already present)
"""
import os
import re

SCHEMAS_DIR = "app/schemas"

CLASS_CONFIG_PATTERN = re.compile(
    r'(\n\s{4}class Config:\n\s{8}orm_mode\s*=\s*True)',
    re.MULTILINE
)

files_fixed = []

for fname in os.listdir(SCHEMAS_DIR):
    if not fname.endswith(".py"):
        continue
    path = os.path.join(SCHEMAS_DIR, fname)
    text = open(path, encoding="utf-8").read()

    if "orm_mode = True" not in text:
        continue

    # Replace class Config: orm_mode = True with model_config
    new_text = CLASS_CONFIG_PATTERN.sub(
        "\n    model_config = ConfigDict(from_attributes=True)",
        text
    )

    # Ensure ConfigDict is imported from pydantic
    if "ConfigDict" not in new_text:
        if "from pydantic import" in new_text:
            new_text = re.sub(
                r"from pydantic import (.*)",
                lambda m: f"from pydantic import {m.group(1)}, ConfigDict",
                new_text,
                count=1
            )
        else:
            new_text = "from pydantic import ConfigDict\n" + new_text

    if new_text != text:
        open(path, "w", encoding="utf-8").write(new_text)
        files_fixed.append(fname)
        print("FIXED: " + fname)

print("Total files fixed: " + str(len(files_fixed)))
