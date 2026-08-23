#!/bin/bash
# DikaAi Web Scraper
echo "🌐 Scraping Indonesian web content..."
cd ~/DikaAi
python -c "from webscraper import run_web_scrape; run_web_scrape()"
echo "✅ Done! Restart DikaAi to train on new data."
