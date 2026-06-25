from pathlib import Path

from app.config.loader import load_project_config


def test_load_project_config_from_repo_root() -> None:
    root = Path(__file__).resolve().parents[1]

    config = load_project_config(root)

    assert config.autofill_rules["profile"]["preferred_name"] == "Sam"
    assert config.autofill_rules["autofill_policy"]["never_click_final_submit"] is True
    assert len(config.companies) >= 100
    assert "Prescreen Answer Templates" in config.prescreen_templates_text

