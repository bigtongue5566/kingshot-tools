# Player-name audit

Use this guide only when the request asks for Chinese, Taiwanese, or language-community signals from player names.

## Core boundary

A name is evidence about the visible name, not verified nationality, residence, language ability, or identity. Report all counts as a lower bound from public names.

By default, use only `player`. Do not use `alliance`, alliance abbreviations, alliance member concentration, kingdom chat assumptions, or a `TW` alliance tag as individual evidence. If the user explicitly asks for alliance analysis, present it in a separate section and never merge it into the player-name classification.

## Suggested codes

| Code | Meaning | Direct list | Guidance |
|---|---|---:|---|
| T | Explicit Taiwan or strong Taiwan-language name signal | Yes | Player name contains 台灣／臺灣／Taiwan／standalone TW／Taiwan flag, or a manually verified Taiwanese expression. |
| Z | Clear Chinese-language Han name | Yes | At least two substantive Han characters with understandable Chinese-language content and no stronger Japanese/Korean context. |
| B | Bopomofo or Taiwan input signal | Usually yes | Review manually; Bopomofo-shaped decorative Latin substitutions are false positives. |
| H | Single Han character or cross-language Han ambiguity | No | Keep as a low-confidence candidate unless additional player-name evidence exists. |
| R | Romanized Chinese candidate | No | `Lin`, `Ming`, `Wei`, and similar forms are highly ambiguous. Do not add them to the direct count. |
| J | Japanese or anime-name context | No | Kana, Japanese names, or clearly Japanese lexical context. This still does not prove nationality. |
| E | Korean or other East Asian script context | No | Hangul or another stronger non-Chinese name signal. |
| D | Pseudo-CJK decoration | No | Stylized Latin letters, repeated radicals, clan wrappers, or decorative glyphs. |
| N | No visible Chinese-language signal | No | Do not describe the person as non-Chinese; the name is simply uninformative. |

## Manual review set

Review every row containing any of these before finalizing:

- Han characters, Bopomofo, standalone `TW`, `Taiwan`, `Formosa`, or a Taiwan flag.
- Kana, Hangul, or mixed Han plus Japanese/Korean script.
- CJK compatibility glyphs, pseudo-CJK styled Latin letters, repeated radicals, or shared decorative wrappers.
- Romanized names proposed as Chinese candidates.
- Every row ultimately included in the direct list.

Normalize Unicode with NFKC for matching, but preserve the original visible name in output. Strip only verified decorative wrappers for analysis; never mutate the displayed name.

## Required audit columns

```text
kingdom,local_mystic_rank,transfer_group_rank,player,mystic,power,
judgment_code,judgment,confidence,reason,direct_chinese_name,snapshot_date
```

An alliance column may exist for locating the player, but it must never be cited as affirmative evidence or determine `direct_chinese_name`. A reason may describe a wrapper inside the visible player name only when the remaining name evidence is stated explicitly.

## Quality check

- Every input player has exactly one audit row.
- Every direct row has a concrete player-name reason and confidence.
- Low-confidence rows do not inflate direct counts.
- Japanese/Korean and decorative false positives were reviewed, not excluded solely by a broad Unicode range.
- The report states that English-named Chinese-speaking players remain undetectable.
