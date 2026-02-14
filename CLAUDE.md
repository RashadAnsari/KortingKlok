# Claude Code Instructions

## On Every Session

Before completing work, always perform these checks:

1. **Database indexes** — Review all backend queries. Add missing indexes. Remove redundant indexes (e.g., those already covered by `unique_together` or composite indexes).
2. **Unused translations** — Remove unused translation keys from both the mobile app (`mobile/lib/l10n/`) and the backend.
3. **Unnecessary comments** — Remove unnecessary or obvious comments from both mobile and backend code.
4. **Unused code** — Remove dead/unreachable code from both mobile and backend.
5. **Client error handling** — Ensure all API calls in the mobile app have proper error handling (ErrorView with retry, SnackBar with retry, or try/catch).
6. **Debug logs** — Remove all `debugPrint`, `print`, or `log` statements that were added for debugging purposes. Production code should not have debug output.
