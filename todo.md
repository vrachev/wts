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
