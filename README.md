# 隨峰而趣 Rayfong's Travelogue

旅運系老師的筆記本：方格子與 Facebook 文章的個人網站，用 GitHub Pages 架設。

- 網站（中文版，首頁打開先看 HELLO）：https://d11522303.github.io/ray-site/
- 英文版：https://d11522303.github.io/ray-site/en/
- 後台：https://d11522303.github.io/ray-site/admin/

## 用後台更新文章

1. 打開後台網址，選「Sign In Using Access Token」（用金鑰登入）。
2. 金鑰的申請方式見下方「第一次使用後台」。
3. 登入後可以：
   - 新增文章：按「新增」，填標題、日期、分類、內文後存檔。
   - 修改文章：點文章，改完按存檔。
   - 隱藏文章：把「公開」關掉再存檔。
   - 加照片：在內文編輯器裡插入圖片。
4. 存檔後大約 1～2 分鐘，網站會自動更新。

### 第一次使用後台：申請金鑰

1. 打開 https://github.com/settings/personal-access-tokens/new
2. Token name 填「網站後台」，Expiration 選一年。
3. Repository access 選「Only select repositories」，再選 `ray-site`。
4. Permissions → Repository permissions → **Contents** 改成 **Read and write**。
5. 按 Generate token，把出現的那串文字複製下來，貼到後台登入畫面。
   這串金鑰等於密碼，不要給別人。

## 資料夾

| 位置 | 內容 |
|---|---|
| `content/articles/` | 所有文章，一篇一個檔案（後台改的就是這裡）。「公開」只控制中文版 |
| `content/en/articles/` | 英文翻譯，檔名和中文文章相同；「published」控制英文版；還沒翻譯的文章只在中文公開時於英文版先顯示中文 |
| `content/en/` | 英文版首頁、關於頁、分類英文名 |
| `src/template.html` | 網站版面、插圖與程式 |
| `admin/` | 後台設定 |
| `images/uploads/` | 後台上傳的照片 |
| `tools/build.py` | 把文章組成網站（GitHub 會自動執行） |
| `tools/import_facebook.py` | 匯入 Facebook 新貼文 |

## 匯入 Facebook 新貼文

Facebook「設定 → 你的資訊 → 下載你的資訊」選 JSON 格式，解壓縮後執行：

```
pip install pyyaml markdown
python tools/import_facebook.py your_posts__check_ins__photos_and_videos_1.json
```

新文章預設「不公開」，到後台「未公開」裡檢查分類後再打開公開。已經存在的文章不會被覆蓋。

分類：證照考試、技職教育、旅行郵輪、每日晨讀、遊戲學習、生活記憶、理財情報、老後提案。
