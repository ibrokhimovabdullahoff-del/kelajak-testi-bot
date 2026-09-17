# Telegram Question CMS

The bot has a database-backed question CMS for Big Five, RIASEC, Child and Future tests.
The **Premium IQ test is not in the CMS**: its questions are images (`assets/iq/`) and the
answer key lives in code (`psytests/iq.py`).

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
4. Edit Uzbek/Russian text, the five answer buttons, category or image URL.
5. Toggle a question off when it should not be shown.
6. Delete obsolete questions.
7. Use **➕ Yangi savol** to add a bilingual question.
8. Changes are applied immediately to the running in-memory test registry.

**If you change a question's meaning, check its five answer buttons too.** The buttons
repeat the question's verb ("Ko‘pincha jonlanadi"), so they are stored per question and do
not update automatically when only the question text is edited.

## Database structure

| Column | Purpose |
|---|---|
| `id` | Stable question ID used by the Telegram CMS |
| `test_key` | `bigfive`, `career`, `child` or `future` |
| `position` | Display/order position inside a test |
| `category` | Trait/scale the answer is scored on |
| `difficulty` | Unused by the psychological tests |
| `enabled` | 1 = active, 0 = hidden |
| `reverse` | Reverse-scored item |
| `kind` | Answer template: `freq`, `deg`, `yesno`, `agree`, `interest`, `custom` |
| `text_uz` / `text_ru` | Question text |
| `options_uz` / `options_ru` | JSON array of the five answer buttons |
| `correct_index` | Unused (legacy text IQ) |
| `image_url` | Optional image link shown under the question |
| `created_at` / `updated_at` | Audit timestamps |

## Content versions and migration

The live bot reads questions **from this table, not from the code**. To change question wording:

1. Make sure `psytests/cms_seed_v<CONTENT_VERSION>.json` exists (`python content_cms.py snapshot`
   writes it from the current code — do this *before* editing questions).
2. Edit the questions in `psytests/*.py`.
3. Bump `CONTENT_VERSION` in `content_cms.py`.

On the next startup:

- a test whose rows are still exactly as first seeded is replaced with the new questions
  (including their answer buttons);
- a test an admin has edited through the CMS is **left untouched** and a warning is logged;
- legacy text IQ rows are removed.

Version 1 → 2 (September 2026): clearer questions, "Bilmayman" middle answer replaced with
"Ba’zan"/"O‘rtacha", number buttons for count questions, answer buttons stored per question
(fixes buttons like "Ha," that showed without a verb). `contenttest.py` covers this migration.

## Deployment

No new Python package is required. On startup `content_cms.init()` creates/seeds/migrates the
table and `content_cms.apply_all()` applies active content before polling starts.
