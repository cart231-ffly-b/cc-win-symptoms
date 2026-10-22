# cc-win-symptoms

Windows で Claude Code やスクリプトを自動で回すと「エラーなしで壊れる」症状を、1つ1ページ（日英）にした静的サイト。困って症状を検索した人が着く入口。中身はすべて `traps.py` 1本から作る。

## 開く

```powershell
python build.py
python -m http.server 8080 -d docs
```

→ http://127.0.0.1:8080/ja/index.html （英語は /en/index.html）

## 確かめる

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\check.ps1            # 全部（claude を3回呼ぶ、約1分半）
powershell -NoProfile -ExecutionPolicy Bypass -File .\check.ps1 -SkipClaude -SkipSlow
```

- `check_links.py`: ページ数（37）、相対リンク切れ、title と description、ハングルの混入
- 各ページの「30秒で確かめる」のコードを、読者と同じく `-File` で実際に流し、最後の行が `REPRODUCED` になるか（作者の PC では17件すべて）。既定のコンソールのコードページで流す（65001 だと t05・t09 が隠れる）

- `check-paste.ps1`: 同じコードを `powershell -Command -` に1行ずつ流す（読者が画面に貼るのに近い形）。2026-10-22 に15件 REPRODUCED（t13 は外した）。直した環境（$OutputEncoding・[Console]::OutputEncoding・PYTHONIOENCODING を UTF-8、単一引用符）では t04/t05/t06/t12 が NOT REPRODUCED に変わることも確認

### 判定の3つ目「CANNOT CHECK」（2026-10-22、相談役の指摘で足した）

- python を使う t04/t05/t06/t07/t13 は、最初に python の版を出す。python が無い・ストアの偽物（何も出さず 9009）なら `CANNOT CHECK`。以前は偽物でも t05/t06 が REPRODUCED と誤って出た。偽物と同じ動きの `python.cmd`（`exit /b 9009`）と、python の無い PATH の両方で `CANNOT CHECK` を確かめた
- t06/t07 は終了コードだけでなく `UnicodeEncodeError` の文字で決める
- h01/h02 はフックが最初に印のファイルを作り、「印がある かつ 書き込まれた」で REPRODUCED。`disableAllHooks` を足した設定で `CANNOT CHECK`（hook called=False）になることを確かめた
- **Python 3.15（2026-10-09 公開、python.org のリリースページで確認）は UTF-8 が既定（PEP 686）。** 3.15 では t06/t07 は起きない見込み。手元は 3.13.7 なので、代わりに `-X utf8` で流して t06/t07 の形が落ちない（exit 0）ことだけ確かめた
- **英語版の Windows（437/1252）の実機では流していない。** check.ps1 が切り替えるのは OEM のコードページだけで、ANSI（t06・t08 に効く）は変えられない

## 直すとき

`traps.py` を直して `python build.py`。`docs/` と `checks/` は生成物なので手で直さない（ただし GitHub Pages が `docs/` を配るので、生成後の `docs/` はコミットする）。確かめるコードは ASCII だけ（build.py が止める）。

## 公開（本人）

1. GitHub に `cc-win-symptoms` を作り、`git -C C:/Users/kosoh/cc-win-symptoms push`
2. Settings → Pages → Branch `main`、フォルダ `/docs`
3. URL は `https://cart231-ffly-b.github.io/cc-win-symptoms/` を仮定している（`build.py` の `BASE`。違ったら直して build）

**今すぐ公開してよい（2026-10-23 に変更）。** cc-win-traps は公開済み、Payhip の支払いは 10-22 から通る。日本語のページから張る note の記事（14か所 10-29・キット 10-31・旗艦2 11-05）は、`build.py` が**作った日の日付**で切り替える。公開前は cc-win-traps と Payhip の英語版に張り、リンク切れを出さない（`JA_NOTE`）。

- **10-29・10-31・11-05 の各日に** `python build.py; python check_links.py` → `docs/` をコミット → push。やらないと日本語のページは古い行き先のまま（切れはしない）
- ある日の見た目を確かめる: `BUILD_DATE=2026-11-05 python build.py`（確かめたら日付なしでもう一度 build して戻す）

以前は「11-05 以降に公開」としていた。理由は note の記事へのリンク切れと、Payhip の支払いが通らないことだった（10-22 に解決）。
