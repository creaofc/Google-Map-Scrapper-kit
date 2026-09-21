# Custom build: pre-installs the Playwright driver so no CDN download is needed.
# 
# Root cause: playwright-1.57.0-linux.zip was removed from playwright.azureedge.net.
# The gosom scraper tries to download it on every job → fails with 404.
#
# Fix: Install playwright@1.57.0 via npm, create a symlink to the package so that
# playwright-go finds the expected "package/cli.js", and set PLAYWRIGHT_NODEJS_PATH
# and PLAYWRIGHT_DRIVER_PATH so that it doesn't try to download anything.

FROM gosom/google-maps-scraper:latest

# Install Node.js runtime (Debian 13 trixie repos)
RUN apt-get update -q && \
    apt-get install -yq --no-install-recommends nodejs npm && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install playwright@1.57.0 via npm (still on npm registry)
RUN npm install -g playwright@1.57.0

# Set environment variables for playwright-go to locate the driver and node
ENV PLAYWRIGHT_DRIVER_PATH=/playwright-driver
ENV PLAYWRIGHT_NODEJS_PATH=/usr/bin/node
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright

# Create driver directory and link package so playwright-go finds package/cli.js
RUN mkdir -p /playwright-driver && \
    ln -s /usr/local/lib/node_modules/playwright /playwright-driver/package

# Pre-install Chromium browser so no download is needed at job runtime
RUN /usr/bin/node /usr/local/lib/node_modules/playwright/cli.js install chromium --with-deps

