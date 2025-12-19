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

## Environment Variables
- `WTS_TERMINAL_MODE`: `split` (default), `tab`, or `cd`
- `WTS_TERMINAL_SPLIT`: `vertical` (default) or `horizontal`

## iTerm2

### Split (default)
- [ ] Vertical split (default): `wts create test-iterm-vsplit -t` → vertical split
- [ ] Horizontal split: `WTS_TERMINAL_SPLIT=horizontal wts create test-iterm-hsplit -t` → horizontal split

### Tab
- [ ] Tab mode: `WTS_TERMINAL_MODE=tab wts create test-iterm-tab -t` → new tab

### CD (no new pane)
- [ ] CD mode: `WTS_TERMINAL_MODE=cd wts create test-iterm-cd -t` → cd in current terminal

## tmux

### Split (default)
- [ ] Vertical split (default): `wts create test-tmux-vsplit -t` → vertical split (panes side by side)
- [ ] Horizontal split: `WTS_TERMINAL_SPLIT=horizontal wts create test-tmux-hsplit -t` → horizontal split (panes stacked)

### Tab (window)
- [ ] Tab mode: `WTS_TERMINAL_MODE=tab wts create test-tmux-tab -t` → new window

### CD (no new pane)
- [ ] CD mode: `WTS_TERMINAL_MODE=cd wts create test-tmux-cd -t` → cd in current pane

## Terminal.app
- [ ] From Terminal.app: `wts create test-terminal -t` → new window (no split support)

## Warp
- [ ] From Warp: `wts create test-warp -t` → new window (no split support)

## Cleanup
```bash
wts delete test-iterm-vsplit
wts delete test-iterm-hsplit
wts delete test-iterm-tab
wts delete test-iterm-cd
wts delete test-tmux-vsplit
wts delete test-tmux-hsplit
wts delete test-tmux-tab
wts delete test-tmux-cd
wts delete test-terminal
wts delete test-warp
```

-- 

* command line autocomplete
