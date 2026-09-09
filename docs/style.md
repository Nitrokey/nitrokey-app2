# Style Guide

## Accent

| Role | Light | Dark |
| --- | --- | --- |
| accent fill (primary buttons, checked boxes) | `#c0392b` | `#c0392b` |
| accent fill, hover / pressed | `#a93226` / `#922b21` | `#a93226` / `#922b21` |
| brand red (Nitrokey logo and icons) | `#c80636` | `#c80636` |
| accent text and borders (selected tab, outline buttons) | `#c0392b` | `#ff6b5b` |
| accent tint (selected rows, text selection) | `#fce8e6` | `#3d1f1a` |

## Neutrals

| Role | Light | Dark |
| --- | --- | --- |
| window background | `#f6f8fa` | `#0d1117` |
| surface (cards, inputs, tab bar) | `#ffffff` | `#161b22` |
| hover fill | `#eaeef2` | `#21262d` |
| border | `#d0d7de` | `#30363d` |
| input focus border | `#6e7781` | `#768390` |
| text | `#24292f` | `#c9d1d9` |
| text, muted | `#57606a` | `#8b949e` |
| text, disabled | `#8c959f` | `#6e7681` |

### Dark in both themes

| Role | Light | Dark |
| --- | --- | --- |
| navigation bar background | `#161b22` | `#161b22` |
| navigation bar border | `#30363d` | `#30363d` |
| navigation bar text | `#cdd9e5` | `#c9d1d9` |
| navigation bar text, muted | `#768390` | `#6e7681` |
| log view and tooltip background | `#1c2128` | `#010409` |
| log view and tooltip border | `#444c56` | `#30363d` |
| log view and tooltip text | `#cdd9e5` | `#c9d1d9` |

## Status

| Role | Light | Dark |
| --- | --- | --- |
| error text | `#c0392b` | `#c0392b` |
| success (TOTP countdown) | `#2da44e` | `#3fb950` |
| warning text | `#9a3412` | `#f0b86e` |
| warning fill / border | `#fff7ed` / `#fed7aa` | `#2b2111` / `#6b4a1f` |

## Icons

| Icons | Light | Dark |
| --- | --- | --- |
| `home`, `help`, `warning` | `#c80636` | `#c80636` |
| `red_nitrokey-app-icon` | `#c91735` | `#c91735` |
| `settings`, `save`, `tick`, `OTP_generate` | `#000000` | `#000000` |
| `add_circle`, `info`, `touch` | `#000000`, no `fill` set | `#000000`, no `fill` set |
| `nitrokey` | black and white | black and white |
| all other themed icons | `#000000` | `#8b949e` |
| `delete`, `dialpad`, `dialpad_off` | `#000000` | white |
| app logo | `#c80636`, wordmark `#1d1d1b` | `#c80636`, wordmark `#ffffff` |

Dark mode has three icon colors: gray, white, and black

Most light mode files have no `fill`, so they go back to the SVG default black. `down_arrow`, `right_arrow` and `dialpad_off` hold a bitmap rather than a path (dark versions are recolored with an SVG filter)

Use the same two colors when adding a themed icon: black for light mode, `#8b949e` for dark mode
