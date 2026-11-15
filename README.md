# spin-finance

[![Sponsor](https://img.shields.io/badge/Sponsor-fitzyracing1-ea4aaa?logo=githubsponsors)](https://github.com/sponsors/fitzyracing1)
[![test](https://github.com/fitzyracing1/spin-finance/actions/workflows/test.yml/badge.svg)](https://github.com/fitzyracing1/spin-finance/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Invoice totals, late fees, and loan payments with exact Decimal math. Same input, same answer, no API, no cost, works offline.

All money is `Decimal`, rounded half-up to cents. There is no floating-point money math.

```sh
python finance.py invoice --item 'Widget,3,10.00' --item 'Fee,1,2.50' --tax 8%
python finance.py invoice --csv items.csv --tax 0.08
python finance.py late-fee --principal 1000 --annual-rate 0.18 --days 15
python finance.py late-fee --principal 1000 --monthly-rate 0.015 --days 45
python finance.py late-fee --principal 1000 --flat 25 --days 10
python finance.py loan --principal 10000 --annual-rate 0.05 --term 36 --amortization
```

Late fees are simple interest (or a flat amount), not compound. Loan payments use the standard fixed installment formula; the last payment is adjusted so the balance lands on 0.00.

## Run it

It's plain Python 3 with no packages to install, so it runs anywhere Python does.

```sh
gh repo clone fitzyracing1/spin-finance
cd spin-finance
python finance.py
python -m pytest -q
```

### Windows (PowerShell)
```powershell
winget install Python.Python.3.12 GitHub.cli
gh auth login
gh repo clone fitzyracing1/spin-finance; cd spin-finance; py finance.py
```

### Mac
```sh
brew install python gh && gh auth login
gh repo clone fitzyracing1/spin-finance && cd spin-finance && python3 finance.py
```

### Linux
```sh
sudo apt install -y python3 gh && gh auth login
gh repo clone fitzyracing1/spin-finance && cd spin-finance && python3 finance.py
```

### Termux (Android)
```sh
pkg install -y python git gh && gh auth login
gh repo clone fitzyracing1/spin-finance ~/spin-finance && cd ~/spin-finance && python finance.py
```

## Support this project

spin-finance is free and MIT licensed. If it saves you time, please [sponsor me on GitHub](https://github.com/sponsors/fitzyracing1). It keeps the tools coming.

| Plan | Price | What you get |
| --- | --- | --- |
| Free | $0 | Everything in this repo, forever |
| Pro | $49/month | Priority issues and help adding your own tools |
| Team | $199/month | Custom tools built for your team, plus Pro |

Plans are paid through [GitHub Sponsors](https://github.com/sponsors/fitzyracing1). You can also star the repo, share it, or open an issue with a tool idea.

## Author

Built by Joshua Almeida ([@fitzyracing1](https://x.com/fitzyracing1), [fitzyracing1.com](https://fitzyracing1.com), [GitHub](https://github.com/fitzyracing1)).

## License

[MIT](LICENSE) © 2026 Joshua Almeida
