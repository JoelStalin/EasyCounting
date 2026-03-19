# Known Issues - 2026-03-18

- Local portal Selenium still depends on `pnpm` and a browser binary being installed on the host.
- The mock API covers only the endpoints needed by the current functional flows.
- Full backend integration for portal login is not exercised by these tests.
- Some backend settings suggest SQLite support, but the async URL normalization currently favors `asyncpg`; this makes a pure SQLite local portal stack a separate fix.
- The suite serves the existing `dist/` artifacts; if frontend source changes without rebuilding, Selenium will validate the last compiled bundle, not the latest TSX.
