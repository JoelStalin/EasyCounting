from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    user_data = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
    local_state = user_data / "Local State"
    if not local_state.exists():
        print(f"No se encontro Local State en: {local_state}")
        return 1

    data = json.loads(local_state.read_text(encoding="utf-8"))
    cache = data.get("profile", {}).get("info_cache", {})
    if not cache:
        print("No se encontraron perfiles en info_cache")
        return 1

    print(f"User Data Dir: {user_data}")
    print("Perfiles encontrados:")
    for directory, info in cache.items():
        name = info.get("name", "")
        gaia = info.get("user_name", "")
        print(f"- profile_directory={directory} | name={name} | account={gaia}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
