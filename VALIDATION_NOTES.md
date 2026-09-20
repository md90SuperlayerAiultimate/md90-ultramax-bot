# Validation notes

- Mobile Overview screenshot at 390x844: compact topbar, menu trigger, hero, operation mode, and metric cards remain visible without horizontal overflow in the captured viewport.
- Mobile Signal Room screenshot at 390x844: breadcrumb, title, locked-live badge, primary signal, score, and chart remain readable.
- Keyboard Tab action on Signal Room completed without runtime error; page remains rendered with Ringkasan link and Workspace language control exposed as interactive elements.
- Automated validation currently: TypeScript passes; 21 Vitest tests pass across 9 files. Live execution remains locked.
Overview keyboard audit: DOM scan found 46 focusable interactive elements and 1 unlabeled element; the first ten focus targets include Close navigation, Overview, Signal room, Market map, Risk lab, Replay, BTC, ETH, SOL, and Analyst workspace with visible text or aria labels. News entries visibly expose FRESH/STALE and SHADOW/PENDING_REVIEW states.
Signal Room keyboard audit: DOM scan found 2 focusable interactive elements in the rendered detail route (Ringkasan and Workspace: ID), with 0 unlabeled elements. This route is intentionally read-only and exposes no order controls. Overview and Signal Room mobile screenshots remain readable at 390x844.
Post-fix Overview keyboard audit: unlabeled interactive count is now 0 across 46 elements. Programmatic focus succeeded for 44 elements; 2 hidden/conditional targets did not accept focus in the current desktop state, indicating they should be excluded from the active tab order or validated only when their mobile/conditional state is open. Visible primary controls show solid outline focus styling.
Final Overview keyboard audit after conditional tabIndex fix: 44 visible focusable interactive elements, 0 unlabeled elements, 0 focus failures, and 44 elements report solid outline focus styling when focused programmatically. Hidden conditional controls are excluded from the active desktop tab order.
