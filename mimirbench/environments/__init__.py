"""Environment families.

Each subpackage is self-contained and exposes (where implemented) a
``generate_task``, a reference ``solver``, a deterministic ``grade``, and a
``build_spec`` that registers it with the eval runner.

Registered today: ``bayesian_games``, ``auctions``, ``hidden_regimes``.
Scaffolded (primitives only): ``market_making``, ``prediction_markets``,
``adversarial_risk``.
"""
