# Project Instructions

- After every functional code change, create a new portable version in `dist/RecordScreen-vX.Y.Z`.
- Bump `VERSION` before building a new portable release.
- Keep `RELEASES.md` updated with the version, date, and short change summary.
- Run the test suite before calling a portable release complete.

## Work Graph

- Work Graph is a local development tool for this repository and is not part of the RecordScreen runtime or portable build.
- Run the local UI with npm run workgraph:ui at http://localhost:4196/.
- Verify the installation with npm run workgraph:doctor.
- Local and Worktree runners detect the current checkout automatically; do not pin MCP to the primary checkout with an absolute cwd.
- A worktree without node_modules reuses the primary checkout devDependencies for MCP and UI. Run npm ci in that worktree for a fully green doctor.
- Use the workgraph MCP server to read and update work items. Do not edit statuses, test evidence, or service fields in .work.bvc files directly.
- Automatic Git snapshots are disabled. Do not enable them without an explicit user request.
- Work Graph-only changes are development configuration, not a functional application change, and do not require a portable release.

### Automatic work-item lifecycle

- The user describes tasks normally and does not need to manage Work Graph manually.
- Before changing code, tests, documentation, or configuration, reuse a suitable open work item or create and claim one through MCP.
- Record material checks through MCP, run assert_task_ready_for_done, and close the item with complete_work_item.
- Read-only answers do not require a new work item unless the user explicitly asks to record them.
