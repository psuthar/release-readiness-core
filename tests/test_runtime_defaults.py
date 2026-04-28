from release_readiness_core.runtime_config import (
    RuntimeConfig,
    parse_runtime_config,
    resolve_runtime_defaults,
)


def test_parse_runtime_config_paths_and_env_sections():
    cfg = parse_runtime_config(
        {
            "paths": {
                "input_json_default_path": "fixtures/sample.json",
                "output_dir_default": "out/release-readiness",
            },
            "env": {
                "base_ref_env_var": "CUSTOM_BASE_REF",
                "enforcement_mode_env_var": "CUSTOM_MODE",
            },
        }
    )
    assert cfg.input_json_default_path == "fixtures/sample.json"
    assert cfg.output_dir_default == "out/release-readiness"
    assert cfg.base_ref_env_var == "CUSTOM_BASE_REF"
    assert cfg.enforcement_mode_env_var == "CUSTOM_MODE"


def test_resolve_runtime_defaults_uses_configured_env_names(monkeypatch):
    cfg = RuntimeConfig(
        base_ref_env_var="CUSTOM_BASE_REF",
        enforcement_mode_env_var="CUSTOM_MODE",
        output_dir_default="out/default",
        input_json_default_path="fixtures/default.json",
    )
    monkeypatch.setenv("CUSTOM_BASE_REF", "origin/release")
    monkeypatch.setenv("CUSTOM_MODE", "block")

    defaults = resolve_runtime_defaults(cfg)
    assert defaults["base_ref"] == "origin/release"
    assert defaults["enforcement_mode"] == "block"
    assert defaults["output_dir"] == "out/default"
    assert defaults["input_json_default_path"] == "fixtures/default.json"
