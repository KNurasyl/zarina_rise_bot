# Zarina Rise Mini App UI Audit

## Проблемы до правки

- Визуальная система была слишком светлой и pastel-heavy: cards, pills, nav и inputs часто сливались с фоном.
- Светлые controls местами наследовали неподходящий цвет текста.
- Bottom navigation и support chips выглядели бледно и выбивались из общей системы.
- Journal form, progress rows и Settings states не имели единой логики dark/light surfaces.
- Блок "От Нурасыла" не был достаточно отделён от остальных карточек.

## Новая тема

Тема: **Warm Plum Rose Theme**.

- Base background: `--zr-bg #2f2230`, `--zr-bg-2 #3a2a39`, `--zr-bg-3 #453341`
- Dark surfaces: `--zr-surface-card rgba(82, 63, 76, 0.92)`, `--zr-surface-elevated rgba(96, 74, 88, 0.96)`
- Light controls: `--zr-light-surface #eadfdc`, `--zr-light-surface-2 #f2e9e5`
- Text on dark: `--zr-text #fff6ef`, `--zr-text-muted #d9c6c8`
- Text on light: `--zr-text-dark #3a2632`, `--zr-text-dark-muted #7a5c68`
- Accents: `--zr-rose #d69a84`, `--zr-rose-dark #b87968`, `--zr-gold #e7b86a`, `--zr-lavender #b8a7d9`
- Success: muted sage, not bright green.

## Исправленные компоненты

- Cards: плотные dark plum surfaces с readable ivory text.
- Inputs/selects/textarea: light surfaces with dark plum text and readable placeholders.
- Primary buttons: rose-gold gradient with white text only on saturated accent.
- Secondary/soft buttons: light surfaces with dark text and rose icons.
- Support chips: light surface + dark muted text; active state uses soft sage.
- Nurasyl card: separate rose/lavender overlay on elevated plum card.
- Progress bars: dark track with rose-gold fill; progress rows use light surface with dark text.
- Settings rows: inactive dark readable rows; active rows use muted sage.
- Bottom nav: light surface with dark muted inactive text and rose active state.
- Home: hero removed from main screen; first content is today's action card.
- Mood flow: отдельный чек-ин с читаемыми карточками состояний и optional note.
- Today: support actions открывают Focus/Mood/Journal flows вместо случайного toggle-поведения.

## Проверенные экраны

- Home
- Today
- Journal
- Progress
- Settings
- Focus flow
- Pause flow
- Mood flow
- Outside Telegram fallback

## Known limitations

- Browser visual QA for real data requires Telegram `initData`; for visual screenshots a temporary local mock was used and removed after verification.
- Google Fonts loading depends on network availability; CSS keeps system fallbacks.
