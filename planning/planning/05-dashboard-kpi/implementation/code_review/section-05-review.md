# Code Review: section-05-readonly-schedule

## Summary

Well-structured read-only schedule component using React.memo, useMemo, and proper interval cleanup. Four real issues were identified and fixed; remaining findings were let go or are by design.

## Findings

### Fixed

| Issue | Resolution |
|-------|-----------|
| `now` frozen at mount — activeBlockId never updates | Added 60s interval to parent, same pattern as NowIndicator |
| NowIndicator boundary: `> endHour*60` inconsistent with exclusive-end convention | Changed to `>= endHour * 60` |
| Auto-scroll useEffect missing prop deps | Changed to `[startHour, endHour, hourHeight]`; effect reads `new Date()` internally to avoid `now` dep |
| `timeToMinutes` called twice per block in useMemo | Pre-compute `startMin`/`endMin` in a single `.map()` before `.filter()`/`.reduce()` |

### Let Go

- Zero-duration block guard — data integrity concern for the API layer, not this component
- Full ARIA role/label on blocks — not in spec for this read-only summary view
- NowIndicator scrolls with content — by design per spec's max-height reasoning
- Arrow character `→` as Unicode literal — acceptable in JSX
- `?date=` query param name — verified as matching calendar page usage in existing CurrentTaskKpi tests

## Interview Transcript

**Q: Active highlight frozen at mount — fix?**
A: Add 60s interval to parent. Accepted.

**Q: Auto-scroll useEffect empty deps — fix?**
A: Add prop deps, scroll only once. Accepted.
