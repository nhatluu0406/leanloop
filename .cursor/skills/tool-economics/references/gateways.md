# Gateway pattern — optional reference

A code-execution or integration gateway can be worthwhile when one narrow interface replaces many always-loaded integration schemas. The benefit is environment-specific: measure startup/context cost and task success before adopting it.

## Safety rules

- LeanLoop does not auto-clone or execute a gateway repository.
- Audit source and permissions first; pin an exact commit or release in your own adoption record.
- Give the gateway only the credentials/scopes required for the task.
- Prefer direct CLI/API calls when they are simpler and equally capable.
- Remove the gateway if measurement does not show a net benefit.

`TOOLS.md` is the policy source; do not treat a third-party gateway as a default dependency.
