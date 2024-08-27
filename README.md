<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/Nat1anWasTaken/Lava">
    <img src="img/logo.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">Lava</h3>

  <p align="center">
    由 Lavalink 驅動且擁有眾多功能且完全開源、免費的音樂機器人
    <br />
    <a href="#關於專案"><strong>閱讀更多 »</strong></a>
    <br />
    <br />
    <a href="README.en-us.md">English</a>
    ·
    <br />
    <a href="https://discord.gg/acgmcity">試用</a>
    ·
    <a href="https://discord.com/invite/3y7mN82NQa">支援群組</a>
    ·
    <a href="https://github.com/Nat1anWasTaken/Lava/issues">回報問題</a>
    ·
    <a href="https://github.com/Nat1anWasTaken/Lava/issues">請求功能</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>目錄</summary>
  <ol>
    <li>
      <a href="#螢幕截圖">螢幕截圖</a>
    </li>
    <li>
      <a href="#開始使用">開始使用</a>
      <ul>
        <li><a href="#spotify-支援">Spotify 支援</a></li>
        <li><a href="#需求">需求</a></li>
      </ul>
    </li>
    <li><a href="#用法">用法</a></li>
    <li><a href="#設定">設定</a></li>
    <li><a href="#計畫">計畫</a></li>
    <li><a href="#授權">授權</a></li>
    <li><a href="#貢獻">貢獻</a><li>
  </ol>
</details>

<!-- SCREENSHOTS -->

## 螢幕截圖

![播放器][player-screenshot]

<p align="right">(<a href="#readme-top">回到頂部</a>)</p>

<!-- GETTING STARTED -->

## 開始使用

如果你只是想體驗的話，你可以到 [Yeecord][yeecord] 直接使用裡面的 `Lava#8364`

### 一鍵架設

你可以透過 [LavaLauncher][LavaLauncher] 這個一鍵式腳本，你可以在裡面按照教學一步一步創建 Lavalink 節點 和 Discord 機器人

### Pterodactyl (翼手龍)
為了方便使用，我們提供 Pterodactyl Egg 並整合了 Lavalink 來方便架設 Lava 機器人

