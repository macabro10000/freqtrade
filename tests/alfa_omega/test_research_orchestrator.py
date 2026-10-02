from alfa_omega.research.research_orchestrator import (
    create_run,
    plan_research_tasks,
)


def test_research_plan_is_deterministic_and_covers_context():
    tasks = plan_research_tasks(
        markets=("BTC/USD",),
        timeframes=("5m",),
        sessions=("LONDON", "NEW_YORK"),
        regimes=("TREND",),
        topics=("SESSION_EFFECT", "FAILURE_ANALYSIS"),
    )
    assert len(tasks) == 4
    assert len({task.task_id for task in tasks}) == 4
    assert {task.session for task in tasks} == {"LONDON", "NEW_YORK"}
    run = create_run(tasks)
    assert run.status == "PLANNED"
    assert run.task_ids == tuple(task.task_id for task in tasks)
