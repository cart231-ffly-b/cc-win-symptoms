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

- `check_links.py`: ページ数（35）、相対リンク切れ、title と description、ハングルの混入
- 各ページの「30秒で確かめる」のコードを、読者と同じく `-File` で実際に流し、最後の行が `REPRODUCED` になるか（作者の PC では16件すべて）。既定のコンソールのコードページで流す（65001 だと t05・t09 が隠れる）

## 直すとき

`traps.py` を直して `python build.py`。`docs/` と `checks/` は生成物なので手で直さない（ただし GitHub Pages が `docs/` を配るので、生成後の `docs/` はコミットする）。確かめるコードは ASCII だけ（build.py が止める）。

## 公開（本人）

1. GitHub に `cc-win-symptoms` を作り、`git -C C:/Users/kosoh/cc-win-symptoms push`
2. Settings → Pages → Branch `main`、フォルダ `/docs`
3. URL は `https://cart231-ffly-b.github.io/cc-win-symptoms/` を仮定している（`build.py` の `BASE`。違ったら直して build）

**公開はリンク先の記事が出た後（11-05 以降）。** ページから note の 14か所（10-29）・キット（10-31）・旗艦2（11-05）と、GitHub の cc-win-traps（未公開）に張っている。
