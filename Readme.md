# TYStream-DiscordBot

🤖 **TYStream-DiscordBot** 是一台 **全中文** 的  Discord 機器人，專為 Twitch & YouTube 直播通知而設計，讓你的社群不再錯過任何精彩直播！

---

## 🚀 功能特色

- ✅ **即時通知**：當指定的 Twitch 或 YouTube 頻道開始直播時，機器人會自動在指定的 Discord 頻道發送通知。  
- ✅ **自訂通知內容**：可自訂通知的頭像、名稱、訊息格式等，使通知更符合你的社群風格。  
- ✅ **多平台支援**：同時支援 Twitch 和 YouTube 直播監測，讓你輕鬆管理所有直播通知。  
- ✅ **基於 [TYStream](https://github.com/Mantouisyummy/TYStream) 開發**：這是由我開發的 Python 套件，專門用來處理 Twitch & YouTube 直播相關功能。  
- ✅ **高效能**: 資料庫使用了 Sqlite + Redis 的結合，讓機器人性能更佳、延遲更低，更即時。

---

## 📌 安裝與設定

### 1️⃣ 安裝機器人

請確保你的環境已安裝 Python 3.10+，然後執行：

```sh
git clone https://github.com/Mantouisyummy/TYStream-DiscordBot.git
cd TYStream-DiscordBot
pip install -r requirements.txt
````

### 2️⃣ 設定環境變數

重命名目錄下的 `example.env` 為 `.env` 並打開檔案，編輯以下的環境變數。

```env
TOKEN= # 機器人令牌
TWITCH_CLIENT_ID= # Twitch 客戶端ID
TWITCH_CLIENT_SECRET= # Twitch 客戶端密碼
YOUTUBE_API_KEY= # Youtube API金鑰
REDIS_HOST= # Redis 主機
REDIS_PORT= # Redis 端口
REDIS_PASSWORD= # Redis 密碼
```

### 3️⃣ 啟動機器人
執行以下指令啟動機器人：
```sh
python main.py
```
大功告成！

***

### ⚙️ 指令教學
待新增...
