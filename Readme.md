# TYStream-DiscordBot

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/Mantouisyummy/TYStream-DiscordBot">
    <img src="img/logo.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">TYStream</h3>
  <p align="center">
    一台全中文的 Discord 機器人，專為 Twitch & YouTube 直播通知而設計，讓你的社群不再錯過任何精彩直播！
    <br />
    <a href="#install-setup"><strong>閱讀更多 »</strong></a>
    <br />
    <br />
    <a href="https://discord.com/oauth2/authorize?client_id=1267467138839613553">邀請機器人</a>
    ·
    <a href="https://github.com/Mantouisyummy/TYStream-DiscordBot">回報問題</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>目錄</summary>
  <ol>
    <li><a href="#features">功能特色</a></li>
    <li><a href="#install-setup">安裝與設定</a></li>
    <li><a href="#install-bot">安裝機器人</a></li>
    <li><a href="#setting-env">設定環境變數</a></li>
    <li><a href="#run-bot">啟動機器人</a></li>
    <li><a href="#tutorial">指令教學</a></li>
  </ol>
</details>


---

## 🚀 功能特色
<a id="features"></a>

- ✅ **即時通知**：當指定的 Twitch 或 YouTube 頻道開始直播時，機器人會自動在指定的 Discord 頻道發送通知。  
- ✅ **自訂通知內容**：可自訂通知的頭像、名稱、訊息格式等，使通知更符合你的社群風格。  
- ✅ **多平台支援**：同時支援 Twitch 和 YouTube 直播監測，讓你輕鬆管理所有直播通知。  
- ✅ **基於 [TYStream](https://github.com/Mantouisyummy/TYStream) 開發**：這是由我開發的 Python 套件，專門用來處理 Twitch & YouTube 直播相關功能。  
- ✅ **高效能**: 資料庫使用了 SQLite + Redis 的結合，讓機器人性能更佳、延遲更低，更即時。

---

## 📌 安裝與設定
<a id="install-setup"></a>

### 1️⃣ 安裝機器人
<a id="install-bot"></a>

請確保你的環境已安裝 Python 3.10+，然後執行：

```sh
git clone https://github.com/Mantouisyummy/TYStream-DiscordBot.git
cd TYStream-DiscordBot
pip install -r requirements.txt
````

### 2️⃣ 設定環境變數
<a id="setting-env"></a>

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
<a id="run-bot"></a>
執行以下指令啟動機器人：
```sh
python main.py
```
大功告成！

***

### ⚙️ 指令教學
<a id="tutorial"></a>
待新增...

<!-- SHIELDS -->

[contributors-shield]: https://img.shields.io/github/contributors/Mantouisyummy/TYStream-DiscordBot.svg?style=for-the-badge

[contributors-url]: https://github.com/Mantouisyummy/TYStream-DiscordBot/graphs/contributors

[forks-shield]: https://img.shields.io/github/forks/Mantouisyummy/TYStream-DiscordBot.svg?style=for-the-badge

[forks-url]: https://github.com/Mantouisyummy/TYStream-DiscordBot/network/members

[stars-shield]: https://img.shields.io/github/stars/Mantouisyummy/TYStream-DiscordBot.svg?style=for-the-badge

[stars-url]: https://github.com/Mantouisyummy/TYStream-DiscordBot/stargazers

[issues-shield]: https://img.shields.io/github/issues/Mantouisyummy/TYStream-DiscordBot.svg?style=for-the-badge

[issues-url]: https://github.com/Mantouisyummy/TYStream-DiscordBot/issues

[license-shield]: https://img.shields.io/github/license/Mantouisyummy/TYStream-DiscordBot.svg?style=for-the-badge

[license-url]:https://github.com/Mantouisyummy/TYStream-DiscordBot/blob/master/LICENSE.txt