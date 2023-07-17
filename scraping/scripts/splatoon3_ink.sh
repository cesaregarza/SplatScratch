poetry run python scraping/splatoon3_ink/splatoon3_ink.py
poetry run scrapy runspider scraping/splatoon3_ink/splatoon3_ink_scrapy.py
rm all_links.txt
echo "Splatoon3 Ink scraping done"