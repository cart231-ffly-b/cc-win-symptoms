# PowerShell Gallery への公開

リポジトリのルートで `python build.py` を実行します。公開前に、`CCDoctor.ps1` の `.LICENSEURI` が指す GitHub 上の `LICENSE` を整えてください。現在のリポジトリには `LICENSE` がありません。

本人が `<キー>` を自身の PowerShell Gallery の API キーに置き換えて実行します。

```powershell
Publish-Script -Path gallery/CCDoctor.ps1 -NuGetApiKey <キー>
```

## 公開後のインストールと実行

```powershell
Install-Script CCDoctor
CCDoctor.ps1
```
