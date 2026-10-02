# SMU evaluation

This candidate includes the develop integration and interface template mappings
for the Engineering SMU schema. It does not support the earlier template schema
or automatically detect the installed SMU. Public YAML option names are unchanged.

For initial NaC evaluation:

- Pin the collection to an exact commit and verify the loaded collection path.
- Use a dedicated lab with the matching SMU templates.
- Evaluate `merged` and `query`; check which states the NaC workflow invokes.
- Keep `replaced` and `overridden` outside this initial evaluation.
- Use `deleted` only for explicitly selected, disposable test objects with a
  reviewed recovery plan. Never use an empty selection for cleanup.

The registry contains 228 bindings and 70 registered withdrawal values. Those
70 retain historical acceptance; they have not all been revalidated on the SMU.
Bounded SMU live checks cover selected paths, not the entire registry. Withdrawal
development and validation remain in progress.

Explicit `enable_vpc_peer_link` on `int_port_channel_trunk_host` is rejected:
the corresponding input is absent from the reviewed SMU template.

When reporting a failure, include the collection commit, installed SMU/template
version, state, sanitized model, and expected versus observed behavior. Do not
attach credentials or unredacted controller/device captures.
