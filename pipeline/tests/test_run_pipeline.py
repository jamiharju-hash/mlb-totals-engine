import pytest

from pipeline.src import run_pipeline as rp


def test_check_env_missing(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "x")
    monkeypatch.setenv("PIPELINE_INGEST_SECRET", "x")
    with pytest.raises(rp.ConfigError):
        rp.check_env()


def test_check_env_ok(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "http://x")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "x")
    monkeypatch.setenv("PIPELINE_INGEST_SECRET", "x")
    rp.check_env()


def test_hard_abort_chadwick(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "http://x")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "x")
    monkeypatch.setenv("PIPELINE_INGEST_SECRET", "x")
    monkeypatch.setattr(rp, "init_pipeline_run", lambda dry_run=False: 1)
    monkeypatch.setattr(rp, "update_pipeline_run", lambda *a, **k: None)
    monkeypatch.setattr(rp, "get_crosswalk", lambda: (_ for _ in ()).throw(rp.QualityCheckError("bad")))
    with pytest.raises(rp.PipelineAbortError):
        rp.run_pipeline(dry_run=True)


def test_soft_failure_retrosheet(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "http://x")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "x")
    monkeypatch.setenv("PIPELINE_INGEST_SECRET", "x")
    monkeypatch.setattr(rp, "init_pipeline_run", lambda dry_run=False: 1)
    monkeypatch.setattr(rp, "update_pipeline_run", lambda *a, **k: None)
    monkeypatch.setattr(rp, "get_crosswalk", lambda: {"ok": True})
    monkeypatch.setattr(rp, "load_seasons", lambda **k: (_ for _ in ()).throw(Exception("nope")))
    out = rp.run_pipeline(dry_run=True)
    assert "retrosheet" in out["sources_failed"]


def test_dry_run_no_upsert(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "http://x")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "x")
    monkeypatch.setenv("PIPELINE_INGEST_SECRET", "x")
    monkeypatch.setattr(rp, "init_pipeline_run", lambda dry_run=False: 1)
    monkeypatch.setattr(rp, "update_pipeline_run", lambda *a, **k: None)

    class Dummy:
        def table(self, *_):
            raise AssertionError("upsert should not be called in dry run")

    monkeypatch.setattr(rp, "_supabase_client", lambda: Dummy())
    rp.run_pipeline(dry_run=True)
