# scraper_es
Scrapers für die Kantonsgerichtsentscheide

## Call example Code:

`$python3 example_scraper.py -p [DIRECTORY WITH THE SCRAPED DATA] -d [SPECIFIC CANTON DIRECTORY TO PROCESS] -f [FILETYPE TO PROCESS]`

## Structure for the resulting XML-Files:

```
<?xml version="1.0" encoding="UTF-8"?>
<text id="BGE20507" author="" title="BGE 6 I 206" source="Servat" page="206-212" topics="|Strafrecht|" subtopics="|Internationales Strafrecht und Rechtshilfe|" language="de" date="1880-05-08" description="Auslieferung von Verbrechern und Angeschuldigten" type="BGE" file="BGE6I206.pdf" year="1880" decade="1880" url="files/BGE6I206.xml">
```

tags to be used in the main part: `<header>, <body>, <p>, <pb>, <footnote> `

and ends with: `</text>`
