# 教材ライブラリ

技術の全体像から基本設計まで学ぶ日本語教材です。ビルド不要の静的HTMLで構成します。

## 公開先

配置後のURLです。今回のローカル変更はまだpushしていません。

- 教材一覧: https://ta-yokoi.github.io/android-learning-guide/
- Android: https://ta-yokoi.github.io/android-learning-guide/android/
- 組み込み開発: https://ta-yokoi.github.io/android-learning-guide/embedded/

## 構成

```
index.html           # 教材一覧
android/index.html   # Android（30章・図38点・78問）
embedded/index.html  # 組み込み開発（13章・図21点・52問・用語85語）
.nojekyll
```

各教材はCSS・SVG・JavaScriptを内包するHTMLです。外部のスクリプト・画像・フォントは不要です。
出典のリンク先を開く場合はインターネット接続が必要です。

## 公開と追加

GitHub Pagesの公開元がmainブランチの/(root)なら、この構成をリポジトリ直下へ配置してpushします。
Pagesのビルド・公開に成功した後にサイトへ反映されます。
github-pagesという親フォルダ自体はアップロードしません。ZIPを使う場合は中身を配置します。
新ジャンルは<genre>/index.htmlを追加し、教材一覧へ相対リンクのカードを追加します。

## 読了記録

Androidはandroid16-learning-guide-completed-v1、組み込み開発はembedded-learning-guide-completed-v1を使います。
同じブラウザ・公開元のlocalStorageに保存し、教材ごとの記録を分離します。
端末間・ブラウザ間では同期しません。保存できない環境では閲覧中のみ保持します。

## 確認範囲

HTML構造・リンク・図・操作ロジックとPC向けコードを検証しました。
実ブラウザ・実スマートフォンでの表示、実機・BSP・電気信号・電源・更新動作は別途確認が必要です。
教材本文と巻末に適用条件・未検証の範囲を記載しています。
コミット・push・公開確認は別途実施します。
