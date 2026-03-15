from typing import Any

from app.core.registry_a import DIRECTIONS, FIVE_ELEMENTS


def get_registry_snapshot() -> dict[str, Any]:
    return {
        "directions": {
            key: {
                "label_ja": profile.label_ja,
                "trigram": profile.trigram,
                "element": profile.element,
                "feng_shui_role": profile.feng_shui_role,
            }
            for key, profile in DIRECTIONS.items()
        },
        "five_elements": {
            key: {
                "label_ja": profile.label_ja,
                "generates": profile.generates,
                "controls": profile.controls,
            }
            for key, profile in FIVE_ELEMENTS.items()
        },
    }


def build_iching_context(question: str | None = None) -> dict[str, Any]:
    normalized_question = (question or "").strip()
    return {
        "question": normalized_question,
        "registry": get_registry_snapshot(),
        "status": "stub",
        "message": "易モジュールは共有コア参照前提で今後拡張します。",
    }