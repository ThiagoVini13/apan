from scripts.export_openapi import OUTPUT, render


def test_versioned_openapi_matches_the_code() -> None:
    assert OUTPUT.read_text(encoding="utf-8") == render(), (
        "The API changed: run `uv run python -m scripts.export_openapi` and regenerate "
        "the frontend types (`npm run api:types`)."
    )
