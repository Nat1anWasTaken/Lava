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
    Multi funtion free & open source Discord music bot powered by Lavalink
    <br />
    <a href="#About Project"><strong>Read more »</strong></a>
    <br />
    <br />
    <a href="README.md">中文</a>
    ·
    <br />
    <a href="https://discord.gg/acgmcity">Try it out!(Chinese server)</a>
    ·
    <a href="https://github.com/Nat1anWasTaken/Lava/issues">Bug report</a>
    ·
    <a href="https://github.com/Nat1anWasTaken/Lava/issues">Request new features</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of contents</summary>
  <ol>
    <li>
      <a href="#screenshots">Screenshots</a>
    </li>
    <li>
      <a href="#get-started">Get started</a>
      <ul>
        <li><a href="#spotify-support">Spotify Support</a></li>
        <li><a href="#requirements">Requirements</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#configs">Configs</a></li>
    <li><a href="todo">ToDo</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contributing">Contributing</a><li>
  </ol>
</details>

<!-- SCREENSHOTS -->

## Screenshots

![player][player-screenshot-en]

<p align="right">(<a href="#readme-top">Back to top</a>)</p>

<!-- GETTING STARTED -->

## Get started

If you just want to experiment what the bot is like, you can join [Yeecord(Chinese)][yeecord] and use `Lava#8364` there

### One click setup

You can use this one click script [LavaLauncher][LavaLauncher], and follow the steps to setup Lavalink and the Discord bot
### Docker

<details>
<summary>Docker compose</summary>

Make sure that Docker is installed on your computer or server already then:

1. Clone this Repository
```bash
git clone https://github.com/Nat1anWasTaken/Lava.git
```

2. cd to project directory
```bash
cd Lava
```

3. Rename `example.stack.env` to `stack.env`
```bash
mv example.stack.env stack.env
```
Fill out `stack.env` 

4. Launch
```bash
docker compose up
```
</details>

<details>
<summary>Docker CLI</summary>

Make sure that Docker is installed on your computer or server already then:

1. Pull the image
```bash
docker pull ghcr.io/nat1anwastaken/lava:latest
```

2. Setup Lavalink, then fill IP and Port into `configs/lavalink.json`, if you're lazy to setup Lavalink, please use Docker Compose instead
```json
{
    "host": "Lavalink IP",
    "port": "Lavalink Port"
}
```

3. Create `stac.env` file, and fill in the following
```env
TOKEN=Bot Token
SPOTIFY_CLIENT_ID=Spotify client id
SPOTIFY_CLIENT_SECRET=Spotify client secret
``` 

4. Start to bot
```bash
docker run -it \
  --name ghcr.io/nat1anwastaken/lava:latest \
  --restart unless-stopped \
  lava
```


</details>

> If you need to skip Spotify auto setup (`Go to the following url: ...`), you can set `SKIP_SPOTIFY_SETUP` to `1`


<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- USAGE EXAMPLES -->

## Usage

After setting up the bot and invited it into your server, you can use `/play` to play music, as like in the example screenshot

Every command usage is explained in command description, you can learn how to use this bot by reading them

<p align="right">(<a href="#readme-top">Back to top</a>)</p>


<!-- CONFIGURATION -->

## Configs
Lava provided a few simple customizble configs for you to custom your bot to your likings such as:

### Progress bar
You can modify `configs/icons.json` to set custom emoji for progress bar
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

### Status
You can modify `configs/activity.json` to set custom status
```json
{
    "type": 0, // 0: Playing, 1: Streaming, 2: Listing, 3: Watching
    "name": "Music", // Status text
    "url": "" // Stream link (Only when using streaming staus)
}
```

<p align="right">(<a href="#readme-top">Back to top</a>)</p>


<!-- ROADMAP -->

## ToDo

ToDo has been moved to [Projects][projects]

<p align="right">(<a href="#readme-top">Back to top</a>)</p>


<!-- LICENSE -->

## License

This project is licensed under MIT License, check `LICENSE.txt` for more information

<p align="right">(<a href="#readme-top">Back to top</a>)</p>

<!-- CONTRIBUTE -->

## Contributing

Head to [CONTRUBUTING.md](CONTRIBUTING.md) for detail


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

[player-screenshot-en]: img/player-en.png
