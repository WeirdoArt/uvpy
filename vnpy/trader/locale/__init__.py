import gettext
import os
from pathlib import Path


localedir: Path = Path(__file__).parent

def _get_preferred_language() -> str:
    """Get the user's preferred language from environment."""
    for env_name in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value: str | None = os.environ.get(env_name)
        if value:
            return value.split(":")[0].split(".")[0]
    return ""

if _get_preferred_language().startswith("zh"):
    translations: gettext.NullTranslations = gettext.NullTranslations()
else:
    translations = gettext.translation("vnpy", localedir=localedir, fallback=True)

_ = translations.gettext
