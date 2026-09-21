from pathlib import Path

from vrcpresence.config import Config
from vrcpresence.engine import Engine
from vrcpresence.history import History
from vrcpresence.log_watcher import LogWatcher

FIXTURES = Path(__file__).parent / "fixtures"


def test_history_records_visit_and_players(tmp_path):
    history = History(tmp_path / "h.db")
    history.start_visit("wrld_a", "1", "Black Cat")
    history.record_player("Kettle")
    history.record_peak(3)
    history.end_visit()

    visits = history.recent_visits()
    assert len(visits) == 1
    assert visits[0].world_name == "Black Cat"
    assert visits[0].peak_players == 3
    assert visits[0].duration_seconds is not None
    assert history.people_met() == [("Kettle", 1)]
    history.close()


def test_history_starting_a_visit_closes_the_previous(tmp_path):
    history = History(tmp_path / "h.db")
    history.start_visit("wrld_a", "1", "A")
    history.start_visit("wrld_b", "2", "B")

    visits = history.recent_visits()
    assert len(visits) == 2
    closed = next(v for v in visits if v.world_name == "A")
    assert closed.left_at is not None
    history.close()


def test_history_totals(tmp_path):
    history = History(tmp_path / "h.db")
    history.start_visit("wrld_a", "1", "A")
    history.record_player("Kettle")
    history.end_visit()
    history.start_visit("wrld_a", "2", "A again")
    history.end_visit()

    totals = history.totals()
    assert totals["visits"] == 2
    assert totals["unique_worlds"] == 1
    assert totals["people_met"] == 1
    history.close()


def _engine_for(tmp_path, log_body: str) -> Engine:
    log = tmp_path / "output_log_00.txt"
    log.write_text(log_body)

    config = Config(
        discord_enabled=False,
        chatbox_enabled=False,
        notifications_enabled=False,
        history_enabled=False,
    )
    return Engine(config, log_watcher=LogWatcher(log_dir=tmp_path))


def test_engine_tick_updates_state(tmp_path):
    engine = _engine_for(tmp_path, (FIXTURES / "session.log").read_text())
    engine.tick()

    assert engine.state.world_name == "The Great Pug"
    assert engine.state.player_count == 2
    assert engine.status.log_found


def test_engine_tokens_for_chatbox(tmp_path):
    engine = _engine_for(tmp_path, (FIXTURES / "session.log").read_text())
    engine.tick()

    tokens = engine.chatbox_tokens()
    assert tokens["world"] == "The Great Pug"
    assert tokens["players"] == "2"
    assert tokens["mode"] == "Desktop"


def test_engine_tick_with_no_log_is_harmless(tmp_path):
    engine = _engine_for(tmp_path, "")
    assert engine.tick() == []
    assert not engine.state.in_world
