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

你也可以透過以下步驟自己架起這台機器人

1. 確保你擁有 [需求](#需求) 裡面的所有東西
2. 將這個 Repository 複製下來
    ```shell
    $ git clone https://github.com/Nat1anWasTaken/Lava.git
    ```
3. 設定當前環境中的變數
    ```env
    TOKEN = 你的機器人 Token
    SPOTIFY_CLIENT_ID = Spotify Client ID
    SPOTIFY_CLIENT_SECRET = Spotify Client Secret
    SPOTIPY_REDIRECT_URI = Redirect URI
    ```
   > `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIPY_REDIRECT_URI` 不是必須的，只有在你想要啟用 Spotify 以及 自動播放
   時才需要提供
4. 將 `configs/` 中的兩個 `.json` 檔案名稱中的 `.example` 刪除，並填入其中內容
  * `lavalink.json`
      ```json
      {
          "nodes": [
              {
                  "host": "localhost",
                  "port": 2333,
                  "password": "password",
                  "name": "test",
                  "region": "us"
              }
          ]
      }
      ```
  * `icons.json`
      ```json
      {
          "empty": "<:empty:1051781423067058197>",
          "progress": {
              "start_point": "<:start_point:1051765647606034462>",
              "start_fill": "<:start_fill:1051765646163202058>",
              "mid_point": "<:mid_point:1051765644363837442>",
              "end_fill": "<:end_fill:1051765641545269299>",
              "end_point": "<:end_point:1051765643172646922>",
              "end": "<:end:1051765640039497748>"
          },
          "control": {
              "rewind": "<:rewind_10:987663342766288936>",
              "forward": "<:forward_10:987663192979288134>",
              "pause": "<:pause:987661771609358366>",
              "resume": "<:play:987643956403781692>",
              "stop": "<:stop:987645074450034718>",
              "previous": "<:previous:987652154133213274>",
              "next": "<:skip:987641543441678416>",
              "shuffle": "<:shuffle:987653133306064908>",
              "repeat": "<:loop:987650404764508200>",
              "autoplay": "<:autoplay:1056145730596769872>"
          }
      }
      ```
5. 安裝必要的前置項
    ```shell
    $ pip install -r requirements.txt
    ```
6. 啟動 `main.py`
    ```shell
    $ python main.py
    ```

### Spotify 支援

要啟用對 `Spotify` 以及 `自動播放`
的支援，你得提供上述的三個環境變數，並在啟動時遵照 [Spotipy Documentation](spotipy-authorization-flow) 中的步驟執行授權

### 需求

* [Python 3.10+][python]
* 一個或以上已經建置好的 [Lavalink][lavalink] 節點

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

[spotipy-authorization-flow]: https://spotipy.readthedocs.io/en/2.22.0/#authorization-code-flow

[issues]: https://github.com/Nat1anWasTaken/Lava/issues

<!-- IMAGES -->

[player-screenshot]: img/player.png