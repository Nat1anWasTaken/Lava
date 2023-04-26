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
    <a href="https://discord.gg/acgmcity">試用</a>
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
    <li><a href="#計畫">計畫</a></li>
    <li><a href="#授權">授權</a></li>
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

### Docker

確保 Docker 已經安裝在你的電腦或伺服器上，接著：

1. Clone 這個 Repository
```bash
git clone https://github.com/Nat1anWasTaken/Lava.git
```

2. cd 到專案目錄
```bash
cd Lava
```

3. 將 `.env.example` 重新命名為 `.env`
```bash
mv .env.example .env
```
填入 `.env` 的內容

4. 啟動
```bash
docker-compose up
```


<p align="right">(<a href="#readme-top">回到頂部</a>)</p>


<!-- USAGE EXAMPLES -->

## 用法

在成功架設起機器人並邀請進伺服器後，你可以直接使用 `/play` 指令播放音樂，就像上方的截圖一樣

每個指令的用途都寫在了指令描述裡，你可以透過他們來學會如何使用這個機器人

<p align="right">(<a href="#readme-top">回到頂部</a>)</p>


<!-- ROADMAP -->

## 計畫

- [ ] 新增更多音樂平台
  - [x] YouTube
  - [x] Spotify
  - [x] SoundCloud
  - [x] Bilibili
  - [x] YouTube-DL
  - [ ] Apple Music
    ...
- [ ] 增加穩定性

如果你發現了任何問題，歡迎至 [Issues][issues] 提出問題

<p align="right">(<a href="#readme-top">回到頂部</a>)</p>


<!-- LICENSE -->

## 授權

這個專案基於 MIT License，查看 `LICENSE.txt` 來獲取更多資訊

<p align="right">(<a href="#readme-top">回到頂部</a>)</p>

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

[LavaLauncher]: https://github.com/Nat1anWasTaken/LavaLauncher

[spotipy-authorization-flow]: https://spotipy.readthedocs.io/en/2.22.0/#authorization-code-flow

[issues]: https://github.com/Nat1anWasTaken/Lava/issues

<!-- IMAGES -->

[player-screenshot]: img/player.png