你可以透過 [這裡](https://github.com/Mantouisyummy/Lava-egg/blob/main/egg-lava.json) 來下載Lava的Egg檔案並匯入.

### Docker

<details>
<summary>Docker compose</summary>

確保 Docker 已經安裝在你的電腦或伺服器上，接著：

1. Clone 這個 Repository
```bash
git clone https://github.com/Nat1anWasTaken/Lava.git
```

2. cd 到專案目錄
```bash
cd Lava
```

3. 將 `example.stack.env` 重新命名為 `stack.env`
```bash
mv example.stack.env stack.env
```
填入 `stack.env` 的內容

4. 啟動
```bash
docker compose up
```
</details>

<details>
<summary>Docker CLI</summary>

確保 Docker 已經安裝在你的電腦或伺服器上，接著：

1. 拉取映像檔
```bash
docker pull ghcr.io/nat1anwastaken/lava:latest
```

2. 設置好你的 Lavalink 節點，並將其 IP 和 Port 填入 `configs/lavalink.json`，如果你懶得架設 Lavalink，請使用 Docker Compose
```json
{
    "host": "Lavalink 節點 IP",
    "port": "Lavalink 節點 Port"
}
```

3. 創建一個 `stac.env` 檔案，並填入以下內容
```env
TOKEN=機器人 Token
SPOTIFY_CLIENT_ID=Spotify client id
SPOTIFY_CLIENT_SECRET=Spotify client secret
``` 

4. 啟動機器人
```bash
docker run -it \
  --name ghcr.io/nat1anwastaken/lava:latest \
  --restart unless-stopped \
  lava
```

</details>

> 如果你有需要跳過 Spotify 自動設定 (`Go to the following url: ...`)，你可以將 `SKIP_SPOTIFY_SETUP` 設定為 `1`


<p align="right">(<a href="#readme-top">回到頂部</a>)</p>


<!-- USAGE EXAMPLES -->

## 用法

在成功架設起機器人並邀請進伺服器後，你可以直接使用 `/play` 指令播放音樂，就像上方的截圖一樣

每個指令的用途都寫在了指令描述裡，你可以透過他們來學會如何使用這個機器人

<p align="right">(<a href="#readme-top">回到頂部</a>)</p>

<!-- CONFIGURATION -->

## Lavalink 配置
> [!WARNING]  
> 由於 YouTube 的種種限制，必須填入一些驗證資訊才能使音樂服務正常工作，具體方式請詳閱下方教學。  

首先，請先使用 `pip install -r requirements.txt` 安裝所有必要的套件   
安裝完後進入到 Lava 的資料夾運行 `docker run quay.io/invidious/youtube-trusted-session-generator`  
運行後你會看到終端輸出以下內容：

```
visitor_data: your visitor_data
po_token: your po_token
```

打開 `configs/application.yml` 後找到以下配置資訊
```yml
plugins:
  youtube:
    pot:
      token: "paste your po_token here"
      visitorData: "paste your visitor_data here"
```
隨後將你獲得的 `po_token` 和 `visitor_data` 分別填入 `token` 和 `visitorData` 中即可完成配置

<p align="right">(<a href="#readme-top">回到頂部</a>)</p>

## 設定
Lava 提供了一些簡單的設定讓你能夠輕鬆地自定義你的音樂機器人，像是：

### 進度條 
你可以透過修改 `configs/icons.json` 來自定義進度條要使用的表情符號
```json
{
    "empty": "⬛",
    "progress": {
        "start_point": "⬜",
        "start_fill": "⬜",
        "mid_point": "⬜",
        "end_fill": "⬛",
        "end_point": "⬛",
        "end": "⬛"
    },
    "control": {
        "rewind": "⏪",
        "forward": "⏩",
        "pause": "⏸️",
        "resume": "▶️",
        "stop": "⏹️",
        "previous": "⏮️",
        "next": "⏭️",
        "shuffle": "🔀",
        "repeat": "🔁",
        "autoplay": "🔥"
    }
}
```

### 狀態
你可以透過修改 `configs/activity.json` 來自定義機器人的狀態
```json
{
    "type": 0, // 0: 正在玩, 1: 正在直播, 2: 正在聆聽, 3: 正在觀看
    "name": "音樂", // 狀態文字
    "url": "" // 直播連結（僅適用於直播狀態）
}
```

<p align="right">(<a href="#readme-top">回到頂部</a>)</p>


<!-- ROADMAP -->

## 計畫

計畫已遷移至 [Projects][projects]

<p align="right">(<a href="#readme-top">回到頂部</a>)</p>


<!-- LICENSE -->

## 授權

這個專案基於 MIT License，查看 `LICENSE.txt` 來獲取更多資訊

<!-- CONTRIBUTE -->

## 貢獻

你可以前往 [CONTRUBUTING.md](CONTRIBUTING.md) 來查看完整的貢獻指南

<!-- SHIELDS -->

[contributors-shield]: https://img.shields.io/github/contributors/Nat1anWasTaken/Lava.svg?style=for-the-badge

[contributors-url]: https://github.com/Nat1anWasTaken/Lava/graphs/contributors

[forks-shield]: https://img.shields.io/github/forks/Nat1anWasTaken/Lava.svg?style=for-the-badge

[forks-url]: https://github.com/Nat1anWasTaken/Lava/network/members

[stars-shield]: https://img.shields.io/github/stars/Nat1anWasTaken/Lava.svg?style=for-the-badge

[stars-url]: https://github.com/Nat1anWasTaken/Lava/stargazers

[issues-shield]: https://img.shields.io/github/issues/Nat1anWasTaken/Lava.svg?style=for-the-badge

[issues-url]: https://github.com/Nat1anWasTaken/Lava/issues

[license-shield]: https://img.shields.io/github/license/Nat1anWasTaken/Lava.svg?style=for-the-badge

[license-url]: https://github.com/Nat1anWasTaken/Lava/blob/master/LICENSE.txt

<!-- LINKS -->

[yeecord]: https://discord.gg/yeecord

[python]: https://python.org

[lavalink]: https://github.com/freyacodes/Lavalink

[projects]: https://github.com/users/Nat1anWasTaken/projects/3

[LavaLauncher]: https://github.com/Nat1anWasTaken/LavaLauncher

[spotipy-authorization-flow]: https://spotipy.readthedocs.io/en/2.22.0/#authorization-code-flow

[issues]: https://github.com/Nat1anWasTaken/Lava/issues

<!-- IMAGES -->

[player-screenshot]: img/player.png
