# Investeringsuitgaven Gemeenten

Visualisatie van de gemeentelijke investeringsuitgaven in Vlaanderen (2014-2024).

## Bron

Bron: Agentschap Binnenlands Bestuur, verwerking Embuild Vlaanderen

## GitHub Pages Setup

Om deze website via GitHub Pages te publiceren:

1. Maak een nieuwe GitHub repository aan (bijvoorbeeld `investeringsuitgaven-gemeenten`)
2. Push de code naar GitHub:
   ```bash
   git remote add origin https://github.com/JOUW-GEBRUIKERSNAAM/investeringsuitgaven-gemeenten.git
   git branch -M main
   git push -u origin main
   ```
3. Ga naar Settings > Pages in je GitHub repository
4. Selecteer "Deploy from a branch"
5. Kies de branch `main` en de folder `/longread_output`
6. Klik op "Save"
7. De website zal beschikbaar zijn op: `https://JOUW-GEBRUIKERSNAAM.github.io/investeringsuitgaven-gemeenten/`

## Lokale ontwikkeling

Open `longread_output/index.html` in een browser of gebruik een lokale server:

```bash
cd longread_output
python -m http.server 8000
```

Open dan http://localhost:8000 in je browser.

