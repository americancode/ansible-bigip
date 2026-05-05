from __future__ import annotations


def validate_login_and_config(validator, objects: dict[str, list]) -> None:
    login_banners = objects["login_banners"]
    config = objects["config"]

    for obj in login_banners:
        validator.validate_target_selectors(obj, label="system login banner object")
        enabled = obj.data.get("enabled")
        if enabled is not None and not isinstance(enabled, bool):
            validator.error(obj.relpath, "system login banner `enabled` must be a boolean")
        if obj.effective_state != "absent" and obj.data.get("enabled", True) and obj.data.get("text") in (None, ""):
            validator.error(obj.relpath, "system login banner with `enabled: true` must define non-empty `text`")
    validator.check_targeted_identity_collisions(login_banners, identity_func=lambda obj: ("system_login_banner",), label="system login banner object")

    for obj in config:
        validator.validate_target_selectors(obj, label="system config object")
    validator.check_targeted_identity_collisions(config, identity_func=lambda obj: ("system_config",), label="system config object")
    for obj in config:
        if "save" in obj.data and not isinstance(obj.data.get("save"), bool):
            validator.error(obj.relpath, "`save` must be a boolean")
