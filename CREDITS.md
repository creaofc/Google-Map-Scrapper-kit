# Credits & Attribution

This kit is a **wrapper** around an existing open-source project. The actual scraping engine is **not**
written by this kit's author — full credit goes to the original author.

## Upstream project

- **Project:** google-maps-scraper
- **Author:** **Georgios Komninos** ([@gosom](https://github.com/gosom))
- **Repository:** https://github.com/gosom/google-maps-scraper
- **License:** MIT License — Copyright (c) 2023 Georgios Komninos
- **Docker image used:** `gosom/google-maps-scraper`

This kit pulls and runs the official published Docker image. It does **not** modify or redistribute the
upstream source code — it only adds a Docker Compose setup, helper scripts, documentation, and a Claude
skill around it. All scraping capability and field extraction come from the upstream project.

## Upstream license (reproduced as required by MIT)

```
MIT License

Copyright (c) 2023 Georgios Komninos

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

If you found this useful, please **⭐ star the upstream repo** to support the original author:
https://github.com/gosom/google-maps-scraper
