# TODO

## --editor flag improvements

### UX: Remove need for `--editor=default`
- [ ] Current: `wts create foo --editor=default` or `wts create foo --editor=cursor`
- [ ] Ideal: `wts create foo --editor` (uses WTS_EDITOR) or `wts create foo --editor=cursor`
- [ ] Options to explore:
  - Click callback that handles missing value
  - Custom Click parameter type
  - `--editor` as flag + separate `--editor-name` option

### Better terminal output
- [ ] Show which editor is being opened: `Opening in cursor...`
- [ ] Show helpful message if editor command fails (e.g., "cursor not found in PATH")
- [ ] Consider: show WTS_EDITOR value when using default

---

# --terminal flag manual tests

## iTerm2
- [ ] From iTerm2: `wts create test-iterm -t` → opens new tab in iTerm2
- [ ] With override: `WTS_TERMINAL=terminal wts create test-override -t` → opens Terminal.app

## Terminal.app
- [ ] From Terminal.app: `wts create test-terminal -t` → opens new tab in Terminal.app

## tmux
- [ ] From tmux: `wts create test-tmux -t` → creates new tmux window
- [ ] With override: `WTS_TERMINAL=iterm2 wts create test-tmux-override -t` → opens iTerm2 tab

## Warp
- [ ] From Warp: `wts create test-warp -t` → opens new Warp window

## Cleanup
```bash
wts delete test-iterm
wts delete test-override
wts delete test-terminal
wts delete test-tmux
wts delete test-tmux-override
wts delete test-warp
```
