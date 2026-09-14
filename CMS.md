# Telegram Question CMS

The bot now has a database-backed question CMS for Big Five, RIASEC, Child/Future tests and Premium IQ.

## Admin

Send `/admin` as an administrator. The panel lists the administrative commands, including:

- `/admin` — admin panel
- `/cms` — question CMS
- `/walletadjust USER_ID AMOUNT [note]` — change a wallet balance
- `/adjustwallet USER_ID AMOUNT [note]` — alias for `/walletadjust`
- `/user USER_ID` — user/wallet management
- `/iqprice` — Premium IQ price

## CMS workflow

1. Open **📝 Savollar CMS**.
2. Select a test.
3. Open a question.
4. Edit Uzbek/Russian text, five answer options, correct answer, category, difficulty or image URL.
5. Toggle a question off when it should not be shown.
6. Delete obsolete questions.
7. Use **➕ Yangi savol** to add a bilingual question.
8. Changes are applied immediately to the running in-memory test registry.

For IQ, `correct_index` is zero-based (0–4). For Big Five/RIASEC, the score is based on the selected 1–5 position; the correct-index field is not used by the personality/career scorer.

## Database structure

The CMS adds `cms_questions` to the existing SQLite database:

| Column | Purpose |
|---|---|
| `id` | Stable question ID used by the Telegram CMS |
| `test_key` | `bigfive`, `career`, `child`, `future` or `iq` |
| `position` | Display/order position inside a test |
| `category` | Trait/scale for psych tests or reasoning category for IQ |
| `difficulty` | 1–5 progressive difficulty |
| `enabled` | 1 = active, 0 = hidden |
| `reverse` | Reverse-scored personality item |
| `kind` | Likert/question response mode |
| `text_uz` | Uzbek question |
| `text_ru` | Russian question |
| `options_uz` | JSON array of five Uzbek options |
| `options_ru` | JSON array of five Russian options |
| `correct_index` | Correct IQ option, 0–4 |
| `image_url` | Optional visual/puzzle image URL |
| `created_at` / `updated_at` | Audit timestamps |

The first startup automatically seeds this table from the existing test definitions, so existing content continues to work without manual data entry.

## Deployment

No new Python package is required: the project already uses `aiosqlite`. On startup, `content_cms.init()` creates/seeds the CMS table and `content_cms.apply_all()` applies active content before polling starts.

If Railway is already connected to the same persistent SQLite volume, restart/redeploy the service once after pulling these changes. The CMS data then lives in the same database configured by `DB_PATH`.

## Image note

Telegram inline keyboard buttons cannot contain arbitrary image thumbnails. The CMS therefore stores an image URL and the question card exposes an **open image** link. A full visual-answer grid requires a separate Telegram media-message flow (photo/media group + answer callbacks), while the CMS/data layer is already prepared for `image_url`.
